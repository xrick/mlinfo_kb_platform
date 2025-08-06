#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實體識別模組
基於規則和模式的實體識別系統
"""

import re
import json
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

@dataclass
class Entity:
    """實體類別"""
    text: str
    label: str
    start: int
    end: int
    confidence: float = 1.0

@dataclass
class Intent:
    """意圖類別"""
    name: str
    confidence: float
    keywords: List[str]

@dataclass
class EntityIntentRelation:
    """實體與意圖關係"""
    entity_text: str
    entity_label: str
    intent_name: str
    relation_type: str
    confidence: float

class EntityRecognitionSystem:
    """實體識別系統"""
    
    def __init__(self, config_path: str = None):
        """
        初始化實體識別系統
        
        Args:
            config_path: 配置文件路徑
        """
        self.config_path = config_path or "sales_rag_app/libs/services/sales_assistant/prompts/entity_patterns.json"
        self.entity_patterns = self._load_entity_patterns()
        self.intent_keywords = self._load_intent_keywords()
        
        # 預定義的實體類型
        self.entity_types = {
            'MODEL_NAME': '筆電型號',
            'MODEL_TYPE': '型號系列',
            'SPEC_TYPE': '規格類型',
            'COMPARISON_WORD': '比較詞彙',
            'TIME_WORD': '時間詞彙',
            'QUANTITY': '數量詞彙'
        }
        
        logging.info("實體識別系統初始化完成")
    
    def _load_entity_patterns(self) -> Dict:
        """載入實體識別模式"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('entity_patterns', {})
        except FileNotFoundError:
            logging.warning(f"實體模式配置文件不存在: {self.config_path}")
            return self._get_default_patterns()
        except Exception as e:
            logging.error(f"載入實體模式配置失敗: {e}")
            return self._get_default_patterns()
    
    def _load_intent_keywords(self) -> Dict:
        """載入意圖關鍵字"""
        try:
            intent_path = "sales_rag_app/libs/services/sales_assistant/prompts/query_keywords.json"
            with open(intent_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('intent_keywords', {})
        except Exception as e:
            logging.error(f"載入意圖關鍵字失敗: {e}")
            return {}
    
    def _get_default_patterns(self) -> Dict:
        """獲取預設的實體識別模式"""
        return {
            'MODEL_NAME': {
                'patterns': [
                    r'[A-Z]{2,3}\d{3}(?:-[A-Z]+)?(?:\s*:\s*[A-Z]+\d+[A-Z]*)?',
                    r'[A-Z]{2,3}\d{3}(?:-[A-Z]+)?'
                ],
                'description': '筆電型號識別'
            },
            'MODEL_TYPE': {
                'patterns': [
                    r'(?:819|839|928|958|960|AC01)(?=系列|型號|筆電|notebook|$|\s|[^\d])'
                ],
                'description': '型號系列識別'
            },
            'SPEC_TYPE': {
                'patterns': [
                    r'\b(?:cpu|gpu|記憶體|內存|内存|硬碟|硬盤|硬盘|電池|电池|螢幕|顯示|屏幕|显示)\b',
                    r'\b(?:processor|memory|storage|battery|screen|display)\b'
                ],
                'description': '規格類型識別'
            },
            'COMPARISON_WORD': {
                'patterns': [
                    r'\b(?:比較|比较|compare|差異|差异|difference|不同|vs|versus)\b'
                ],
                'description': '比較詞彙識別'
            },
            'TIME_WORD': {
                'patterns': [
                    r'\b(?:現在|目前|當前|current|now)\b'
                ],
                'description': '時間詞彙識別'
            },
            'QUANTITY': {
                'patterns': [
                    r'\b\d+(?:\.\d+)?\s*(?:GB|TB|Wh|W|kg|g|mm|inch)\b'
                ],
                'description': '數量詞彙識別'
            }
        }
    
    def recognize_entities(self, text: str) -> List[Entity]:
        """
        實體識別
        
        Args:
            text: 輸入文本
            
        Returns:
            識別出的實體列表
        """
        entities = []
        
        for entity_type, config in self.entity_patterns.items():
            patterns = config.get('patterns', [])
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    entity = Entity(
                        text=match.group(),
                        label=entity_type,
                        start=match.start(),
                        end=match.end(),
                        confidence=self._calculate_entity_confidence(match, entity_type)
                    )
                    entities.append(entity)
        
        # 去重並按位置排序
        entities = self._deduplicate_entities(entities)
        entities.sort(key=lambda x: x.start)
        
        logging.info(f"識別到 {len(entities)} 個實體: {[e.text for e in entities]}")
        return entities
    
    def _calculate_entity_confidence(self, match, entity_type: str) -> float:
        """計算實體識別的信心度"""
        base_confidence = 0.8
        
        # 根據實體類型調整信心度
        if entity_type == 'MODEL_NAME':
            # 檢查是否在預定義的模型名稱列表中
            if match.group() in self._get_available_modelnames():
                base_confidence = 1.0
            else:
                base_confidence = 0.7
        elif entity_type == 'MODEL_TYPE':
            if match.group() in ['819', '839', '928', '958', '960', 'AC01']:
                base_confidence = 1.0
            else:
                base_confidence = 0.6
        
        # 根據匹配長度調整
        length_factor = min(len(match.group()) / 10, 1.0)
        return base_confidence * (0.8 + 0.2 * length_factor)
    
    def _get_available_modelnames(self) -> List[str]:
        """獲取可用的模型名稱列表"""
        # 這裡可以從配置文件或數據庫獲取
        return [
            'AB819-S: FP6', 'AG958', 'AG958P', 'AG958V', 'AHP819: FP7R2',
            'AHP839', 'AHP958', 'AKK839', 'AMD819-S: FT6', 'AMD819: FT6',
            'APX819: FP7R2', 'APX839', 'APX958', 'ARB819-S: FP7R2', 'ARB839'
        ]
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """去除重複的實體"""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            key = (entity.text.lower(), entity.start, entity.end)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def detect_intent(self, text: str) -> Intent:
        """
        意圖檢測
        
        Args:
            text: 輸入文本
            
        Returns:
            檢測到的意圖
        """
        best_intent = 'general'
        best_confidence = 0.0
        matched_keywords = []
        
        text_lower = text.lower()
        
        for intent_name, config in self.intent_keywords.items():
            keywords = config.get('keywords', [])
            score = 0.0
            temp_keywords = []
            
            # 關鍵詞匹配
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += 1.0
                    temp_keywords.append(keyword)
            
            # 計算信心度
            if keywords:
                confidence = score / len(keywords)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_intent = intent_name
                    matched_keywords = temp_keywords
        
        return Intent(
            name=best_intent,
            confidence=best_confidence,
            keywords=matched_keywords
        )
    
    def identify_relations(self, text: str, entities: List[Entity], intent: Intent) -> List[EntityIntentRelation]:
        """
        識別實體與意圖之間的關係
        
        Args:
            text: 原始文本
            entities: 識別出的實體
            intent: 檢測到的意圖
            
        Returns:
            實體與意圖的關係列表
        """
        relations = []
        
        for entity in entities:
            relation_type = self._determine_relation_type(entity, intent, text)
            confidence = self._calculate_relation_confidence(entity, intent, text)
            
            relation = EntityIntentRelation(
                entity_text=entity.text,
                entity_label=entity.label,
                intent_name=intent.name,
                relation_type=relation_type,
                confidence=confidence
            )
            relations.append(relation)
        
        return relations
    
    def _determine_relation_type(self, entity: Entity, intent: Intent, text: str) -> str:
        """判斷關係類型"""
        entity_type = entity.label
        intent_name = intent.name
        
        # 根據實體類型和意圖類型判斷關係
        if entity_type == 'MODEL_NAME':
            if intent_name in ['comparison', 'specifications']:
                return 'target_model'
            else:
                return 'subject_model'
        
        elif entity_type == 'MODEL_TYPE':
            return 'model_series'
        
        elif entity_type == 'SPEC_TYPE':
            return 'specification_query'
        
        elif entity_type == 'COMPARISON_WORD':
            return 'comparison_indicator'
        
        elif entity_type == 'QUANTITY':
            return 'specification_value'
        
        else:
            return 'related_to'
    
    def _calculate_relation_confidence(self, entity: Entity, intent: Intent, text: str) -> float:
        """計算關係信心度"""
        base_confidence = entity.confidence * intent.confidence
        
        # 根據實體在文本中的位置調整
        text_length = len(text)
        position_factor = 1.0 - (entity.start / text_length) * 0.2
        
        # 根據實體與意圖關鍵詞的距離調整
        distance_factor = self._calculate_distance_factor(entity, intent, text)
        
        return base_confidence * position_factor * distance_factor
    
    def _calculate_distance_factor(self, entity: Entity, intent: Intent, text: str) -> float:
        """計算距離因子"""
        if not intent.keywords:
            return 1.0
        
        # 找到最近的關鍵詞距離
        min_distance = float('inf')
        for keyword in intent.keywords:
            keyword_pos = text.lower().find(keyword.lower())
            if keyword_pos != -1:
                distance = abs(entity.start - keyword_pos)
                min_distance = min(min_distance, distance)
        
        if min_distance == float('inf'):
            return 0.5
        
        # 距離越近，因子越大
        return max(0.5, 1.0 - (min_distance / len(text)))
    
    def process_text(self, text: str) -> Dict:
        """
        處理文本，返回完整的分析結果
        
        Args:
            text: 輸入文本
            
        Returns:
            包含實體、意圖和關係的完整分析結果
        """
        # 實體識別
        entities = self.recognize_entities(text)
        
        # 意圖檢測
        intent = self.detect_intent(text)
        
        # 關係識別
        relations = self.identify_relations(text, entities, intent)
        
        # 構建結果
        result = {
            'original_text': text,
            'timestamp': self._get_timestamp(),
            'entities': [
                {
                    'text': e.text,
                    'label': e.label,
                    'start': e.start,
                    'end': e.end,
                    'confidence': e.confidence
                }
                for e in entities
            ],
            'intent': {
                'name': intent.name,
                'confidence': intent.confidence,
                'keywords': intent.keywords
            },
            'relations': [
                {
                    'entity_text': r.entity_text,
                    'entity_label': r.entity_label,
                    'intent_name': r.intent_name,
                    'relation_type': r.relation_type,
                    'confidence': r.confidence
                }
                for r in relations
            ]
        }
        
        return result
    
    def _get_timestamp(self) -> str:
        """獲取當前時間戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def save_to_json(self, results: List[Dict], filename: str) -> bool:
        """
        保存結果到JSON文件
        
        Args:
            results: 分析結果列表
            filename: 輸出文件名
            
        Returns:
            是否保存成功
        """
        try:
            output_data = {
                'metadata': {
                    'created_at': self._get_timestamp(),
                    'total_entries': len(results),
                    'version': '1.0.0'
                },
                'results': results
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"結果已保存到: {filename}")
            return True
            
        except Exception as e:
            logging.error(f"保存JSON文件失敗: {e}")
            return False 