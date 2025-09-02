"""
StateTransition - 狀態轉換系統
實現智能狀態轉換邏輯和狀態解析器

主要組件：
1. StateTransition - 狀態轉換數據結構
2. StateResolver - 抽象狀態解析器基類
3. 各種具體狀態解析器實現
4. 業務規則引擎
5. 狀態轉換預測器
"""

import logging
import json
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
import random

logger = logging.getLogger(__name__)


class TransitionResult(Enum):
    """狀態轉換結果"""
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    FALLBACK = "fallback"


class ConditionOperator(Enum):
    """條件運算符"""
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    CONTAINS = "in"
    EXISTS = "exists"
    REGEX_MATCH = "regex"


@dataclass
class StateCondition:
    """狀態條件"""
    field_path: str  # 例如 "slots.usage_purpose"
    operator: ConditionOperator
    expected_value: Any
    weight: float = 1.0  # 條件權重
    
    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, float]:
        """
        評估條件
        
        Returns:
            (條件是否滿足, 置信度分數)
        """
        try:
            # 解析字段路徑
            field_value = self._get_nested_value(context, self.field_path)
            
            # 執行條件判斷
            result = False
            confidence = 0.0
            
            if self.operator == ConditionOperator.EQUALS:
                result = field_value == self.expected_value
                confidence = 1.0 if result else 0.0
                
            elif self.operator == ConditionOperator.NOT_EQUALS:
                result = field_value != self.expected_value
                confidence = 1.0 if result else 0.0
                
            elif self.operator == ConditionOperator.GREATER_THAN:
                result = field_value > self.expected_value
                confidence = 1.0 if result else 0.0
                
            elif self.operator == ConditionOperator.LESS_THAN:
                result = field_value < self.expected_value
                confidence = 1.0 if result else 0.0
                
            elif self.operator == ConditionOperator.CONTAINS:
                result = self.expected_value in str(field_value)
                confidence = 1.0 if result else 0.0
                
            elif self.operator == ConditionOperator.EXISTS:
                result = field_value is not None
                confidence = 1.0 if result else 0.0
                
            # 模糊匹配的置信度計算
            if not result and field_value is not None and self.expected_value is not None:
                similarity = self._calculate_similarity(field_value, self.expected_value)
                confidence = similarity * 0.5  # 部分匹配的置信度
            
            return result, confidence * self.weight
            
        except Exception as e:
            logger.warning(f"條件評估失敗: {e}")
            return False, 0.0
    
    def _get_nested_value(self, context: Dict[str, Any], field_path: str) -> Any:
        """獲取嵌套字段值"""
        keys = field_path.split('.')
        value = context
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _calculate_similarity(self, value1: Any, value2: Any) -> float:
        """計算兩個值的相似度"""
        try:
            str1, str2 = str(value1).lower(), str(value2).lower()
            
            # 簡單的 Jaccard 相似度
            set1, set2 = set(str1.split()), set(str2.split())
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            
            return intersection / union if union > 0 else 0.0
            
        except Exception:
            return 0.0


