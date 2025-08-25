#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chunking Strategy Pattern Implementation
實現分塊策略模式，支援多種分塊策略
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum


class ChunkingStrategyType(Enum):
    """分塊策略類型"""
    PARENT_CHILD = "parent_child"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class ChunkingStrategy(ABC):
    """分塊策略抽象基類"""
    
    def __init__(self, strategy_name: str):
        self.strategy_name = strategy_name
        self.logger = logging.getLogger(f"{__name__}.{strategy_name}")
    
    @abstractmethod
    def create_chunks(self, product: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        創建產品分塊
        
        Args:
            product: 產品數據字典
            
        Returns:
            (parent_chunk, child_chunks): Parent chunk和Child chunks列表
        """
        pass
    
    @abstractmethod
    def batch_create_chunks(self, products: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        批量創建產品分塊
        
        Args:
            products: 產品列表
            
        Returns:
            (all_parent_chunks, all_child_chunks): 所有父分塊和子分塊
        """
        pass
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """
        生成文本嵌入向量
        
        Args:
            text: 輸入文本
            
        Returns:
            嵌入向量
        """
        pass
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """獲取策略信息"""
        return {
            "strategy_name": self.strategy_name,
            "strategy_type": self.get_strategy_type(),
            "description": self.get_description()
        }
    
    @abstractmethod
    def get_strategy_type(self) -> ChunkingStrategyType:
        """獲取策略類型"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """獲取策略描述"""
        pass


class ChunkingContext:
    """分塊上下文 - 使用Strategy模式"""
    
    def __init__(self, default_strategy: ChunkingStrategy = None):
        self.logger = logging.getLogger(__name__)
        self._strategy = default_strategy
        self._strategies = {}
        
        if default_strategy:
            self._strategies[default_strategy.get_strategy_type()] = default_strategy
    
    def set_strategy(self, strategy: ChunkingStrategy):
        """設置分塊策略"""
        self._strategy = strategy
        self._strategies[strategy.get_strategy_type()] = strategy
        self.logger.info(f"設置分塊策略: {strategy.strategy_name}")
    
    def get_strategy(self, strategy_type: ChunkingStrategyType = None) -> ChunkingStrategy:
        """獲取分塊策略"""
        if strategy_type:
            return self._strategies.get(strategy_type, self._strategy)
        return self._strategy
    
    def create_chunks(self, product: Dict[str, Any], strategy_type: ChunkingStrategyType = None) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        使用指定策略創建分塊
        
        Args:
            product: 產品數據
            strategy_type: 策略類型，如果為None則使用當前策略
            
        Returns:
            (parent_chunk, child_chunks): 分塊結果
        """
        strategy = self.get_strategy(strategy_type)
        if not strategy:
            raise ValueError("未設置分塊策略")
        
        return strategy.create_chunks(product)
    
    def batch_create_chunks(self, products: List[Dict[str, Any]], strategy_type: ChunkingStrategyType = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        使用指定策略批量創建分塊
        
        Args:
            products: 產品列表
            strategy_type: 策略類型，如果為None則使用當前策略
            
        Returns:
            (all_parent_chunks, all_child_chunks): 分塊結果
        """
        strategy = self.get_strategy(strategy_type)
        if not strategy:
            raise ValueError("未設置分塊策略")
        
        return strategy.batch_create_chunks(products)
    
    def generate_embedding(self, text: str, strategy_type: ChunkingStrategyType = None) -> List[float]:
        """
        使用指定策略生成嵌入向量
        
        Args:
            text: 輸入文本
            strategy_type: 策略類型，如果為None則使用當前策略
            
        Returns:
            嵌入向量
        """
        strategy = self.get_strategy(strategy_type)
        if not strategy:
            raise ValueError("未設置分塊策略")
        
        return strategy.generate_embedding(text)
    
    def get_available_strategies(self) -> List[Dict[str, Any]]:
        """獲取所有可用策略信息"""
        return [strategy.get_strategy_info() for strategy in self._strategies.values()]
    
    def switch_strategy(self, strategy_type: ChunkingStrategyType):
        """切換到指定策略"""
        strategy = self._strategies.get(strategy_type)
        if strategy:
            self._strategy = strategy
            self.logger.info(f"切換到策略: {strategy.strategy_name}")
        else:
            raise ValueError(f"策略 {strategy_type.value} 不可用")
