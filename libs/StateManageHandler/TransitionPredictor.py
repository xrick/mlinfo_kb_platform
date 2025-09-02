"""
TransitionPredictor - 狀態轉換預測器
基於歷史數據和模式識別預測下一步可能的狀態轉換

功能：
1. 基於歷史模式的狀態預測
2. 用戶行為模式分析
3. 轉換機率計算
4. 預測準確度評估
"""

import logging
import json
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np

logger = logging.getLogger(__name__)


class TransitionPredictor:
    """狀態轉換預測器"""
    
    def __init__(self, history_window_days: int = 30):
        """
        初始化轉換預測器
        
        Args:
            history_window_days: 歷史數據窗口天數
        """
        self.history_window_days = history_window_days
        self.transition_history = []
        self.pattern_cache = {}
        self.accuracy_metrics = {
            "total_predictions": 0,
            "correct_predictions": 0,
            "accuracy_rate": 0.0
        }
        
        # 狀態轉換圖
        self.transition_graph = defaultdict(Counter)
        
        logger.info("TransitionPredictor 初始化完成")
    
    async def predict_next_states(
        self, 
        context: Dict[str, Any], 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        預測下一步可能的狀態
        
        Args:
            context: 當前上下文
            top_k: 返回前 k 個預測結果
            
        Returns:
            預測結果列表，包含狀態和機率
        """
        try:
            current_state = context.get("stage", "UNKNOWN")
            
            # 多種預測方法的結合
            predictions = []
            
            # 1. 基於歷史轉換圖的預測
            graph_predictions = await self._predict_from_transition_graph(current_state)
            predictions.extend(graph_predictions)
            
            # 2. 基於用戶行為模式的預測
            pattern_predictions = await self._predict_from_user_patterns(context)
            predictions.extend(pattern_predictions)
            
            # 3. 基於上下文特徵的預測
            context_predictions = await self._predict_from_context_features(context)
            predictions.extend(context_predictions)
            
            # 4. 基於時間模式的預測
            temporal_predictions = await self._predict_from_temporal_patterns(context)
            predictions.extend(temporal_predictions)
            
            # 合併和排序預測結果
            merged_predictions = self._merge_predictions(predictions)
            
            # 返回前 k 個預測
            top_predictions = sorted(
                merged_predictions.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:top_k]
            
            result = []
            for state, probability in top_predictions:
                result.append({
                    "next_state": state,
                    "probability": probability,
                    "confidence": self._calculate_prediction_confidence(state, context),
                    "reasoning": self._get_prediction_reasoning(state, context)
                })
            
            self.accuracy_metrics["total_predictions"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"預測狀態轉換失敗: {e}", exc_info=True)
            return [{
                "next_state": context.get("stage", "UNKNOWN"),
                "probability": 0.5,
                "confidence": 0.0,
                "reasoning": "預測失敗，使用默認狀態"
            }]
    
    async def _predict_from_transition_graph(
        self, 
        current_state: str
    ) -> List[Tuple[str, float]]:
        """基於狀態轉換圖預測"""
        if current_state not in self.transition_graph:
            return []
        
        state_counts = self.transition_graph[current_state]
        total_transitions = sum(state_counts.values())
        
        if total_transitions == 0:
            return []
        
        predictions = []
        for next_state, count in state_counts.items():
            probability = count / total_transitions
            predictions.append((next_state, probability * 0.4))  # 權重 40%
        
        return predictions
    
    async def _predict_from_user_patterns(
        self, 
        context: Dict[str, Any]
    ) -> List[Tuple[str, float]]:
        """基於用戶行為模式預測"""
        user_id = context.get("user_id")
        if not user_id:
            return []
        
        # 分析用戶的歷史行為模式
        user_patterns = self._get_user_patterns(user_id)
        
        predictions = []
        for pattern in user_patterns:
            if self._context_matches_pattern(context, pattern):
                predictions.append((
                    pattern["next_state"], 
                    pattern["confidence"] * 0.3  # 權重 30%
                ))
        
        return predictions
    
    async def _predict_from_context_features(
        self, 
        context: Dict[str, Any]
    ) -> List[Tuple[str, float]]:
        """基於上下文特徵預測"""
        features = self._extract_context_features(context)
        
        # 簡化的特徵基礎預測
        predictions = []
        
        # 意圖基礎預測
        intent = features.get("intent", "")
        if intent == "ask_recommendation":
            predictions.append(("RECOMMENDATION_PREPARATION", 0.8 * 0.2))
        elif intent == "ask_comparison":
            predictions.append(("PRODUCT_COMPARISON", 0.9 * 0.2))
        elif intent == "ask_price":
            predictions.append(("PRICE_FOCUSED_ELICITATION", 0.7 * 0.2))
        
        # 槽位完整度基礎預測
        slots_completeness = features.get("slots_completeness", 0.0)
        if slots_completeness > 0.8:
            predictions.append(("RECOMMENDATION_PREPARATION", 0.9 * 0.2))
        elif slots_completeness < 0.3:
            predictions.append(("FUNNEL_QUESTION", 0.8 * 0.2))
        
        return predictions
    
    async def _predict_from_temporal_patterns(
        self, 
        context: Dict[str, Any]
    ) -> List[Tuple[str, float]]:
        """基於時間模式預測"""
        current_time = datetime.now()
        
        predictions = []
        
        # 會話時長影響
        session_duration = self._get_session_duration(context)
        
        if session_duration > timedelta(minutes=10):
            # 長會話可能需要結束或快速決策
            predictions.append(("PURCHASE_GUIDANCE", 0.6 * 0.1))
            predictions.append(("END", 0.4 * 0.1))
        elif session_duration < timedelta(minutes=2):
            # 短會話可能還在收集信息
            predictions.append(("FUNNEL_QUESTION", 0.8 * 0.1))
            predictions.append(("ELICITATION", 0.6 * 0.1))
        
        # 一天中的時間影響
        hour = current_time.hour
        if 9 <= hour <= 17:  # 工作時間
            predictions.append(("RECOMMENDATION_PREPARATION", 0.7 * 0.05))
        elif 19 <= hour <= 22:  # 晚上購物時間
            predictions.append(("PRODUCT_COMPARISON", 0.8 * 0.05))
        
        return predictions
    
    def _merge_predictions(
        self, 
        predictions: List[Tuple[str, float]]
    ) -> Dict[str, float]:
        """合併多個預測結果"""
        merged = defaultdict(float)
        
        for state, probability in predictions:
            merged[state] += probability
        
        # 正規化機率
        total_prob = sum(merged.values())
        if total_prob > 0:
            for state in merged:
                merged[state] = merged[state] / total_prob
        
        return dict(merged)
    
    def _calculate_prediction_confidence(
        self, 
        predicted_state: str, 
        context: Dict[str, Any]
    ) -> float:
        """計算預測置信度"""
        # 基於多個因素計算置信度
        confidence_factors = []
        
        # 歷史數據量
        if predicted_state in self.transition_graph.get(context.get("stage", ""), {}):
            transition_count = self.transition_graph[context.get("stage", "")][predicted_state]
            confidence_factors.append(min(transition_count / 10, 1.0))
        
        # 上下文匹配度
        context_confidence = context.get("confidence", 0.0)
        confidence_factors.append(context_confidence)
        
        # 預測器準確度
        confidence_factors.append(self.accuracy_metrics["accuracy_rate"])
        
        # 計算平均置信度
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        else:
            return 0.5
    
    def _get_prediction_reasoning(
        self, 
        predicted_state: str, 
        context: Dict[str, Any]
    ) -> str:
        """獲取預測推理"""
        reasons = []
        
        current_state = context.get("stage", "UNKNOWN")
        
        # 常見轉換推理
        transition_reasons = {
            ("INIT", "FUNNEL_START"): "新用戶開始對話流程",
            ("FUNNEL_QUESTION", "RECOMMENDATION_PREPARATION"): "收集到足夠的用戶需求信息",
            ("RECOMMENDATION_PREPARATION", "RECOMMENDATION_PRESENTATION"): "完成產品搜尋和排序",
            ("RECOMMENDATION_PRESENTATION", "PRODUCT_QA"): "用戶對推薦產品有疑問",
            ("PRODUCT_QA", "PURCHASE_GUIDANCE"): "用戶滿意推薦結果"
        }
        
        reason_key = (current_state, predicted_state)
        if reason_key in transition_reasons:
            reasons.append(transition_reasons[reason_key])
        
        # 基於上下文的推理
        intent = context.get("intent", "")
        if intent and predicted_state:
            intent_reasons = {
                "ask_recommendation": f"用戶請求推薦，預測轉向{predicted_state}",
                "ask_comparison": f"用戶需要比較，預測轉向{predicted_state}",
                "ask_price": f"用戶關心價格，預測轉向{predicted_state}"
            }
            if intent in intent_reasons:
                reasons.append(intent_reasons[intent])
        
        return "; ".join(reasons) if reasons else f"基於歷史模式預測轉向{predicted_state}"
    
    def _extract_context_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """提取上下文特徵"""
        slots = context.get("slots", {})
        
        return {
            "intent": context.get("intent", ""),
            "confidence": context.get("confidence", 0.0),
            "stage": context.get("stage", ""),
            "slots_count": len(slots),
            "slots_completeness": self._calculate_slots_completeness(slots),
            "user_message_length": len(context.get("user_message", "")),
            "has_question_mark": "?" in context.get("user_message", ""),
            "session_id": context.get("session_id", "")
        }
    
    def _calculate_slots_completeness(self, slots: Dict[str, Any]) -> float:
        """計算槽位完整度"""
        required_slots = ["usage_purpose", "price_range"]
        optional_slots = ["cpu_performance", "gpu_performance", "portability", "screen_size"]
        
        required_filled = sum(1 for slot in required_slots if slots.get(slot))
        optional_filled = sum(1 for slot in optional_slots if slots.get(slot))
        
        completeness = (
            (required_filled / len(required_slots)) * 0.7 +
            (optional_filled / len(optional_slots)) * 0.3
        )
        
        return min(completeness, 1.0)
    
    def _get_user_patterns(self, user_id: str) -> List[Dict[str, Any]]:
        """獲取用戶行為模式"""
        # 這裡應該從數據庫或緩存中獲取用戶的歷史行為模式
        # 現在返回示例模式
        return [
            {
                "pattern_id": f"{user_id}_pattern_1",
                "context_features": {"intent": "ask_recommendation", "confidence": 0.8},
                "next_state": "RECOMMENDATION_PREPARATION",
                "confidence": 0.85,
                "frequency": 15
            }
        ]
    
    def _context_matches_pattern(
        self, 
        context: Dict[str, Any], 
        pattern: Dict[str, Any]
    ) -> bool:
        """檢查上下文是否匹配模式"""
        context_features = self._extract_context_features(context)
        pattern_features = pattern.get("context_features", {})
        
        # 簡單的特徵匹配
        matches = 0
        total_features = len(pattern_features)
        
        for feature, expected_value in pattern_features.items():
            if context_features.get(feature) == expected_value:
                matches += 1
        
        # 匹配度超過 70% 認為匹配
        return matches / total_features >= 0.7 if total_features > 0 else False
    
    def _get_session_duration(self, context: Dict[str, Any]) -> timedelta:
        """獲取會話時長"""
        # 從上下文或會話數據中計算時長
        # 這裡返回示例時長
        return timedelta(minutes=5)
    
    def record_transition(
        self, 
        from_state: str, 
        to_state: str, 
        context: Dict[str, Any]
    ):
        """記錄實際的狀態轉換"""
        # 更新轉換圖
        self.transition_graph[from_state][to_state] += 1
        
        # 記錄歷史
        self.transition_history.append({
            "from_state": from_state,
            "to_state": to_state,
            "context_features": self._extract_context_features(context),
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制歷史長度
        if len(self.transition_history) > 10000:
            self.transition_history = self.transition_history[-10000:]
    
    def update_prediction_accuracy(self, predicted_state: str, actual_state: str):
        """更新預測準確度"""
        if predicted_state == actual_state:
            self.accuracy_metrics["correct_predictions"] += 1
        
        # 計算準確率
        if self.accuracy_metrics["total_predictions"] > 0:
            self.accuracy_metrics["accuracy_rate"] = (
                self.accuracy_metrics["correct_predictions"] / 
                self.accuracy_metrics["total_predictions"]
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """獲取預測器指標"""
        return {
            **self.accuracy_metrics,
            "total_transitions_recorded": len(self.transition_history),
            "unique_states": len(self.transition_graph),
            "total_transition_pairs": sum(
                len(transitions) for transitions in self.transition_graph.values()
            ),
            "last_updated": datetime.now().isoformat()
        }