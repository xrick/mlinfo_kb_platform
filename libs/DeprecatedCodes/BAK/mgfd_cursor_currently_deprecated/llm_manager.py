#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD LLM 管理器
支援多種 LLM 提供商和緩存功能
"""

import logging
import hashlib
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import os

# Import availability tracking
OLLAMA_AVAILABLE = False
OPENAI_AVAILABLE = False
ANTHROPIC_AVAILABLE = False

try:
    from langchain_ollama import OllamaLLM
    OLLAMA_AVAILABLE = True
except ImportError:
    pass

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    pass

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass

LANGCHAIN_AVAILABLE = OLLAMA_AVAILABLE or OPENAI_AVAILABLE or ANTHROPIC_AVAILABLE

class MGFDLLMManager:
    """MGFD LLM 管理器"""
    
    def __init__(self, 
                 provider: str = "ollama",
                 model_name: str = "deepseek-r1:7b",
                 temperature: float = 0.1,
                 max_tokens: int = 1000,
                 cache_enabled: bool = True,
                 cache_ttl: int = 3600):
        """
        初始化 LLM 管理器
        
        Args:
            provider: LLM 提供商 (ollama/openai/anthropic)
            model_name: 模型名稱
            temperature: 溫度參數
            max_tokens: 最大 token 數
            cache_enabled: 是否啟用緩存
            cache_ttl: 緩存過期時間 (秒)
        """
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        
        self.logger = logging.getLogger(__name__)
        self.llm = None
        self._response_cache: Dict[str, Dict[str, Any]] = {}
        self.principal_prompt: Optional[str] = None
        self.ai_coder_prompt: Optional[str] = None
        # 延遲載入器，避免循環依賴
        self._config_loader = None
        
        # 初始化 LLM
        self._initialize_llm()
        # 載入主提示
        self._load_principal_prompt()
        # 載入 AI Coder 提示
        self._load_ai_coder_prompt()
    
    def _initialize_llm(self):
        """初始化 LLM"""
        if not LANGCHAIN_AVAILABLE:
            self.logger.warning("所有 LangChain 提供商套件都不可用，將使用模擬 LLM")
            return
        
        try:
            if self.provider == "ollama":
                if not OLLAMA_AVAILABLE:
                    self.logger.warning("langchain-ollama 套件不可用，將使用模擬 LLM")
                    return
                self.llm = OllamaLLM(
                    model=self.model_name,
                    temperature=self.temperature
                )
            elif self.provider == "openai":
                if not OPENAI_AVAILABLE:
                    self.logger.warning("langchain-openai 套件不可用，將使用模擬 LLM")
                    return
                self.llm = ChatOpenAI(
                    model=self.model_name,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
            elif self.provider == "anthropic":
                if not ANTHROPIC_AVAILABLE:
                    self.logger.warning("langchain-anthropic 套件不可用，將使用模擬 LLM")
                    return
                self.llm = ChatAnthropic(
                    model=self.model_name,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
            else:
                raise ValueError(f"不支援的 LLM 提供商: {self.provider}")
            
            self.logger.info(f"成功初始化 {self.provider} LLM: {self.model_name}")
            
        except Exception as e:
            self.logger.error(f"初始化 {self.provider} LLM 失敗: {e}")
            self.llm = None

    # ===== 主提示與模板構建 =====
    def _ensure_config_loader(self):
        if self._config_loader is None:
            try:
                from .config_loader import MGFDConfigLoader
                self._config_loader = MGFDConfigLoader()
            except Exception as e:
                self.logger.warning(f"初始化配置載入器失敗: {e}")
                self._config_loader = None

    def _load_principal_prompt(self, custom_path: Optional[str] = None):
        """載入主提示 (HumanData/PromptsHub/MGFD_Principal_Prompts/MGFD_Principal_Prompt_20250821.txt)"""
        try:
            if custom_path:
                path = Path(custom_path)
            else:
                # 專案根目錄 = libs/mgfd_cursor/../../
                root = Path(__file__).resolve().parents[2]
                path = root / 'HumanData' / 'PromptsHub' / 'MGFD_Principal_Prompts' / 'MGFD_Principal_Prompt_20250821.txt'
            if path.exists():
                self.principal_prompt = path.read_text(encoding='utf-8')
                self.logger.info(f"已載入主提示: {path}")
            else:
                self.logger.warning(f"主提示不存在: {path}")
        except Exception as e:
            self.logger.warning(f"載入主提示失敗: {e}")
            self.principal_prompt = None

    def _load_ai_coder_prompt(self, custom_path: Optional[str] = None):
        """載入 AI Coder 獨立初始化提示 (HumanData/PromptsHub/MGFD_Principal_Prompts/ai_coder_indepnedent_initialization_prompt.txt)"""
        try:
            if custom_path:
                path = Path(custom_path)
            else:
                # 專案根目錄 = libs/mgfd_cursor/../../
                root = Path(__file__).resolve().parents[2]
                path = root / 'HumanData' / 'PromptsHub' / 'MGFD_Principal_Prompts' / 'ai_coder_indepnedent_initialization_prompt.txt'
            if path.exists():
                self.ai_coder_prompt = path.read_text(encoding='utf-8')
                self.logger.info(f"已載入 AI Coder 提示: {path}")
            else:
                self.logger.warning(f"AI Coder 提示不存在: {path}")
        except Exception as e:
            self.logger.warning(f"載入 AI Coder 提示失敗: {e}")
            self.ai_coder_prompt = None

    def build_think_prompt(self, instruction: str, context: Dict[str, Any]) -> str:
        """組裝 Think 階段提示，夾帶主提示與模板。"""
        self._ensure_config_loader()
        think_cfg = {}
        if self._config_loader:
            think_cfg = self._config_loader.get_think_prompts() or {}
        
        # 選擇性讀取特定槽位或場景的模板
        selected_template = self._select_think_template(instruction, context, think_cfg)
        
        principal = self.principal_prompt or ''
        # 標記關鍵字以支援 _mock_response 測試
        marker = "槽位分析"
        
        # 如果有選中的特定模板，使用它；否則使用通用模板
        if selected_template:
            prompt = (
                f"{principal}\n\n[Think:{marker}]\n"
                f"{selected_template}\n"
                f"Context: {json.dumps(context, ensure_ascii=False)}\n"
            )
        else:
            prompt = (
                f"{principal}\n\n[Think:{marker}]\n"
                f"Instruction: {instruction}\n"
                f"Context: {json.dumps(context, ensure_ascii=False)}\n"
                f"Output: 僅輸出 JSON，包含 extracted_slots 與 reasoning。"
            )
        
        return prompt

    def _select_think_template(self, instruction: str, context: Dict[str, Any], think_cfg: Dict[str, Any]) -> Optional[str]:
        """根據指令和上下文選擇合適的 Think 模板"""
        # 檢查是否為槽位分析
        if "槽位" in instruction or "slot" in instruction.lower():
            # 嘗試根據目標槽位選擇特定模板
            target_slot = self._extract_target_slot_from_context(context)
            if target_slot:
                slot_templates = think_cfg.get("slot_analysis_by_slot", {})
                if target_slot in slot_templates:
                    template_config = slot_templates[target_slot]
                    template = template_config.get("template", "")
                    # 替換模板變數
                    return self._replace_template_variables(template, context)
        
        # 檢查是否為行動決策
        if "行動" in instruction or "action" in instruction.lower() or "決策" in instruction:
            # 根據場景選擇決策模板
            scene = self._identify_decision_scene(context)
            if scene:
                scene_templates = think_cfg.get("action_decision_by_scene", {})
                if scene in scene_templates:
                    template_config = scene_templates[scene]
                    template = template_config.get("template", "")
                    return self._replace_template_variables(template, context)
        
        return None

    def _extract_target_slot_from_context(self, context: Dict[str, Any]) -> Optional[str]:
        """從上下文中提取目標槽位"""
        # 檢查是否有明確的目標槽位
        if "target_slot" in context:
            return context["target_slot"]
        
        # 檢查缺失的槽位
        missing_slots = context.get("missing_slots", [])
        if missing_slots:
            return missing_slots[0]
        
        # 檢查已填寫的槽位，推測下一個目標
        filled_slots = context.get("filled_slots", {})
        required_slots = ["usage_purpose", "budget_range", "brand_preference"]
        for slot in required_slots:
            if slot not in filled_slots:
                return slot
        
        return None

    def _identify_decision_scene(self, context: Dict[str, Any]) -> Optional[str]:
        """識別決策場景"""
        missing_slots = context.get("missing_slots", [])
        filled_slots = context.get("filled_slots", {})
        user_input = context.get("user_input", "")
        
        # 檢查是否為缺失必要槽位場景
        if missing_slots:
            return "missing_required_slot"
        
        # 檢查是否為模糊輸入場景
        if len(user_input.strip()) < 5 or any(word in user_input.lower() for word in ["不知道", "隨便", "都可以"]):
            return "ambiguous_input"
        
        return None

    def _replace_template_variables(self, template: str, context: Dict[str, Any]) -> str:
        """替換模板中的變數"""
        # 簡單的變數替換
        result = template
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                if isinstance(value, (list, dict)):
                    result = result.replace(placeholder, json.dumps(value, ensure_ascii=False))
                else:
                    result = result.replace(placeholder, str(value))
        
        return result

    def build_action_decision_prompt(self, instruction: str, context: Dict[str, Any]) -> str:
        """組裝行動決策提示，夾帶主提示與模板。"""
        self._ensure_config_loader()
        act_cfg = {}
        if self._config_loader:
            act_cfg = self._config_loader.get_act_prompts() or {}
        
        # 選擇性讀取特定場景的模板
        selected_template = self._select_act_template(instruction, context, act_cfg)
        
        principal = self.principal_prompt or ''
        marker = "行動決策"
        
        if selected_template:
            prompt = (
                f"{principal}\n\n[Think:{marker}]\n"
                f"{selected_template}\n"
                f"Context: {json.dumps(context, ensure_ascii=False)}\n"
            )
        else:
            prompt = (
                f"{principal}\n\n[Think:{marker}]\n"
                f"Instruction: {instruction}\n"
                f"Context: {json.dumps(context, ensure_ascii=False)}\n"
                f"Output: 僅輸出 JSON，包含 action、target_slot、reasoning、confidence。"
            )
        
        return prompt

    def _select_act_template(self, instruction: str, context: Dict[str, Any], act_cfg: Dict[str, Any]) -> Optional[str]:
        """根據指令和上下文選擇合適的 Act 模板"""
        # 檢查是否為槽位詢問
        if "詢問" in instruction or "elicit" in instruction.lower():
            target_slot = self._extract_target_slot_from_context(context)
            if target_slot:
                slot_templates = act_cfg.get("slot_elicitation_by_slot", {})
                if target_slot in slot_templates:
                    template_config = slot_templates[target_slot]
                    template = template_config.get("template", "")
                    return self._replace_template_variables(template, context)
        
        # 檢查是否為澄清請求
        if "澄清" in instruction or "clarify" in instruction.lower():
            scene = self._identify_clarification_scene(context)
            if scene:
                scene_templates = act_cfg.get("clarification_by_scene", {})
                if scene in scene_templates:
                    template_config = scene_templates[scene]
                    template = template_config.get("template", "")
                    return self._replace_template_variables(template, context)
        
        return None

    def _identify_clarification_scene(self, context: Dict[str, Any]) -> Optional[str]:
        """識別澄清場景"""
        user_input = context.get("user_input", "")
        
        # 檢查是否同時提到系列和目的
        series_keywords = ["958", "928", "AC01", "系列", "比較"]
        purpose_keywords = ["遊戲", "工作", "學習", "商務", "辦公"]
        
        has_series = any(keyword in user_input for keyword in series_keywords)
        has_purpose = any(keyword in user_input for keyword in purpose_keywords)
        
        if has_series and has_purpose:
            return "series_vs_purpose"
        
        return None
    
    def classify_slot(self, prompt: str) -> str:
        """
        使用LLM進行槽位分類
        
        Args:
            prompt: 槽位分類提示詞
            
        Returns:
            分類結果JSON字符串
        """
        try:
            self.logger.info("執行槽位分類...")
            
            # 使用緩存檢查
            if self.cache_enabled:
                cache_key = self._generate_cache_key(prompt, {})
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    self.logger.info("從緩存返回槽位分類結果")
                    return cached_result
            
            # 調用LLM
            result = self._call_llm(prompt)
            
            # 緩存結果
            if self.cache_enabled and result:
                self._save_to_cache(cache_key, result)
            
            self.logger.info("槽位分類完成")
            return result
            
        except Exception as e:
            self.logger.error(f"槽位分類失敗: {e}")
            # 返回未知分類的默認結果
            return json.dumps({
                "classified_slot": "unknown",
                "confidence": 0.0,
                "extracted_value": None,
                "reasoning": f"分類過程中出現錯誤: {str(e)}",
                "alternative_slots": []
            }, ensure_ascii=False)

    def analyze_slots(self, user_input: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """使用 Think 提示進行槽位分析，回傳 JSON 結果。"""
        instruction = "根據使用者輸入，從既有槽位架構中抽取可能值，並附上信心分數。"
        context = {
            "user_input": user_input,
            "filled_slots": state.get("filled_slots", {}),
        }
        prompt = self.build_think_prompt(instruction, context)
        raw = self.invoke(prompt)
        try:
            return json.loads(raw)
        except Exception:
            # 異常時回退格式
            return {"extracted_slots": {}, "reasoning": "fallback"}

    def decide_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """使用 Think 提示進行行動決策，回傳 JSON 結果。"""
        instruction = "基於缺失的必要槽位，決定下一步行動（如 ELICIT_INFORMATION），並指定 target_slot。"
        context = {
            "filled_slots": state.get("filled_slots", {}),
            "required_slots": list(getattr(state, 'required_slots', ['usage_purpose','budget_range'])),
        }
        prompt = self.build_action_decision_prompt(instruction, context)
        raw = self.invoke(prompt)
        try:
            return json.loads(raw)
        except Exception:
            return {"action": "ELICIT_INFORMATION", "target_slot": "budget_range", "reasoning": "fallback", "confidence": 0.5}
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """
        調用 LLM
        
        Args:
            prompt: 提示詞
            **kwargs: 額外參數
            
        Returns:
            LLM 回應
        """
        # 檢查緩存
        cache_key = self._generate_cache_key(prompt, kwargs)
        if self.cache_enabled and cache_key in self._response_cache:
            cached_response = self._response_cache[cache_key]
            if self._is_cache_valid(cached_response):
                self.logger.debug("使用緩存的 LLM 回應")
                return cached_response["response"]
        
        # 調用 LLM
        try:
            if self.llm is None:
                # 模擬回應
                response = self._mock_response(prompt)
            else:
                response = self.llm.invoke(prompt, **kwargs)
                if hasattr(response, 'content'):
                    response = response.content
                elif hasattr(response, 'text'):
                    response = response.text
                else:
                    response = str(response)
            
            # 緩存回應
            if self.cache_enabled:
                self._cache_response(cache_key, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"LLM 調用失敗: {e}")
            return self._get_fallback_response(prompt)
    
    def invoke_with_cache(self, prompt: str, cache_key: Optional[str] = None, **kwargs) -> str:
        """
        帶緩存的 LLM 調用
        
        Args:
            prompt: 提示詞
            cache_key: 自定義緩存鍵
            **kwargs: 額外參數
            
        Returns:
            LLM 回應
        """
        if cache_key is None:
            cache_key = self._generate_cache_key(prompt, kwargs)
        
        # 檢查緩存
        if self.cache_enabled and cache_key in self._response_cache:
            cached_response = self._response_cache[cache_key]
            if self._is_cache_valid(cached_response):
                self.logger.debug("使用緩存的 LLM 回應")
                return cached_response["response"]
        
        # 調用 LLM
        response = self.invoke(prompt, **kwargs)
        
        # 緩存回應
        if self.cache_enabled:
            self._cache_response(cache_key, response)
        
        return response
    
    def invoke_structured(self, prompt: str, expected_format: str = "json", **kwargs) -> Dict[str, Any]:
        """
        結構化 LLM 調用
        
        Args:
            prompt: 提示詞
            expected_format: 期望的輸出格式
            **kwargs: 額外參數
            
        Returns:
            結構化回應
        """
        # 添加格式要求到提示詞
        if expected_format == "json":
            prompt += "\n\n請以 JSON 格式回應。"
        elif expected_format == "list":
            prompt += "\n\n請以列表格式回應。"
        
        response = self.invoke(prompt, **kwargs)
        
        # 解析結構化回應
        try:
            if expected_format == "json":
                return json.loads(response)
            elif expected_format == "list":
                # 簡單的列表解析
                lines = response.strip().split('\n')
                return [line.strip() for line in lines if line.strip()]
            else:
                return {"raw_response": response}
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON 解析失敗: {e}")
            return {"raw_response": response, "parse_error": str(e)}
    
    def _generate_cache_key(self, prompt: str, kwargs: Dict[str, Any]) -> str:
        """生成緩存鍵"""
        content = f"{prompt}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _cache_response(self, cache_key: str, response: str):
        """緩存回應"""
        self._response_cache[cache_key] = {
            "response": response,
            "timestamp": datetime.now().timestamp(),
            "ttl": self.cache_ttl
        }
        
        # 清理過期緩存
        self._cleanup_expired_cache()
    
    def _is_cache_valid(self, cached_response: Dict[str, Any]) -> bool:
        """檢查緩存是否有效"""
        timestamp = cached_response.get("timestamp", 0)
        ttl = cached_response.get("ttl", self.cache_ttl)
        
        current_time = datetime.now().timestamp()
        return (current_time - timestamp) < ttl
    
    def _cleanup_expired_cache(self):
        """清理過期緩存"""
        current_time = datetime.now().timestamp()
        expired_keys = []
        
        for key, cached_response in self._response_cache.items():
            if not self._is_cache_valid(cached_response):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._response_cache[key]
        
        if expired_keys:
            self.logger.debug(f"清理了 {len(expired_keys)} 個過期緩存")
    
    def _mock_response(self, prompt: str) -> str:
        """模擬 LLM 回應（用於測試）"""
        if "槽位分析" in prompt or "slot_analysis" in prompt:
            return json.dumps({
                "extracted_slots": {
                    "usage_purpose": {
                        "value": "business",
                        "confidence": 0.8
                    }
                },
                "reasoning": "用戶提到工作相關需求"
            })
        elif "行動決策" in prompt or "action_decision" in prompt:
            return json.dumps({
                "action": "ELICIT_INFORMATION",
                "target_slot": "budget_range",
                "reasoning": "需要收集預算信息",
                "confidence": 0.9
            })
        else:
            return "這是一個模擬的 LLM 回應。"
    
    def _get_fallback_response(self, prompt: str) -> str:
        """獲取回退回應"""
        if "錯誤" in prompt or "error" in prompt.lower():
            return "抱歉，系統暫時無法處理您的請求，請稍後再試。"
        elif "問候" in prompt or "greeting" in prompt.lower():
            return "您好！我是您的筆電購物助手，很高興為您服務。"
        else:
            return "我理解您的需求，讓我為您提供協助。"
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取緩存統計信息"""
        current_time = datetime.now().timestamp()
        valid_cache_count = 0
        expired_cache_count = 0
        
        for cached_response in self._response_cache.values():
            if self._is_cache_valid(cached_response):
                valid_cache_count += 1
            else:
                expired_cache_count += 1
        
        return {
            "total_cache_entries": len(self._response_cache),
            "valid_cache_entries": valid_cache_count,
            "expired_cache_entries": expired_cache_count,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl
        }
    
    def clear_cache(self):
        """清理所有緩存"""
        self._response_cache.clear()
        self.logger.info("已清理所有 LLM 緩存")
    
    def update_config(self, 
                     provider: Optional[str] = None,
                     model_name: Optional[str] = None,
                     temperature: Optional[float] = None,
                     max_tokens: Optional[int] = None,
                     cache_enabled: Optional[bool] = None,
                     cache_ttl: Optional[int] = None):
        """更新配置"""
        if provider is not None:
            self.provider = provider
        if model_name is not None:
            self.model_name = model_name
        if temperature is not None:
            self.temperature = temperature
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if cache_enabled is not None:
            self.cache_enabled = cache_enabled
        if cache_ttl is not None:
            self.cache_ttl = cache_ttl
        
        # 重新初始化 LLM
        self._initialize_llm()
        self.logger.info("LLM 配置已更新")
    
    def get_ai_coder_prompt(self) -> Optional[str]:
        """獲取 AI Coder 提示"""
        return self.ai_coder_prompt

    def get_status(self) -> Dict[str, Any]:
        """獲取 LLM 狀態"""
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "llm_available": self.llm is not None,
            "ai_coder_prompt_loaded": self.ai_coder_prompt is not None,
            "provider_availability": {
                "ollama": OLLAMA_AVAILABLE,
                "openai": OPENAI_AVAILABLE,
                "anthropic": ANTHROPIC_AVAILABLE,
                "langchain_available": LANGCHAIN_AVAILABLE
            },
            "cache_stats": self.get_cache_stats()
        }

    def think_phase(self, instruction: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Think階段：生成結構化指令
        
        Args:
            instruction: 指令內容
            context: 上下文信息
            
        Returns:
            結構化指令
        """
        try:
            # 構建Think階段提示詞
            prompt = self._build_think_prompt(instruction, context)
            
            # 調用LLM
            response = self.invoke(prompt)
            
            # 解析回應
            result = self._parse_think_response(response)
            
            self.logger.info(f"Think階段結果: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Think階段失敗: {e}")
            return {
                "action": "ELICIT_SLOT",
                "target_slot": "usage_purpose",
                "reasoning": "默認回退策略",
                "confidence": 0.5
            }
    
    def act_phase(self, instruction: str, context: Dict[str, Any]) -> str:
        """
        Act階段：生成自然語言回應
        
        Args:
            instruction: 指令內容
            context: 上下文信息
            
        Returns:
            自然語言回應
        """
        try:
            # 構建Act階段提示詞
            prompt = self._build_act_prompt(instruction, context)
            
            # 調用LLM
            response = self.invoke(prompt)
            
            # 解析回應
            result = self._parse_act_response(response)
            
            self.logger.info(f"Act階段結果: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Act階段失敗: {e}")
            return "抱歉，我現在有點問題，請稍後再試。"
    
    def extract_slots_with_llm(self, text: str, slot_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用LLM進行槽位提取
        
        Args:
            text: 用戶輸入文本
            slot_schema: 槽位架構
            
        Returns:
            提取的槽位信息
        """
        try:
            # 構建槽位提取提示詞
            prompt = self._build_slot_extraction_prompt(text, slot_schema)
            
            # 調用LLM
            response = self.invoke(prompt)
            
            # 解析回應
            result = self._parse_slot_extraction_response(response)
            
            self.logger.info(f"槽位提取結果: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"槽位提取失敗: {e}")
            return {}

    def _build_think_prompt(self, instruction: str, context: Dict[str, Any]) -> str:
        """構建Think階段提示詞"""
        chat_history = context.get("chat_history", [])
        filled_slots = context.get("filled_slots", {})
        
        # 格式化對話歷史
        history_text = ""
        for msg in chat_history[-5:]:  # 只取最近5條消息
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            history_text += f"{role}: {content}\n"
        
        prompt = f"""
你是一個對話狀態分析專家。分析當前對話狀態，決定下一步行動。

對話歷史：
{history_text}

已填槽位：{filled_slots}

請分析並決定：
1. 是否需要收集更多信息
2. 下一個要詢問的槽位
3. 是否可以進行推薦

輸出格式：JSON
{{
  "action": "ELICIT_SLOT" | "RECOMMEND_PRODUCTS" | "CLARIFY_INPUT",
  "target_slot": "slot_name",
  "reasoning": "決策理由",
  "confidence": 0.95
}}

只輸出JSON格式，不要其他文字。
"""
        return prompt
    
    def _build_act_prompt(self, instruction: str, context: Dict[str, Any]) -> str:
        """構建Act階段提示詞"""
        chat_history = context.get("chat_history", [])
        target_slot = context.get("target_slot", "")
        known_info = context.get("known_info", {})
        
        # 格式化對話歷史
        history_text = ""
        for msg in chat_history[-3:]:  # 只取最近3條消息
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            history_text += f"{role}: {content}\n"
        
        prompt = f"""
你是一位專業的筆電銷售顧問。根據對話歷史和需要收集的信息，生成自然、親切的詢問。

對話歷史：
{history_text}

需要收集：{target_slot}
已了解信息：{known_info}

要求：
1. 語氣自然親切
2. 考慮已了解的信息
3. 提供相關的建議選項
4. 不超過50字

回應格式：
{{
  "content": "詢問內容",
  "suggestions": ["選項1", "選項2", "選項3"],
  "tone": "friendly"
}}

只輸出JSON格式，不要其他文字。
"""
        return prompt
    
    def _build_slot_extraction_prompt(self, text: str, slot_schema: Dict[str, Any]) -> str:
        """構建槽位提取提示詞"""
        prompt = f"""
你是一個專業的筆電銷售助手，需要從用戶輸入中提取結構化信息。

用戶輸入：{text}

請提取以下信息：
- 使用目的 (usage_purpose): gaming, business, student, creative, general
- 預算範圍 (budget_range): budget, mid_range, premium, luxury
- 性能需求 (performance_features): fast, portable, powerful, quiet, battery
- 品牌偏好 (brand_preference): asus, acer, lenovo, hp, dell, apple
- 便攜性需求 (portability_need): ultra_portable, balanced, desktop_replacement

輸出格式：JSON
{{
  "extracted_slots": {{
    "usage_purpose": "business",
    "budget_range": "mid_range",
    "performance_features": ["fast", "portable"],
    "brand_preference": "asus",
    "portability_need": "balanced"
  }},
  "confidence": 0.9,
  "reasoning": "提取理由"
}}

只輸出JSON格式，不要其他文字。
"""
        return prompt
    
    def _parse_think_response(self, response: str) -> Dict[str, Any]:
        """解析Think階段回應"""
        try:
            if isinstance(response, str):
                # 提取JSON部分
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = response[start_idx:end_idx]
                    return json.loads(json_str)
            
            return {
                "action": "ELICIT_SLOT",
                "target_slot": "usage_purpose",
                "reasoning": "解析失敗，使用默認策略",
                "confidence": 0.5
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Think回應JSON解析失敗: {e}")
            return {
                "action": "ELICIT_SLOT",
                "target_slot": "usage_purpose",
                "reasoning": "JSON解析失敗，使用默認策略",
                "confidence": 0.5
            }
    
    def _parse_act_response(self, response: str) -> str:
        """解析Act階段回應"""
        try:
            if isinstance(response, str):
                # 嘗試解析JSON
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = response[start_idx:end_idx]
                    parsed = json.loads(json_str)
                    return parsed.get("content", response)
            
            return response
            
        except json.JSONDecodeError:
            # 如果不是JSON格式，直接返回原始回應
            return response
    
    def _parse_slot_extraction_response(self, response: str) -> Dict[str, Any]:
        """解析槽位提取回應"""
        try:
            if isinstance(response, str):
                # 提取JSON部分
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = response[start_idx:end_idx]
                    parsed = json.loads(json_str)
                    return parsed.get("extracted_slots", {})
            
            return {}
            
        except json.JSONDecodeError as e:
            self.logger.error(f"槽位提取回應JSON解析失敗: {e}")
            return {}
