#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Slot Extractor V2
增強版槽位提取器 - 結合正則表達式、語義匹配和策略模式
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from .similarity_engine import SimilarityEngine
from .special_cases_knowledge import SpecialCasesKnowledge


class ExtractionStrategyType(Enum):
    """提取策略類型"""
    REGEX = "regex"
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class ExtractionStrategy(ABC):
    """提取策略抽象基類"""
    
    def __init__(self, strategy_name: str):
        self.strategy_name = strategy_name
        self.logger = logging.getLogger(f"{__name__}.{strategy_name}")
    
    @abstractmethod
    def extract_slots(self, user_input: str, slot_schema: Dict[str, Any]) -> Dict[str, Any]:
        """提取槽位"""
        pass
    
    @abstractmethod
    def get_confidence(self) -> float:
        """獲取置信度"""
        pass
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """獲取策略信息"""
        return {
            "strategy_name": self.strategy_name,
            "strategy_type": self.get_strategy_type(),
            "confidence": self.get_confidence()
        }
    
    @abstractmethod
    def get_strategy_type(self) -> ExtractionStrategyType:
        """獲取策略類型"""
        pass


class RegexExtractionStrategy(ExtractionStrategy):
    """正則表達式提取策略"""
    
    def __init__(self, slot_synonyms_enhanced: Dict[str, Any]):
        super().__init__("RegexExtractionStrategy")
        self.slot_synonyms = slot_synonyms_enhanced
        self._confidence = 0.0
    
    def extract_slots(self, user_input: str, slot_schema: Dict[str, Any]) -> Dict[str, Any]:
        """使用正則表達式提取槽位"""
        extracted_slots = {}
        total_matches = 0
        
        for slot_name, slot_config in self.slot_synonyms.items():
            if slot_name not in slot_schema:
                continue
                
            for value_name, value_config in slot_config.items():
                if "regex" not in value_config:
                    continue
                
                for pattern in value_config["regex"]:
                    try:
                        matches = re.findall(pattern, user_input, re.IGNORECASE)
                        if matches:
                            extracted_slots[slot_name] = value_name
                            total_matches += 1
                            self.logger.debug(f"正則匹配成功: {slot_name}={value_name} (pattern: {pattern})")
                            break
                    except re.error as e:
                        self.logger.warning(f"正則表達式錯誤: {pattern}, 錯誤: {e}")
                        continue
        
        # 計算置信度
        if total_matches > 0:
            self._confidence = min(0.95, 0.7 + (total_matches * 0.1))
        else:
            self._confidence = 0.0
        
        return extracted_slots
    
    def get_confidence(self) -> float:
        return self._confidence
    
    def get_strategy_type(self) -> ExtractionStrategyType:
        return ExtractionStrategyType.REGEX


class SemanticExtractionStrategy(ExtractionStrategy):
    """語義提取策略"""
    
    def __init__(self, similarity_engine: SimilarityEngine, slot_synonyms_enhanced: Dict[str, Any]):
        super().__init__("SemanticExtractionStrategy")
        self.similarity_engine = similarity_engine
        self.slot_synonyms = slot_synonyms_enhanced
        self._confidence = 0.0
        self.similarity_threshold = 0.75
    
    def extract_slots(self, user_input: str, slot_schema: Dict[str, Any]) -> Dict[str, Any]:
        """使用語義相似度提取槽位"""
        extracted_slots = {}
        best_matches = {}
        
        for slot_name, slot_config in self.slot_synonyms.items():
            if slot_name not in slot_schema:
                continue
            
            slot_best_match = None
            slot_best_score = 0.0
            
            for value_name, value_config in slot_config.items():
                if "semantic" not in value_config:
                    continue
                
                for semantic_term in value_config["semantic"]:
                    try:
                        similarity = self.similarity_engine.calculate_similarity(
                            user_input, semantic_term
                        )
                        
                        if similarity > slot_best_score and similarity >= self.similarity_threshold:
                            slot_best_score = similarity
                            slot_best_match = value_name
                            
                    except Exception as e:
                        self.logger.debug(f"語義計算失敗: {e}")
                        continue
            
            if slot_best_match:
                extracted_slots[slot_name] = slot_best_match
                best_matches[slot_name] = slot_best_score
                self.logger.debug(f"語義匹配成功: {slot_name}={slot_best_match} (score: {slot_best_score:.3f})")
        
        # 計算置信度
        if best_matches:
            avg_score = sum(best_matches.values()) / len(best_matches)
            self._confidence = min(0.9, avg_score)
        else:
            self._confidence = 0.0
        
        return extracted_slots
    
    def get_confidence(self) -> float:
        return self._confidence
    
    def get_strategy_type(self) -> ExtractionStrategyType:
        return ExtractionStrategyType.SEMANTIC