@dataclass
class StateTransition:
    """
    狀態轉換配置
    
    定義從一個狀態轉換到另一個狀態的完整規則
    """
    # 核心配置
    actions: List[Callable[[Dict[str, Any]], Dict[str, Any]]] = field(default_factory=list)
    next_state_resolver: Optional['StateResolver'] = None
    
    # 轉換條件
    preconditions: List[StateCondition] = field(default_factory=list)
    postconditions: List[StateCondition] = field(default_factory=list)
    
    # 配置參數
    timeout_ms: int = 30000
    retry_policy: Optional['RetryPolicy'] = None
    rollback_enabled: bool = True
    
    # 擴展功能
    context_enrichment: List[Callable[[Dict[str, Any]], Dict[str, Any]]] = field(default_factory=list)
    adaptive_behavior: bool = False
    performance_critical: bool = False
    success_metrics: List[str] = field(default_factory=list)
    
    # 元數據
    description: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行狀態轉換
        
        Returns:
            轉換執行結果
        """
        start_time = datetime.now()
        
        try:
            # 1. 檢查前置條件
            preconditions_result = await self._check_preconditions(context)
            if not preconditions_result['passed']:
                return {
                    "success": False,
                    "error": "前置條件不滿足",
                    "failed_conditions": preconditions_result['failed'],
                    "result_type": TransitionResult.FAILED
                }
            
            # 2. 上下文豐富化
            enriched_context = await self._enrich_context(context)
            
            # 3. 執行轉換動作
            actions_result = await self._execute_actions(enriched_context)
            if not actions_result['success']:
                return {
                    "success": False,
                    "error": actions_result['error'],
                    "result_type": TransitionResult.FAILED
                }
            
            # 4. 決定下一個狀態
            next_state = await self._resolve_next_state(enriched_context)
            
            # 5. 檢查後置條件
            postconditions_result = await self._check_postconditions(enriched_context)
            
            # 6. 組裝結果
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "next_state": next_state,
                "context_updates": enriched_context,
                "execution_time_ms": execution_time * 1000,
                "preconditions_confidence": preconditions_result['confidence'],
                "postconditions_passed": postconditions_result['passed'],
                "result_type": TransitionResult.SUCCESS,
                "timestamp": datetime.now().isoformat()
            }
            
            # 7. 性能關鍵路徑的特殊處理
            if self.performance_critical:
                result["performance_metrics"] = await self._collect_performance_metrics(execution_time)
            
            return result
            
        except Exception as e:
            logger.error(f"狀態轉換執行失敗: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "result_type": TransitionResult.FAILED,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_preconditions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """檢查前置條件"""
        if not self.preconditions:
            return {"passed": True, "confidence": 1.0, "failed": []}
        
        passed_conditions = []
        failed_conditions = []
        total_confidence = 0.0
        
        for condition in self.preconditions:
            passed, confidence = condition.evaluate(context)
            total_confidence += confidence
            
            if passed:
                passed_conditions.append(condition.field_path)
            else:
                failed_conditions.append({
                    "field_path": condition.field_path,
                    "operator": condition.operator.value,
                    "expected": condition.expected_value,
                    "actual": condition._get_nested_value(context, condition.field_path)
                })
        
        # 條件通過閾值（可配置）
        pass_threshold = 0.7
        overall_confidence = total_confidence / len(self.preconditions)
        
        return {
            "passed": overall_confidence >= pass_threshold,
            "confidence": overall_confidence,
            "failed": failed_conditions,
            "passed_count": len(passed_conditions),
            "total_count": len(self.preconditions)
        }
    
    async def _enrich_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """上下文豐富化"""
        enriched_context = context.copy()
        
        for enricher in self.context_enrichment:
            try:
                enrichment_result = await enricher(enriched_context)
                if isinstance(enrichment_result, dict):
                    enriched_context.update(enrichment_result)
            except Exception as e:
                logger.warning(f"上下文豐富化失敗: {e}")
        
        return enriched_context
    
    async def _execute_actions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """執行轉換動作"""
        if not self.actions:
            return {"success": True, "results": []}
        
        action_results = []
        
        for action in self.actions:
            try:
                if asyncio.iscoroutinefunction(action):
                    action_result = await action(context)
                else:
                    action_result = action(context)
                
                if isinstance(action_result, dict):
                    context.update(action_result)
                    action_results.append({
                        "action": action.__name__ if hasattr(action, '__name__') else str(action),
                        "success": True,
                        "result": action_result
                    })
                else:
                    action_results.append({
                        "action": action.__name__ if hasattr(action, '__name__') else str(action),
                        "success": False,
                        "error": "動作未返回字典格式"
                    })
                    
            except Exception as e:
                logger.error(f"執行動作失敗: {e}")
                action_results.append({
                    "action": action.__name__ if hasattr(action, '__name__') else str(action),
                    "success": False,
                    "error": str(e)
                })
                
                # 如果不允許部分失敗，則整體失敗
                return {
                    "success": False,
                    "error": f"動作執行失敗: {str(e)}",
                    "action_results": action_results
                }
        
        return {"success": True, "action_results": action_results}
    
    async def _resolve_next_state(self, context: Dict[str, Any]) -> str:
        """解析下一個狀態"""
        if not self.next_state_resolver:
            return context.get("stage", "UNKNOWN")
        
        try:
            return await self.next_state_resolver.resolve_next_state(context)
        except Exception as e:
            logger.error(f"解析下一個狀態失敗: {e}")
            return context.get("stage", "ERROR")
    
    async def _check_postconditions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """檢查後置條件"""
        # 實現與前置條件類似的邏輯
        return {"passed": True, "confidence": 1.0}
    
    async def _collect_performance_metrics(self, execution_time: float) -> Dict[str, Any]:
        """收集性能指標"""
        return {
            "execution_time_ms": execution_time * 1000,
            "memory_usage_mb": 0.0,  # 可以實際測量內存使用
            "cpu_usage_percent": 0.0  # 可以實際測量 CPU 使用
        }


# =================== 狀態解析器基類和實現 ===================

class StateResolver(ABC):
    """狀態解析器抽象基類"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def resolve_next_state(self, context: Dict[str, Any]) -> str:
        """解析下一個狀態"""
        pass


