"""
回應生成策略抽象基類
定義所有回應生成策略必須實作的介面
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum


class ResponseType(Enum):
    """回應類型枚舉"""
    FUNNEL_QUESTION = "funnel_question"
    RECOMMENDATION = "recommendation"
    ELICITATION = "elicitation"
    GENERAL = "general"


class ResponseStrategy(ABC):
    """回應生成策略抽象基類"""
    
    def __init__(self, strategy_name: str):
        self.strategy_name = strategy_name
        self.logger = logging.getLogger(f"{__name__}.{strategy_name}")
    
    @abstractmethod
    def generate_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成回應
        
        Args:
            context: 當前上下文
            
        Returns:
            生成的回應字典
        """
        pass
    
    @abstractmethod
    def get_response_type(self) -> ResponseType:
        """獲取回應類型"""
        pass
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        驗證上下文是否適合此策略
        
        Args:
            context: 當前上下文
            
        Returns:
            是否適合使用此策略
        """
        # 預設實作：檢查基本必要字段
        required_fields = ["session_id", "user_message"]
        return all(field in context for field in required_fields)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """獲取策略信息"""
        return {
            "strategy_name": self.strategy_name,
            "response_type": self.get_response_type().value,
            "description": self.get_description()
        }
    
    def get_description(self) -> str:
        """獲取策略描述"""
        return f"{self.strategy_name} - {self.get_response_type().value} 回應生成策略"
    
    def preprocess_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        預處理上下文
        
        Args:
            context: 原始上下文
            
        Returns:
            預處理後的上下文
        """
        # 預設實作：添加策略相關的預處理邏輯
        processed_context = context.copy()
        processed_context["strategy_name"] = self.strategy_name
        processed_context["response_type"] = self.get_response_type().value
        return processed_context
    
    def postprocess_response(self, response: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        後處理回應
        
        Args:
            response: 原始回應
            context: 當前上下文
            
        Returns:
            後處理後的回應
        """
        # 預設實作：添加通用後處理邏輯
        processed_response = response.copy()
        processed_response["strategy_used"] = self.strategy_name
        processed_response["response_type"] = self.get_response_type().value
        return processed_response
