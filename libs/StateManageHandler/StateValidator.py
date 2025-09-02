"""
StateValidator - 狀態驗證器
提供全面的狀態轉換和上下文驗證功能

驗證類型：
1. 狀態一致性驗證
2. 業務邏輯驗證
3. 數據完整性驗證
4. 安全性驗證
5. 性能和資源驗證
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """驗證嚴重性等級"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationType(Enum):
    """驗證類型"""
    STATE_CONSISTENCY = "state_consistency"
    BUSINESS_LOGIC = "business_logic"
    DATA_INTEGRITY = "data_integrity"
    SECURITY = "security"
    PERFORMANCE = "performance"
    SCHEMA = "schema"


@dataclass
class ValidationResult:
    """驗證結果"""
    validation_type: ValidationType
    severity: ValidationSeverity
    passed: bool
    message: str
    field_path: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    suggestion: Optional[str] = None
    error_code: Optional[str] = None


class StateValidator:
    """狀態驗證器"""
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
        self.validation_history = []
        self.error_patterns = self._load_error_patterns()
        
        # 驗證統計
        self.metrics = {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "validation_types": {},
            "error_patterns": {}
        }
        
        logger.info("StateValidator 初始化完成")
    
    async def validate_state_transition(
        self, 
        from_state: str, 
        to_state: str, 
        context: Dict[str, Any]
    ) -> List[ValidationResult]:
        """
        驗證狀態轉換的合法性
        
        Args:
            from_state: 源狀態
            to_state: 目標狀態
            context: 當前上下文
            
        Returns:
            驗證結果列表
        """
        validation_results = []
        
        try:
            # 1. 狀態一致性驗證
            consistency_results = await self._validate_state_consistency(from_state, to_state, context)
            validation_results.extend(consistency_results)
            
            # 2. 業務邏輯驗證
            business_results = await self._validate_business_logic(from_state, to_state, context)
            validation_results.extend(business_results)
            
            # 3. 數據完整性驗證
            integrity_results = await self._validate_data_integrity(context)
            validation_results.extend(integrity_results)
            
            # 4. 安全性驗證
            security_results = await self._validate_security(context)
            validation_results.extend(security_results)
            
            # 5. 性能驗證
            performance_results = await self._validate_performance(context)
            validation_results.extend(performance_results)
            
            # 更新統計
            await self._update_validation_metrics(validation_results)
            
            # 記錄驗證歷史
            self._record_validation_history(from_state, to_state, validation_results)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"狀態轉換驗證失敗: {e}", exc_info=True)
            return [ValidationResult(
                validation_type=ValidationType.STATE_CONSISTENCY,
                severity=ValidationSeverity.CRITICAL,
                passed=False,
                message=f"驗證過程發生錯誤: {str(e)}",
                error_code="VALIDATION_ERROR"
            )]
    
    async def validate_context(self, context: Dict[str, Any]) -> List[ValidationResult]:
        """
        驗證上下文數據
        
        Args:
            context: 要驗證的上下文
            
        Returns:
            驗證結果列表
        """
        validation_results = []
        
        try:
            # Schema 驗證
            schema_results = await self._validate_context_schema(context)
            validation_results.extend(schema_results)
            
            # 數據類型驗證
            type_results = await self._validate_data_types(context)
            validation_results.extend(type_results)
            
            # 必填字段驗證
            required_results = await self._validate_required_fields(context)
            validation_results.extend(required_results)
            
            # 數據範圍驗證
            range_results = await self._validate_data_ranges(context)
            validation_results.extend(range_results)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"上下文驗證失敗: {e}")
            return [ValidationResult(
                validation_type=ValidationType.DATA_INTEGRITY,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message=f"上下文驗證錯誤: {str(e)}"
            )]
    
    async def _validate_state_consistency(
        self, 
        from_state: str, 
        to_state: str, 
        context: Dict[str, Any]
    ) -> List[ValidationResult]:
        """驗證狀態一致性"""
        results = []
        
        # 檢查非法狀態轉換
        illegal_transitions = {
            "END": ["INIT", "FUNNEL_START", "FUNNEL_QUESTION"],  # 結束狀態不能回到開始
            "INIT": ["END"]  # 初始狀態不能直接結束
        }
        
        if from_state in illegal_transitions and to_state in illegal_transitions[from_state]:
            results.append(ValidationResult(
                validation_type=ValidationType.STATE_CONSISTENCY,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message=f"非法狀態轉換: {from_state} -> {to_state}",
                suggestion="檢查狀態機邏輯，確保轉換順序正確"
            ))
        
        # 檢查狀態循環
        if await self._detect_state_loop(from_state, to_state, context):
            results.append(ValidationResult(
                validation_type=ValidationType.STATE_CONSISTENCY,
                severity=ValidationSeverity.WARNING,
                passed=False,
                message=f"檢測到可能的狀態循環: {from_state} -> {to_state}",
                suggestion="確認是否為預期的循環行為"
            ))
        
        # 狀態名稱格式驗證
        if not self._validate_state_name_format(to_state):
            results.append(ValidationResult(
                validation_type=ValidationType.STATE_CONSISTENCY,
                severity=ValidationSeverity.WARNING,
                passed=False,
                message=f"狀態名稱格式不規範: {to_state}",
                suggestion="使用 UPPER_CASE_WITH_UNDERSCORE 格式"
            ))
        
        return results
    
    async def _validate_business_logic(
        self, 
        from_state: str, 
        to_state: str, 
        context: Dict[str, Any]
    ) -> List[ValidationResult]:
        """驗證業務邏輯"""
        results = []
        
        # 檢查推薦前是否有足夠信息
        if to_state == "RECOMMENDATION_PREPARATION":
            slots = context.get("slots", {})
            required_slots = ["usage_purpose", "price_range"]
            
            missing_slots = [slot for slot in required_slots if not slots.get(slot)]
            if missing_slots:
                results.append(ValidationResult(
                    validation_type=ValidationType.BUSINESS_LOGIC,
                    severity=ValidationSeverity.ERROR,
                    passed=False,
                    message=f"推薦準備前缺少必要信息: {missing_slots}",
                    suggestion="繼續收集用戶需求信息"
                ))
        
        # 檢查用戶意圖與狀態轉換的一致性
        intent = context.get("intent", "")
        if intent == "goodbye" and to_state not in ["END"]:
            results.append(ValidationResult(
                validation_type=ValidationType.BUSINESS_LOGIC,
                severity=ValidationSeverity.WARNING,
                passed=False,
                message="用戶表達告別意圖但狀態未轉向結束",
                suggestion="考慮轉向 END 狀態"
            ))
        
        # 檢查會話時長
        session_duration = self._calculate_session_duration(context)
        if session_duration and session_duration > timedelta(minutes=30):
            results.append(ValidationResult(
                validation_type=ValidationType.BUSINESS_LOGIC,
                severity=ValidationSeverity.WARNING,
                passed=False,
                message="會話時長過長，可能影響用戶體驗",
                suggestion="考慮主動引導至決策或結束"
            ))
        
        return results
    
    async def _validate_data_integrity(self, context: Dict[str, Any]) -> List[ValidationResult]:
        """驗證數據完整性"""
        results = []
        
        # 檢查關鍵字段
        critical_fields = ["session_id", "stage"]
        for field in critical_fields:
            if field not in context or not context[field]:
                results.append(ValidationResult(
                    validation_type=ValidationType.DATA_INTEGRITY,
                    severity=ValidationSeverity.CRITICAL,
                    passed=False,
                    message=f"缺少關鍵字段: {field}",
                    field_path=field
                ))
        
        # 檢查數據類型
        type_checks = {
            "confidence": (float, int),
            "slots": dict,
            "user_message": str
        }
        
        for field, expected_types in type_checks.items():
            if field in context and context[field] is not None:
                if not isinstance(context[field], expected_types):
                    results.append(ValidationResult(
                        validation_type=ValidationType.DATA_INTEGRITY,
                        severity=ValidationSeverity.ERROR,
                        passed=False,
                        message=f"字段類型錯誤: {field}",
                        field_path=field,
                        expected_value=str(expected_types),
                        actual_value=type(context[field]).__name__
                    ))
        
        # 檢查數據一致性
        slots = context.get("slots", {})
        if "price_range" in slots:
            price_range = slots["price_range"]
            if isinstance(price_range, str) and not self._validate_price_range_format(price_range):
                results.append(ValidationResult(
                    validation_type=ValidationType.DATA_INTEGRITY,
                    severity=ValidationSeverity.WARNING,
                    passed=False,
                    message="價格範圍格式不規範",
                    field_path="slots.price_range",
                    actual_value=price_range,
                    suggestion="使用標準格式如 '20000-30000' 或 '低於20000'"
                ))
        
        return results
    
    async def _validate_security(self, context: Dict[str, Any]) -> List[ValidationResult]:
        """驗證安全性"""
        results = []
        
        # 檢查敏感信息
        user_message = context.get("user_message", "")
        if self._contains_sensitive_info(user_message):
            results.append(ValidationResult(
                validation_type=ValidationType.SECURITY,
                severity=ValidationSeverity.WARNING,
                passed=False,
                message="用戶輸入可能包含敏感信息",
                suggestion="考慮過濾或加密敏感數據"
            ))
        
        # 檢查會話ID格式
        session_id = context.get("session_id", "")
        if session_id and not self._validate_session_id_format(session_id):
            results.append(ValidationResult(
                validation_type=ValidationType.SECURITY,
                severity=ValidationSeverity.WARNING,
                passed=False,
                message="會話ID格式不安全",
                field_path="session_id",
                suggestion="使用更安全的會話ID生成策略"
            ))
        
        # 檢查惡意輸入
        if self._detect_malicious_input(user_message):
            results.append(ValidationResult(
                validation_type=ValidationType.SECURITY,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message="檢測到可能的惡意輸入",
                suggestion="清理和驗證用戶輸入"
            ))
        
        return results
    
    async def _validate_performance(self, context: Dict[str, Any]) -> List[ValidationResult]:
        """驗證性能相關指標"""
        results = []
        
        # 檢查上下文大小
        context_size = len(json.dumps(context))
        if context_size > 100000:  # 100KB
            results.append(ValidationResult(
                validation_type=ValidationType.PERFORMANCE,
                severity=ValidationSeverity.WARNING,
                passed=False,
                message=f"上下文過大: {context_size} bytes",
                suggestion="考慮清理不必要的數據"
            ))
        
        # 檢查槽位數量
        slots = context.get("slots", {})
        if len(slots) > 50:
            results.append(ValidationResult(
                validation_type=ValidationType.PERFORMANCE,
                severity=ValidationSeverity.WARNING,
                passed=False,
                message=f"槽位過多: {len(slots)}",
                suggestion="清理不再需要的槽位"
            ))
        
        # 檢查歷史記錄長度
        history = context.get("history", [])
        if len(history) > 100:
            results.append(ValidationResult(
                validation_type=ValidationType.PERFORMANCE,
                severity=ValidationSeverity.INFO,
                passed=False,
                message=f"歷史記錄過長: {len(history)}",
                suggestion="考慮截斷舊的歷史記錄"
            ))
        
        return results
    
    async def _validate_context_schema(self, context: Dict[str, Any]) -> List[ValidationResult]:
        """驗證上下文結構"""
        results = []
        
        # 定義預期的 schema
        expected_schema = {
            "session_id": str,
            "stage": str,
            "user_message": str,
            "intent": str,
            "confidence": (float, int),
            "slots": dict,
            "history": list,
            "user_profile": dict
        }
        
        for field, expected_type in expected_schema.items():
            if field in context and context[field] is not None:
                if not isinstance(context[field], expected_type):
                    results.append(ValidationResult(
                        validation_type=ValidationType.SCHEMA,
                        severity=ValidationSeverity.ERROR,
                        passed=False,
                        message=f"Schema 驗證失敗: {field}",
                        field_path=field,
                        expected_value=str(expected_type),
                        actual_value=type(context[field]).__name__
                    ))
        
        return results
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """載入驗證規則"""
        return {
            "max_session_duration_hours": 2,
            "max_context_size_bytes": 100000,
            "max_slots_count": 50,
            "max_history_length": 100,
            "required_fields": ["session_id", "stage"],
            "sensitive_patterns": [
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # 信用卡號
                r'\b\d{3}-\d{2}-\d{4}\b',  # 社會安全號碼
                r'\b[\w\.-]+@[\w\.-]+\.\w+\b'  # 電子郵件
            ]
        }
    
    def _load_error_patterns(self) -> List[Dict[str, Any]]:
        """載入錯誤模式"""
        return [
            {
                "pattern": "timeout",
                "severity": ValidationSeverity.ERROR,
                "category": "performance"
            },
            {
                "pattern": "null_pointer|none_type",
                "severity": ValidationSeverity.CRITICAL,
                "category": "data_integrity"
            }
        ]
    
    async def _detect_state_loop(
        self, 
        from_state: str, 
        to_state: str, 
        context: Dict[str, Any]
    ) -> bool:
        """檢測狀態循環"""
        history = context.get("history", [])
        
        # 檢查最近的狀態歷史
        recent_states = [h.get("state") for h in history[-5:] if h.get("state")]
        
        # 如果最近的狀態中出現重複，可能是循環
        if recent_states.count(to_state) >= 3:
            return True
        
        return False
    
    def _validate_state_name_format(self, state_name: str) -> bool:
        """驗證狀態名稱格式"""
        pattern = r'^[A-Z][A-Z0-9_]*$'
        return bool(re.match(pattern, state_name))
    
    def _calculate_session_duration(self, context: Dict[str, Any]) -> Optional[timedelta]:
        """計算會話時長"""
        # 這裡應該根據實際的會話開始時間計算
        # 暫時返回示例時長
        return timedelta(minutes=5)
    
    def _validate_price_range_format(self, price_range: str) -> bool:
        """驗證價格範圍格式"""
        patterns = [
            r'^\d+-\d+$',  # 20000-30000
            r'^低於\d+$',   # 低於20000
            r'^高於\d+$',   # 高於50000
            r'^\d+以下$',   # 30000以下
            r'^\d+以上$'    # 40000以上
        ]
        
        return any(re.match(pattern, price_range) for pattern in patterns)
    
    def _contains_sensitive_info(self, text: str) -> bool:
        """檢查是否包含敏感信息"""
        for pattern in self.validation_rules["sensitive_patterns"]:
            if re.search(pattern, text):
                return True
        return False
    
    def _validate_session_id_format(self, session_id: str) -> bool:
        """驗證會話ID格式"""
        # 檢查長度和字符
        if len(session_id) < 16:
            return False
        
        # 檢查是否只包含字母數字和連字符
        pattern = r'^[a-zA-Z0-9\-_]+$'
        return bool(re.match(pattern, session_id))
    
    def _detect_malicious_input(self, text: str) -> bool:
        """檢測惡意輸入"""
        malicious_patterns = [
            r'<script',  # XSS
            r'javascript:',  # JavaScript injection
            r'SELECT.*FROM',  # SQL injection
            r'UNION.*SELECT',  # SQL injection
            r'DROP.*TABLE'  # SQL injection
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in malicious_patterns)
    
    async def _validate_data_types(self, context: Dict[str, Any]) -> List[ValidationResult]:
        """驗證數據類型"""
        results = []
        
        # 特定字段的類型檢查已在 _validate_data_integrity 中完成
        # 這裡可以添加更詳細的類型驗證邏輯
        
        return results
    
    async def _validate_required_fields(self, context: Dict[str, Any]) -> List[ValidationResult]:
        """驗證必填字段"""
        results = []
        
        required_fields = self.validation_rules["required_fields"]
        for field in required_fields:
            if field not in context or context[field] is None:
                results.append(ValidationResult(
                    validation_type=ValidationType.DATA_INTEGRITY,
                    severity=ValidationSeverity.CRITICAL,
                    passed=False,
                    message=f"缺少必填字段: {field}",
                    field_path=field
                ))
        
        return results
    
    async def _validate_data_ranges(self, context: Dict[str, Any]) -> List[ValidationResult]:
        """驗證數據範圍"""
        results = []
        
        # 置信度範圍檢查
        confidence = context.get("confidence")
        if confidence is not None and (confidence < 0 or confidence > 1):
            results.append(ValidationResult(
                validation_type=ValidationType.DATA_INTEGRITY,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message="置信度超出有效範圍 [0, 1]",
                field_path="confidence",
                actual_value=confidence
            ))
        
        return results
    
    async def _update_validation_metrics(self, validation_results: List[ValidationResult]):
        """更新驗證統計"""
        self.metrics["total_validations"] += 1
        
        has_errors = any(not result.passed for result in validation_results)
        if has_errors:
            self.metrics["failed_validations"] += 1
        else:
            self.metrics["passed_validations"] += 1
        
        # 更新驗證類型統計
        for result in validation_results:
            validation_type = result.validation_type.value
            if validation_type not in self.metrics["validation_types"]:
                self.metrics["validation_types"][validation_type] = 0
            self.metrics["validation_types"][validation_type] += 1
    
    def _record_validation_history(
        self, 
        from_state: str, 
        to_state: str, 
        validation_results: List[ValidationResult]
    ):
        """記錄驗證歷史"""
        self.validation_history.append({
            "timestamp": datetime.now().isoformat(),
            "from_state": from_state,
            "to_state": to_state,
            "results_count": len(validation_results),
            "errors_count": sum(1 for r in validation_results if not r.passed),
            "severities": [r.severity.value for r in validation_results if not r.passed]
        })
        
        # 限制歷史長度
        if len(self.validation_history) > 1000:
            self.validation_history = self.validation_history[-1000:]
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """獲取驗證摘要"""
        return {
            "metrics": self.metrics,
            "success_rate": self.metrics["passed_validations"] / max(self.metrics["total_validations"], 1),
            "recent_errors": self.validation_history[-10:],
            "timestamp": datetime.now().isoformat()
        }
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """獲取當前驗證規則"""
        return self.validation_rules
    
    def update_validation_rules(self, new_rules: Dict[str, Any]):
        """更新驗證規則"""
        self.validation_rules.update(new_rules)
        logger.info("驗證規則已更新")