class FixedResolver(StateResolver):
    """固定狀態解析器"""
    
    def __init__(self, next_state: str):
        super().__init__(f"FixedResolver({next_state})")
        self.next_state = next_state
    
    async def resolve_next_state(self, context: Dict[str, Any]) -> str:
        return self.next_state


class ConditionalResolver(StateResolver):
    """條件狀態解析器"""
    
    def __init__(self, state_mapping: Dict[str, str], default_state: str = "UNKNOWN"):
        super().__init__("ConditionalResolver")
        self.state_mapping = state_mapping
        self.default_state = default_state
    
    async def resolve_next_state(self, context: Dict[str, Any]) -> str:
        """根據條件映射解析狀態"""
        for condition_key, next_state in self.state_mapping.items():
            if await self._evaluate_condition(condition_key, context):
                return next_state
        
        return self.default_state
    
    async def _evaluate_condition(self, condition_key: str, context: Dict[str, Any]) -> bool:
        """評估條件鍵"""
        # 簡單的條件評估邏輯
        if condition_key == "user_cooperative":
            return context.get("user_sentiment", "neutral") in ["positive", "cooperative"]
        elif condition_key == "user_impatient":
            return context.get("user_sentiment", "neutral") == "impatient"
        elif condition_key == "slots_sufficient":
            slots = context.get("slots", {})
            required_slots = ["usage_purpose", "price_range"]
            return all(slot in slots and slots[slot] for slot in required_slots)
        elif condition_key == "need_more_info":
            slots = context.get("slots", {})
            return len(slots) < 3
        
        # 默認條件評估
        return condition_key in context and context[condition_key]


