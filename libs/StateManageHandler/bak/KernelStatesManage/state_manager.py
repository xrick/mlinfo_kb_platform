#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
狀態管理器
負責管理和處理各種系統狀態
"""

import json
import logging
import redis
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime, timedelta


class StateManager:
    """
    狀態管理器
    負責管理和處理各種系統狀態，包括會話狀態、系統狀態等
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        初始化狀態管理器
        
        Args:
            redis_client: Redis 客戶端，如果為 None 則嘗試連接本地 Redis
        """
        self.logger = logging.getLogger(__name__)
        
        # 初始化 Redis 連接
        self.redis_client = redis_client
        if self.redis_client is None:
            try:
                self.redis_client = redis.Redis(
                    host='localhost', 
                    port=6379, 
                    db=0, 
                    decode_responses=True
                )
                # 測試連接
                self.redis_client.ping()
                self.logger.info("Redis 連接成功")
            except Exception as e:
                self.logger.warning(f"Redis 連接失敗: {e}")
                self.redis_client = None
        
        # 狀態配置
        self.state_config = {
            "session_ttl": 3600,  # 會話狀態 TTL (秒)
            "system_state_ttl": 86400,  # 系統狀態 TTL (秒)
            "cache_ttl": 1800,  # 緩存 TTL (秒)
        }
        
        self.logger.info("狀態管理器初始化完成")
    
    def save_session_state(self, session_id: str, state_data: Dict[str, Any]) -> bool:
        """
        保存會話狀態
        
        Args:
            session_id: 會話 ID
            state_data: 狀態數據
            
        Returns:
            是否成功
        """
        try:
            if not self.redis_client:
                self.logger.error("Redis 客戶端不可用")
                return False
            
            # 添加時間戳
            state_data["timestamp"] = datetime.now().isoformat()
            state_data["session_id"] = session_id
            
            # 保存到 Redis
            key = f"session:{session_id}"
            self.redis_client.setex(
                key,
                self.state_config["session_ttl"],
                json.dumps(state_data, ensure_ascii=False)
            )
            
            self.logger.info(f"保存會話狀態成功: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存會話狀態失敗 {session_id}: {e}")
            return False
    
    def load_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        載入會話狀態
        
        Args:
            session_id: 會話 ID
            
        Returns:
            狀態數據，如果不存在則返回 None
        """
        try:
            if not self.redis_client:
                self.logger.error("Redis 客戶端不可用")
                return None
            
            key = f"session:{session_id}"
            state_json = self.redis_client.get(key)
            
            if state_json:
                state_data = json.loads(state_json)
                self.logger.info(f"載入會話狀態成功: {session_id}")
                return state_data
            else:
                self.logger.info(f"會話狀態不存在: {session_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"載入會話狀態失敗 {session_id}: {e}")
            return None
    
    def delete_session_state(self, session_id: str) -> bool:
        """
        刪除會話狀態
        
        Args:
            session_id: 會話 ID
            
        Returns:
            是否成功
        """
        try:
            if not self.redis_client:
                self.logger.error("Redis 客戶端不可用")
                return False
            
            key = f"session:{session_id}"
            result = self.redis_client.delete(key)
            
            if result > 0:
                self.logger.info(f"刪除會話狀態成功: {session_id}")
                return True
            else:
                self.logger.info(f"會話狀態不存在: {session_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"刪除會話狀態失敗 {session_id}: {e}")
            return False
    
    def update_session_state(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新會話狀態
        
        Args:
            session_id: 會話 ID
            updates: 要更新的數據
            
        Returns:
            是否成功
        """
        try:
            # 載入現有狀態
            current_state = self.load_session_state(session_id)
            if current_state is None:
                # 如果狀態不存在，創建新狀態
                current_state = {
                    "session_id": session_id,
                    "created_at": datetime.now().isoformat()
                }
            
            # 更新狀態
            current_state.update(updates)
            current_state["updated_at"] = datetime.now().isoformat()
            
            # 保存更新後的狀態
            return self.save_session_state(session_id, current_state)
            
        except Exception as e:
            self.logger.error(f"更新會話狀態失敗 {session_id}: {e}")
            return False
    
    def save_system_state(self, state_name: str, state_data: Dict[str, Any]) -> bool:
        """
        保存系統狀態
        
        Args:
            state_name: 狀態名稱
            state_data: 狀態數據
            
        Returns:
            是否成功
        """
        try:
            if not self.redis_client:
                self.logger.error("Redis 客戶端不可用")
                return False
            
            # 添加時間戳
            state_data["timestamp"] = datetime.now().isoformat()
            state_data["state_name"] = state_name
            
            # 保存到 Redis
            key = f"system:{state_name}"
            self.redis_client.setex(
                key,
                self.state_config["system_state_ttl"],
                json.dumps(state_data, ensure_ascii=False)
            )
            
            self.logger.info(f"保存系統狀態成功: {state_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存系統狀態失敗 {state_name}: {e}")
            return False
    
    def load_system_state(self, state_name: str) -> Optional[Dict[str, Any]]:
        """
        載入系統狀態
        
        Args:
            state_name: 狀態名稱
            
        Returns:
            狀態數據，如果不存在則返回 None
        """
        try:
            if not self.redis_client:
                self.logger.error("Redis 客戶端不可用")
                return None
            
            key = f"system:{state_name}"
            state_json = self.redis_client.get(key)
            
            if state_json:
                state_data = json.loads(state_json)
                self.logger.info(f"載入系統狀態成功: {state_name}")
                return state_data
            else:
                self.logger.info(f"系統狀態不存在: {state_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"載入系統狀態失敗 {state_name}: {e}")
            return None
    
    def list_active_sessions(self) -> List[str]:
        """
        列出所有活躍會話
        
        Returns:
            會話 ID 列表
        """
        try:
            if not self.redis_client:
                self.logger.error("Redis 客戶端不可用")
                return []
            
            # 獲取所有會話鍵
            session_keys = self.redis_client.keys("session:*")
            session_ids = [key.split(":", 1)[1] for key in session_keys]
            
            self.logger.info(f"找到 {len(session_ids)} 個活躍會話")
            return session_ids
            
        except Exception as e:
            self.logger.error(f"列出活躍會話失敗: {e}")
            return []
    
    def list_system_states(self) -> List[str]:
        """
        列出所有系統狀態
        
        Returns:
            系統狀態名稱列表
        """
        try:
            if not self.redis_client:
                self.logger.error("Redis 客戶端不可用")
                return []
            
            # 獲取所有系統狀態鍵
            state_keys = self.redis_client.keys("system:*")
            state_names = [key.split(":", 1)[1] for key in state_keys]
            
            self.logger.info(f"找到 {len(state_names)} 個系統狀態")
            return state_names
            
        except Exception as e:
            self.logger.error(f"列出系統狀態失敗: {e}")
            return []
    
    def get_state_info(self, state_type: str, state_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取狀態信息
        
        Args:
            state_type: 狀態類型 (session/system)
            state_id: 狀態 ID
            
        Returns:
            狀態信息字典
        """
        try:
            if not self.redis_client:
                self.logger.error("Redis 客戶端不可用")
                return None
            
            key = f"{state_type}:{state_id}"
            
            # 獲取 TTL
            ttl = self.redis_client.ttl(key)
            
            # 獲取狀態數據
            state_json = self.redis_client.get(key)
            
            info = {
                "state_type": state_type,
                "state_id": state_id,
                "exists": state_json is not None,
                "ttl_seconds": ttl if ttl > 0 else None,
                "expires_at": None
            }
            
            if state_json:
                state_data = json.loads(state_json)
                info["data_size"] = len(state_json)
                info["last_updated"] = state_data.get("timestamp")
                
                if ttl > 0:
                    info["expires_at"] = (datetime.now() + timedelta(seconds=ttl)).isoformat()
            
            return info
            
        except Exception as e:
            self.logger.error(f"獲取狀態信息失敗 {state_type}:{state_id}: {e}")
            return None
    
    def clear_expired_states(self) -> int:
        """
        清理過期的狀態
        
        Returns:
            清理的狀態數量
        """
        try:
            if not self.redis_client:
                self.logger.error("Redis 客戶端不可用")
                return 0
            
            # Redis 會自動清理過期的鍵，這裡只是記錄
            session_count = len(self.list_active_sessions())
            system_count = len(self.list_system_states())
            
            self.logger.info(f"當前活躍會話: {session_count}, 系統狀態: {system_count}")
            return session_count + system_count
            
        except Exception as e:
            self.logger.error(f"清理過期狀態失敗: {e}")
            return 0
    
    def backup_state(self, state_type: str, state_id: str, backup_path: Optional[str] = None) -> bool:
        """
        備份狀態
        
        Args:
            state_type: 狀態類型
            state_id: 狀態 ID
            backup_path: 備份路徑
            
        Returns:
            是否成功
        """
        try:
            # 載入狀態
            if state_type == "session":
                state_data = self.load_session_state(state_id)
            elif state_type == "system":
                state_data = self.load_system_state(state_id)
            else:
                self.logger.error(f"不支援的狀態類型: {state_type}")
                return False
            
            if state_data is None:
                self.logger.error(f"狀態不存在: {state_type}:{state_id}")
                return False
            
            # 設定備份路徑
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = Path(__file__).resolve().parents[2] / "backups" / "states"
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_path = backup_dir / f"{state_type}_{state_id}_{timestamp}.json"
            
            # 保存備份
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"備份狀態成功: {state_type}:{state_id} -> {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"備份狀態失敗 {state_type}:{state_id}: {e}")
            return False
    
    def restore_state(self, state_type: str, state_id: str, backup_path: str) -> bool:
        """
        恢復狀態
        
        Args:
            state_type: 狀態類型
            state_id: 狀態 ID
            backup_path: 備份文件路徑
            
        Returns:
            是否成功
        """
        try:
            # 讀取備份文件
            with open(backup_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            # 恢復狀態
            if state_type == "session":
                return self.save_session_state(state_id, state_data)
            elif state_type == "system":
                return self.save_system_state(state_id, state_data)
            else:
                self.logger.error(f"不支援的狀態類型: {state_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"恢復狀態失敗 {state_type}:{state_id}: {e}")
            return False
