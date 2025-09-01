"""
信息收集策略
處理需要進一步收集信息的情況
"""

import logging
from typing import Dict, Any, List, Optional
from ..ResponseStrategy import ResponseStrategy, ResponseType


class ElicitationStrategy(ResponseStrategy):
    """信息收集策略"""
    
    def __init__(self):
        super().__init__("ElicitationStrategy")
        self.elicitation_templates = self._load_elicitation_templates()
    
    def _load_elicitation_templates(self) -> Dict[str, str]:
        """載入信息收集模板"""
        return {
            "general_clarification": "請您提供更多細節，這樣我才能給您更準確的建議。",
            "usage_clarification": "請問您具體會用這台電腦做什麼呢？例如：文書處理、影片剪輯、遊戲等。",
            "budget_clarification": "您的預算大概是多少呢？這樣我可以推薦最適合的選擇。",
            "preference_clarification": "您對品牌、重量、螢幕大小有什麼特別的偏好嗎？",
            "technical_clarification": "您對電腦的效能有什麼要求嗎？例如：處理速度、記憶體大小等。",
            "urgency_clarification": "您需要多快拿到這台電腦呢？這會影響我推薦的型號。"
        }
    
    def generate_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成信息收集回應
        
        Args:
            context: 當前上下文
            
        Returns:
            信息收集回應字典
        """
        try:
            # 分析需要收集的信息類型
            missing_info = self._analyze_missing_information(context)
            
            if not missing_info:
                # 如果沒有缺失信息，轉向其他策略
                return self._create_completion_response(context)
            
            # 生成針對性的信息收集回應
            response = self._create_elicitation_response(context, missing_info)
            
            self.logger.info(f"生成信息收集回應，針對: {missing_info}")
            return response
            
        except Exception as e:
            self.logger.error(f"生成信息收集回應時發生錯誤: {e}")
            return self._create_error_response(context)
    
    def get_response_type(self) -> ResponseType:
        """獲取回應類型"""
        return ResponseType.ELICITATION
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        驗證上下文是否適合信息收集策略
        
        Args:
            context: 當前上下文
            
        Returns:
            是否適合使用此策略
        """
        # 檢查是否需要收集更多信息
        needs_elicitation = context.get("needs_elicitation", False)
        is_elicitation_stage = context.get("stage") == "ELICITATION"
        has_insufficient_info = self._has_insufficient_information(context)
        
        return needs_elicitation or is_elicitation_stage or has_insufficient_info
    
    def _analyze_missing_information(self, context: Dict[str, Any]) -> List[str]:
        """
        分析缺失的信息
        
        Args:
            context: 當前上下文
            
        Returns:
            缺失信息類型列表
        """
        missing_info = []
        slots = context.get("slots", {})
        
        # 檢查關鍵信息是否缺失
        if not slots.get("usage_purpose"):
            missing_info.append("usage_purpose")
        
        if not slots.get("price_range"):
            missing_info.append("price_range")
        
        if not slots.get("portability"):
            missing_info.append("portability")
        
        # 檢查是否有模糊的信息需要澄清
        if self._has_ambiguous_information(context):
            missing_info.append("clarification")
        
        return missing_info
    
    def _has_insufficient_information(self, context: Dict[str, Any]) -> bool:
        """
        檢查是否有不足的信息
        
        Args:
            context: 當前上下文
            
        Returns:
            是否信息不足
        """
        slots = context.get("slots", {})
        
        # 檢查關鍵槽位是否填充
        key_slots = ["usage_purpose", "price_range"]
        filled_key_slots = sum(1 for slot in key_slots if slot in slots and slots[slot])
        
        return filled_key_slots < 2
    
    def _has_ambiguous_information(self, context: Dict[str, Any]) -> bool:
        """
        檢查是否有模糊的信息
        
        Args:
            context: 當前上下文
            
        Returns:
            是否有模糊信息
        """
        # 檢查用戶輸入是否包含模糊詞彙
        user_message = context.get("user_message", "").lower()
        ambiguous_words = ["大概", "差不多", "隨便", "都可以", "不知道"]
        
        return any(word in user_message for word in ambiguous_words)
    
    def _create_elicitation_response(self, context: Dict[str, Any], missing_info: List[str]) -> Dict[str, Any]:
        """
        創建信息收集回應
        
        Args:
            context: 當前上下文
            missing_info: 缺失信息列表
            
        Returns:
            信息收集回應字典
        """
        # 選擇最優先的缺失信息
        priority_missing = self._get_priority_missing_info(missing_info)
        
        # 生成針對性的問題
        question = self._generate_elicitation_question(priority_missing, context)
        
        return {
            "type": "elicitation",
            "message": question,
            "elicitation_type": priority_missing,
            "missing_info": missing_info,
            "session_id": context.get("session_id"),
            "stage": "ELICITATION",
            "needs_elicitation": True
        }
    
    def _get_priority_missing_info(self, missing_info: List[str]) -> str:
        """
        獲取優先級最高的缺失信息
        
        Args:
            missing_info: 缺失信息列表
            
        Returns:
            優先級最高的缺失信息類型
        """
        # 優先級順序
        priority_order = ["usage_purpose", "price_range", "portability", "clarification"]
        
        for info_type in priority_order:
            if info_type in missing_info:
                return info_type
        
        # 如果沒有匹配的優先級，返回第一個
        return missing_info[0] if missing_info else "general_clarification"
    
    def _generate_elicitation_question(self, info_type: str, context: Dict[str, Any]) -> str:
        """
        生成針對性的信息收集問題
        
        Args:
            info_type: 信息類型
            context: 當前上下文
            
        Returns:
            針對性問題
        """
        if info_type == "usage_purpose":
            return self.elicitation_templates["usage_clarification"]
        elif info_type == "price_range":
            return self.elicitation_templates["budget_clarification"]
        elif info_type == "portability":
            return self.elicitation_templates["preference_clarification"]
        elif info_type == "clarification":
            return self.elicitation_templates["general_clarification"]
        else:
            return self.elicitation_templates["general_clarification"]
    
    def _create_completion_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建信息收集完成回應
        
        Args:
            context: 當前上下文
            
        Returns:
            完成回應字典
        """
        return {
            "type": "elicitation_completion",
            "message": "謝謝您提供的詳細信息！現在我可以為您推薦最適合的筆電了。",
            "session_id": context.get("session_id"),
            "stage": "RECOMMENDATION",
            "needs_recommendation": True
        }
    
    def _create_error_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建錯誤回應
        
        Args:
            context: 當前上下文
            
        Returns:
            錯誤回應字典
        """
        return {
            "type": "general",
            "message": "抱歉，我在處理您的信息時遇到了問題。請稍後再試。",
            "session_id": context.get("session_id"),
            "error": True
        }
    
    def get_elicitation_progress(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        獲取信息收集進度
        
        Args:
            context: 當前上下文
            
        Returns:
            進度信息字典
        """
        slots = context.get("slots", {})
        missing_info = self._analyze_missing_information(context)
        
        # 計算完成度
        total_slots = 5  # 假設總共有5個重要槽位
        filled_slots = sum(1 for slot in slots if slots[slot])
        completion_percentage = (filled_slots / total_slots) * 100 if total_slots > 0 else 0
        
        return {
            "total_slots": total_slots,
            "filled_slots": filled_slots,
            "missing_info": missing_info,
            "completion_percentage": completion_percentage,
            "can_proceed": len(missing_info) == 0
        }
