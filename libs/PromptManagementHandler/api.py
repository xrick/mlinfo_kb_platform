#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt 管理器便捷 API
提供簡化的接口來使用 Prompt 管理器
"""

from typing import Optional, List, Dict, Any
from .prompt_manager import PromptManager, get_global_prompt_manager


def get_prompt(prompt_name: str, force_reload: bool = False) -> Optional[str]:
    """
    便捷函數：獲取指定的 Prompt
    
    Args:
        prompt_name: Prompt 名稱
        force_reload: 是否強制重新載入
        
    Returns:
        Prompt 內容，如果不存在則返回 None
    """
    manager = get_global_prompt_manager()
    return manager.get_prompt(prompt_name, force_reload)


def get_multiple_prompts(prompt_names: List[str], force_reload: bool = False) -> Dict[str, str]:
    """
    便捷函數：批量獲取多個 Prompt
    
    Args:
        prompt_names: Prompt 名稱列表
        force_reload: 是否強制重新載入
        
    Returns:
        包含 Prompt 內容的字典
    """
    manager = get_global_prompt_manager()
    return manager.get_multiple_prompts(prompt_names, force_reload)


def reload_prompt(prompt_name: str) -> bool:
    """
    便捷函數：重新載入指定的 Prompt
    
    Args:
        prompt_name: Prompt 名稱
        
    Returns:
        是否成功重新載入
    """
    manager = get_global_prompt_manager()
    return manager.reload_prompt(prompt_name)


def clear_cache(prompt_name: Optional[str] = None):
    """
    便捷函數：清理緩存
    
    Args:
        prompt_name: 指定的 Prompt 名稱，如果為 None 則清理所有緩存
    """
    manager = get_global_prompt_manager()
    manager.clear_cache(prompt_name)


def list_available_prompts() -> List[str]:
    """
    便捷函數：列出所有可用的 Prompt
    
    Returns:
        Prompt 名稱列表
    """
    manager = get_global_prompt_manager()
    return manager.list_available_prompts()


def list_cached_prompts() -> List[str]:
    """
    便捷函數：列出所有已緩存的 Prompt
    
    Returns:
        已緩存的 Prompt 名稱列表
    """
    manager = get_global_prompt_manager()
    return manager.list_cached_prompts()


def get_cache_stats() -> Dict[str, Any]:
    """
    便捷函數：獲取緩存統計信息
    
    Returns:
        緩存統計信息
    """
    manager = get_global_prompt_manager()
    return manager.get_cache_stats()


def get_prompt_info(prompt_name: str) -> Dict[str, Any]:
    """
    便捷函數：獲取 Prompt 的詳細信息
    
    Args:
        prompt_name: Prompt 名稱
        
    Returns:
        Prompt 信息字典
    """
    manager = get_global_prompt_manager()
    return manager.get_prompt_info(prompt_name)


def add_prompt_path(prompt_name: str, file_path: str):
    """
    便捷函數：添加 Prompt 路徑配置
    
    Args:
        prompt_name: Prompt 名稱
        file_path: 文件路徑（相對於專案根目錄）
    """
    manager = get_global_prompt_manager()
    manager.add_prompt_path(prompt_name, file_path)


def remove_prompt_path(prompt_name: str):
    """
    便捷函數：移除 Prompt 路徑配置
    
    Args:
        prompt_name: Prompt 名稱
    """
    manager = get_global_prompt_manager()
    manager.remove_prompt_path(prompt_name)


# 預定義的常用 Prompt 獲取函數
def get_mgfd_principal_prompt() -> Optional[str]:
    """獲取 MGFD 主提示"""
    return get_prompt("mgfd_principal")


def get_ai_coder_initialization_prompt() -> Optional[str]:
    """獲取 AI Coder 初始化提示"""
    return get_prompt("ai_coder_initialization")


def get_slot_collection_prompt() -> Optional[str]:
    """獲取槽位收集提示"""
    return get_prompt("slot_collection")


def get_sales_rag_prompt() -> Optional[str]:
    """獲取銷售 RAG 提示"""
    return get_prompt("sales_rag")


def get_guest_reception_prompt() -> Optional[str]:
    """獲取客戶接待提示"""
    return get_prompt("guest_reception")


def get_sales_keywords_config() -> Optional[str]:
    """獲取銷售關鍵字配置"""
    return get_prompt("sales_keywords")


# 組合提示函數
def get_combined_prompt(prompt_names: List[str], separator: str = "\n\n") -> Optional[str]:
    """
    組合多個 Prompt
    
    Args:
        prompt_names: Prompt 名稱列表
        separator: 分隔符
        
    Returns:
        組合後的 Prompt 內容
    """
    prompts = get_multiple_prompts(prompt_names)
    
    if not prompts:
        return None
    
    return separator.join(prompts.values())


def get_mgfd_with_ai_coder_prompt() -> Optional[str]:
    """獲取 MGFD 主提示與 AI Coder 提示的組合"""
    return get_combined_prompt(["mgfd_principal", "ai_coder_initialization"])


def get_sales_with_ai_coder_prompt() -> Optional[str]:
    """獲取銷售 RAG 提示與 AI Coder 提示的組合"""
    return get_combined_prompt(["sales_rag", "ai_coder_initialization"])
