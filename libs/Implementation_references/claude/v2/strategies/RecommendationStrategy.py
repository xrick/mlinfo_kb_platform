"""
推薦回應策略
處理產品推薦回應的生成
"""

import logging
from typing import Dict, Any, List, Optional
from ..ResponseStrategy import ResponseStrategy, ResponseType


class RecommendationStrategy(ResponseStrategy):
    """推薦回應策略"""
    
    def __init__(self):
        super().__init__("RecommendationStrategy")
        self.recommendation_templates = self._load_recommendation_templates()
    
    def _load_recommendation_templates(self) -> Dict[str, str]:
        """載入推薦回應模板"""
        return {
            "intro": "根據您的需求，我為您推薦以下幾款筆電：",
            "single_recommendation": "基於您的需求，我特別推薦這款筆電：",
            "comparison_intro": "讓我為您比較這幾款筆電的差異：",
            "summary": "總結來說，{recommendation}",
            "no_match": "抱歉，目前沒有完全符合您需求的筆電，但我可以推薦一些相近的選擇。"
        }
    
    def generate_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成推薦回應
        
        Args:
            context: 當前上下文
            
        Returns:
            推薦回應字典
        """
        try:
            # 獲取推薦數據
            recommendations = context.get("recommendations", [])
            comparison_data = context.get("comparison_data", [])
            
            if not recommendations:
                return self._create_no_recommendation_response(context)
            
            # 根據推薦數量選擇不同的回應格式
            if len(recommendations) == 1:
                response = self._create_single_recommendation_response(context, recommendations[0])
            else:
                response = self._create_multiple_recommendation_response(context, recommendations, comparison_data)
            
            # 添加推薦摘要
            response["recommendation_summary"] = self._generate_recommendation_summary(context, recommendations)
            
            self.logger.info(f"生成推薦回應，包含 {len(recommendations)} 個推薦")
            return response
            
        except Exception as e:
            self.logger.error(f"生成推薦回應時發生錯誤: {e}")
            return self._create_error_response(context)
    
    def get_response_type(self) -> ResponseType:
        """獲取回應類型"""
        return ResponseType.RECOMMENDATION
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        驗證上下文是否適合推薦策略
        
        Args:
            context: 當前上下文
            
        Returns:
            是否適合使用此策略
        """
        # 檢查是否有推薦數據或處於推薦階段
        has_recommendations = "recommendations" in context and context["recommendations"]
        is_recommendation_stage = context.get("stage") == "RECOMMENDATION"
        needs_recommendation = context.get("needs_recommendation", False)
        
        return has_recommendations or is_recommendation_stage or needs_recommendation
    
    def _create_single_recommendation_response(self, context: Dict[str, Any], recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建單一推薦回應
        
        Args:
            context: 當前上下文
            recommendation: 推薦產品數據
            
        Returns:
            單一推薦回應字典
        """
        return {
            "type": "recommendation",
            "message": f"{self.recommendation_templates['single_recommendation']}",
            "recommendations": [recommendation],
            "session_id": context.get("session_id"),
            "stage": "RECOMMENDATION",
            "recommendation_count": 1
        }
    
    def _create_multiple_recommendation_response(self, context: Dict[str, Any], recommendations: List[Dict[str, Any]], comparison_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        創建多個推薦回應
        
        Args:
            context: 當前上下文
            recommendations: 推薦產品列表
            comparison_data: 比較數據
            
        Returns:
            多個推薦回應字典
        """
        response = {
            "type": "recommendation",
            "message": f"{self.recommendation_templates['intro']}",
            "recommendations": recommendations,
            "session_id": context.get("session_id"),
            "stage": "RECOMMENDATION",
            "recommendation_count": len(recommendations)
        }
        
        # 如果有比較數據，添加比較表格
        if comparison_data:
            response["comparison_table"] = comparison_data
            response["comparison_message"] = self.recommendation_templates["comparison_intro"]
        
        return response
    
    def _create_no_recommendation_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建無推薦回應
        
        Args:
            context: 當前上下文
            
        Returns:
            無推薦回應字典
        """
        return {
            "type": "recommendation",
            "message": self.recommendation_templates["no_match"],
            "recommendations": [],
            "session_id": context.get("session_id"),
            "stage": "ELICITATION",
            "needs_elicitation": True,
            "recommendation_count": 0
        }
    
    def _generate_recommendation_summary(self, context: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> str:
        """
        生成推薦摘要
        
        Args:
            context: 當前上下文
            recommendations: 推薦產品列表
            
        Returns:
            推薦摘要字符串
        """
        if not recommendations:
            return "目前沒有找到完全符合您需求的筆電。"
        
        # 根據推薦數量生成不同的摘要
        if len(recommendations) == 1:
            product = recommendations[0]
            return f"我特別推薦 {product.get('name', '這款筆電')}，它完全符合您的需求。"
        else:
            # 選擇最佳推薦
            best_recommendation = self._select_best_recommendation(recommendations, context)
            return f"在這些推薦中，我特別推薦 {best_recommendation.get('name', '第一款')}，它最符合您的需求。"
    
    def _select_best_recommendation(self, recommendations: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        選擇最佳推薦
        
        Args:
            recommendations: 推薦產品列表
            context: 當前上下文
            
        Returns:
            最佳推薦產品
        """
        # 簡單的選擇邏輯：選擇第一個推薦
        # 實際應用中可以根據評分、匹配度等進行更複雜的選擇
        return recommendations[0] if recommendations else {}
    
    def _create_error_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建錯誤回應
        
        Args:
            context: 當前上下文
            
        Returns:
            錯誤回應字典
        """
        return {
            "type": "general",
            "message": "抱歉，我在生成推薦時遇到了問題。請稍後再試。",
            "session_id": context.get("session_id"),
            "error": True
        }
    
    def format_recommendation_data(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        格式化推薦數據
        
        Args:
            recommendations: 原始推薦數據
            
        Returns:
            格式化後的推薦數據
        """
        formatted_recommendations = []
        
        for rec in recommendations:
            formatted_rec = {
                "name": rec.get("name", "未知型號"),
                "brand": rec.get("brand", "未知品牌"),
                "price": rec.get("price", "價格待詢"),
                "specs": rec.get("specs", {}),
                "highlights": rec.get("highlights", []),
                "match_score": rec.get("match_score", 0),
                "recommendation_reason": rec.get("recommendation_reason", "")
            }
            formatted_recommendations.append(formatted_rec)
        
        return formatted_recommendations
