"""
回應策略工廠
負責策略的註冊、選擇和管理
"""

import logging
from typing import Dict, Any, Optional, List
from .ResponseStrategy import ResponseStrategy, ResponseType


class ResponseStrategyFactory:
    """回應策略工廠"""
    
    def __init__(self):
        self.strategies: Dict[str, ResponseStrategy] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_strategy(self, strategy: ResponseStrategy) -> None:
        """
        註冊策略
        
        Args:
            strategy: 要註冊的策略實例
        """
        strategy_type = strategy.get_response_type().value
        self.strategies[strategy_type] = strategy
        self.logger.info(f"註冊策略: {strategy_type} - {strategy.strategy_name}")
    
    def get_strategy(self, response_type: str) -> Optional[ResponseStrategy]:
        """
        根據回應類型獲取策略
        
        Args:
            response_type: 回應類型
            
        Returns:
            對應的策略實例，如果不存在則返回 None
        """
        strategy = self.strategies.get(response_type)
        if strategy:
            self.logger.debug(f"獲取策略: {response_type}")
        else:
            self.logger.warning(f"未找到策略: {response_type}")
        return strategy
    
    def select_strategy_by_context(self, context: Dict[str, Any]) -> ResponseStrategy:
        """
        根據上下文智能選擇策略
        
        Args:
            context: 當前上下文
            
        Returns:
            選擇的策略實例
        """
        # 優先級順序：明確指定 > 意圖推斷 > 默認策略
        strategy = None
        
        # 1. 檢查是否有明確指定的回應類型
        if "response_type" in context:
            strategy = self.get_strategy(context["response_type"])
            if strategy:
                self.logger.info(f"使用明確指定的策略: {context['response_type']}")
                return strategy
        
        # 2. 根據意圖推斷策略
        intent = context.get("intent", "")
        stage = context.get("stage", "")
        
        if intent == "ask_recommendation" or stage == "RECOMMENDATION":
            strategy = self.get_strategy("recommendation")
            if strategy:
                self.logger.info("根據意圖選擇推薦策略")
                return strategy
        
        if stage == "FUNNEL_QUESTION" or context.get("needs_funnel_question"):
            strategy = self.get_strategy("funnel_question")
            if strategy:
                self.logger.info("根據階段選擇漏斗問題策略")
                return strategy
        
        if stage == "ELICITATION" or context.get("needs_elicitation"):
            strategy = self.get_strategy("elicitation")
            if strategy:
                self.logger.info("根據階段選擇信息收集策略")
                return strategy
        
        # 3. 使用默認策略
        strategy = self.get_strategy("general")
        if strategy:
            self.logger.info("使用默認通用策略")
            return strategy
        
        # 4. 如果沒有可用策略，拋出異常
        raise ValueError("沒有可用的回應策略")
    
    def get_available_strategies(self) -> List[Dict[str, Any]]:
        """
        獲取所有可用策略的信息
        
        Returns:
            策略信息列表
        """
        return [strategy.get_strategy_info() for strategy in self.strategies.values()]
    
    def validate_strategy(self, strategy: ResponseStrategy, context: Dict[str, Any]) -> bool:
        """
        驗證策略是否適合當前上下文
        
        Args:
            strategy: 要驗證的策略
            context: 當前上下文
            
        Returns:
            策略是否適合
        """
        return strategy.validate_context(context)
    
    def get_best_strategy(self, context: Dict[str, Any]) -> ResponseStrategy:
        """
        獲取最適合當前上下文的策略
        
        Args:
            context: 當前上下文
            
        Returns:
            最適合的策略
        """
        # 首先嘗試智能選擇
        try:
            return self.select_strategy_by_context(context)
        except ValueError:
            # 如果智能選擇失敗，返回第一個可用策略
            if self.strategies:
                first_strategy = list(self.strategies.values())[0]
                self.logger.warning(f"智能選擇失敗，使用第一個可用策略: {first_strategy.strategy_name}")
                return first_strategy
            else:
                raise ValueError("沒有註冊任何策略")
    
    def clear_strategies(self) -> None:
        """清除所有註冊的策略"""
        self.strategies.clear()
        self.logger.info("清除所有策略")
    
    def remove_strategy(self, response_type: str) -> bool:
        """
        移除指定策略
        
        Args:
            response_type: 要移除的策略類型
            
        Returns:
            是否成功移除
        """
        if response_type in self.strategies:
            del self.strategies[response_type]
            self.logger.info(f"移除策略: {response_type}")
            return True
        else:
            self.logger.warning(f"策略不存在: {response_type}")
            return False
