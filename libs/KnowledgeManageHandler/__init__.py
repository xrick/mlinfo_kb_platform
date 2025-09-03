"""
KnowledgeManageHandler 模組
知識管理處理器
負責管理和處理各種知識庫
支援 SQLite 和 Polars 數據源
"""

from .knowledge_manager import KnowledgeManager

# Polars 相關導入
try:
    from .polars_helper import PolarsHelper, PolarsConnectionError, PolarsQueryError, PolarsMemoryError
    __all__ = ['KnowledgeManager', 'PolarsHelper', 'PolarsConnectionError', 'PolarsQueryError', 'PolarsMemoryError']
except ImportError:
    __all__ = ['KnowledgeManager']
