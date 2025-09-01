"""
通用回應策略
處理一般性的回應生成
"""

import logging
from typing import Dict, Any, List, Optional
from ..ResponseStrategy import ResponseStrategy, ResponseType


class GeneralResponseStrategy(ResponseStrategy):
    """通用回應策略"""
    
    def __init__(self):
        super().__init__("GeneralResponseStrategy")
        self.general_templates = self._load_general_templates()
    
    def _load_general_templates(self) -> Dict[str, str]:
        """載入通用回應模板"""
        return {
            "greeting": "您好！我是您的筆電購物助手，有什麼可以幫您的嗎？",
            "goodbye": "謝謝您的使用！如果還有任何問題，隨時歡迎詢問。",
            "thanks": "不客氣！很高興能幫助您。",
            "confirmation": "好的，我明白了。",
            "clarification": "請您再說清楚一點，這樣我才能給您更準確的建議。",
            "error": "抱歉，我遇到了一些問題。請稍後再試。",
            "unknown_intent": "抱歉，我不太理解您的意思。請您重新描述一下您的需求。",
            "help": "我可以幫您：\n1. 推薦適合的筆電\n2. 比較不同型號\n3. 回答產品相關問題\n請告訴我您需要什麼幫助。"
        }
    
    def generate_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成通用回應
        
        Args:
            context: 當前上下文
            
        Returns:
            通用回應字典
        """
        try:
            # 分析用戶意圖
            intent = context.get("intent", "unknown")
            
            # 根據意圖生成相應的回應
            if intent == "greet":
                response = self._create_greeting_response(context)
            elif intent == "goodbye":
                response = self._create_goodbye_response(context)
            elif intent == "thanks":
                response = self._create_thanks_response(context)
            elif intent == "confirm":
                response = self._create_confirmation_response(context)
            elif intent == "clarify":
                response = self._create_clarification_response(context)
            elif intent == "help":
                response = self._create_help_response(context)
            else:
                response = self._create_unknown_intent_response(context)
            
            self.logger.info(f"生成通用回應 - 意圖: {intent}")
            return response
            
        except Exception as e:
            self.logger.error(f"生成通用回應時發生錯誤: {e}")
            return self._create_error_response(context)
    
    def get_response_type(self) -> ResponseType:
        """獲取回應類型"""
        return ResponseType.GENERAL
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        驗證上下文是否適合通用策略
        
        Args:
            context: 當前上下文
            
        Returns:
            是否適合使用此策略
        """
        # 通用策略作為備選策略，總是返回 True
        return True
    
    def _create_greeting_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建問候回應
        
        Args:
            context: 當前上下文
            
        Returns:
            問候回應字典
        """
        return {
            "type": "general",
            "message": self.general_templates["greeting"],
            "session_id": context.get("session_id"),
            "stage": "INIT",
            "intent": "greet"
        }
    
    def _create_goodbye_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建告別回應
        
        Args:
            context: 當前上下文
            
        Returns:
            告別回應字典
        """
        return {
            "type": "general",
            "message": self.general_templates["goodbye"],
            "session_id": context.get("session_id"),
            "stage": "END",
            "intent": "goodbye"
        }
    
    def _create_thanks_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建感謝回應
        
        Args:
            context: 當前上下文
            
        Returns:
            感謝回應字典
        """
        return {
            "type": "general",
            "message": self.general_templates["thanks"],
            "session_id": context.get("session_id"),
            "intent": "thanks"
        }
    
    def _create_confirmation_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建確認回應
        
        Args:
            context: 當前上下文
            
        Returns:
            確認回應字典
        """
        return {
            "type": "general",
            "message": self.general_templates["confirmation"],
            "session_id": context.get("session_id"),
            "intent": "confirm"
        }
    
    def _create_clarification_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建澄清回應
        
        Args:
            context: 當前上下文
            
        Returns:
            澄清回應字典
        """
        return {
            "type": "general",
            "message": self.general_templates["clarification"],
            "session_id": context.get("session_id"),
            "stage": "ELICITATION",
            "needs_elicitation": True,
            "intent": "clarify"
        }
    
    def _create_help_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建幫助回應
        
        Args:
            context: 當前上下文
            
        Returns:
            幫助回應字典
        """
        return {
            "type": "general",
            "message": self.general_templates["help"],
            "session_id": context.get("session_id"),
            "intent": "help"
        }
    
    def _create_unknown_intent_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建未知意圖回應
        
        Args:
            context: 當前上下文
            
        Returns:
            未知意圖回應字典
        """
        return {
            "type": "general",
            "message": self.general_templates["unknown_intent"],
            "session_id": context.get("session_id"),
            "stage": "ELICITATION",
            "needs_elicitation": True,
            "intent": "unknown"
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
            "message": self.general_templates["error"],
            "session_id": context.get("session_id"),
            "error": True
        }
    
    def get_available_intents(self) -> List[str]:
        """
        獲取支援的意圖列表
        
        Returns:
            支援的意圖列表
        """
        return [
            "greet", "goodbye", "thanks", "confirm", 
            "clarify", "help", "unknown"
        ]
    
    def get_template(self, template_name: str) -> str:
        """
        獲取指定模板
        
        Args:
            template_name: 模板名稱
            
        Returns:
            模板內容
        """
        return self.general_templates.get(template_name, "")
    
    def add_template(self, template_name: str, template_content: str) -> None:
        """
        添加新模板
        
        Args:
            template_name: 模板名稱
            template_content: 模板內容
        """
        self.general_templates[template_name] = template_content
        self.logger.info(f"添加新模板: {template_name}")
    
    def remove_template(self, template_name: str) -> bool:
        """
        移除模板
        
        Args:
            template_name: 模板名稱
            
        Returns:
            是否成功移除
        """
        if template_name in self.general_templates:
            del self.general_templates[template_name]
            self.logger.info(f"移除模板: {template_name}")
            return True
        else:
            self.logger.warning(f"模板不存在: {template_name}")
            return False
