#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD ActionExecutor 模組
實現Act階段的執行邏輯和動態提示生成
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

class ActionExecutor:
    """動作執行器 - 資訊引導節點"""
    
    def __init__(self, llm_manager, config_loader):
        """
        初始化動作執行器
        
        Args:
            llm_manager: LLM管理器
            config_loader: 配置載入器
        """
        self.llm_manager = llm_manager
        self.config_loader = config_loader
        self.logger = logging.getLogger(__name__)
        
        # 動作處理器映射 - 修正為與ActionType枚舉值一致
        self.action_handlers = {
            "elicit_information": self._handle_elicit_slot,
            "recommend_products": self._handle_recommend_products,
            "clarify_input": self._handle_clarify_input,
            "handle_interruption": self._handle_interruption,
            "special_case_response": self._handle_special_case
        }
    
    def execute_action(self, command: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行動作
        
        Args:
            command: 結構化指令
            state: 對話狀態
            
        Returns:
            執行結果
        """
        try:
            action = command.get("action", "")
            target_slot = command.get("target_slot")
            
            # 獲取對應的動作處理器
            handler = self.action_handlers.get(action)
            if handler:
                result = handler(command, state)
                return {
                    "success": True,
                    "result": result
                }
            else:
                self.logger.warning(f"未知動作類型: {action}")
                fallback_result = self._handle_unknown_action(command, state)
                return {
                    "success": True,
                    "result": fallback_result
                }
                
        except Exception as e:
            self.logger.error(f"執行動作失敗: {e}")
            error_result = self._handle_error(command, state, str(e))
            return {
                "success": False,
                "error": str(e),
                "result": error_result
            }
    
    def _handle_elicit_slot(self, command: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """處理信息收集動作"""
        target_slot = command.get("target_slot", "")
        
        # 生成動態提示
        prompt = self._generate_elicitation_prompt(target_slot, state)
        
        # 調用LLM生成回應
        instruction = f"生成關於{target_slot}的詢問"
        context = {
            "chat_history": state.get("chat_history", []),
            "target_slot": target_slot,
            "known_info": state.get("filled_slots", {})
        }
        
        response = self.llm_manager.act_phase(instruction, context)
        
        # 生成建議選項
        suggestions = self._generate_suggestions(target_slot, state)
        
        return {
            "action_type": "elicitation",
            "target_slot": target_slot,
            "content": response,
            "suggestions": suggestions,
            "confidence": command.get("confidence", 0.8)
        }
    
    def _handle_recommend_products(self, command: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """處理產品推薦動作"""
        filled_slots = state.get("filled_slots", {})
        
        # 生成推薦提示
        prompt = self._generate_recommendation_prompt(filled_slots, state)
        
        # 調用LLM生成推薦
        instruction = "根據用戶需求生成產品推薦"
        context = {
            "chat_history": state.get("chat_history", []),
            "filled_slots": filled_slots,
            "user_preferences": state.get("user_preferences", {})
        }
        
        response = self.llm_manager.act_phase(instruction, context)
        
        # 生成推薦產品列表（這裡可以調用產品知識庫）
        recommendations = self._generate_product_recommendations(filled_slots)
        
        return {
            "action_type": "recommendation",
            "content": response,
            "recommendations": recommendations,
            "confidence": command.get("confidence", 0.9)
        }
    
    def _handle_clarify_input(self, command: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """處理輸入澄清動作"""
        # 生成澄清提示
        instruction = "澄清用戶的模糊輸入"
        context = {
            "chat_history": state.get("chat_history", []),
            "filled_slots": state.get("filled_slots", {})
        }
        
        response = self.llm_manager.act_phase(instruction, context)
        
        return {
            "action_type": "clarification",
            "content": response,
            "confidence": command.get("confidence", 0.7)
        }
    
    def _handle_interruption(self, command: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """處理中斷意圖"""
        # 生成重新開始的回應
        instruction = "處理用戶的中斷意圖，重新開始對話"
        context = {
            "chat_history": state.get("chat_history", [])
        }
        
        response = self.llm_manager.act_phase(instruction, context)
        
        return {
            "action_type": "interruption",
            "content": response,
            "confidence": command.get("confidence", 0.9)
        }
    
    def _handle_unknown_action(self, command: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """處理未知動作"""
        return {
            "action_type": "unknown",
            "content": "抱歉，我不太理解您的需求。請重新描述一下您想要什麼樣的筆電？",
            "confidence": 0.5
        }
    
    def _handle_error(self, command: Dict[str, Any], state: Dict[str, Any], error: str) -> Dict[str, Any]:
        """處理錯誤情況"""
        return {
            "action_type": "error",
            "content": "抱歉，系統遇到了一些問題。請稍後再試。",
            "error": error,
            "confidence": 0.3
        }
    
    def _generate_elicitation_prompt(self, target_slot: str, state: Dict[str, Any]) -> str:
        """生成信息收集提示詞"""
        filled_slots = state.get("filled_slots", {})
        chat_history = state.get("chat_history", [])
        
        # 獲取槽位配置
        slot_config = self._get_slot_config(target_slot)
        
        # 構建上下文信息
        context_info = self._build_context_info(filled_slots)
        
        prompt = f"""
你是一位專業的筆電銷售顧問。需要向用戶詢問關於 {target_slot} 的信息。

已了解的信息：{context_info}
槽位描述：{slot_config.get('description', '')}
選項：{slot_config.get('options', [])}

請生成一個自然、親切的詢問，要求：
1. 語氣友好自然
2. 考慮已了解的信息
3. 提供相關的建議選項
4. 不超過50字

回應格式：
{{
  "content": "詢問內容",
  "suggestions": ["選項1", "選項2", "選項3"],
  "tone": "friendly"
}}
"""
        return prompt
    
    def _generate_recommendation_prompt(self, filled_slots: Dict[str, Any], state: Dict[str, Any]) -> str:
        """生成推薦提示詞"""
        chat_history = state.get("chat_history", [])
        
        # 格式化用戶需求
        requirements = self._format_user_requirements(filled_slots)
        
        prompt = f"""
你是一位專業的筆電銷售顧問。根據用戶的需求生成產品推薦。

用戶需求：{requirements}

請生成推薦回應，要求：
1. 專業且親切
2. 突出產品優勢
3. 符合用戶需求
4. 提供購買建議

回應格式：
{{
  "content": "推薦內容",
  "recommendations": [
    {{
      "name": "產品名稱",
      "brand": "品牌",
      "price": "價格",
      "features": ["特點1", "特點2"],
      "reason": "推薦理由"
    }}
  ]
}}
"""
        return prompt
    
    def _generate_suggestions(self, target_slot: str, state: Dict[str, Any]) -> List[str]:
        """生成建議選項"""
        slot_config = self._get_slot_config(target_slot)
        options = slot_config.get("options", [])
        
        # 根據槽位類型生成建議
        if target_slot == "usage_purpose":
            return ["遊戲", "商務工作", "學習", "創作設計", "一般使用"]
        elif target_slot == "budget_range":
            return ["2-3萬", "3-4萬", "4-5萬", "5萬以上"]
        elif target_slot == "brand_preference":
            return ["華碩", "宏碁", "聯想", "惠普", "戴爾", "蘋果"]
        else:
            return options[:3] if len(options) > 3 else options
    
    def _generate_product_recommendations(self, filled_slots: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成產品推薦列表"""
        # 這裡可以調用產品知識庫進行實際的產品過濾
        # 目前返回模擬數據
        recommendations = [
            {
                "id": "1",
                "name": "ASUS VivoBook S15",
                "brand": "ASUS",
                "price": "35,900",
                "features": ["輕薄便攜", "快速開機", "商務適用"],
                "reason": "符合您的商務需求和預算"
            },
            {
                "id": "2", 
                "name": "Lenovo ThinkPad E14",
                "brand": "Lenovo",
                "price": "32,900",
                "features": ["穩定可靠", "長效電池", "專業鍵盤"],
                "reason": "ThinkPad系列商務筆電的經典選擇"
            }
        ]
        
        return recommendations
    
    def _get_slot_config(self, slot_name: str) -> Dict[str, Any]:
        """獲取槽位配置"""
        # 這裡可以從配置檔案載入
        slot_configs = {
            "usage_purpose": {
                "description": "使用目的",
                "options": ["gaming", "business", "student", "creative", "general"]
            },
            "budget_range": {
                "description": "預算範圍",
                "options": ["budget", "mid_range", "premium", "luxury"]
            },
            "brand_preference": {
                "description": "品牌偏好",
                "options": ["asus", "acer", "lenovo", "hp", "dell", "apple"]
            }
        }
        
        return slot_configs.get(slot_name, {})
    
    def _build_context_info(self, filled_slots: Dict[str, Any]) -> str:
        """構建上下文信息"""
        if not filled_slots:
            return "尚未了解任何信息"
        
        context_parts = []
        for slot_name, value in filled_slots.items():
            if value:
                context_parts.append(f"{slot_name}: {value}")
        
        return ", ".join(context_parts) if context_parts else "尚未了解任何信息"
    
    def _format_user_requirements(self, filled_slots: Dict[str, Any]) -> str:
        """格式化用戶需求"""
        if not filled_slots:
            return "尚未提供具體需求"
        
        requirements = []
        
        # 格式化使用目的
        if "usage_purpose" in filled_slots:
            purpose_map = {
                "gaming": "遊戲",
                "business": "商務工作",
                "student": "學習",
                "creative": "創作設計",
                "general": "一般使用"
            }
            purpose = purpose_map.get(filled_slots["usage_purpose"], filled_slots["usage_purpose"])
            requirements.append(f"使用目的：{purpose}")
        
        # 格式化預算範圍
        if "budget_range" in filled_slots:
            budget_map = {
                "budget": "平價",
                "mid_range": "中價位",
                "premium": "高價位",
                "luxury": "頂級"
            }
            budget = budget_map.get(filled_slots["budget_range"], filled_slots["budget_range"])
            requirements.append(f"預算範圍：{budget}")
        
        # 格式化性能需求
        if "performance_features" in filled_slots:
            features = filled_slots["performance_features"]
            if isinstance(features, list) and features:
                feature_names = []
                for feature in features:
                    if feature == "fast":
                        feature_names.append("快速開關機")
                    elif feature == "portable":
                        feature_names.append("輕便攜帶")
                    elif feature == "powerful":
                        feature_names.append("高效能")
                
                if feature_names:
                    requirements.append(f"性能需求：{', '.join(feature_names)}")
        
        return "；".join(requirements) if requirements else "尚未提供具體需求"
    
    def _handle_special_case(self, command: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理特殊案例回應
        
        Args:
            command: 包含特殊案例信息的指令
            state: 當前對話狀態
            
        Returns:
            特殊案例回應結果
        """
        special_case = command.get("special_case", {})
        case_id = special_case.get("case_id", "")
        response_type = special_case.get("response_type", "")
        
        self.logger.info(f"處理特殊案例: {case_id} - {response_type}")
        
        # 檢查是否是循環打破案例
        if special_case.get("loop_breaking", False):
            return self._handle_loop_breaking_case(special_case, state)
        
        # 處理不同類型的特殊案例回應
        if response_type == "performance_clarification_funnel":
            return self._handle_performance_clarification(special_case, state)
        elif response_type == "guided_consultation_start":
            return self._handle_guided_consultation(special_case, state)
        elif response_type == "specialized_recommendation_prep":
            return self._handle_specialized_recommendation(special_case, state)
        else:
            return self._handle_generic_special_case(special_case, state)
    
    def _handle_loop_breaking_case(self, special_case: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """處理循環打破案例"""
        self.logger.info("執行循環打破處理")
        
        return {
            "action_type": "special_case_response",
            "case_id": special_case.get("case_id", ""),
            "content": special_case.get("message", ""),
            "funnel_question": special_case.get("funnel_question", {}),
            "loop_breaking": True,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_performance_clarification(self, special_case: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """處理效能澄清案例"""
        return {
            "action_type": "elicitation",
            "target_slot": "performance_priority",
            "content": special_case.get("message", ""),
            "funnel_question": special_case.get("funnel_question", {}),
            "special_case_id": special_case.get("case_id", ""),
            "confidence": special_case.get("similarity_score", 0.8),
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_guided_consultation(self, special_case: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """處理引導式諮詢案例"""
        return {
            "action_type": "elicitation",
            "target_slot": "usage_purpose",
            "content": special_case.get("message", ""),
            "funnel_question": special_case.get("funnel_question", {}),
            "special_case_id": special_case.get("case_id", ""),
            "tone": "reassuring_and_helpful",
            "confidence": special_case.get("similarity_score", 0.8),
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_specialized_recommendation(self, special_case: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """處理專門推薦案例"""
        # 提取推薦響應中的後續問題
        follow_up_questions = special_case.get("follow_up_questions", [])
        
        return {
            "action_type": "clarification",
            "content": special_case.get("message", ""),
            "specialized_criteria": special_case.get("specialized_criteria", {}),
            "follow_up_questions": follow_up_questions,
            "special_case_id": special_case.get("case_id", ""),
            "confidence": special_case.get("similarity_score", 0.8),
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_generic_special_case(self, special_case: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """處理通用特殊案例"""
        return {
            "action_type": "special_case_response",
            "content": special_case.get("message", ""),
            "case_id": special_case.get("case_id", ""),
            "response_type": special_case.get("response_type", ""),
            "confidence": special_case.get("similarity_score", 0.8),
            "timestamp": datetime.now().isoformat()
        }
