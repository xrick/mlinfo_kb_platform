#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semantic Query Classification System using Parent-Child Chunking Strategy

This system replaces the rule-based intent detection with semantic understanding
using embeddings and hierarchical knowledge organization.
"""

import os
import json
import logging
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from sentence_transformers import SentenceTransformer
import pickle
from dataclasses import dataclass
from pathlib import Path


@dataclass
class QueryResult:
    """Structured result from semantic query classification"""
    query_category: str
    confidence: float
    target_models: List[str]
    priority_specs: List[str]
    response_strategy: str
    semantic_context: Dict[str, Any]
    reasoning: str


class SemanticQueryClassifier:
    """
    Semantic Query Classification using Parent-Child Chunking Strategy
    
    This system organizes laptop information hierarchically:
    - Parents: Usage scenarios (Gaming, Business, Student, etc.)
    - Children: Specific features/specifications relevant to each scenario
    
    Uses semantic similarity to understand user intent without rigid rules.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the semantic classifier"""
        self.model = SentenceTransformer(model_name)
        self.knowledge_base = self._build_hierarchical_knowledge_base()
        self.embeddings_cache = {}
        self._load_or_generate_embeddings()
        
        # Model categorization based on observed patterns
        self.model_categories = {
            "819": {
                "type": "business_student", 
                "strengths": ["battery_life", "portability", "value"],
                "target_users": ["business", "student", "office_work"]
            },
            "839": {
                "type": "mid_range", 
                "strengths": ["balanced", "value", "everyday_use"],
                "target_users": ["general", "student", "light_work"]
            },
            "958": {
                "type": "gaming_performance", 
                "strengths": ["gaming", "performance", "gpu", "cpu"],
                "target_users": ["gaming", "creative", "power_user"]
            }
        }
        
    def _build_hierarchical_knowledge_base(self) -> Dict[str, Any]:
        """
        Build parent-child hierarchical knowledge base
        
        Structure:
        Parent Categories -> Child Features -> Semantic Descriptions
        """
        return {
            "battery_power": {
                "parent_concept": "電池續航能力",
                "semantic_phrases": [
                    "省電", "續航", "電池", "長時間使用", "不插電", "行動辦公",
                    "哪個比較省電", "用很久", "不用常充電", "電池怎麼樣", "續航如何",
                    "能用多久", "會很耗電嗎", "battery life", "power saving", "long lasting"
                ],
                "priority_specs": ["battery", "cpu", "thermal"],
                "relevant_models": ["819"],
                "response_focus": "battery_comparison"
            },
            
            "gaming_performance": {
                "parent_concept": "遊戲效能表現",
                "semantic_phrases": [
                    "遊戲", "電競", "gaming", "高效能", "顯卡", "gpu", "玩遊戲",
                    "適合遊戲的", "電競筆電", "遊戲效果", "fps", "顯示效果",
                    "跑遊戲", "遊戲體驗", "performance", "graphics", "rtx"
                ],
                "priority_specs": ["gpu", "cpu", "memory", "thermal"],
                "relevant_models": ["958"],
                "response_focus": "performance_comparison"
            },
            
            "business_productivity": {
                "parent_concept": "商務辦公需求",
                "semantic_phrases": [
                    "辦公", "商務", "business", "工作", "文書處理", "office",
                    "適合辦公的", "商務筆電", "上班用", "工作需要", "企業",
                    "productivity", "professional", "work", "corporate"
                ],
                "priority_specs": ["cpu", "memory", "battery", "keyboard"],
                "relevant_models": ["819"],
                "response_focus": "business_features"
            },
            
            "student_budget": {
                "parent_concept": "學生預算考量",
                "semantic_phrases": [
                    "學生", "student", "便宜", "划算", "性價比", "預算",
                    "學生用", "讀書", "寫作業", "上課", "學習", "經濟實惠",
                    "affordable", "budget", "cost effective", "value for money"
                ],
                "priority_specs": ["cpu", "memory", "battery", "value"],
                "relevant_models": ["819", "839"],
                "response_focus": "value_comparison"
            },
            
            "display_quality": {
                "parent_concept": "螢幕顯示品質",
                "semantic_phrases": [
                    "螢幕", "顯示", "screen", "display", "畫質", "解析度",
                    "螢幕效果", "顯示效果", "看影片", "視覺效果", "色彩",
                    "brightness", "resolution", "visual quality"
                ],
                "priority_specs": ["lcd", "lcdconnector", "gpu"],
                "relevant_models": ["958", "839", "819"],
                "response_focus": "display_comparison"
            },
            
            "general_recommendation": {
                "parent_concept": "一般推薦需求",
                "semantic_phrases": [
                    "推薦", "recommend", "哪個好", "什麼比較好", "選擇",
                    "有什麼推薦", "建議", "哪款", "比較", "選購",
                    "suggestion", "advice", "which one", "best choice"
                ],
                "priority_specs": ["cpu", "gpu", "memory", "battery"],
                "relevant_models": ["819", "839", "958"],
                "response_focus": "general_comparison"
            },
            
            "specifications_inquiry": {
                "parent_concept": "規格查詢需求",
                "semantic_phrases": [
                    "規格", "spec", "specification", "參數", "配置",
                    "詳細", "功能", "features", "technical", "details"
                ],
                "priority_specs": ["cpu", "gpu", "memory", "storage", "battery"],
                "relevant_models": ["819", "839", "958"],
                "response_focus": "detailed_specs"
            },
            
            "comparison_request": {
                "parent_concept": "產品比較請求",
                "semantic_phrases": [
                    "比較", "comparison", "對比", "差異", "區別", "哪個",
                    "比較一下", "差別", "不同", "versus", "vs", "compare"
                ],
                "priority_specs": ["cpu", "gpu", "memory", "battery", "value"],
                "relevant_models": ["819", "839", "958"],
                "response_focus": "side_by_side_comparison"
            }
        }
    
    def _load_or_generate_embeddings(self):
        """Load cached embeddings or generate new ones"""
        cache_file = Path(__file__).parent / "semantic_embeddings_cache.pkl"
        
        try:
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    self.embeddings_cache = pickle.load(f)
                logging.info("Loaded cached semantic embeddings")
            else:
                self._generate_embeddings()
                self._save_embeddings_cache(cache_file)
        except Exception as e:
            logging.warning(f"Failed to load embeddings cache: {e}")
            self._generate_embeddings()
    
    def _generate_embeddings(self):
        """Generate embeddings for all semantic phrases in knowledge base"""
        logging.info("Generating semantic embeddings for knowledge base...")
        
        for category, data in self.knowledge_base.items():
            phrases = data["semantic_phrases"]
            embeddings = self.model.encode(phrases)
            self.embeddings_cache[category] = {
                "phrases": phrases,
                "embeddings": embeddings,
                "parent_concept": data["parent_concept"]
            }
        
        logging.info(f"Generated embeddings for {len(self.knowledge_base)} categories")
    
    def _save_embeddings_cache(self, cache_file: Path):
        """Save embeddings to cache file"""
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self.embeddings_cache, f)
            logging.info(f"Saved embeddings cache to {cache_file}")
        except Exception as e:
            logging.warning(f"Failed to save embeddings cache: {e}")
    
    def classify_query(self, query: str) -> QueryResult:
        """
        Classify query using semantic similarity with parent-child chunks
        
        Args:
            query: User query string
            
        Returns:
            QueryResult with semantic classification and recommendations
        """
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query])[0]
            
            # Calculate semantic similarities
            similarities = {}
            
            for category, cached_data in self.embeddings_cache.items():
                phrase_embeddings = cached_data["embeddings"]
                
                # Calculate cosine similarities with all phrases
                cos_similarities = np.dot(phrase_embeddings, query_embedding) / (
                    np.linalg.norm(phrase_embeddings, axis=1) * np.linalg.norm(query_embedding)
                )
                
                # Use max similarity as category score
                max_similarity = float(np.max(cos_similarities))
                similarities[category] = max_similarity
            
            # Find best matching category
            best_category = max(similarities.keys(), key=lambda k: similarities[k])
            confidence = similarities[best_category]
            
            # Get category data
            category_data = self.knowledge_base[best_category]
            
            # Determine target models based on semantic context
            target_models = self._determine_target_models(query, best_category, category_data)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(query, best_category, confidence, similarities)
            
            return QueryResult(
                query_category=best_category,
                confidence=confidence,
                target_models=target_models,
                priority_specs=category_data["priority_specs"],
                response_strategy=category_data["response_focus"],
                semantic_context={
                    "parent_concept": category_data["parent_concept"],
                    "all_similarities": similarities,
                    "semantic_matches": self._find_matching_phrases(query, best_category)
                },
                reasoning=reasoning
            )
            
        except Exception as e:
            logging.error(f"Error in semantic query classification: {e}")
            # Fallback to general recommendation
            return self._create_fallback_result(query)
    
    def _determine_target_models(self, query: str, category: str, category_data: Dict) -> List[str]:
        """Determine which models are most relevant based on semantic analysis"""
        
        # Start with category-recommended models
        target_models = category_data.get("relevant_models", [])
        
        # Check for explicit model mentions in query
        query_lower = query.lower()
        explicit_models = []
        
        for model_series in ["819", "839", "958"]:
            if model_series in query_lower:
                explicit_models.append(model_series)
        
        # If explicit models mentioned, prioritize them
        if explicit_models:
            # Reorder to put explicit models first
            target_models = explicit_models + [m for m in target_models if m not in explicit_models]
        
        # Add semantic context-based model inference
        if not target_models:
            # Use all models if no specific recommendations
            target_models = ["819", "839", "958"]
        
        return target_models[:3]  # Limit to top 3 models
    
    def _find_matching_phrases(self, query: str, category: str) -> List[str]:
        """Find which specific phrases in the category matched the query"""
        query_lower = query.lower()
        category_phrases = self.knowledge_base[category]["semantic_phrases"]
        
        matches = []
        for phrase in category_phrases:
            if phrase.lower() in query_lower or query_lower in phrase.lower():
                matches.append(phrase)
        
        return matches
    
    def _generate_reasoning(self, query: str, category: str, confidence: float, 
                          similarities: Dict[str, float]) -> str:
        """Generate human-readable reasoning for the classification"""
        
        category_data = self.knowledge_base[category]
        parent_concept = category_data["parent_concept"]
        
        # Find second-best category for comparison
        sorted_categories = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
        second_best = sorted_categories[1] if len(sorted_categories) > 1 else None
        
        reasoning = f"查詢意圖分析：'{query}' 最符合 '{parent_concept}' 類別 (信心度: {confidence:.3f})"
        
        if second_best and second_best[1] > 0.3:
            second_concept = self.knowledge_base[second_best[0]]["parent_concept"]
            reasoning += f"，次要意圖可能是 '{second_concept}' (信心度: {second_best[1]:.3f})"
        
        matching_phrases = self._find_matching_phrases(query, category)
        if matching_phrases:
            reasoning += f"。匹配關鍵概念：{', '.join(matching_phrases[:3])}"
        
        return reasoning
    
    def _create_fallback_result(self, query: str) -> QueryResult:
        """Create fallback result when classification fails"""
        return QueryResult(
            query_category="general_recommendation",
            confidence=0.5,
            target_models=["819", "839", "958"],
            priority_specs=["cpu", "gpu", "memory", "battery"],
            response_strategy="general_comparison",
            semantic_context={
                "parent_concept": "一般推薦需求",
                "fallback": True,
                "original_query": query
            },
            reasoning=f"無法確定具體意圖，提供一般性推薦回應"
        )
    
    def get_category_info(self, category: str) -> Dict[str, Any]:
        """Get detailed information about a category"""
        return self.knowledge_base.get(category, {})
    
    def get_model_category_info(self, model_series: str) -> Dict[str, Any]:
        """Get information about a specific model series"""
        return self.model_categories.get(model_series, {})
    
    def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """Analyze the complexity and multiple intents in a query"""
        result = self.classify_query(query)
        similarities = result.semantic_context.get("all_similarities", {})
        
        # Find high-confidence categories (above threshold)
        high_confidence_categories = {
            cat: score for cat, score in similarities.items() 
            if score > 0.3
        }
        
        return {
            "primary_intent": result.query_category,
            "multiple_intents": len(high_confidence_categories) > 1,
            "intent_distribution": high_confidence_categories,
            "complexity_score": len(high_confidence_categories),
            "needs_clarification": False  # This system avoids clarification
        }


# Test interface for validation
def test_semantic_classifier():
    """Test the semantic classifier with problematic queries"""
    classifier = SemanticQueryClassifier()
    
    test_queries = [
        "哪款筆電比較省電？",
        "推薦適合遊戲的",
        "958和819哪個好？",
        "學生用什麼好？",
        "螢幕效果怎麼樣？",
        "有什麼推薦的嗎？",
        "筆電規格",
        "比較一下",
        "哪個性價比高？",
        "適合辦公的筆電"
    ]
    
    results = []
    for query in test_queries:
        result = classifier.classify_query(query)
        results.append({
            "query": query,
            "category": result.query_category,
            "confidence": result.confidence,
            "models": result.target_models,
            "strategy": result.response_strategy,
            "reasoning": result.reasoning
        })
        
        print(f"\n查詢: {query}")
        print(f"分類: {result.query_category} (信心度: {result.confidence:.3f})")
        print(f"推薦型號: {result.target_models}")
        print(f"回應策略: {result.response_strategy}")
        print(f"推理: {result.reasoning}")
    
    return results


if __name__ == "__main__":
    # Run test when executed directly
    test_results = test_semantic_classifier()