class DynamicStateResolver(StateResolver):
    """動態狀態解析器"""
    
    def __init__(self, base_mapping: Dict[str, str]):
        super().__init__("DynamicStateResolver")
        self.base_mapping = base_mapping
        self.ml_predictor = None  # 將在後續實現
        self.rule_engine = BusinessRuleEngine()
        self.history = []  # 決策歷史
    
    async def resolve_next_state(self, context: Dict[str, Any]) -> str:
        """智能解析下一個狀態"""
        # 1. 基於規則的判斷
        rule_based_state = await self.rule_engine.evaluate(context)
        if rule_based_state:
            self._record_decision("rule_based", rule_based_state, context)
            return rule_based_state
        
        # 2. 歷史模式匹配
        pattern_based_state = await self._analyze_historical_patterns(context)
        if pattern_based_state:
            self._record_decision("pattern_based", pattern_based_state, context)
            return pattern_based_state
        
        # 3. 基礎映射
        for condition, state in self.base_mapping.items():
            if await self._evaluate_base_condition(condition, context):
                self._record_decision("base_mapping", state, context)
                return state
        
        # 4. 默認狀態
        default_state = context.get("stage", "UNKNOWN")
        self._record_decision("default", default_state, context)
        return default_state
    
    async def _analyze_historical_patterns(self, context: Dict[str, Any]) -> Optional[str]:
        """分析歷史模式"""
        if len(self.history) < 3:
            return None
        
        # 尋找相似的歷史上下文
        similar_decisions = []
        current_features = self._extract_features(context)
        
        for hist_decision in self.history[-10:]:  # 查看最近10個決策
            hist_features = hist_decision.get("features", {})
            similarity = self._calculate_feature_similarity(current_features, hist_features)
            
            if similarity > 0.7:
                similar_decisions.append(hist_decision)
        
        # 返回最頻繁的狀態
        if similar_decisions:
            state_counts = {}
            for decision in similar_decisions:
                state = decision["state"]
                state_counts[state] = state_counts.get(state, 0) + 1
            
            return max(state_counts, key=state_counts.get)
        
        return None
    
    def _extract_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """提取上下文特徵"""
        return {
            "intent": context.get("intent", ""),
            "confidence": context.get("confidence", 0.0),
            "slots_count": len(context.get("slots", {})),
            "user_sentiment": context.get("user_sentiment", "neutral"),
            "stage": context.get("stage", ""),
            "message_length": len(context.get("user_message", "")),
            "has_question": "?" in context.get("user_message", "")
        }
    
    def _calculate_feature_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """計算特徵相似度"""
        if not features1 or not features2:
            return 0.0
        
        total_similarity = 0.0
        feature_count = 0
        
        for key in set(features1.keys()) & set(features2.keys()):
            val1, val2 = features1[key], features2[key]
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # 數值相似度
                max_val = max(abs(val1), abs(val2), 1)
                similarity = 1 - abs(val1 - val2) / max_val
            else:
                # 字符串相似度
                similarity = 1.0 if val1 == val2 else 0.0
            
            total_similarity += similarity
            feature_count += 1
        
        return total_similarity / feature_count if feature_count > 0 else 0.0
    
    async def _evaluate_base_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """評估基礎條件"""
        # 重用 ConditionalResolver 的邏輯
        temp_resolver = ConditionalResolver({condition: "temp"})
        return await temp_resolver._evaluate_condition(condition, context)
    
    def _record_decision(self, decision_type: str, state: str, context: Dict[str, Any]):
        """記錄決策歷史"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "decision_type": decision_type,
            "state": state,
            "features": self._extract_features(context),
            "context_summary": {
                "intent": context.get("intent", ""),
                "stage": context.get("stage", ""),
                "slots_count": len(context.get("slots", {}))
            }
        })
        
        # 限制歷史長度
        if len(self.history) > 100:
            self.history = self.history[-100:]


class BusinessRuleEngine:
    """業務規則引擎"""
    
    def __init__(self):
        self.rules = self._load_business_rules()
    
    def _load_business_rules(self) -> List[Dict[str, Any]]:
        """載入業務規則"""
        return [
            {
                "name": "emergency_support",
                "condition": lambda ctx: ctx.get("user_message", "").lower() in ["help", "emergency", "urgent"],
                "next_state": "EMERGENCY_SUPPORT"
            },
            {
                "name": "price_focused",
                "condition": lambda ctx: "price" in ctx.get("user_message", "").lower() or "budget" in ctx.get("user_message", "").lower(),
                "next_state": "PRICE_FOCUSED_ELICITATION"
            },
            {
                "name": "technical_question",
                "condition": lambda ctx: any(term in ctx.get("user_message", "").lower() 
                                           for term in ["spec", "cpu", "gpu", "ram", "storage", "technical"]),
                "next_state": "TECHNICAL_QA"
            }
        ]
    
    async def evaluate(self, context: Dict[str, Any]) -> Optional[str]:
        """評估業務規則"""
        for rule in self.rules:
            try:
                if rule["condition"](context):
                    logger.info(f"業務規則觸發: {rule['name']} -> {rule['next_state']}")
                    return rule["next_state"]
            except Exception as e:
                logger.warning(f"業務規則評估失敗 {rule['name']}: {e}")
        
        return None


@dataclass  
class RetryPolicy:
    """重試策略"""
    max_retries: int = 3
    initial_delay_ms: int = 1000
    backoff_multiplier: float = 2.0
    max_delay_ms: int = 10000
    
    async def execute_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """執行帶重試的操作"""
        delay = self.initial_delay_ms
        
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(operation):
                    return await operation(*args, **kwargs)
                else:
                    return operation(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries:
                    raise e
                
                logger.warning(f"操作失敗，第 {attempt + 1} 次重試: {e}")
                await asyncio.sleep(delay / 1000)
                delay = min(delay * self.backoff_multiplier, self.max_delay_ms)