"""
Multi-Guided Funnel Dialogue (MGFD) Cursor Implementation
第一版MGFD實現，獨立於現有系統
"""

from .dialogue_manager import MGFDDialogueManager
from .state_machine import create_notebook_sales_graph
from .knowledge_base import NotebookKnowledgeBase
from .models import NotebookDialogueState

__all__ = [
    "MGFDDialogueManager",
    "create_notebook_sales_graph", 
    "NotebookKnowledgeBase",
    "NotebookDialogueState"
]
