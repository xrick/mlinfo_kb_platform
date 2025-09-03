"""
Action Hub 模組
提供 JSON 流程定義系統，支援開發者除錯和未來流程引擎執行
"""

from .flow_engine.flow_validator import FlowValidator, ValidationResult
from .flow_engine.flow_executor import FlowExecutor

# 導出主要類別
__all__ = [
    'FlowValidator',
    'ValidationResult',
    'FlowExecutor'
]

# 版本信息
__version__ = "1.0.0"
__author__ = "System Architect"
__description__ = "JSON 流程定義系統"
