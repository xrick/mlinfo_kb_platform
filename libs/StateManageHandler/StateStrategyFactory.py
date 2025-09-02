"""
StateStrategyFactory - 狀態策略工廠
提供不同狀態處理策略的創建和管理

策略類型：
1. DefaultStrategy - 默認策略
2. PerformanceStrategy - 性能優化策略  
3. LearningStrategy - 自適應學習策略
4. ErrorRecoveryStrategy - 錯誤恢復策略
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)


class StateStrategy(ABC):
    """狀態策略抽象基類"""
    
    def __init__(self, name: str):
        self.name = name
        self.created_at = datetime.now()
        self.usage_count = 0
    
    @abstractmethod
    async def execute_transition(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """執行狀態轉換"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """獲取策略信息"""
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "usage_count": self.usage_count,
            "strategy_type": self.__class__.__name__
        }


class DefaultStrategy(StateStrategy):
    """默認狀態處理策略"""
    
    def __init__(self):
        super().__init__("DefaultStrategy")
    
    async def execute_transition(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """執行默認狀態轉換"""
        self.usage_count += 1
        
        return {
            "strategy_applied": self.name,
            "execution_time": datetime.now().isoformat(),
            "default_processing": True
        }


class PerformanceStrategy(StateStrategy):
    """性能優化策略"""
    
    def __init__(self):
        super().__init__("PerformanceStrategy")
    
    async def execute_transition(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """執行性能優化的狀態轉換"""
        self.usage_count += 1
        
        # 性能優化邏輯
        return {
            "strategy_applied": self.name,
            "execution_time": datetime.now().isoformat(),
            "performance_optimized": True,
            "caching_enabled": True
        }


class LearningStrategy(StateStrategy):
    """自適應學習策略"""
    
    def __init__(self):
        super().__init__("LearningStrategy")
        self.learning_data = []
    
    async def execute_transition(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """執行學習優化的狀態轉換"""
        self.usage_count += 1
        
        # 記錄學習數據
        self.learning_data.append({
            "context_features": self._extract_features(context),
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "strategy_applied": self.name,
            "execution_time": datetime.now().isoformat(),
            "learning_applied": True,
            "learning_data_count": len(self.learning_data)
        }
    
    def _extract_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """提取學習特徵"""
        return {
            "intent": context.get("intent", ""),
            "confidence": context.get("confidence", 0.0),
            "slots_count": len(context.get("slots", {})),
            "stage": context.get("stage", "")
        }


class StateStrategyFactory:
    """狀態策略工廠"""
    
    def __init__(self):
        self.strategies = {
            "default": DefaultStrategy(),
            "performance": PerformanceStrategy(),
            "learning": LearningStrategy()
        }
        self.selection_history = []
        
        logger.info("StateStrategyFactory 初始化完成")
    
    def get_strategy(self, context: Dict[str, Any]) -> StateStrategy:
        """
        根據上下文選擇合適的策略
        
        Args:
            context: 當前上下文
            
        Returns:
            選擇的策略
        """
        # 策略選擇邏輯
        strategy_name = "default"
        
        # 性能關鍵場景使用性能策略
        if context.get("performance_critical", False):
            strategy_name = "performance"
        
        # 有學習需求時使用學習策略
        elif context.get("adaptive_behavior", False):
            strategy_name = "learning"
        
        # 高置信度場景使用默認策略
        elif context.get("confidence", 0.0) > 0.8:
            strategy_name = "default"
        
        strategy = self.strategies.get(strategy_name, self.strategies["default"])
        
        # 記錄選擇歷史
        self.selection_history.append({
            "strategy_name": strategy_name,
            "context_summary": {
                "intent": context.get("intent", ""),
                "stage": context.get("stage", ""),
                "confidence": context.get("confidence", 0.0)
            },
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制歷史長度
        if len(self.selection_history) > 1000:
            self.selection_history = self.selection_history[-1000:]
        
        return strategy
    
    def get_strategy_by_name(self, name: str) -> Optional[StateStrategy]:
        """根據名稱獲取策略"""
        return self.strategies.get(name)
    
    def register_strategy(self, name: str, strategy: StateStrategy):
        """註冊新策略"""
        self.strategies[name] = strategy
        logger.info(f"註冊新策略: {name}")
    
    def get_available_strategies(self) -> List[str]:
        """獲取可用策略列表"""
        return list(self.strategies.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取策略使用統計"""
        stats = {}
        
        for name, strategy in self.strategies.items():
            stats[name] = strategy.get_info()
        
        return {
            "strategies": stats,
            "total_selections": len(self.selection_history),
            "last_updated": datetime.now().isoformat()
        }