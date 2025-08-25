#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全域 Prompt 管理器
提供動態載入和管理各種 Prompt 的功能
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import hashlib


class PromptManager:
    """
    全域 Prompt 管理器
    提供動態載入、緩存和管理各種 Prompt 的功能
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        初始化 Prompt 管理器
        
        Args:
            base_path: Prompt 文件的基礎路徑，默認為專案根目錄
        """
        self.logger = logging.getLogger(__name__)
        
        # 設定基礎路徑
        if base_path is None:
            # 專案根目錄 = libs/PromptManagementHandler/../../
            self.base_path = Path(__file__).resolve().parents[2]
        else:
            self.base_path = Path(base_path)
        
        # Prompt 緩存
        self._prompt_cache: Dict[str, Dict[str, Any]] = {}
        
        # 緩存配置
        self.cache_enabled = True
        self.cache_ttl = 3600  # 1小時
        
        # 預定義的 Prompt 路徑配置
        self._prompt_paths = {
            # MGFD 相關 Prompts
            "mgfd_principal": "HumanData/PromptsHub/MGFD_Principal_Prompts/MGFD_Principal_Prompt_20250821.txt",
            "ai_coder_initialization": "HumanData/PromptsHub/MGFD_Principal_Prompts/ai_coder_indepnedent_initialization_prompt.txt",
            "slot_collection": "HumanData/PromptsHub/prompts_for_collect_slot_values/MGFD_collect_slot_value_prompt_v1.txt",
            
            # 銷售相關 Prompts
            "sales_rag": "libs/services/sales_assistant/prompts/sales_prompt.txt",
            "sales_keywords": "libs/services/sales_assistant/prompts/query_keywords.json",
            
            # 其他 Prompts
            "guest_reception": "HumanData/PromptsHub/basic_prompts_for_users/recept_guest_prompt1.txt",
        }
        
        # 載入 Prompt 路徑配置
        self._load_prompt_paths_config()
        
        self.logger.info(f"Prompt 管理器初始化完成，基礎路徑: {self.base_path}")
    
    def _load_prompt_paths_config(self):
        """載入 Prompt 路徑配置文件"""
        config_path = self.base_path / "HumanData" / "PromptsHub" / "prompt_paths_config.json"
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    custom_paths = json.load(f)
                    self._prompt_paths.update(custom_paths)
                self.logger.info(f"載入自定義 Prompt 路徑配置: {len(custom_paths)} 個")
            except Exception as e:
                self.logger.warning(f"載入 Prompt 路徑配置失敗: {e}")
        else:
            self.logger.info("使用默認 Prompt 路徑配置")
    
    def get_prompt(self, prompt_name: str, force_reload: bool = False) -> Optional[str]:
        """
        獲取指定的 Prompt
        
        Args:
            prompt_name: Prompt 名稱
            force_reload: 是否強制重新載入
            
        Returns:
            Prompt 內容，如果不存在則返回 None
        """
        try:
            # 檢查緩存
            if not force_reload and self.cache_enabled:
                cached_prompt = self._get_from_cache(prompt_name)
                if cached_prompt:
                    self.logger.debug(f"從緩存獲取 Prompt: {prompt_name}")
                    return cached_prompt
            
            # 載入 Prompt
            prompt_content = self._load_prompt_file(prompt_name)
            
            if prompt_content:
                # 緩存 Prompt
                if self.cache_enabled:
                    self._save_to_cache(prompt_name, prompt_content)
                
                self.logger.info(f"成功載入 Prompt: {prompt_name}")
                return prompt_content
            else:
                self.logger.warning(f"Prompt 不存在或載入失敗: {prompt_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"獲取 Prompt 失敗 {prompt_name}: {e}")
            return None
    
    def get_multiple_prompts(self, prompt_names: List[str], force_reload: bool = False) -> Dict[str, str]:
        """
        批量獲取多個 Prompt
        
        Args:
            prompt_names: Prompt 名稱列表
            force_reload: 是否強制重新載入
            
        Returns:
            包含 Prompt 內容的字典
        """
        results = {}
        
        for prompt_name in prompt_names:
            prompt_content = self.get_prompt(prompt_name, force_reload)
            if prompt_content:
                results[prompt_name] = prompt_content
        
        return results
    
    def _load_prompt_file(self, prompt_name: str) -> Optional[str]:
        """
        載入 Prompt 文件
        
        Args:
            prompt_name: Prompt 名稱
            
        Returns:
            Prompt 內容
        """
        try:
            # 獲取文件路徑
            file_path = self._get_prompt_file_path(prompt_name)
            
            if not file_path or not file_path.exists():
                self.logger.warning(f"Prompt 文件不存在: {prompt_name} -> {file_path}")
                return None
            
            # 讀取文件內容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return content
            
        except Exception as e:
            self.logger.error(f"載入 Prompt 文件失敗 {prompt_name}: {e}")
            return None
    
    def _get_prompt_file_path(self, prompt_name: str) -> Optional[Path]:
        """
        獲取 Prompt 文件路徑
        
        Args:
            prompt_name: Prompt 名稱
            
        Returns:
            文件路徑
        """
        # 檢查預定義路徑
        if prompt_name in self._prompt_paths:
            relative_path = self._prompt_paths[prompt_name]
            return self.base_path / relative_path
        
        # 檢查是否為完整路徑
        if os.path.isabs(prompt_name):
            return Path(prompt_name)
        
        # 嘗試常見的 Prompt 目錄
        common_dirs = [
            "HumanData/PromptsHub",
            "HumanData/PromptsHub/MGFD_Principal_Prompts",
            "HumanData/PromptsHub/prompts_for_collect_slot_values",
            "HumanData/PromptsHub/basic_prompts_for_users",
            "libs/services/sales_assistant/prompts",
            "docs",
        ]
        
        for common_dir in common_dirs:
            potential_path = self.base_path / common_dir / f"{prompt_name}.txt"
            if potential_path.exists():
                return potential_path
            
            potential_path = self.base_path / common_dir / prompt_name
            if potential_path.exists():
                return potential_path
        
        return None
    
    def _get_from_cache(self, prompt_name: str) -> Optional[str]:
        """從緩存獲取 Prompt"""
        if prompt_name not in self._prompt_cache:
            return None
        
        cache_entry = self._prompt_cache[prompt_name]
        
        # 檢查是否過期
        if self._is_cache_expired(cache_entry):
            del self._prompt_cache[prompt_name]
            return None
        
        return cache_entry.get("content")
    
    def _save_to_cache(self, prompt_name: str, content: str):
        """保存 Prompt 到緩存"""
        cache_entry = {
            "content": content,
            "timestamp": datetime.now().timestamp(),
            "size": len(content)
        }
        self._prompt_cache[prompt_name] = cache_entry
    
    def _is_cache_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """檢查緩存是否過期"""
        timestamp = cache_entry.get("timestamp", 0)
        current_time = datetime.now().timestamp()
        return (current_time - timestamp) > self.cache_ttl
    
    def add_prompt_path(self, prompt_name: str, file_path: str):
        """
        添加 Prompt 路徑配置
        
        Args:
            prompt_name: Prompt 名稱
            file_path: 文件路徑（相對於專案根目錄）
        """
        self._prompt_paths[prompt_name] = file_path
        self.logger.info(f"添加 Prompt 路徑配置: {prompt_name} -> {file_path}")
    
    def remove_prompt_path(self, prompt_name: str):
        """
        移除 Prompt 路徑配置
        
        Args:
            prompt_name: Prompt 名稱
        """
        if prompt_name in self._prompt_paths:
            del self._prompt_paths[prompt_name]
            self.logger.info(f"移除 Prompt 路徑配置: {prompt_name}")
    
    def list_available_prompts(self) -> List[str]:
        """
        列出所有可用的 Prompt
        
        Returns:
            Prompt 名稱列表
        """
        return list(self._prompt_paths.keys())
    
    def list_cached_prompts(self) -> List[str]:
        """
        列出所有已緩存的 Prompt
        
        Returns:
            已緩存的 Prompt 名稱列表
        """
        return list(self._prompt_cache.keys())
    
    def clear_cache(self, prompt_name: Optional[str] = None):
        """
        清理緩存
        
        Args:
            prompt_name: 指定的 Prompt 名稱，如果為 None 則清理所有緩存
        """
        if prompt_name:
            if prompt_name in self._prompt_cache:
                del self._prompt_cache[prompt_name]
                self.logger.info(f"清理 Prompt 緩存: {prompt_name}")
        else:
            self._prompt_cache.clear()
            self.logger.info("清理所有 Prompt 緩存")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        獲取緩存統計信息
        
        Returns:
            緩存統計信息
        """
        current_time = datetime.now().timestamp()
        valid_cache_count = 0
        expired_cache_count = 0
        total_size = 0
        
        for cache_entry in self._prompt_cache.values():
            if self._is_cache_expired(cache_entry):
                expired_cache_count += 1
            else:
                valid_cache_count += 1
                total_size += cache_entry.get("size", 0)
        
        return {
            "total_cached": len(self._prompt_cache),
            "valid_cached": valid_cache_count,
            "expired_cached": expired_cache_count,
            "total_size_bytes": total_size,
            "cache_enabled": self.cache_enabled,
            "cache_ttl_seconds": self.cache_ttl
        }
    
    def reload_prompt(self, prompt_name: str) -> bool:
        """
        重新載入指定的 Prompt
        
        Args:
            prompt_name: Prompt 名稱
            
        Returns:
            是否成功重新載入
        """
        try:
            # 清理緩存
            self.clear_cache(prompt_name)
            
            # 重新載入
            content = self.get_prompt(prompt_name, force_reload=True)
            
            if content:
                self.logger.info(f"成功重新載入 Prompt: {prompt_name}")
                return True
            else:
                self.logger.warning(f"重新載入 Prompt 失敗: {prompt_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"重新載入 Prompt 時發生錯誤 {prompt_name}: {e}")
            return False
    
    def get_prompt_info(self, prompt_name: str) -> Dict[str, Any]:
        """
        獲取 Prompt 的詳細信息
        
        Args:
            prompt_name: Prompt 名稱
            
        Returns:
            Prompt 信息字典
        """
        info = {
            "name": prompt_name,
            "configured_path": self._prompt_paths.get(prompt_name),
            "actual_path": None,
            "exists": False,
            "cached": False,
            "cache_info": None,
            "size": 0
        }
        
        # 檢查實際文件路徑
        file_path = self._get_prompt_file_path(prompt_name)
        if file_path:
            info["actual_path"] = str(file_path)
            info["exists"] = file_path.exists()
            if file_path.exists():
                info["size"] = file_path.stat().st_size
        
        # 檢查緩存信息
        if prompt_name in self._prompt_cache:
            info["cached"] = True
            cache_entry = self._prompt_cache[prompt_name]
            info["cache_info"] = {
                "timestamp": cache_entry.get("timestamp"),
                "size": cache_entry.get("size"),
                "expired": self._is_cache_expired(cache_entry)
            }
        
        return info


# 全域實例
_global_prompt_manager: Optional[PromptManager] = None


def get_global_prompt_manager() -> PromptManager:
    """
    獲取全域 Prompt 管理器實例
    
    Returns:
        全域 Prompt 管理器實例
    """
    global _global_prompt_manager
    
    if _global_prompt_manager is None:
        _global_prompt_manager = PromptManager()
    
    return _global_prompt_manager


def set_global_prompt_manager(prompt_manager: PromptManager):
    """
    設定全域 Prompt 管理器實例
    
    Args:
        prompt_manager: Prompt 管理器實例
    """
    global _global_prompt_manager
    _global_prompt_manager = prompt_manager
