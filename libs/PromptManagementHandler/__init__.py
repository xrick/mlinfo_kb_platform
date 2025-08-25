"""
PromptManagementHandler 模組
全域 Prompt 管理系統
"""

from .prompt_manager import PromptManager, get_global_prompt_manager, set_global_prompt_manager
from .api import (
    get_prompt, get_multiple_prompts, reload_prompt, clear_cache,
    list_available_prompts, list_cached_prompts, get_cache_stats,
    get_prompt_info, add_prompt_path, remove_prompt_path,
    get_mgfd_principal_prompt, get_ai_coder_initialization_prompt,
    get_slot_collection_prompt, get_sales_rag_prompt,
    get_guest_reception_prompt, get_sales_keywords_config,
    get_combined_prompt, get_mgfd_with_ai_coder_prompt,
    get_sales_with_ai_coder_prompt
)

__all__ = [
    'PromptManager', 'get_global_prompt_manager', 'set_global_prompt_manager',
    'get_prompt', 'get_multiple_prompts', 'reload_prompt', 'clear_cache',
    'list_available_prompts', 'list_cached_prompts', 'get_cache_stats',
    'get_prompt_info', 'add_prompt_path', 'remove_prompt_path',
    'get_mgfd_principal_prompt', 'get_ai_coder_initialization_prompt',
    'get_slot_collection_prompt', 'get_sales_rag_prompt',
    'get_guest_reception_prompt', 'get_sales_keywords_config',
    'get_combined_prompt', 'get_mgfd_with_ai_coder_prompt',
    'get_sales_with_ai_coder_prompt'
]
