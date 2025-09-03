"""
流程驗證器
負責驗證流程定義的完整性和正確性
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


# 設置日誌
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """驗證結果數據類別"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class FlowValidator:
    """流程定義驗證器"""
    
    def __init__(self):
        """初始化流程驗證器"""
        logger.info("流程驗證器初始化完成")
    
    def validate(self, flow_definition: Dict[str, Any]) -> ValidationResult:
        """
        驗證流程定義的完整性和正確性
        
        Args:
            flow_definition: 流程定義字典
            
        Returns:
            驗證結果
        """
        errors = []
        warnings = []
        
        logger.info("開始驗證流程定義")
        
        # 驗證基本結構
        if not self._validate_basic_structure(flow_definition):
            errors.append("流程定義基本結構不完整")
        
        # 驗證狀態定義
        state_validation = self._validate_states(flow_definition.get("states", {}))
        errors.extend(state_validation.errors)
        warnings.extend(state_validation.warnings)
        
        # 驗證流程轉換
        transition_validation = self._validate_transitions(flow_definition.get("flow_transitions", {}))
        errors.extend(transition_validation.errors)
        warnings.extend(transition_validation.warnings)
        
        # 驗證配置一致性
        config_validation = self._validate_configuration_consistency(flow_definition)
        errors.extend(config_validation.errors)
        warnings.extend(config_validation.warnings)
        
        # 驗證 JSON Schema
        schema_validation = self._validate_json_schema(flow_definition)
        if not schema_validation.is_valid:
            errors.extend(schema_validation.errors)
        
        # 生成驗證結果
        validation_result = ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
        if validation_result.is_valid:
            logger.info("流程定義驗證通過")
        else:
            logger.warning(f"流程定義驗證失敗，發現 {len(errors)} 個錯誤")
        
        return validation_result
    
    def _validate_basic_structure(self, flow_definition: Dict[str, Any]) -> bool:
        """驗證基本結構"""
        required_sections = ["flow_metadata", "states", "flow_transitions"]
        
        for section in required_sections:
            if section not in flow_definition:
                logger.error(f"缺少必需章節: {section}")
                return False
        
        return True
    
    def _validate_states(self, states: Dict[str, Any]) -> ValidationResult:
        """驗證狀態定義"""
        errors = []
        warnings = []
        
        if not states:
            errors.append("狀態定義不能為空")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        # 檢查每個狀態的完整性
        for state_id, state_config in states.items():
            state_validation = self._validate_single_state(state_id, state_config)
            errors.extend(state_validation.errors)
            warnings.extend(state_validation.warnings)
        
        # 檢查執行順序的連續性
        execution_orders = []
        for state_config in states.values():
            if "execution_order" in state_config:
                execution_orders.append(state_config["execution_order"])
        
        if execution_orders:
            execution_orders.sort()
            expected_orders = list(range(1, len(execution_orders) + 1))
            if execution_orders != expected_orders:
                errors.append(f"執行順序不連續: 期望 {expected_orders}, 實際 {execution_orders}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_single_state(self, state_id: str, state_config: Dict[str, Any]) -> ValidationResult:
        """驗證單個狀態"""
        errors = []
        warnings = []
        
        # 檢查必需字段
        required_fields = ["state_id", "state_name", "action_function", "next_state"]
        for field in required_fields:
            if field not in state_config:
                errors.append(f"狀態 {state_id} 缺少必需字段: {field}")
        
        # 檢查字段類型
        if "execution_order" in state_config:
            if not isinstance(state_config["execution_order"], int):
                errors.append(f"狀態 {state_id} 的 execution_order 必須是整數")
        
        if "timeout_seconds" in state_config:
            if not isinstance(state_config["timeout_seconds"], (int, float)):
                errors.append(f"狀態 {state_id} 的 timeout_seconds 必須是數字")
        
        # 檢查重試策略
        if "retry_policy" in state_config:
            retry_validation = self._validate_retry_policy(state_id, state_config["retry_policy"])
            errors.extend(retry_validation.errors)
            warnings.extend(retry_validation.warnings)
        
        # 檢查錯誤處理
        if "error_handling" in state_config:
            error_handling_validation = self._validate_error_handling(state_id, state_config["error_handling"])
            errors.extend(error_handling_validation.errors)
            warnings.extend(error_handling_validation.warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_retry_policy(self, state_id: str, retry_policy: Dict[str, Any]) -> ValidationResult:
        """驗證重試策略"""
        errors = []
        warnings = []
        
        if "max_attempts" in retry_policy:
            if not isinstance(retry_policy["max_attempts"], int) or retry_policy["max_attempts"] < 0:
                errors.append(f"狀態 {state_id} 的 max_attempts 必須是非負整數")
        
        if "retry_delay_seconds" in retry_policy:
            if not isinstance(retry_policy["retry_delay_seconds"], (int, float)) or retry_policy["retry_delay_seconds"] < 0:
                errors.append(f"狀態 {state_id} 的 retry_delay_seconds 必須是非負數字")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_error_handling(self, state_id: str, error_handling: Dict[str, Any]) -> ValidationResult:
        """驗證錯誤處理配置"""
        errors = []
        warnings = []
        
        if "on_error" not in error_handling:
            warnings.append(f"狀態 {state_id} 的錯誤處理缺少 on_error 策略")
        
        if "fallback_values" in error_handling:
            if not isinstance(error_handling["fallback_values"], dict):
                errors.append(f"狀態 {state_id} 的 fallback_values 必須是字典")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_transitions(self, transitions: Dict[str, Any]) -> ValidationResult:
        """驗證流程轉換"""
        errors = []
        warnings = []
        
        if not transitions:
            errors.append("流程轉換定義不能為空")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        # 檢查線性序列
        if "linear_sequence" in transitions:
            linear_sequence = transitions["linear_sequence"]
            if not isinstance(linear_sequence, list):
                errors.append("linear_sequence 必須是列表")
            elif len(linear_sequence) == 0:
                errors.append("linear_sequence 不能為空")
        
        # 檢查轉換規則
        if "transition_rules" in transitions:
            transition_rules = transitions["transition_rules"]
            if not isinstance(transition_rules, dict):
                errors.append("transition_rules 必須是字典")
            else:
                for state_id, rule in transition_rules.items():
                    rule_validation = self._validate_transition_rule(state_id, rule)
                    errors.extend(rule_validation.errors)
                    warnings.extend(rule_validation.warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_transition_rule(self, state_id: str, rule: Dict[str, Any]) -> ValidationResult:
        """驗證轉換規則"""
        errors = []
        warnings = []
        
        if "next" not in rule:
            errors.append(f"轉換規則 {state_id} 缺少 next 字段")
        
        if "condition" not in rule:
            warnings.append(f"轉換規則 {state_id} 缺少 condition 字段")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_configuration_consistency(self, flow_definition: Dict[str, Any]) -> ValidationResult:
        """驗證配置一致性"""
        errors = []
        warnings = []
        
        # 檢查流程配置
        if "flow_configuration" in flow_definition:
            flow_config = flow_definition["flow_configuration"]
            
            if "execution_mode" in flow_config:
                valid_modes = ["linear", "parallel", "conditional"]
                if flow_config["execution_mode"] not in valid_modes:
                    errors.append(f"無效的執行模式: {flow_config['execution_mode']}")
            
            if "timeout_seconds" in flow_config:
                if not isinstance(flow_config["timeout_seconds"], (int, float)) or flow_config["timeout_seconds"] <= 0:
                    errors.append("timeout_seconds 必須是正數")
        
        # 檢查調試配置
        if "debug_configuration" in flow_definition:
            debug_config = flow_definition["debug_configuration"]
            
            if "debug_log_level" in debug_config:
                valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                if debug_config["debug_log_level"] not in valid_levels:
                    errors.append(f"無效的日誌級別: {debug_config['debug_log_level']}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_json_schema(self, flow_definition: Dict[str, Any]) -> ValidationResult:
        """驗證 JSON Schema（基本驗證）"""
        errors = []
        warnings = []
        
        try:
            # 嘗試序列化和反序列化，檢查 JSON 格式
            json_str = json.dumps(flow_definition)
            parsed = json.loads(json_str)
            
            if parsed != flow_definition:
                warnings.append("JSON 序列化/反序列化後數據不一致")
                
        except (TypeError, ValueError) as e:
            errors.append(f"JSON 格式錯誤: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_flow_file(self, file_path: str) -> ValidationResult:
        """
        驗證流程定義檔案
        
        Args:
            file_path: 流程定義檔案路徑
            
        Returns:
            驗證結果
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                flow_definition = json.load(f)
            
            return self.validate(flow_definition)
            
        except FileNotFoundError:
            return ValidationResult(
                is_valid=False,
                errors=[f"檔案不存在: {file_path}"],
                warnings=[]
            )
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"JSON 解析錯誤: {e}"],
                warnings=[]
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"檔案讀取錯誤: {e}"],
                warnings=[]
            )


# 導出主要類別
__all__ = ['FlowValidator', 'ValidationResult']
