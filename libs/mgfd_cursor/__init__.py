"""
Multi-Guided Funnel Dialogue (MGFD) Cursor Implementation
重構後的MGFD實現，基於原始設計文檔
"""

# 為避免在導入套件時就載入重型依賴（例如 redis、LLM 客戶端），改為惰性載入需要的物件。
# 這可防止像「僅導入 NotebookKnowledgeBase」的情境也被迫安裝/載入不必要相依。

# 設定可導出的名稱（不會在此時觸發實際匯入）
__all__ = [
    # 新的MGFD系統組件
    "MGFDSystem",
    "UserInputHandler",
    "DialogueManager",
    "ActionExecutor",
    "ResponseGenerator",
    "MGFDLLMManager",
    "ConfigLoader",
    "StateManager",
    "create_state_manager",
    "NotebookKnowledgeBase",
    "NotebookDialogueState",
]


def __getattr__(name):
    """PEP 562 惰性載入：在屬性被首次訪問時才進行實際匯入。

    這可避免套件初始化時就觸發對 heavy dependency 的匯入（例如 redis）。
    """
    if name == "MGFDSystem":
        from .mgfd_system import MGFDSystem as _MGFDSystem
        return _MGFDSystem
    if name == "UserInputHandler":
        from .user_input_handler import UserInputHandler as _UserInputHandler
        return _UserInputHandler
    if name == "DialogueManager":
        from .dialogue_manager import DialogueManager as _DialogueManager
        return _DialogueManager
    if name == "ActionExecutor":
        from .action_executor import ActionExecutor as _ActionExecutor
        return _ActionExecutor
    if name == "ResponseGenerator":
        from .response_generator import ResponseGenerator as _ResponseGenerator
        return _ResponseGenerator
    if name == "RedisStateManager":
        # This is now part of StateManager
        from .state_manager import StateManager as _RedisStateManager
        return _RedisStateManager
    if name == "MGFDLLMManager":
        from .llm_manager import MGFDLLMManager as _MGFDLLMManager
        return _MGFDLLMManager
    if name == "ConfigLoader":
        from .config_loader import ConfigLoader as _ConfigLoader
        return _ConfigLoader
    if name == "StateManager":
        from .state_manager import StateManager as _StateManager
        return _StateManager
    if name == "create_state_manager":
        from .state_manager import create_state_manager as _create
        return _create
    if name == "NotebookKnowledgeBase":
        from .knowledge_base import NotebookKnowledgeBase as _NotebookKnowledgeBase
        return _NotebookKnowledgeBase
    if name == "NotebookDialogueState":
        from .models import NotebookDialogueState as _NotebookDialogueState
        return _NotebookDialogueState
    raise AttributeError(f"module 'libs.mgfd_cursor' has no attribute {name!r}")
