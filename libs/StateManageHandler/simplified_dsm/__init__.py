"""
DSM 簡化狀態機模組
保持原有的 8 個狀態，實現簡單的線性流程和清晰的職責分工
"""

from .dsm_state_enum import DSMState, DSMStateInfo
from .simplified_state_machine import SimplifiedStateMachine
from .state_flow_controller import StateFlowController
from .linear_flow_executor import LinearFlowExecutor

# 導出主要類別
__all__ = [
    'DSMState',
    'DSMStateInfo', 
    'SimplifiedStateMachine',
    'StateFlowController',
    'LinearFlowExecutor'
]

# 版本信息
__version__ = "1.0.0"
__author__ = "System Architect"
__description__ = "DSM 簡化狀態機實現"
