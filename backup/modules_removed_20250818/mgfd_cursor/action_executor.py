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
        
        # 初始化RAG檢索系統
        try:
            from .chunking import ProductChunkingEngine
            from .hybrid_retriever import HybridProductRetriever
            
            self.chunking_engine = ProductChunkingEngine()
            self.hybrid_retriever = HybridProductRetriever(self.chunking_engine)
            self.rag_enabled = True
            self.logger.info("RAG檢索系統初始化成功")
        except Exception as e:
            self.logger.error(f"RAG檢索系統初始化失敗: {e}")
            self.chunking_engine = None
            self.hybrid_retriever = None
            self.rag_enabled = False
        
        # 動作處理器映射 - 修正為與ActionType枚舉值一致
        self.action_handlers = {
            "elicit_information": self._handle_elicit_slot,
            "recommend_products": self._handle_recommend_products,
            "recommend_popular_products": self._handle_recommend_popular_products,
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
            "confidence": command.get("confidence", 0.8),
            "session_id": state.get("session_id", "")
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
            "confidence": command.get("confidence", 0.9),
            "session_id": state.get("session_id", "")
        }
    
    def _handle_recommend_popular_products(self, command: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """處理熱門產品推薦動作 - 使用RAG檢索系統"""
        try:
            # 優先使用RAG檢索系統
            if self.rag_enabled and self.hybrid_retriever:
                popular_products = self.hybrid_retriever.retrieve_popular_products()
                
                if popular_products:
                    # 生成基於RAG的推薦回應
                    response = self._generate_rag_based_popular_response(popular_products)
                    
                    return {
                        "action_type": "popular_recommendation",
                        "content": response,
                        "recommendations": popular_products,
                        "confidence": command.get("confidence", 0.95),
                        "data_source": "rag_retrieval_system"
                    }
            
            # 降級到傳統方法
            self.logger.warning("RAG系統不可用，使用傳統方法")
            popular_products = self._get_popular_products()
            response = self._generate_popular_recommendation_response(popular_products)
            
            return {
                "action_type": "popular_recommendation",
                "content": response,
                "recommendations": popular_products,
                "confidence": command.get("confidence", 0.85),
                "data_source": "legacy_knowledge_base"
            }
            
        except Exception as e:
            self.logger.error(f"熱門產品推薦失敗: {e}")
            return self._handle_recommend_products(command, state)  # 降級到一般推薦
    
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
            "confidence": command.get("confidence", 0.7),
            "session_id": state.get("session_id", "")
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
            "confidence": command.get("confidence", 0.9),
            "session_id": state.get("session_id", "")
        }
    
    def _handle_unknown_action(self, command: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """處理未知動作"""
        return {
            "action_type": "unknown",
            "content": "抱歉，我不太理解您的需求。請重新描述一下您想要什麼樣的筆電？",
            "confidence": 0.5,
            "session_id": state.get("session_id", "")
        }
    
    def _handle_error(self, command: Dict[str, Any], state: Dict[str, Any], error: str) -> Dict[str, Any]:
        """處理錯誤情況"""
        return {
            "action_type": "error",
            "content": "抱歉，系統遇到了一些問題。請稍後再試。",
            "error": error,
            "confidence": 0.3,
            "session_id": state.get("session_id", "")
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
        """生成產品推薦列表 - 修復版，基於公司產品資料庫"""
        try:
            # 從知識庫獲取公司產品
            from .knowledge_base import NotebookKnowledgeBase
            
            kb = NotebookKnowledgeBase()
            all_products = kb.load_products()
            
            if not all_products:
                self.logger.warning("無法載入產品資料進行推薦")
                return []
            
            # 基於用戶槽位過濾產品
            filtered_products = self._filter_products_by_slots(all_products, filled_slots)
            
            # 為產品生成推薦理由
            recommendations = []
            for product in filtered_products[:3]:  # 取前3個
                recommendation = {
                    "id": product.get('modeltype', 'unknown'),
                    "name": product.get('modelname', 'Unknown Model'),
                    "brand": self._extract_brand_from_product(product),
                    "price": self._format_price(product),
                    "features": self._extract_key_features(product),
                    "reason": self._generate_recommendation_reason(product, filled_slots)
                }
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"生成產品推薦失敗: {e}")
            return []
    
    def _filter_products_by_slots(self, products: List[Dict], filled_slots: Dict[str, Any]) -> List[Dict]:
        """基於用戶槽位過濾產品"""
        filtered = products.copy()
        
        try:
            # 基於使用目的過濾
            if 'usage_purpose' in filled_slots:
                usage = filled_slots['usage_purpose'].lower()
                if usage == 'gaming':
                    # 遊戲用戶偏好高效能GPU
                    filtered = [p for p in filtered if 'rtx' in p.get('gpu', '').lower() or 'gtx' in p.get('gpu', '').lower()]
                elif usage == 'business':
                    # 商務用戶偏好穩定性和電池續航
                    pass  # 目前保留所有產品
            
            # 基於品牌偏好過濾
            if 'brand_preference' in filled_slots:
                brand = filled_slots['brand_preference'].lower()
                if brand:
                    filtered = [p for p in filtered if brand in p.get('modelname', '').lower()]
            
            return filtered
            
        except Exception as e:
            self.logger.debug(f"產品過濾失敗: {e}")
            return products
    
    def _extract_brand_from_product(self, product: Dict[str, Any]) -> str:
        """從產品數據中提取品牌"""
        modelname = product.get('modelname', '')
        # 根據型號名稱推斷品牌 (這裡需要根據實際數據調整)
        if 'AB' in modelname:
            return "Company Brand"  # 假設AB開頭是公司品牌
        return "Unknown Brand"
    
    def _format_price(self, product: Dict[str, Any]) -> str:
        """格式化產品價格"""
        # 這裡需要根據實際產品數據結構調整
        # 暫時返回估算價格
        modeltype = product.get('modeltype', '')
        if modeltype in ['819', '958']:
            return "45,000-55,000"
        elif modeltype in ['839']:
            return "35,000-45,000"
        else:
            return "價格面議"
    
    def _extract_key_features(self, product: Dict[str, Any]) -> List[str]:
        """提取產品關鍵特色"""
        features = []
        
        try:
            # 如果產品已經有預處理的特色，直接使用
            if 'key_features' in product and product['key_features']:
                return product['key_features'][:3]
            
            # 基於CPU
            cpu = product.get('cpu', '')
            if any(term in cpu.lower() for term in ['i7', 'i9', 'ryzen 7', 'ryzen 9']):
                features.append("高效能處理器")
            elif any(term in cpu.lower() for term in ['i5', 'ryzen 5']):
                features.append("均衡效能")
            
            # 基於GPU
            gpu = product.get('gpu', '')
            if any(term in gpu.lower() for term in ['rtx', 'gtx', 'radeon']):
                features.append("獨立顯卡")
            elif 'integrated' not in gpu.lower() and gpu.strip():
                features.append("內建圖形處理")
            
            # 基於記憶體
            memory = product.get('memory', '')
            if any(term in memory.lower() for term in ['16gb', '32gb']):
                features.append("大容量記憶體")
            elif '8gb' in memory.lower():
                features.append("標準記憶體")
            
            # 基於儲存
            storage = product.get('storage', '')
            if 'ssd' in storage.lower():
                features.append("SSD高速儲存")
            elif 'nvme' in storage.lower():
                features.append("NVMe超高速儲存")
            
            # 基於顯示器
            lcd = product.get('lcd', '')
            if 'fhd' in lcd.lower() and '144hz' in lcd.lower():
                features.append("高刷新率螢幕")
            elif 'fhd' in lcd.lower():
                features.append("全高清顯示")
            
            # 基於電池
            battery = product.get('battery', '')
            if any(term in battery.lower() for term in ['55wh', '65wh', '90wh']):
                features.append("長效電池")
            
            return features[:3] if features else ["高品質", "值得信賴"]
            
        except Exception as e:
            self.logger.debug(f"提取特色失敗: {e}")
            return ["高品質", "值得信賴"]
    
    def _generate_recommendation_reason(self, product: Dict[str, Any], filled_slots: Dict[str, Any]) -> str:
        """生成推薦理由"""
        try:
            usage = filled_slots.get('usage_purpose', 'general')
            
            if usage == 'gaming':
                return "適合遊戲和高效能需求"
            elif usage == 'business':
                return "商務辦公的理想選擇"
            elif usage == 'study':
                return "學習和日常使用的好夥伴"
            else:
                return "綜合表現優秀，適合多種用途"
                
        except Exception:
            return "優質產品，值得推薦"
    
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
            "session_id": state.get("session_id", ""),
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
            "session_id": state.get("session_id", ""),
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
            "session_id": state.get("session_id", ""),
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
            "session_id": state.get("session_id", ""),
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
            "session_id": state.get("session_id", ""),
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_popular_products(self) -> List[Dict[str, Any]]:
        """獲取熱門產品列表 - 修復版，從公司產品資料庫獲取"""
        try:
            # 從知識庫獲取真實公司產品
            from .knowledge_base import NotebookKnowledgeBase
            
            kb = NotebookKnowledgeBase()
            all_products = kb.load_products()
            
            if not all_products:
                self.logger.warning("無法載入產品資料，返回空列表")
                return []
            
            # 為產品計算熱門度評分 (基於產品特性)
            for product in all_products:
                product['popularity_score'] = self._calculate_popularity_score(product)
            
            # 按熱門度排序並取前5個
            popular_products = sorted(
                all_products, 
                key=lambda x: x.get('popularity_score', 0), 
                reverse=True
            )[:5]
            
            self.logger.info(f"成功載入 {len(popular_products)} 個熱門公司產品")
            return popular_products
            
        except Exception as e:
            self.logger.error(f"獲取熱門產品失敗: {e}")
            # 緊急情況下返回空列表，而非硬編碼的非公司產品
            return []
    
    def _calculate_popularity_score(self, product: Dict[str, Any]) -> float:
        """計算產品熱門度評分 (基於產品特性)"""
        score = 5.0  # 基礎分數
        
        try:
            # 基於CPU等級加分
            cpu = product.get('cpu', '').lower()
            if 'i7' in cpu or 'i9' in cpu or 'ryzen 7' in cpu or 'ryzen 9' in cpu:
                score += 1.5
            elif 'i5' in cpu or 'ryzen 5' in cpu:
                score += 1.0
            
            # 基於GPU等級加分
            gpu = product.get('gpu', '').lower()
            if 'rtx' in gpu or 'gtx' in gpu or 'radeon' in gpu:
                score += 1.5
            elif 'integrated' not in gpu and gpu.strip():
                score += 0.5
            
            # 基於記憶體容量加分
            memory = product.get('memory', '').lower()
            if '16gb' in memory or '32gb' in memory:
                score += 1.0
            elif '8gb' in memory:
                score += 0.5
            
            # 基於儲存類型加分
            storage = product.get('storage', '').lower()
            if 'ssd' in storage:
                score += 0.5
            
            # 基於型號熱門度 (某些型號系列更受歡迎)
            modeltype = product.get('modeltype', '')
            if modeltype in ['819', '839', '958']:  # 假設這些是熱門型號
                score += 0.5
            
            return min(score, 10.0)  # 最高10分
            
        except Exception as e:
            self.logger.debug(f"計算熱門度評分失敗: {e}")
            return 5.0  # 返回預設分數
    
    def _generate_popular_recommendation_response(self, products: List[Dict[str, Any]]) -> str:
        """生成熱門產品推薦回應"""
        if not products:
            return "抱歉，目前無法載入產品資料。請聯繫技術支援或稍後再試。"
        
        response = "🔥 **目前最受歡迎的筆電推薦** 🔥\n\n"
        response += "根據產品特性、性能表現和市場定位，我為您推薦以下熱門選擇：\n\n"
        
        for i, product in enumerate(products, 1):
            # 提取產品名稱
            product_name = product.get('modelname', f"產品型號 {product.get('modeltype', 'Unknown')}")
            
            # 格式化價格
            price = self._format_price(product)
            
            # 提取特色
            features = self._extract_key_features(product)
            
            # 計算評分
            popularity_score = product.get('popularity_score', 5.0)
            
            # 生成簡介
            description = self._generate_product_description(product)
            
            response += f"**{i}. {product_name}**\n"
            response += f"   💰 建議售價：NT$ {price}\n"
            response += f"   ⭐ 綜合評分：{popularity_score:.1f}/10\n"
            response += f"   ✨ 主要特色：{', '.join(features)}\n"
            response += f"   📝 產品簡介：{description}\n\n"
        
        response += "以上都是我們公司的優質產品，具備出色的性價比和可靠品質。\n"
        response += "您對哪一款比較感興趣？我可以為您提供更詳細的規格說明和選購建議。"
        
        return response
    
    def _generate_product_description(self, product: Dict[str, Any]) -> str:
        """生成產品簡介"""
        try:
            cpu = product.get('cpu', '').split(',')[0] if product.get('cpu') else "處理器"
            gpu = product.get('gpu', '').split('\n')[0] if product.get('gpu') else "顯示晶片"
            lcd = product.get('lcd', '')
            
            # 提取螢幕尺寸
            screen_size = "15.6吋" if "15.6" in lcd else "筆電螢幕"
            
            # 基於產品類型生成描述
            modeltype = product.get('modeltype', '')
            if modeltype == '819':
                return f"搭載{cpu}處理器的{screen_size}商用筆電，適合商務辦公與日常使用"
            elif modeltype == '839':
                return f"經濟實惠的{screen_size}筆電，{cpu}提供穩定效能"
            elif modeltype == '958':
                return f"高階{screen_size}筆電，{cpu}配置適合專業工作需求"
            else:
                return f"搭載{cpu}的{screen_size}筆電，性能穩定可靠"
                
        except Exception:
            return "高品質筆電，性能穩定，適合多種使用需求"
    
    def _generate_rag_based_popular_response(self, products: List[Dict[str, Any]]) -> str:
        """生成基於RAG檢索的熱門產品回應"""
        if not products:
            return "抱歉，目前無法載入產品資料。請聯繫技術支援或稍後再試。"
        
        response = "🔥 **基於智能檢索的熱門筆電推薦** 🔥\n\n"
        response += "通過我們的AI檢索系統，根據產品特性、性能表現和用戶回饋，為您推薦以下最受歡迎的選擇：\n\n"
        
        for i, product in enumerate(products, 1):
            # 從RAG檢索結果提取信息
            modelname = product.get('modelname', 'Unknown Model')
            modeltype = product.get('modeltype', 'Unknown')
            popularity_score = product.get('popularity_score', 5.0)
            key_features = product.get('key_features', [])
            primary_usage = product.get('primary_usage', 'general')
            price_tier = product.get('price_tier', 'standard')
            
            # 從原始產品數據提取詳細信息
            raw_product = product.get('raw_product', {})
            
            # 格式化價格
            price = self._format_price(raw_product)
            
            # 生成產品描述
            description = self._generate_rag_product_description(product, raw_product)
            
            # 格式化適用場景
            usage_text = self._format_usage_scenario(primary_usage)
            
            # 格式化價格等級
            price_text = self._format_price_tier(price_tier)
            
            response += f"**{i}. {modelname}** ({modeltype}系列)\n"
            response += f"   💰 建議售價：NT$ {price}\n"
            response += f"   ⭐ AI推薦指數：{popularity_score:.1f}/10\n"
            response += f"   🎯 適用場景：{usage_text}\n"
            response += f"   💎 價格定位：{price_text}\n"
            response += f"   ✨ 核心特色：{', '.join(key_features[:3])}\n"
            response += f"   📝 產品簡介：{description}\n\n"
        
        response += "以上推薦基於我們的智能分析系統，結合產品規格、市場定位和用戶需求匹配度進行篩選。\n"
        response += "每款產品都是我們公司的優質產品，具備出色的性價比和可靠品質。\n\n"
        response += "您對哪一款比較感興趣？我可以為您提供更詳細的技術規格、使用建議或比較分析。"
        
        return response
    
    def _generate_rag_product_description(self, product: Dict[str, Any], raw_product: Dict[str, Any]) -> str:
        """生成基於RAG數據的產品描述"""
        try:
            primary_usage = product.get('primary_usage', 'general')
            price_tier = product.get('price_tier', 'standard')
            
            # 從原始數據提取關鍵規格
            cpu = raw_product.get('cpu', '').split(',')[0] if raw_product.get('cpu') else "高效處理器"
            lcd = raw_product.get('lcd', '')
            screen_size = "15.6吋" if "15.6" in lcd else "專業顯示器"
            
            # 基於主要用途和價格等級生成描述
            if primary_usage == 'gaming' and price_tier in ['premium', 'mid_range']:
                return f"搭載{cpu}的{screen_size}高效能筆電，專為遊戲和創作設計"
            elif primary_usage == 'business':
                return f"商務專業筆電，{cpu}配置，{screen_size}設計，適合企業辦公環境"
            elif price_tier == 'premium':
                return f"頂級配置筆電，採用{cpu}處理器，{screen_size}專業級顯示，性能卓越"
            elif price_tier == 'budget':
                return f"經濟實惠的{screen_size}筆電，{cpu}提供穩定效能，適合日常使用"
            else:
                return f"均衡配置的{screen_size}筆電，搭載{cpu}，適合多種應用場景"
                
        except Exception:
            return "高品質筆電，性能穩定，適合專業和日常使用需求"
    
    def _format_usage_scenario(self, primary_usage: str) -> str:
        """格式化適用場景"""
        usage_map = {
            'gaming': '遊戲娛樂、高效能運算',
            'business': '商務辦公、會議簡報',
            'creative': '創作設計、影音編輯',
            'general': '日常辦公、學習娛樂'
        }
        return usage_map.get(primary_usage, '多用途應用')
    
    def _format_price_tier(self, price_tier: str) -> str:
        """格式化價格等級"""
        tier_map = {
            'premium': '高階旗艦',
            'mid_range': '中階主流',
            'budget': '經濟實惠',
            'standard': '標準配置'
        }
        return tier_map.get(price_tier, '標準配置')
