#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版實體識別模組
基於規則和模式的實體識別系統，支援模糊匹配和上下文推斷
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
    match_type: str = "exact"  # exact, fuzzy, context, inferred

@dataclass
class Intent:
    """意圖類別"""
    name: str
    confidence: float
    keywords: List[str]
    match_type: str = "keyword"

@dataclass
class EntityIntentRelation:
    """實體與意圖關係"""
    entity_text: str
    entity_label: str
    intent_name: str
    relation_type: str
    confidence: float

class EnhancedEntityRecognitionSystem:
    """增強版實體識別系統"""
    
    def __init__(self, 
                 entity_config_path: str = None, 
                 intent_config_path: str = None):
        """
        初始化增強版實體識別系統
        
        Args:
            entity_config_path: 實體配置文件路徑
            intent_config_path: 意圖配置文件路徑
        """
        self.entity_config_path = entity_config_path or "sales_rag_app/libs/services/sales_assistant/prompts/entity_patterns_enhanced.json"
        self.intent_config_path = intent_config_path or "sales_rag_app/libs/services/sales_assistant/prompts/query_keywords_enhanced.json"
        
        self.entity_patterns = self._load_entity_patterns()
        self.intent_keywords = self._load_intent_keywords()
        self.recognition_strategy = self.entity_patterns.get('recognition_strategy', {})
        
        # 預設信心度權重
        self.confidence_weights = self.recognition_strategy.get('confidence_weights', {
            'exact_match': 1.0,
            'fuzzy_match': 0.8,
            'context_match': 0.7,
            'pattern_match': 0.6,
            'implicit_match': 0.5
        })
        
        logging.info("增強版實體識別系統初始化完成")
    
    def _load_entity_patterns(self) -> Dict:
        """載入增強版實體識別模式"""
        try:
            with open(self.entity_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except FileNotFoundError:
            logging.warning(f"增強版實體模式配置文件不存在: {self.entity_config_path}")
            return self._get_fallback_entity_patterns()
        except Exception as e:
            logging.error(f"載入增強版實體模式配置失敗: {e}")
            return self._get_fallback_entity_patterns()
    
    def _load_intent_keywords(self) -> Dict:
        """載入增強版意圖關鍵字"""
        try:
            with open(self.intent_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('intent_keywords', {})
        except Exception as e:
            logging.error(f"載入增強版意圖關鍵字失敗: {e}")
            return {}
    
    def _get_fallback_entity_patterns(self) -> Dict:
        """獲取後備實體識別模式"""
        return {
            'entity_patterns': {
                'MODEL_NAME': {
                    'exact_patterns': [r'[A-Z]{2,3}\d{3}(?:-[A-Z]+)?'],
                    'fuzzy_patterns': [r'\b(819|839|958)系列\b'],
                    'description': '筆電型號識別'
                }
            }
        }
    
    def recognize_entities_enhanced(self, text: str) -> List[Entity]:
        """
        增強版實體識別，支援多種匹配策略
        
        Args:
            text: 輸入文本
            
        Returns:
            識別出的實體列表
        """
        entities = []
        entity_patterns = self.entity_patterns.get('entity_patterns', {})
        
        for entity_type, config in entity_patterns.items():
            # 1. 精確模式匹配
            exact_entities = self._match_exact_patterns(text, entity_type, config)
            entities.extend(exact_entities)
            
            # 2. 模糊模式匹配
            fuzzy_entities = self._match_fuzzy_patterns(text, entity_type, config)
            entities.extend(fuzzy_entities)
            
            # 3. 增強模式匹配
            enhanced_entities = self._match_enhanced_patterns(text, entity_type, config)
            entities.extend(enhanced_entities)
            
            # 4. 上下文推斷
            context_entities = self._infer_from_context(text, entity_type, config)
            entities.extend(context_entities)
        
        # 去重、排序和合併
        entities = self._deduplicate_and_merge_entities(entities)
        entities.sort(key=lambda x: (x.start, -x.confidence))
        
        logging.info(f"增強版識別到 {len(entities)} 個實體: {[(e.text, e.label, e.match_type, e.confidence) for e in entities]}")
        return entities
    
    def _match_exact_patterns(self, text: str, entity_type: str, config: Dict) -> List[Entity]:
        """精確模式匹配"""
        entities = []
        exact_patterns = config.get('exact_patterns', config.get('patterns', []))
        
        for pattern in exact_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = Entity(
                    text=match.group(),
                    label=entity_type,
                    start=match.start(),
                    end=match.end(),
                    confidence=self.confidence_weights['exact_match'],
                    match_type="exact"
                )
                entities.append(entity)
        
        return entities
    
    def _match_fuzzy_patterns(self, text: str, entity_type: str, config: Dict) -> List[Entity]:
        """模糊模式匹配"""
        entities = []
        fuzzy_patterns = config.get('fuzzy_patterns', [])
        
        for pattern in fuzzy_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = Entity(
                    text=match.group(),
                    label=entity_type,
                    start=match.start(),
                    end=match.end(),
                    confidence=self.confidence_weights['fuzzy_match'],
                    match_type="fuzzy"
                )
                entities.append(entity)
        
        return entities
    
    def _match_enhanced_patterns(self, text: str, entity_type: str, config: Dict) -> List[Entity]:
        """增強模式匹配"""
        entities = []
        enhanced_patterns = config.get('enhanced_patterns', [])
        question_patterns = config.get('question_patterns', [])
        
        all_patterns = enhanced_patterns + question_patterns
        
        for pattern in all_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = Entity(
                    text=match.group(),
                    label=entity_type,
                    start=match.start(),
                    end=match.end(),
                    confidence=self.confidence_weights['pattern_match'],
                    match_type="pattern"
                )
                entities.append(entity)
        
        return entities
    
    def _infer_from_context(self, text: str, entity_type: str, config: Dict) -> List[Entity]:
        """從上下文推斷實體"""
        entities = []
        context_mapping = config.get('context_mapping', {})
        
        if not context_mapping:
            return entities
        
        text_lower = text.lower()
        
        for context_word, mapped_values in context_mapping.items():
            if context_word.lower() in text_lower:
                for value in mapped_values:
                    entity = Entity(
                        text=value,
                        label=entity_type,
                        start=0,  # 推斷的實體沒有具體位置
                        end=0,
                        confidence=self.confidence_weights['context_match'],
                        match_type="context"
                    )
                    entities.append(entity)
        
        return entities
    
    def _deduplicate_and_merge_entities(self, entities: List[Entity]) -> List[Entity]:
        """去重並合併實體"""
        if not entities:
            return []
        
        # 按照文本和標籤分組
        entity_groups = {}
        for entity in entities:
            key = (entity.text.lower(), entity.label)
            if key not in entity_groups:
                entity_groups[key] = []
            entity_groups[key].append(entity)
        
        # 對每組選擇最佳實體
        merged_entities = []
        for key, group in entity_groups.items():
            # 選擇信心度最高的實體
            best_entity = max(group, key=lambda x: x.confidence)
            merged_entities.append(best_entity)
        
        return merged_entities
    
    def detect_hierarchical_intent_enhanced(self, text: str) -> dict:
        """
        增強版階層式意圖檢測，支援更靈活的匹配
        
        Args:
            text: 輸入文本
            
        Returns:
            包含基礎意圖、細分意圖和相關資訊的字典
        """
        try:
            text_lower = text.lower()
            base_intents = {}
            sub_intents = {}
            all_matched_keywords = []
            
            # 1. 檢測基礎意圖（使用增強關鍵字）
            for intent_name, intent_config in self.intent_keywords.items():
                # 基礎關鍵字匹配
                base_keywords = intent_config.get('keywords', [])
                patterns = intent_config.get('patterns', [])
                
                score = 0.0
                matched_keywords = []
                
                # 關鍵字匹配
                for keyword in base_keywords:
                    if keyword.lower() in text_lower:
                        keyword_score = self._calculate_keyword_score(keyword, text_lower)
                        score += keyword_score
                        matched_keywords.append(keyword)
                
                # 模式匹配
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        pattern_score = 1.5  # 模式匹配給予更高分數
                        score += pattern_score
                        matched_keywords.append(f"pattern:{pattern}")
                
                if score > 0:
                    confidence = min(score / max(len(base_keywords), 1), 1.0)
                    base_intents[intent_name] = {
                        "score": score,
                        "confidence": confidence,
                        "keywords": matched_keywords,
                        "description": intent_config.get("description", "")
                    }
                    all_matched_keywords.extend(matched_keywords)
                
                # 2. 檢測細分意圖
                sub_intent_configs = intent_config.get('sub_intents', {})
                for sub_intent_name, sub_config in sub_intent_configs.items():
                    sub_keywords = sub_config.get('keywords', [])
                    sub_patterns = sub_config.get('patterns', [])
                    sub_score = 0.0
                    sub_matched_keywords = []
                    
                    # 細分關鍵字匹配
                    for keyword in sub_keywords:
                        if keyword.lower() in text_lower:
                            keyword_score = self._calculate_keyword_score(keyword, text_lower) * 1.2  # 細分意圖權重更高
                            sub_score += keyword_score
                            sub_matched_keywords.append(keyword)
                    
                    # 細分模式匹配
                    for pattern in sub_patterns:
                        if re.search(pattern, text, re.IGNORECASE):
                            pattern_score = 2.0  # 細分模式匹配分數更高
                            sub_score += pattern_score
                            sub_matched_keywords.append(f"pattern:{pattern}")
                    
                    if sub_score > 0:
                        sub_confidence = min(sub_score / max(len(sub_keywords), 1), 1.0)
                        sub_intents[sub_intent_name] = {
                            "score": sub_score,
                            "confidence": sub_confidence,
                            "keywords": sub_matched_keywords,
                            "parent_intent": intent_name,
                            "description": sub_config.get("description", ""),
                            "priority_specs": sub_config.get("priority_specs", []),
                            "scenarios": sub_config.get("scenarios", [])
                        }
                        all_matched_keywords.extend(sub_matched_keywords)
            
            # 3. 合併和排序意圖
            all_intents = {}
            
            # 添加基礎意圖
            for intent_name, intent_data in base_intents.items():
                all_intents[intent_name] = intent_data
            
            # 添加細分意圖（給予更高權重）
            for sub_intent_name, sub_intent_data in sub_intents.items():
                sub_intent_data["score"] *= 1.3
                all_intents[sub_intent_name] = sub_intent_data
            
            # 按分數排序
            sorted_intents = sorted(all_intents.items(), key=lambda x: x[1]["score"], reverse=True)
            
            # 構建結果
            result = {
                "base_intents": base_intents,
                "sub_intents": sub_intents,
                "all_intents": sorted_intents,
                "primary_intent": "general",
                "primary_intent_type": "base",
                "confidence_score": 0.0,
                "matched_keywords": all_matched_keywords,
                "high_confidence_intents": [],
                "intent_analysis": {
                    "total_base_intents": len(base_intents),
                    "total_sub_intents": len(sub_intents),
                    "has_hierarchical_match": len(sub_intents) > 0,
                    "enhanced_matching": True
                }
            }
            
            # 設定主要意圖（降低閾值以提供更多有用回應）
            if sorted_intents:
                primary_intent_name = sorted_intents[0][0]
                primary_intent_data = sorted_intents[0][1]
                
                result["primary_intent"] = primary_intent_name
                result["confidence_score"] = primary_intent_data["confidence"]
                
                # 判斷是基礎意圖還是細分意圖
                if primary_intent_name in sub_intents:
                    result["primary_intent_type"] = "sub"
                    result["parent_intent"] = primary_intent_data.get("parent_intent")
                    result["priority_specs"] = primary_intent_data.get("priority_specs", [])
                    result["scenarios"] = primary_intent_data.get("scenarios", [])
                else:
                    result["primary_intent_type"] = "base"
                
                # 提取高信心度的意圖列表（降低閾值從0.3到0.2）
                high_confidence_intents = [
                    {
                        "name": intent_name,
                        "type": "sub" if intent_name in sub_intents else "base",
                        "confidence": intent_data["confidence"],
                        "keywords": intent_data["keywords"]
                    }
                    for intent_name, intent_data in sorted_intents
                    if intent_data["confidence"] > 0.2  # 降低閾值
                ]
                
                result["high_confidence_intents"] = high_confidence_intents
            
            return result
            
        except Exception as e:
            logging.error(f"增強版階層式意圖檢測失敗: {e}")
            return {
                "base_intents": {},
                "sub_intents": {},
                "all_intents": [],
                "primary_intent": "general",
                "primary_intent_type": "base",
                "confidence_score": 0.0,
                "matched_keywords": [],
                "intent_analysis": {
                    "total_base_intents": 0,
                    "total_sub_intents": 0,
                    "has_hierarchical_match": False,
                    "enhanced_matching": False,
                    "error": str(e)
                },
                "high_confidence_intents": []
            }
    
    def _calculate_keyword_score(self, keyword: str, text_lower: str) -> float:
        """計算關鍵字匹配分數"""
        base_score = 1.0
        
        # 根據關鍵字長度調整權重
        length_factor = (len(keyword) / 10.0 + 0.5)
        base_score *= length_factor
        
        # 檢查是否為完整詞彙匹配
        if f" {keyword.lower()} " in f" {text_lower} ":
            base_score *= 1.5
        
        # 檢查關鍵字在文本中的位置（前面的權重更高）
        keyword_pos = text_lower.find(keyword.lower())
        if keyword_pos != -1:
            position_factor = 1.0 - (keyword_pos / len(text_lower)) * 0.2
            base_score *= position_factor
        
        return base_score
    
    def generate_smart_response_context(self, text: str, entities: List[Entity], intent_result: Dict) -> Dict:
        """
        生成智能回應上下文，用於指導回應生成
        
        Args:
            text: 原始查詢文本
            entities: 識別出的實體
            intent_result: 意圖檢測結果
            
        Returns:
            智能回應上下文
        """
        context = {
            "original_query": text,
            "detected_entities": [
                {
                    "text": e.text,
                    "label": e.label,
                    "confidence": e.confidence,
                    "match_type": e.match_type
                }
                for e in entities
            ],
            "intent_analysis": intent_result,
            "response_strategy": self._determine_response_strategy(text, entities, intent_result),
            "recommended_models": self._recommend_models_from_context(text, entities, intent_result),
            "priority_specs": self._extract_priority_specs(intent_result),
            "user_context": self._analyze_user_context(text, entities, intent_result)
        }
        
        return context
    
    def _determine_response_strategy(self, text: str, entities: List[Entity], intent_result: Dict) -> str:
        """確定回應策略"""
        # 檢查是否有比較意圖
        if any(e.label == "COMPARISON_WORD" or e.label == "IMPLICIT_COMPARISON" for e in entities):
            return "comparison"
        
        # 檢查是否有具體型號
        model_entities = [e for e in entities if e.label in ["MODEL_NAME", "MODEL_TYPE"]]
        if model_entities:
            if len(model_entities) > 1:
                return "model_comparison"
            else:
                return "single_model_detail"
        
        # 檢查主要意圖
        primary_intent = intent_result.get("primary_intent", "general")
        
        if primary_intent in ["battery", "display", "cpu", "gpu", "memory", "storage"]:
            return "spec_comparison"
        elif primary_intent == "latest":
            return "latest_products"
        elif primary_intent in ["usage_scenario"]:
            return "scenario_recommendation"
        else:
            return "general_recommendation"
    
    def _recommend_models_from_context(self, text: str, entities: List[Entity], intent_result: Dict) -> List[str]:
        """根據上下文推薦型號"""
        recommended = []
        
        # 從實體中提取已識別的型號
        for entity in entities:
            if entity.label in ["MODEL_NAME", "MODEL_TYPE"] and entity.match_type == "context":
                recommended.append(entity.text)
        
        # 根據使用場景推薦
        scenarios = intent_result.get("scenarios", [])
        if "遊戲" in scenarios or "電競" in scenarios:
            recommended.append("958")
        elif "商務" in scenarios or "辦公" in scenarios:
            recommended.append("819")
        elif "學習" in scenarios:
            recommended.extend(["819", "839"])
        
        # 如果沒有具體推薦，根據意圖推薦
        if not recommended:
            primary_intent = intent_result.get("primary_intent", "general")
            if primary_intent in ["gaming_gpu", "gaming_cpu", "gaming_memory"]:
                recommended.append("958")
            elif primary_intent in ["long_battery", "energy_efficient_cpu"]:
                recommended.append("819")
            else:
                recommended.extend(["958", "839", "819"])  # 默認顯示所有
        
        return list(set(recommended))  # 去重
    
    def _extract_priority_specs(self, intent_result: Dict) -> List[str]:
        """提取優先規格"""
        priority_specs = intent_result.get("priority_specs", [])
        
        # 如果沒有優先規格，根據主要意圖推斷
        if not priority_specs:
            primary_intent = intent_result.get("primary_intent", "general")
            spec_mapping = {
                "battery": ["battery", "cpu"],
                "display": ["lcd", "gpu"],
                "cpu": ["cpu", "memory"],
                "gpu": ["gpu", "cpu", "memory"],
                "memory": ["memory", "cpu"],
                "storage": ["storage", "cpu"],
                "portability": ["structconfig", "battery"],
                "connectivity": ["iointerface", "wireless"]
            }
            priority_specs = spec_mapping.get(primary_intent, ["cpu", "gpu", "memory"])
        
        return priority_specs
    
    def _analyze_user_context(self, text: str, entities: List[Entity], intent_result: Dict) -> Dict:
        """分析用戶上下文"""
        context = {
            "query_type": "unknown",
            "user_expertise": "beginner",  # beginner, intermediate, expert
            "urgency": "normal",  # low, normal, high
            "specificity": "general"  # specific, moderate, general
        }
        
        # 分析查詢類型
        if any(e.label == "COMPARISON_WORD" for e in entities):
            context["query_type"] = "comparison"
        elif any(e.label == "MODEL_NAME" for e in entities):
            context["query_type"] = "specific_model"
        elif intent_result.get("primary_intent") != "general":
            context["query_type"] = "spec_inquiry"
        
        # 分析用戶專業程度
        technical_terms = ["cpu", "gpu", "ram", "ssd", "nvme", "ddr", "ryzen", "radeon"]
        if any(term in text.lower() for term in technical_terms):
            context["user_expertise"] = "intermediate"
        
        detailed_specs = ["tdp", "pcie", "cores", "threads", "cache", "bandwidth"]
        if any(term in text.lower() for term in detailed_specs):
            context["user_expertise"] = "expert"
        
        # 分析查詢具體程度
        if len(entities) > 3:
            context["specificity"] = "specific"
        elif len(entities) > 1:
            context["specificity"] = "moderate"
        
        return context

    def detect_intent(self, text: str) -> Intent:
        """
        為向後兼容提供的意圖檢測接口
        """
        hierarchical_result = self.detect_hierarchical_intent_enhanced(text)
        
        return Intent(
            name=hierarchical_result.get("primary_intent", "general"),
            confidence=hierarchical_result.get("confidence_score", 0.0),
            keywords=hierarchical_result.get("matched_keywords", []),
            match_type="enhanced"
        )

    def process_text_enhanced(self, text: str) -> Dict:
        """
        增強版文本處理，返回完整的分析結果
        
        Args:
            text: 輸入文本
            
        Returns:
            包含實體、意圖、關係和智能回應上下文的完整分析結果
        """
        # 實體識別
        entities = self.recognize_entities_enhanced(text)
        
        # 意圖檢測
        intent_result = self.detect_hierarchical_intent_enhanced(text)
        
        # 生成智能回應上下文
        smart_context = self.generate_smart_response_context(text, entities, intent_result)
        
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
                    'confidence': e.confidence,
                    'match_type': e.match_type
                }
                for e in entities
            ],
            'intent_analysis': intent_result,
            'smart_context': smart_context,
            'enhanced_features': {
                'fuzzy_matching': True,
                'context_inference': True,
                'smart_response_guidance': True,
                'lowered_thresholds': True
            }
        }
        
        return result
    
    def _get_timestamp(self) -> str:
        """獲取當前時間戳"""
        from datetime import datetime
        return datetime.now().isoformat()