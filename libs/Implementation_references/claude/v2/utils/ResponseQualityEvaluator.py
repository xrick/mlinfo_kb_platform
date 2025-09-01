"""
回應品質評估器
提供回應品質的全面評估功能
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime


class ResponseQualityEvaluator:
    """回應品質評估器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.evaluation_weights = self._load_evaluation_weights()
    
    def _load_evaluation_weights(self) -> Dict[str, float]:
        """載入評估權重"""
        return {
            "completeness": 0.25,
            "clarity": 0.20,
            "relevance": 0.25,
            "consistency": 0.15,
            "accuracy": 0.15
        }
    
    def evaluate_response(
        self, 
        response: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        評估回應品質
        
        Args:
            response: 回應字典
            context: 當前上下文
        
        Returns:
            包含評估結果的字典
        """
        try:
            evaluation = {
                "completeness": self._evaluate_completeness(response, context),
                "clarity": self._evaluate_clarity(response),
                "relevance": self._evaluate_relevance(response, context),
                "consistency": self._evaluate_consistency(response, context),
                "accuracy": self._evaluate_accuracy(response, context),
                "overall_score": 0.0,
                "improvement_suggestions": [],
                "evaluation_timestamp": datetime.now().isoformat()
            }
            
            # 計算總分
            evaluation["overall_score"] = self._calculate_overall_score(evaluation)
            
            # 生成改進建議
            evaluation["improvement_suggestions"] = self._generate_suggestions(evaluation)
            
            self.logger.info(f"回應品質評估完成，總分: {evaluation['overall_score']:.2f}")
            return evaluation
            
        except Exception as e:
            self.logger.error(f"評估回應品質時發生錯誤: {e}")
            return self._create_error_evaluation(str(e))
    
    def _evaluate_completeness(self, response: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        評估完整性
        
        Args:
            response: 回應字典
            context: 當前上下文
        
        Returns:
            完整性分數 (0.0-1.0)
        """
        score = 0.0
        max_score = 1.0
        
        # 檢查必要字段
        required_fields = ["type", "message"]
        for field in required_fields:
            if field in response and response[field]:
                score += 0.3
        
        # 檢查回應類型特定的必要字段
        response_type = response.get("type", "")
        if response_type == "funnel_question":
            if "question" in response and "options" in response:
                score += 0.4
        elif response_type == "recommendation":
            if "recommendations" in response:
                score += 0.4
        elif response_type == "elicitation":
            if "elicitation_type" in response:
                score += 0.4
        
        # 檢查會話ID
        if "session_id" in response:
            score += 0.1
        
        return min(score, max_score)
    
    def _evaluate_clarity(self, response: Dict[str, Any]) -> float:
        """
        評估清晰度
        
        Args:
            response: 回應字典
        
        Returns:
            清晰度分數 (0.0-1.0)
        """
        score = 0.0
        max_score = 1.0
        
        message = response.get("message", "")
        if not message:
            return 0.0
        
        # 檢查消息長度
        message_length = len(message.strip())
        if 10 <= message_length <= 500:
            score += 0.3
        elif message_length > 500:
            score += 0.1  # 太長扣分
        
        # 檢查是否包含明確的指示
        if any(word in message for word in ["請", "建議", "推薦", "可以"]):
            score += 0.2
        
        # 檢查是否避免技術術語（除非必要）
        technical_terms = ["API", "SDK", "framework", "algorithm"]
        if not any(term in message for term in technical_terms):
            score += 0.2
        
        # 檢查語法正確性（簡單檢查）
        if message.endswith((".", "！", "？")):
            score += 0.1
        
        # 檢查是否有重複內容
        words = message.split()
        if len(words) == len(set(words)) or len(words) < 20:
            score += 0.2
        
        return min(score, max_score)
    
    def _evaluate_relevance(self, response: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        評估相關性
        
        Args:
            response: 回應字典
            context: 當前上下文
        
        Returns:
            相關性分數 (0.0-1.0)
        """
        score = 0.0
        max_score = 1.0
        
        # 檢查回應類型是否與上下文匹配
        user_intent = context.get("intent", "")
        response_type = response.get("type", "")
        
        if user_intent == "ask_recommendation" and response_type == "recommendation":
            score += 0.4
        elif user_intent == "greet" and response_type == "general":
            score += 0.4
        elif "funnel" in user_intent and response_type == "funnel_question":
            score += 0.4
        elif user_intent == "clarify" and response_type in ["elicitation", "general"]:
            score += 0.4
        
        # 檢查回應是否針對用戶需求
        user_message = context.get("user_message", "").lower()
        response_message = response.get("message", "").lower()
        
        # 簡單的關鍵詞匹配
        if any(word in response_message for word in ["筆電", "電腦", "推薦", "建議"]):
            score += 0.3
        
        # 檢查是否包含用戶提到的具體需求
        if user_message and any(word in response_message for word in user_message.split()[:5]):
            score += 0.3
        
        return min(score, max_score)
    
    def _evaluate_consistency(self, response: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        評估一致性
        
        Args:
            response: 回應字典
            context: 當前上下文
        
        Returns:
            一致性分數 (0.0-1.0)
        """
        score = 0.0
        max_score = 1.0
        
        # 檢查語氣一致性
        response_message = response.get("message", "")
        if "您" in response_message and "我" in response_message:
            score += 0.3  # 保持禮貌的對話語氣
        
        # 檢查格式一致性
        if "session_id" in response and "timestamp" in response:
            score += 0.2
        
        # 檢查回應類型一致性
        response_type = response.get("type", "")
        if response_type in ["funnel_question", "recommendation", "elicitation", "general"]:
            score += 0.3
        
        # 檢查與之前回應的一致性
        history = context.get("history", [])
        if history:
            last_response = history[-1] if history else {}
            last_type = last_response.get("type", "")
            if response_type == last_type or response_type in ["general"]:
                score += 0.2
        
        return min(score, max_score)
    
    def _evaluate_accuracy(self, response: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        評估準確性
        
        Args:
            response: 回應字典
            context: 當前上下文
        
        Returns:
            準確性分數 (0.0-1.0)
        """
        score = 0.0
        max_score = 1.0
        
        # 檢查是否有錯誤標記
        if not response.get("error", False):
            score += 0.4
        
        # 檢查回應是否包含有效信息
        message = response.get("message", "")
        if message and len(message.strip()) > 0:
            score += 0.3
        
        # 檢查推薦數據的準確性（如果有）
        if "recommendations" in response:
            recommendations = response["recommendations"]
            if isinstance(recommendations, list) and len(recommendations) > 0:
                score += 0.3
        
        # 檢查問題選項的準確性（如果有）
        if "options" in response:
            options = response["options"]
            if isinstance(options, list) and len(options) > 0:
                score += 0.2
        
        return min(score, max_score)
    
    def _calculate_overall_score(self, evaluation: Dict[str, Any]) -> float:
        """
        計算總分
        
        Args:
            evaluation: 評估結果字典
        
        Returns:
            總分 (0.0-1.0)
        """
        total_score = 0.0
        
        for metric, weight in self.evaluation_weights.items():
            if metric in evaluation:
                total_score += evaluation[metric] * weight
        
        return min(total_score, 1.0)
    
    def _generate_suggestions(self, evaluation: Dict[str, Any]) -> List[str]:
        """
        生成改進建議
        
        Args:
            evaluation: 評估結果字典
        
        Returns:
            改進建議列表
        """
        suggestions = []
        
        # 完整性建議
        if evaluation["completeness"] < 0.7:
            suggestions.append("建議增加更多必要信息以提高完整性")
        
        # 清晰度建議
        if evaluation["clarity"] < 0.7:
            suggestions.append("建議使用更清晰的語言表達")
        
        # 相關性建議
        if evaluation["relevance"] < 0.7:
            suggestions.append("建議確保回應與用戶需求更相關")
        
        # 一致性建議
        if evaluation["consistency"] < 0.7:
            suggestions.append("建議保持回應風格的一致性")
        
        # 準確性建議
        if evaluation["accuracy"] < 0.7:
            suggestions.append("建議檢查回應內容的準確性")
        
        # 總體建議
        if evaluation["overall_score"] < 0.6:
            suggestions.append("整體回應品質需要改進，建議重新生成")
        
        return suggestions
    
    def _create_error_evaluation(self, error_message: str) -> Dict[str, Any]:
        """
        創建錯誤評估結果
        
        Args:
            error_message: 錯誤消息
        
        Returns:
            錯誤評估字典
        """
        return {
            "completeness": 0.0,
            "clarity": 0.0,
            "relevance": 0.0,
            "consistency": 0.0,
            "accuracy": 0.0,
            "overall_score": 0.0,
            "improvement_suggestions": [f"評估過程發生錯誤: {error_message}"],
            "evaluation_timestamp": datetime.now().isoformat(),
            "error": True
        }
    
    def get_evaluation_summary(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """
        獲取評估摘要
        
        Args:
            evaluation: 評估結果字典
        
        Returns:
            評估摘要字典
        """
        return {
            "overall_score": evaluation.get("overall_score", 0.0),
            "quality_level": self._get_quality_level(evaluation.get("overall_score", 0.0)),
            "main_issues": self._identify_main_issues(evaluation),
            "suggestions_count": len(evaluation.get("improvement_suggestions", [])),
            "evaluation_timestamp": evaluation.get("evaluation_timestamp", "")
        }
    
    def _get_quality_level(self, score: float) -> str:
        """
        獲取品質等級
        
        Args:
            score: 總分
        
        Returns:
            品質等級字符串
        """
        if score >= 0.9:
            return "優秀"
        elif score >= 0.8:
            return "良好"
        elif score >= 0.7:
            return "一般"
        elif score >= 0.6:
            return "需要改進"
        else:
            return "不合格"
    
    def _identify_main_issues(self, evaluation: Dict[str, Any]) -> List[str]:
        """
        識別主要問題
        
        Args:
            evaluation: 評估結果字典
        
        Returns:
            主要問題列表
        """
        issues = []
        
        for metric, score in evaluation.items():
            if metric in self.evaluation_weights and score < 0.6:
                metric_names = {
                    "completeness": "完整性",
                    "clarity": "清晰度",
                    "relevance": "相關性",
                    "consistency": "一致性",
                    "accuracy": "準確性"
                }
                issues.append(f"{metric_names.get(metric, metric)}不足")
        
        return issues