class KeywordExtractionStrategy(ExtractionStrategy):
    """關鍵詞提取策略"""
    
    def __init__(self, slot_synonyms_enhanced: Dict[str, Any]):
        super().__init__("KeywordExtractionStrategy")
        self.slot_synonyms = slot_synonyms_enhanced
        self._confidence = 0.0
    
    def extract_slots(self, user_input: str, slot_schema: Dict[str, Any]) -> Dict[str, Any]:
        """使用關鍵詞匹配提取槽位"""
        extracted_slots = {}
        total_matches = 0
        
        user_input_lower = user_input.lower()
        
        for slot_name, slot_config in self.slot_synonyms.items():
            if slot_name not in slot_schema:
                continue
                
            for value_name, value_config in slot_config.items():
                if "keywords" not in value_config:
                    continue
                
                for keyword in value_config["keywords"]:
                    if keyword.lower() in user_input_lower:
                        extracted_slots[slot_name] = value_name
                        total_matches += 1
                        self.logger.debug(f"關鍵詞匹配成功: {slot_name}={value_name} (keyword: {keyword})")
                        break
        
        # 計算置信度
        if total_matches > 0:
            self._confidence = min(0.85, 0.6 + (total_matches * 0.1))
        else:
            self._confidence = 0.0
        
        return extracted_slots
    
    def get_confidence(self) -> float:
        return self._confidence
    
    def get_strategy_type(self) -> ExtractionStrategyType:
        return ExtractionStrategyType.KEYWORD


class HybridExtractionStrategy(ExtractionStrategy):
    """混合提取策略"""
    
    def __init__(self, strategies: List[ExtractionStrategy]):
        super().__init__("HybridExtractionStrategy")
        self.strategies = strategies
        self._confidence = 0.0
    
    def extract_slots(self, user_input: str, slot_schema: Dict[str, Any]) -> Dict[str, Any]:
        """使用混合策略提取槽位"""
        all_results = {}
        strategy_weights = {
            ExtractionStrategyType.REGEX: 0.4,
            ExtractionStrategyType.SEMANTIC: 0.35,
            ExtractionStrategyType.KEYWORD: 0.25
        }
        
        # 執行所有策略
        for strategy in self.strategies:
            try:
                result = strategy.extract_slots(user_input, slot_schema)
                strategy_type = strategy.get_strategy_type()
                weight = strategy_weights.get(strategy_type, 0.1)
                
                for slot_name, slot_value in result.items():
                    if slot_name not in all_results:
                        all_results[slot_name] = {
                            'value': slot_value,
                            'confidence': strategy.get_confidence() * weight,
                            'strategies': [strategy_type.value]
                        }
                    else:
                        # 如果多個策略都匹配到同一個槽位，取最高置信度
                        current_confidence = all_results[slot_name]['confidence']
                        new_confidence = strategy.get_confidence() * weight
                        
                        if new_confidence > current_confidence:
                            all_results[slot_name]['value'] = slot_value
                            all_results[slot_name]['confidence'] = new_confidence
                        
                        all_results[slot_name]['strategies'].append(strategy_type.value)
                        
            except Exception as e:
                self.logger.error(f"策略執行失敗: {strategy.strategy_name}, 錯誤: {e}")
                continue
        
        # 轉換為最終結果
        extracted_slots = {}
        total_confidence = 0.0
        
        for slot_name, slot_info in all_results.items():
            if slot_info['confidence'] >= 0.3:  # 最低置信度閾值
                extracted_slots[slot_name] = slot_info['value']
                total_confidence += slot_info['confidence']
        
        # 計算整體置信度
        if extracted_slots:
            self._confidence = total_confidence / len(extracted_slots)
        else:
            self._confidence = 0.0
        
        return extracted_slots
    
    def get_confidence(self) -> float:
        return self._confidence
    
    def get_strategy_type(self) -> ExtractionStrategyType:
        return ExtractionStrategyType.HYBRID


