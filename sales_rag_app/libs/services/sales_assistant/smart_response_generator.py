#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Response Generation Engine with Semantic Understanding

This engine generates intelligent, immediate responses based on semantic query classification,
eliminating the need for clarification requests.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .semantic_query_classifier import QueryResult, SemanticQueryClassifier


@dataclass
class SmartResponse:
    """Structured response from smart generation engine"""
    response_type: str
    immediate_answer: str
    recommendation_summary: str
    target_models: List[str]
    priority_specs: List[str]
    helpful_suggestions: List[str]
    confidence_level: str
    needs_data_lookup: bool
    lookup_strategy: str


class SmartResponseGenerator:
    """
    Smart Response Generation Engine
    
    Generates immediate, helpful responses without clarification requests.
    Uses semantic understanding to provide contextual recommendations.
    """
    
    def __init__(self):
        """Initialize the response generator"""
        self.semantic_classifier = SemanticQueryClassifier()
        
        # Response templates for different strategies
        self.response_templates = {
            "battery_comparison": {
                "immediate_answer": "根據電池續航需求，我來為您推薦最適合的筆電型號：",
                "focus_message": "🔋 以下是續航能力出色的型號比較：",
                "recommendation_strategy": "highlight_battery_specs"
            },
            
            "performance_comparison": {
                "immediate_answer": "根據高效能需求，我來為您分析適合的遊戲筆電：",
                "focus_message": "🎮 以下是高效能型號的詳細比較：",
                "recommendation_strategy": "highlight_performance_specs"
            },
            
            "business_features": {
                "immediate_answer": "根據商務辦公需求，我來推薦最適合的專業型號：",
                "focus_message": "💼 以下是商務型筆電的特色比較：",
                "recommendation_strategy": "highlight_business_specs"
            },
            
            "value_comparison": {
                "immediate_answer": "根據預算和性價比考量，我來為您推薦最划算的選擇：",
                "focus_message": "💰 以下是高性價比型號的比較分析：",
                "recommendation_strategy": "highlight_value_specs"
            },
            
            "display_comparison": {
                "immediate_answer": "根據螢幕顯示需求，我來為您分析各型號的顯示效果：",
                "focus_message": "🖥️ 以下是螢幕規格的詳細比較：",
                "recommendation_strategy": "highlight_display_specs"
            },
            
            "general_comparison": {
                "immediate_answer": "根據您的查詢，我來為您提供全面的型號比較：",
                "focus_message": "📊 以下是各型號的綜合比較分析：",
                "recommendation_strategy": "comprehensive_comparison"
            },
            
            "detailed_specs": {
                "immediate_answer": "我來為您提供詳細的規格資訊：",
                "focus_message": "📋 以下是完整的規格對照表：",
                "recommendation_strategy": "detailed_specification_table"
            },
            
            "side_by_side_comparison": {
                "immediate_answer": "我來為您進行詳細的型號對比分析：",
                "focus_message": "⚖️ 以下是並列比較結果：",
                "recommendation_strategy": "side_by_side_analysis"
            }
        }
        
        # Model-specific talking points
        self.model_highlights = {
            "819": {
                "strengths": ["超長續航8-10小時", "輕薄便攜設計", "商務辦公最佳選擇", "高性價比"],
                "best_for": ["商務人士", "學生", "移動辦公", "長時間使用"],
                "key_specs": ["battery", "cpu", "memory", "keyboard"]
            },
            "839": {
                "strengths": ["均衡配置", "適中價位", "日常使用穩定", "多功能性"],
                "best_for": ["一般用戶", "學生", "輕度工作", "娛樂需求"],
                "key_specs": ["cpu", "memory", "storage", "lcd"]
            },
            "958": {
                "strengths": ["高效能處理器", "強勁顯卡", "遊戲流暢體驗", "創作者友好"],
                "best_for": ["遊戲玩家", "創作者", "高效能需求", "專業應用"],
                "key_specs": ["gpu", "cpu", "memory", "thermal"]
            }
        }
    
    def generate_smart_response(self, query: str) -> SmartResponse:
        """
        Generate intelligent response based on semantic understanding
        
        Args:
            query: User query string
            
        Returns:
            SmartResponse with immediate helpful content
        """
        try:
            # Classify query semantically
            query_result = self.semantic_classifier.classify_query(query)
            
            # Generate immediate response
            response = self._create_immediate_response(query, query_result)
            
            return response
            
        except Exception as e:
            logging.error(f"Error generating smart response: {e}")
            return self._create_fallback_response(query)
    
    def _create_immediate_response(self, query: str, query_result: QueryResult) -> SmartResponse:
        """Create immediate response based on semantic classification"""
        
        # Get response template
        template = self.response_templates.get(
            query_result.response_strategy, 
            self.response_templates["general_comparison"]
        )
        
        # Generate immediate answer
        immediate_answer = template["immediate_answer"]
        
        # Create recommendation summary
        recommendation_summary = self._generate_recommendation_summary(query_result)
        
        # Generate helpful suggestions
        helpful_suggestions = self._generate_helpful_suggestions(query, query_result)
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(query_result.confidence)
        
        # Determine data lookup strategy
        lookup_strategy = self._determine_lookup_strategy(query_result)
        
        return SmartResponse(
            response_type=query_result.response_strategy,
            immediate_answer=immediate_answer,
            recommendation_summary=recommendation_summary,
            target_models=query_result.target_models,
            priority_specs=query_result.priority_specs,
            helpful_suggestions=helpful_suggestions,
            confidence_level=confidence_level,
            needs_data_lookup=True,  # Always provide data-backed responses
            lookup_strategy=lookup_strategy
        )
    
    def _generate_recommendation_summary(self, query_result: QueryResult) -> str:
        """Generate contextual recommendation summary"""
        
        category = query_result.query_category
        models = query_result.target_models
        
        # Category-specific recommendations
        category_recommendations = {
            "battery_power": f"🔋 推薦 {', '.join(models)} 系列，續航能力優異，適合長時間使用",
            "gaming_performance": f"🎮 推薦 {', '.join(models)} 系列，高效能配置，遊戲體驗流暢",
            "business_productivity": f"💼 推薦 {', '.join(models)} 系列，商務功能完整，穩定可靠",
            "student_budget": f"🎓 推薦 {', '.join(models)} 系列，性價比高，適合學生使用",
            "display_quality": f"🖥️ 推薦 {', '.join(models)} 系列，螢幕顯示效果優秀",
            "general_recommendation": f"📊 推薦 {', '.join(models)} 系列，綜合表現優異",
            "specifications_inquiry": f"📋 提供 {', '.join(models)} 系列的完整規格資訊",
            "comparison_request": f"⚖️ 提供 {', '.join(models)} 系列的詳細比較分析"
        }
        
        base_recommendation = category_recommendations.get(
            category, 
            f"📌 推薦 {', '.join(models)} 系列，根據您的需求進行分析"
        )
        
        # Add model-specific highlights
        model_details = []
        for model in models[:2]:  # Focus on top 2 models
            if model in self.model_highlights:
                strengths = self.model_highlights[model]["strengths"][:2]  # Top 2 strengths
                detail = f"{model}系列：{', '.join(strengths)}"
                model_details.append(detail)
        
        if model_details:
            base_recommendation += f"\\n\\n✨ 特色亮點：\\n" + "\\n".join([f"• {detail}" for detail in model_details])
        
        return base_recommendation
    
    def _generate_helpful_suggestions(self, query: str, query_result: QueryResult) -> List[str]:
        """Generate helpful suggestions based on context"""
        
        suggestions = []
        category = query_result.query_category
        models = query_result.target_models
        
        # Category-specific suggestions
        if category == "battery_power":
            suggestions = [
                "考慮您的實際使用時間需求（4-6小時 vs 8-10小時）",
                "建議了解充電習慣和使用環境",
                "省電模式設定可延長2-3小時續航"
            ]
        elif category == "gaming_performance":
            suggestions = [
                "確認您主要玩的遊戲類型和畫質要求",
                "考慮是否需要支援VR或4K遊戲",
                "散熱效能會影響長時間遊戲的穩定性"
            ]
        elif category == "business_productivity":
            suggestions = [
                "評估是否需要經常攜帶外出使用",
                "考慮企業安全需求（如TPM、指紋辨識）",
                "鍵盤舒適度對長時間打字很重要"
            ]
        elif category == "student_budget":
            suggestions = [
                "建議關注保固期限和售後服務",
                "考慮是否需要升級空間（記憶體、硬碟）",
                "學生優惠方案可節省額外費用"
            ]
        else:
            # General suggestions
            suggestions = [
                f"可進一步比較 {', '.join(models)} 系列的具體差異",
                "建議考慮您的預算範圍和使用需求",
                "歡迎詢問任何特定規格的詳細資訊"
            ]
        
        # Add model-specific suggestions
        if len(models) > 1:
            suggestions.append(f"如需深入比較 {' vs '.join(models[:2])}，我可提供詳細分析")
        
        return suggestions[:4]  # Limit to 4 suggestions
    
    def _determine_confidence_level(self, confidence: float) -> str:
        """Determine confidence level description"""
        if confidence >= 0.7:
            return "高信心度"
        elif confidence >= 0.4:
            return "中等信心度"
        else:
            return "基礎推薦"
    
    def _determine_lookup_strategy(self, query_result: QueryResult) -> str:
        """Determine the best data lookup strategy"""
        
        strategy_mapping = {
            "battery_comparison": "focus_battery_specs",
            "performance_comparison": "focus_performance_specs",
            "business_features": "focus_business_specs",
            "value_comparison": "focus_value_specs",
            "display_comparison": "focus_display_specs",
            "general_comparison": "comprehensive_lookup",
            "detailed_specs": "complete_specifications",
            "side_by_side_comparison": "parallel_comparison"
        }
        
        return strategy_mapping.get(query_result.response_strategy, "comprehensive_lookup")
    
    def _create_fallback_response(self, query: str) -> SmartResponse:
        """Create fallback response when classification fails"""
        return SmartResponse(
            response_type="general_fallback",
            immediate_answer="我來為您提供筆電推薦和比較分析：",
            recommendation_summary="📊 根據您的查詢，我將提供全系列型號的綜合分析，幫助您找到最適合的選擇",
            target_models=["819", "839", "958"],
            priority_specs=["cpu", "gpu", "memory", "battery"],
            helpful_suggestions=[
                "您可以告訴我具體的使用需求（如遊戲、辦公、學習）",
                "我可以詳細比較任意兩個型號的差異",
                "歡迎詢問任何規格的詳細資訊"
            ],
            confidence_level="基礎推薦",
            needs_data_lookup=True,
            lookup_strategy="comprehensive_lookup"
        )
    
    def get_context_for_llm(self, smart_response: SmartResponse, query: str) -> Dict[str, Any]:
        """
        Generate context information for LLM prompt construction
        
        This provides structured information that can be used to build
        enhanced prompts for the existing LLM system.
        """
        return {
            "enhanced_prompt_context": {
                "user_intent_analysis": {
                    "detected_category": smart_response.response_type,
                    "confidence": smart_response.confidence_level,
                    "immediate_response": smart_response.immediate_answer
                },
                "recommendation_guidance": {
                    "focus_models": smart_response.target_models,
                    "priority_specs": smart_response.priority_specs,
                    "presentation_strategy": smart_response.lookup_strategy
                },
                "response_enhancement": {
                    "summary_suggestion": smart_response.recommendation_summary,
                    "additional_suggestions": smart_response.helpful_suggestions,
                    "should_clarify": False  # This system never requests clarification
                }
            },
            "user_query": query,
            "response_type": smart_response.response_type
        }


def test_smart_response_generator():
    """Test the smart response generator"""
    generator = SmartResponseGenerator()
    
    test_queries = [
        "哪款筆電比較省電？",
        "推薦適合遊戲的",
        "學生用什麼好？",
        "有什麼推薦的嗎？"
    ]
    
    for query in test_queries:
        print(f"\\n{'='*60}")
        print(f"查詢: {query}")
        print(f"{'='*60}")
        
        response = generator.generate_smart_response(query)
        
        print(f"回應類型: {response.response_type}")
        print(f"即時回答: {response.immediate_answer}")
        print(f"推薦總結: {response.recommendation_summary}")
        print(f"目標型號: {response.target_models}")
        print(f"優先規格: {response.priority_specs}")
        print(f"有用建議: {response.helpful_suggestions}")
        print(f"信心度: {response.confidence_level}")
        
        # Test LLM context generation
        llm_context = generator.get_context_for_llm(response, query)
        print(f"\\nLLM整合資訊: {llm_context['enhanced_prompt_context']['user_intent_analysis']}")


if __name__ == "__main__":
    test_smart_response_generator()