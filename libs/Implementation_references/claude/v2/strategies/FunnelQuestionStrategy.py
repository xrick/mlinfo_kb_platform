"""
漏斗問題策略
處理漏斗對話中的問題生成
"""

import logging
from typing import Dict, Any, List, Optional
from ..ResponseStrategy import ResponseStrategy, ResponseType


class FunnelQuestionStrategy(ResponseStrategy):
    """漏斗問題策略"""
    
    def __init__(self):
        super().__init__("FunnelQuestionStrategy")
        self.funnel_questions = self._load_funnel_questions()
    
    def _load_funnel_questions(self) -> List[Dict[str, Any]]:
        """載入漏斗問題配置"""
        return [
            {
                "id": "usage_purpose",
                "question": "請問您買這台電腦，最主要是用來做什麼呢？",
                "options": ["工作", "學習", "遊戲", "娛樂", "其他"],
                "slot_name": "usage_purpose",
                "priority": 1
            },
            {
                "id": "price_range",
                "question": "方便請問一下您的預算大概是多少呢？",
                "options": ["2萬以下", "2-3萬", "3-4萬", "4-5萬", "5萬以上"],
                "slot_name": "price_range",
                "priority": 2
            },
            {
                "id": "portability",
                "question": "會經常需要把它帶出門嗎？對於重量有沒有特別的偏好？",
                "options": ["很常攜帶，希望輕便", "偶爾攜帶", "主要放在家裡使用"],
                "slot_name": "portability",
                "priority": 3
            },
            {
                "id": "screen_size",
                "question": "對於螢幕大小有什麼偏好嗎？",
                "options": ["13吋以下（輕便）", "14-15吋（平衡）", "16吋以上（大螢幕）"],
                "slot_name": "screen_size",
                "priority": 4
            },
            {
                "id": "brand",
                "question": "過去有用過哪個品牌的電腦嗎？有沒有特別喜歡或不喜歡的品牌？",
                "options": ["華碩", "宏碁", "聯想", "戴爾", "惠普", "沒有特別偏好"],
                "slot_name": "brand",
                "priority": 5
            }
        ]
    
    def generate_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成漏斗問題回應
        
        Args:
            context: 當前上下文
            
        Returns:
            漏斗問題回應字典
        """
        try:
            # 獲取當前需要詢問的問題
            current_question = self._get_next_question(context)
            
            if not current_question:
                # 如果沒有更多問題，轉向推薦階段
                return self._create_completion_response(context)
            
            # 構建問題回應
            response = {
                "type": "funnel_question",
                "question": current_question["question"],
                "options": current_question["options"],
                "question_id": current_question["id"],
                "slot_name": current_question["slot_name"],
                "message": f"讓我幫您找到最適合的筆電。{current_question['question']}",
                "session_id": context.get("session_id"),
                "stage": "FUNNEL_QUESTION"
            }
            
            self.logger.info(f"生成漏斗問題: {current_question['id']}")
            return response
            
        except Exception as e:
            self.logger.error(f"生成漏斗問題時發生錯誤: {e}")
            return self._create_error_response(context)
    
    def get_response_type(self) -> ResponseType:
        """獲取回應類型"""
        return ResponseType.FUNNEL_QUESTION
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        驗證上下文是否適合漏斗問題策略
        
        Args:
            context: 當前上下文
            
        Returns:
            是否適合使用此策略
        """
        # 檢查是否在漏斗階段
        stage = context.get("stage", "")
        needs_funnel = context.get("needs_funnel_question", False)
        
        return (stage == "FUNNEL_QUESTION" or 
                needs_funnel or 
                context.get("intent") == "ask_recommendation")
    
    def _get_next_question(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        獲取下一個需要詢問的問題
        
        Args:
            context: 當前上下文
            
        Returns:
            下一個問題配置，如果沒有則返回 None
        """
        # 獲取已填充的槽位
        filled_slots = context.get("slots", {})
        
        # 按優先級排序問題
        sorted_questions = sorted(self.funnel_questions, key=lambda x: x["priority"])
        
        # 找到第一個未填充的問題
        for question in sorted_questions:
            slot_name = question["slot_name"]
            if slot_name not in filled_slots or not filled_slots[slot_name]:
                return question
        
        # 如果所有問題都已回答，檢查是否達到推薦條件
        if self._can_generate_recommendation(filled_slots):
            return None
        
        # 如果還不能推薦，返回第一個問題
        return sorted_questions[0] if sorted_questions else None
    
    def _can_generate_recommendation(self, filled_slots: Dict[str, Any]) -> bool:
        """
        檢查是否可以生成推薦
        
        Args:
            filled_slots: 已填充的槽位
            
        Returns:
            是否可以生成推薦
        """
        # 關鍵槽位：用途和預算
        key_slots = ["usage_purpose", "price_range"]
        filled_key_slots = sum(1 for slot in key_slots if slot in filled_slots and filled_slots[slot])
        
        # 至少需要2個關鍵槽位才能生成推薦
        return filled_key_slots >= 2
    
    def _create_completion_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建漏斗完成回應
        
        Args:
            context: 當前上下文
            
        Returns:
            完成回應字典
        """
        return {
            "type": "funnel_completion",
            "message": "太好了！我已經收集到足夠的信息。讓我為您推薦最適合的筆電。",
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
            "message": "抱歉，我在處理您的問題時遇到了問題。請稍後再試。",
            "session_id": context.get("session_id"),
            "error": True
        }
    
    def get_funnel_progress(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        獲取漏斗進度
        
        Args:
            context: 當前上下文
            
        Returns:
            進度信息字典
        """
        filled_slots = context.get("slots", {})
        total_questions = len(self.funnel_questions)
        answered_questions = sum(1 for q in self.funnel_questions 
                               if q["slot_name"] in filled_slots and filled_slots[q["slot_name"]])
        
        return {
            "total_questions": total_questions,
            "answered_questions": answered_questions,
            "progress_percentage": (answered_questions / total_questions) * 100 if total_questions > 0 else 0,
            "can_recommend": self._can_generate_recommendation(filled_slots)
        }
