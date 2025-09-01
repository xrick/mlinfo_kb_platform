"""
Multi-Guided Funnel Dialogue (MGFD) Cursor Implementation
重構後的MGFD實現，基於原始設計文檔
"""

# 新的MGFD系統組件
from .mgfd_system import MGFDSystem
from ....libs.mgfd_modules.user_input_handler import UserInputHandler
from .dialogue_manager import DialogueManager
from .action_executor import ActionExecutor
from .response_generator import ResponseGenerator
from .redis_state_manager import RedisStateManager
from .llm_manager import MGFDLLMManager
from .config_loader import ConfigLoader

# 保留舊的組件以向後兼容
from .state_machine import create_notebook_sales_graph
from .knowledge_base import NotebookKnowledgeBase
from .models import NotebookDialogueState

__all__ = [
    # 新的MGFD系統組件
    "MGFDSystem",
    "UserInputHandler", 
    "DialogueManager",
    "ActionExecutor",
    "ResponseGenerator",
    "RedisStateManager",
    "MGFDLLMManager",
    "ConfigLoader",
    
    # 舊的組件（向後兼容）
    "create_notebook_sales_graph",
    "NotebookKnowledgeBase", 
    "NotebookDialogueState"
]