class EnhancedSlotExtractorV2:
    """增強版槽位提取器 V2"""
    
    def __init__(self, llm_manager, slot_schema: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.llm_manager = llm_manager
        self.slot_schema = slot_schema
        
        # 初始化組件
        self.similarity_engine = SimilarityEngine()
        self.special_cases_knowledge = SpecialCasesKnowledge()
        
        # 載入增強的槽位同義詞
        self.slot_synonyms_enhanced = self._load_enhanced_slot_synonyms()
        
        # 初始化提取策略
        self.strategies = self._initialize_strategies()
        self.hybrid_strategy = HybridExtractionStrategy(self.strategies)
        
        self.logger.info("EnhancedSlotExtractorV2 初始化完成")
    
    def _load_enhanced_slot_synonyms(self) -> Dict[str, Any]:
        """載入增強的槽位同義詞"""
        try:
            import json
            from pathlib import Path
            
            # 嘗試載入增強版本
            enhanced_path = Path(__file__).parent / "humandata" / "slot_synonyms_enhanced.json"
            if enhanced_path.exists():
                with open(enhanced_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # 如果增強版本不存在，載入基礎版本
            base_path = Path(__file__).parent / "humandata" / "slot_synonyms.json"
            if base_path.exists():
                with open(base_path, 'r', encoding='utf-8') as f:
                    base_data = json.load(f)
                    # 轉換為增強格式
                    return self._convert_to_enhanced_format(base_data)
            
            self.logger.warning("無法載入槽位同義詞檔案")
            return {}
            
        except Exception as e:
            self.logger.error(f"載入槽位同義詞失敗: {e}")
            return {}
    
    def _convert_to_enhanced_format(self, base_data: Dict[str, Any]) -> Dict[str, Any]:
        """將基礎格式轉換為增強格式"""
        enhanced_data = {}
        
        for slot_name, slot_values in base_data.items():
            enhanced_data[slot_name] = {}
            for value_name, keywords in slot_values.items():
                enhanced_data[slot_name][value_name] = {
                    "keywords": keywords,
                    "regex": [f"\\b{re.escape(kw)}\\b" for kw in keywords[:3]],  # 前3個關鍵詞轉為正則
                    "semantic": keywords  # 所有關鍵詞都可用於語義匹配
                }
        
        return enhanced_data
    
    def _initialize_strategies(self) -> List[ExtractionStrategy]:
        """初始化提取策略"""
        strategies = [
            RegexExtractionStrategy(self.slot_synonyms_enhanced),
            SemanticExtractionStrategy(self.similarity_engine, self.slot_synonyms_enhanced),
            KeywordExtractionStrategy(self.slot_synonyms_enhanced)
        ]
        return strategies
    
    def extract_slots_with_classification(self, user_input: str, current_slots: Dict[str, Any], 
                                        session_id: str) -> Dict[str, Any]:
        """使用分類方法提取槽位"""
        try:
            self.logger.info(f"增強型槽位提取V2，輸入: {user_input[:50]}...")
            
            # 步驟1: 檢查特殊案例
            special_case_result = self.special_cases_knowledge.match_special_case(user_input)
            if special_case_result:
                self.logger.info(f"找到特殊案例匹配: {special_case_result['case_id']}")
                return {
                    "success": True,
                    "extraction_method": "special_case_knowledge",
                    "extracted_slots": special_case_result.get("inferred_slots", {}),
                    "confidence": special_case_result.get("confidence", 0.9),
                    "special_case_id": special_case_result['case_id']
                }
            
            # 步驟2: 使用混合策略提取
            hybrid_result = self.hybrid_strategy.extract_slots(user_input, self.slot_schema)
            
            if hybrid_result:
                self.logger.info(f"混合策略提取成功: {len(hybrid_result)} 個槽位")
                return {
                    "success": True,
                    "extraction_method": "hybrid_strategy",
                    "extracted_slots": hybrid_result,
                    "confidence": self.hybrid_strategy.get_confidence(),
                    "strategy_details": {
                        strategy.get_strategy_type().value: strategy.get_confidence()
                        for strategy in self.strategies
                    }
                }
            
            # 步驟3: 使用LLM進行智能提取
            llm_result = self._extract_with_llm(user_input, current_slots)
            if llm_result:
                self.logger.info("LLM提取成功")
                return {
                    "success": True,
                    "extraction_method": "llm_classification",
                    "extracted_slots": llm_result,
                    "confidence": 0.8
                }
            
            # 步驟4: 返回空結果
            self.logger.info("未找到匹配的槽位")
            return {
                "success": True,
                "extraction_method": "no_match",
                "extracted_slots": {},
                "confidence": 0.0
            }
            
        except Exception as e:
            self.logger.error(f"槽位提取失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "extracted_slots": {},
                "confidence": 0.0
            }
    
    def _extract_with_llm(self, user_input: str, current_slots: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM進行智能槽位提取"""
        try:
            # 這裡可以實現LLM-based的槽位提取邏輯
            # 暫時返回空結果，可以根據需要擴展
            return {}
        except Exception as e:
            self.logger.error(f"LLM提取失敗: {e}")
            return {}
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """獲取策略信息"""
        return {
            "available_strategies": [
                strategy.get_strategy_info() for strategy in self.strategies
            ],
            "hybrid_strategy": self.hybrid_strategy.get_strategy_info(),
            "slot_schema": self.slot_schema,
            "enhanced_synonyms_loaded": len(self.slot_synonyms_enhanced) > 0
        }
