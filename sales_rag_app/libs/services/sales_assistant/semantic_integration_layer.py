#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semantic Integration Layer

This module integrates the semantic query classification system with the existing
SalesAssistantService architecture, replacing rule-based clarification with
immediate intelligent responses.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from .semantic_query_classifier import SemanticQueryClassifier, QueryResult
from .smart_response_generator import SmartResponseGenerator, SmartResponse


class SemanticIntegrationLayer:
    """
    Integration layer between semantic understanding and existing service architecture
    
    This layer:
    1. Processes queries using semantic classification
    2. Generates immediate smart responses
    3. Provides compatibility with existing data retrieval methods
    4. Eliminates clarification requests
    """
    
    def __init__(self):
        """Initialize the integration layer"""
        self.semantic_classifier = SemanticQueryClassifier()
        self.response_generator = SmartResponseGenerator()
        
        # Available model names and types for compatibility
        self.AVAILABLE_MODELNAMES = [
            'AB819-S: FP6', 'AG958', 'AG958P', 'AG958V', 'AHP819: FP7R2',
            'AHP839', 'AHP958', 'AKK839', 'AMD819-S: FT6', 'AMD819: FT6',
            'AMD958: R7X', 'AMD958: R9X', 'Intel819-S: FP7', 'Intel819: FP7',
            'Intel958: Core5', 'Intel958: Core7', 'Intel958: Core9'
        ]
        
        self.AVAILABLE_MODELTYPES = ['819', '839', '958']
        
        # Spec fields for data retrieval compatibility
        self.spec_fields = [
            'modeltype', 'version', 'modelname', 'mainboard', 'devtime',
            'pm', 'structconfig', 'lcd', 'touchpanel', 'iointerface', 
            'ledind', 'powerbutton', 'keyboard', 'webcamera', 'touchpad', 
            'fingerprint', 'audio', 'battery', 'cpu', 'gpu', 'memory', 
            'lcdconnector', 'storage', 'wifislot', 'thermal', 'tpm', 'rtc', 
            'wireless', 'lan', 'bluetooth', 'softwareconfig', 'ai', 'accessory', 
            'certfications', 'otherfeatures'
        ]
    
    def process_query_semantically(self, query: str) -> Dict[str, Any]:
        """
        Process query using semantic understanding
        
        Args:
            query: User query string
            
        Returns:
            Dictionary compatible with existing service structure but enhanced
        """
        try:
            # Step 1: Semantic classification
            semantic_result = self.semantic_classifier.classify_query(query)
            
            # Step 2: Generate smart response
            smart_response = self.response_generator.generate_smart_response(query)
            
            # Step 3: Create compatible result structure
            compatible_result = self._create_compatible_result(
                query, semantic_result, smart_response
            )
            
            logging.info(f"Semantic processing complete for query: '{query}'")
            logging.info(f"Category: {semantic_result.query_category}, Confidence: {semantic_result.confidence:.3f}")
            
            return compatible_result
            
        except Exception as e:
            logging.error(f"Error in semantic processing: {e}")
            return self._create_fallback_result(query)
    
    def _create_compatible_result(self, query: str, semantic_result: QueryResult, 
                                smart_response: SmartResponse) -> Dict[str, Any]:
        """Create result structure compatible with existing service"""
        
        # Map semantic model recommendations to available model names
        target_modelnames = self._map_to_available_models(semantic_result.target_models)
        target_modeltypes = semantic_result.target_models
        
        # Determine query type based on available models
        query_type = "unknown"
        if target_modelnames:
            query_type = "specific_model"
        elif target_modeltypes:
            query_type = "model_type"
        
        # Create enhanced result structure
        result = {
            # Original service compatibility
            "modelnames": target_modelnames,
            "modeltypes": target_modeltypes,
            "intents": [semantic_result.query_category],
            "primary_intent": semantic_result.query_category,
            "query_type": query_type,
            "confidence_score": semantic_result.confidence,
            "original_query": query,
            
            # Enhanced semantic features
            "semantic_enhancement": {
                "query_classification": {
                    "category": semantic_result.query_category,
                    "parent_concept": semantic_result.semantic_context.get("parent_concept"),
                    "confidence": semantic_result.confidence,
                    "reasoning": semantic_result.reasoning
                },
                "smart_response": {
                    "immediate_answer": smart_response.immediate_answer,
                    "recommendation_summary": smart_response.recommendation_summary,
                    "helpful_suggestions": smart_response.helpful_suggestions,
                    "confidence_level": smart_response.confidence_level
                },
                "data_strategy": {
                    "lookup_strategy": smart_response.lookup_strategy,
                    "priority_specs": semantic_result.priority_specs,
                    "needs_data_lookup": smart_response.needs_data_lookup
                },
                "clarification_status": {
                    "needs_clarification": False,  # Semantic system never requests clarification
                    "can_proceed_immediately": True,
                    "fallback_response_available": True
                }
            }
        }
        
        return result
    
    def _map_to_available_models(self, semantic_models: List[str]) -> List[str]:
        """Map semantic model series to actual available model names"""
        model_mapping = {
            "819": [name for name in self.AVAILABLE_MODELNAMES if "819" in name],
            "839": [name for name in self.AVAILABLE_MODELNAMES if "839" in name],
            "958": [name for name in self.AVAILABLE_MODELNAMES if "958" in name]
        }
        
        mapped_models = []
        for series in semantic_models:
            if series in model_mapping:
                # Add representative models from each series
                series_models = model_mapping[series][:3]  # Limit to 3 per series
                mapped_models.extend(series_models)
        
        return mapped_models
    
    def should_clarify_semantic(self, result: Dict[str, Any]) -> bool:
        """
        Determine if clarification is needed (should be False for semantic system)
        
        This method always returns False because the semantic system provides
        immediate responses instead of requesting clarification.
        """
        enhancement = result.get("semantic_enhancement", {})
        clarification_status = enhancement.get("clarification_status", {})
        
        # Semantic system never requires clarification
        return clarification_status.get("needs_clarification", False)
    
    def generate_enhanced_prompt_context(self, result: Dict[str, Any], 
                                       context_data: List[Dict]) -> str:
        """
        Generate enhanced prompt context for LLM using semantic understanding
        
        Args:
            result: Semantic processing result
            context_data: Retrieved specification data
            
        Returns:
            Enhanced context string for LLM prompt
        """
        try:
            enhancement = result.get("semantic_enhancement", {})
            query_classification = enhancement.get("query_classification", {})
            smart_response = enhancement.get("smart_response", {})
            data_strategy = enhancement.get("data_strategy", {})
            
            # Build enhanced context
            context_parts = []
            
            # 1. Intent understanding context
            context_parts.append(f"用戶意圖分析：{query_classification.get('parent_concept', 'unknown')}")
            context_parts.append(f"分析信心度：{query_classification.get('confidence', 0):.3f}")
            context_parts.append(f"推理說明：{query_classification.get('reasoning', '')}")
            
            # 2. Response guidance
            context_parts.append(f"\\n建議回應重點：{smart_response.get('immediate_answer', '')}")
            context_parts.append(f"推薦總結方向：{smart_response.get('recommendation_summary', '')}")
            
            # 3. Data focus instructions
            priority_specs = data_strategy.get("priority_specs", [])
            if priority_specs:
                context_parts.append(f"\\n重點規格欄位：{', '.join(priority_specs)}")
            
            lookup_strategy = data_strategy.get("lookup_strategy", "")
            context_parts.append(f"資料呈現策略：{lookup_strategy}")
            
            # 4. Helpful suggestions
            suggestions = smart_response.get("helpful_suggestions", [])
            if suggestions:
                context_parts.append(f"\\n建議補充資訊：")
                for i, suggestion in enumerate(suggestions[:3], 1):
                    context_parts.append(f"{i}. {suggestion}")
            
            # 5. Data context
            if context_data:
                context_parts.append(f"\\n可用資料：{len(context_data)} 筆型號資料")
                model_names = [item.get('modelname', 'unknown') for item in context_data[:5]]
                context_parts.append(f"包含型號：{', '.join(model_names)}")
            
            enhanced_context = "\\n".join(context_parts)
            
            logging.info(f"Generated enhanced prompt context ({len(enhanced_context)} chars)")
            return enhanced_context
            
        except Exception as e:
            logging.error(f"Error generating enhanced prompt context: {e}")
            return "提供筆電型號比較和推薦資訊"
    
    def _create_fallback_result(self, query: str) -> Dict[str, Any]:
        """Create fallback result when semantic processing fails"""
        return {
            "modelnames": [],
            "modeltypes": ["819", "839", "958"],
            "intents": ["general"],
            "primary_intent": "general",
            "query_type": "model_type",
            "confidence_score": 0.5,
            "original_query": query,
            "semantic_enhancement": {
                "query_classification": {
                    "category": "general_recommendation",
                    "parent_concept": "一般推薦需求",
                    "confidence": 0.5,
                    "reasoning": "語義處理異常，提供一般性推薦"
                },
                "smart_response": {
                    "immediate_answer": "我來為您提供筆電推薦：",
                    "recommendation_summary": "📊 提供全系列型號的綜合比較分析",
                    "helpful_suggestions": ["歡迎詢問具體需求", "可詳細比較任意型號"],
                    "confidence_level": "基礎推薦"
                },
                "data_strategy": {
                    "lookup_strategy": "comprehensive_lookup",
                    "priority_specs": ["cpu", "gpu", "memory", "battery"],
                    "needs_data_lookup": True
                },
                "clarification_status": {
                    "needs_clarification": False,
                    "can_proceed_immediately": True,
                    "fallback_response_available": True
                }
            }
        }
    
    def get_semantic_analysis_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of semantic analysis for logging/debugging"""
        enhancement = result.get("semantic_enhancement", {})
        
        return {
            "query": result.get("original_query", ""),
            "detected_category": enhancement.get("query_classification", {}).get("category", "unknown"),
            "confidence": enhancement.get("query_classification", {}).get("confidence", 0.0),
            "target_models": result.get("modeltypes", []),
            "clarification_needed": enhancement.get("clarification_status", {}).get("needs_clarification", False),
            "can_proceed": enhancement.get("clarification_status", {}).get("can_proceed_immediately", True)
        }
    
    def extract_models_for_data_lookup(self, result: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Extract model information for data lookup compatibility
        
        Returns:
            Tuple of (modelnames, modeltypes) for existing data retrieval methods
        """
        modelnames = result.get("modelnames", [])
        modeltypes = result.get("modeltypes", [])
        
        # Ensure we have some models to work with
        if not modelnames and not modeltypes:
            modeltypes = ["819", "839", "958"]  # Default to all series
        
        return modelnames, modeltypes


