#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心狀態管理器
負責管理系統核心狀態
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime, timedelta
from ..state_manager import StateManager


class KernelStateManager:
    """
    核心狀態管理器
    負責管理系統核心狀態，包括 MGFD 系統狀態、LLM 狀態等
    """
    
    def __init__(self, state_manager: Optional[StateManager] = None):
        """
        初始化核心狀態管理器
        
        Args:
            state_manager: 狀態管理器實例
        """
        self.logger = logging.getLogger(__name__)
        
        # 使用傳入的狀態管理器或創建新的
        self.state_manager = state_manager or StateManager()
        
        # 核心狀態配置
        self.kernel_states = {
            "mgfd_system": {
                "description": "MGFD 系統狀態",
                "ttl": 3600,  # 1小時
                "auto_save": True
            },
            "llm_status": {
                "description": "LLM 狀態",
                "ttl": 1800,  # 30分鐘
                "auto_save": True
            },
            "prompt_cache": {
                "description": "Prompt 緩存狀態",
                "ttl": 7200,  # 2小時
                "auto_save": True
            },
            "knowledge_base": {
                "description": "知識庫狀態",
                "ttl": 86400,  # 24小時
                "auto_save": True
            },
            "user_sessions": {
                "description": "用戶會話狀態",
                "ttl": 1800,  # 30分鐘
                "auto_save": True
            }
        }
        
        self.logger.info("核心狀態管理器初始化完成")
    
    def save_mgfd_system_state(self, state_data: Dict[str, Any]) -> bool:
        """
        保存 MGFD 系統狀態
        
        Args:
            state_data: 系統狀態數據
            
        Returns:
            是否成功
        """
        try:
            # 添加核心狀態信息
            enhanced_state = {
                **state_data,
                "kernel_state_type": "mgfd_system",
                "kernel_version": "1.0.0",
                "last_updated": datetime.now().isoformat()
            }
            
            success = self.state_manager.save_system_state("mgfd_system", enhanced_state)
            
            if success:
                self.logger.info("保存 MGFD 系統狀態成功")
            else:
                self.logger.error("保存 MGFD 系統狀態失敗")
            
            return success
            
        except Exception as e:
            self.logger.error(f"保存 MGFD 系統狀態時發生錯誤: {e}")
            return False
    
    def load_mgfd_system_state(self) -> Optional[Dict[str, Any]]:
        """
        載入 MGFD 系統狀態
        
        Returns:
            系統狀態數據
        """
        try:
            state_data = self.state_manager.load_system_state("mgfd_system")
            
            if state_data:
                self.logger.info("載入 MGFD 系統狀態成功")
            else:
                self.logger.info("MGFD 系統狀態不存在")
            
            return state_data
            
        except Exception as e:
            self.logger.error(f"載入 MGFD 系統狀態時發生錯誤: {e}")
            return None
    
    def save_llm_status(self, llm_info: Dict[str, Any]) -> bool:
        """
        保存 LLM 狀態
        
        Args:
            llm_info: LLM 信息
            
        Returns:
            是否成功
        """
        try:
            # 添加 LLM 狀態信息
            enhanced_info = {
                **llm_info,
                "kernel_state_type": "llm_status",
                "status_check_time": datetime.now().isoformat(),
                "is_available": llm_info.get("is_available", False)
            }
            
            success = self.state_manager.save_system_state("llm_status", enhanced_info)
            
            if success:
                self.logger.info("保存 LLM 狀態成功")
            else:
                self.logger.error("保存 LLM 狀態失敗")
            
            return success
            
        except Exception as e:
            self.logger.error(f"保存 LLM 狀態時發生錯誤: {e}")
            return False
    
    def load_llm_status(self) -> Optional[Dict[str, Any]]:
        """
        載入 LLM 狀態
        
        Returns:
            LLM 狀態數據
        """
        try:
            status_data = self.state_manager.load_system_state("llm_status")
            
            if status_data:
                self.logger.info("載入 LLM 狀態成功")
            else:
                self.logger.info("LLM 狀態不存在")
            
            return status_data
            
        except Exception as e:
            self.logger.error(f"載入 LLM 狀態時發生錯誤: {e}")
            return None
    
    def save_prompt_cache_state(self, cache_info: Dict[str, Any]) -> bool:
        """
        保存 Prompt 緩存狀態
        
        Args:
            cache_info: 緩存信息
            
        Returns:
            是否成功
        """
        try:
            # 添加緩存狀態信息
            enhanced_info = {
                **cache_info,
                "kernel_state_type": "prompt_cache",
                "cache_update_time": datetime.now().isoformat(),
                "cache_size": cache_info.get("cache_size", 0)
            }
            
            success = self.state_manager.save_system_state("prompt_cache", enhanced_info)
            
            if success:
                self.logger.info("保存 Prompt 緩存狀態成功")
            else:
                self.logger.error("保存 Prompt 緩存狀態失敗")
            
            return success
            
        except Exception as e:
            self.logger.error(f"保存 Prompt 緩存狀態時發生錯誤: {e}")
            return False
    
    def load_prompt_cache_state(self) -> Optional[Dict[str, Any]]:
        """
        載入 Prompt 緩存狀態
        
        Returns:
            緩存狀態數據
        """
        try:
            cache_data = self.state_manager.load_system_state("prompt_cache")
            
            if cache_data:
                self.logger.info("載入 Prompt 緩存狀態成功")
            else:
                self.logger.info("Prompt 緩存狀態不存在")
            
            return cache_data
            
        except Exception as e:
            self.logger.error(f"載入 Prompt 緩存狀態時發生錯誤: {e}")
            return None
    
    def save_knowledge_base_state(self, kb_info: Dict[str, Any]) -> bool:
        """
        保存知識庫狀態
        
        Args:
            kb_info: 知識庫信息
            
        Returns:
            是否成功
        """
        try:
            # 添加知識庫狀態信息
            enhanced_info = {
                **kb_info,
                "kernel_state_type": "knowledge_base",
                "kb_update_time": datetime.now().isoformat(),
                "kb_version": kb_info.get("version", "1.0.0")
            }
            
            success = self.state_manager.save_system_state("knowledge_base", enhanced_info)
            
            if success:
                self.logger.info("保存知識庫狀態成功")
            else:
                self.logger.error("保存知識庫狀態失敗")
            
            return success
            
        except Exception as e:
            self.logger.error(f"保存知識庫狀態時發生錯誤: {e}")
            return False
    
    def load_knowledge_base_state(self) -> Optional[Dict[str, Any]]:
        """
        載入知識庫狀態
        
        Returns:
            知識庫狀態數據
        """
        try:
            kb_data = self.state_manager.load_system_state("knowledge_base")
            
            if kb_data:
                self.logger.info("載入知識庫狀態成功")
            else:
                self.logger.info("知識庫狀態不存在")
            
            return kb_data
            
        except Exception as e:
            self.logger.error(f"載入知識庫狀態時發生錯誤: {e}")
            return None
    
    def save_user_session_state(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        保存用戶會話狀態
        
        Args:
            session_id: 會話 ID
            session_data: 會話數據
            
        Returns:
            是否成功
        """
        try:
            # 添加會話狀態信息
            enhanced_data = {
                **session_data,
                "kernel_state_type": "user_session",
                "session_start_time": session_data.get("start_time", datetime.now().isoformat()),
                "last_activity": datetime.now().isoformat()
            }
            
            success = self.state_manager.save_session_state(session_id, enhanced_data)
            
            if success:
                self.logger.info(f"保存用戶會話狀態成功: {session_id}")
            else:
                self.logger.error(f"保存用戶會話狀態失敗: {session_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"保存用戶會話狀態時發生錯誤 {session_id}: {e}")
            return False
    
    def load_user_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        載入用戶會話狀態
        
        Args:
            session_id: 會話 ID
            
        Returns:
            會話狀態數據
        """
        try:
            session_data = self.state_manager.load_session_state(session_id)
            
            if session_data:
                self.logger.info(f"載入用戶會話狀態成功: {session_id}")
            else:
                self.logger.info(f"用戶會話狀態不存在: {session_id}")
            
            return session_data
            
        except Exception as e:
            self.logger.error(f"載入用戶會話狀態時發生錯誤 {session_id}: {e}")
            return None
    
    def get_kernel_state_summary(self) -> Dict[str, Any]:
        """
        獲取核心狀態摘要
        
        Returns:
            狀態摘要字典
        """
        try:
            summary = {
                "timestamp": datetime.now().isoformat(),
                "kernel_states": {},
                "active_sessions": [],
                "system_health": "unknown"
            }
            
            # 檢查各個核心狀態
            for state_name, config in self.kernel_states.items():
                state_data = self.state_manager.load_system_state(state_name)
                
                summary["kernel_states"][state_name] = {
                    "exists": state_data is not None,
                    "description": config["description"],
                    "last_updated": state_data.get("last_updated") if state_data else None,
                    "auto_save": config["auto_save"]
                }
            
            # 獲取活躍會話
            active_sessions = self.state_manager.list_active_sessions()
            summary["active_sessions"] = active_sessions
            
            # 評估系統健康狀態
            health_score = 0
            total_states = len(self.kernel_states)
            
            for state_name in self.kernel_states:
                if summary["kernel_states"][state_name]["exists"]:
                    health_score += 1
            
            if health_score == total_states:
                summary["system_health"] = "healthy"
            elif health_score >= total_states * 0.7:
                summary["system_health"] = "warning"
            else:
                summary["system_health"] = "critical"
            
            self.logger.info(f"核心狀態摘要生成成功，健康狀態: {summary['system_health']}")
            return summary
            
        except Exception as e:
            self.logger.error(f"獲取核心狀態摘要時發生錯誤: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "system_health": "error"
            }
    
    def cleanup_expired_kernel_states(self) -> int:
        """
        清理過期的核心狀態
        
        Returns:
            清理的狀態數量
        """
        try:
            cleaned_count = 0
            
            # 清理過期的系統狀態
            for state_name in self.kernel_states:
                state_info = self.state_manager.get_state_info("system", state_name)
                
                if state_info and not state_info["exists"]:
                    # 狀態已過期，記錄清理
                    cleaned_count += 1
                    self.logger.info(f"核心狀態已過期: {state_name}")
            
            # 清理過期的會話狀態
            active_sessions = self.state_manager.list_active_sessions()
            for session_id in active_sessions:
                session_info = self.state_manager.get_state_info("session", session_id)
                
                if session_info and not session_info["exists"]:
                    # 會話已過期，記錄清理
                    cleaned_count += 1
                    self.logger.info(f"用戶會話已過期: {session_id}")
            
            self.logger.info(f"清理了 {cleaned_count} 個過期的核心狀態")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"清理過期核心狀態時發生錯誤: {e}")
            return 0
    
    def backup_kernel_states(self, backup_dir: Optional[str] = None) -> bool:
        """
        備份所有核心狀態
        
        Args:
            backup_dir: 備份目錄
            
        Returns:
            是否成功
        """
        try:
            if backup_dir is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = Path(__file__).resolve().parents[3] / "backups" / "kernel_states" / timestamp
                backup_dir.mkdir(parents=True, exist_ok=True)
            else:
                backup_dir = Path(backup_dir)
                backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_success = True
            
            # 備份系統狀態
            for state_name in self.kernel_states:
                success = self.state_manager.backup_state("system", state_name, 
                                                         str(backup_dir / f"{state_name}.json"))
                if not success:
                    backup_success = False
                    self.logger.error(f"備份系統狀態失敗: {state_name}")
            
            # 備份活躍會話
            active_sessions = self.state_manager.list_active_sessions()
            for session_id in active_sessions:
                success = self.state_manager.backup_state("session", session_id,
                                                         str(backup_dir / f"session_{session_id}.json"))
                if not success:
                    backup_success = False
                    self.logger.error(f"備份會話狀態失敗: {session_id}")
            
            if backup_success:
                self.logger.info(f"核心狀態備份成功: {backup_dir}")
            else:
                self.logger.warning("部分核心狀態備份失敗")
            
            return backup_success
            
        except Exception as e:
            self.logger.error(f"備份核心狀態時發生錯誤: {e}")
            return False