def test_semantic_integration():
    """Test the semantic integration layer"""
    integration = SemanticIntegrationLayer()
    
    test_queries = [
        "哪款筆電比較省電？",
        "推薦適合遊戲的",
        "學生用什麼好？",
        "有什麼推薦的嗎？"
    ]
    
    for query in test_queries:
        print(f"\\n{'='*70}")
        print(f"測試查詢: {query}")
        print(f"{'='*70}")
        
        # Process query
        result = integration.process_query_semantically(query)
        
        # Check clarification status
        needs_clarification = integration.should_clarify_semantic(result)
        print(f"需要澄清: {'否' if not needs_clarification else '是'}")
        
        # Get analysis summary
        summary = integration.get_semantic_analysis_summary(result)
        print(f"語義分析: {summary}")
        
        # Extract models for data lookup
        modelnames, modeltypes = integration.extract_models_for_data_lookup(result)
        print(f"資料查詢目標: modelnames={modelnames[:2]}, modeltypes={modeltypes}")
        
        # Generate enhanced context (simulated)
        mock_context_data = [{"modelname": "AG958", "cpu": "高效能處理器"}]
        enhanced_context = integration.generate_enhanced_prompt_context(result, mock_context_data)
        print(f"\\n增強提示內容預覽: {enhanced_context[:200]}...")


if __name__ == "__main__":
    test_semantic_integration()