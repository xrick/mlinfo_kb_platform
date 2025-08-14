#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD Redis狀態管理器
實現會話狀態持久化和對話歷史管理
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import redis
import numpy as np

class RedisStateManager:
    """Redis狀態管理器"""
    
    def __init__(self, redis_client: redis.Redis, session_timeout: int = 3600):
        """
        初始化Redis狀態管理器
        
        Args:
            redis_client: Redis客戶端
            session_timeout: 會話超時時間（秒）
        """
        self.redis_client = redis_client
        self.session_timeout = session_timeout
        self.logger = logging.getLogger(__name__)
        
        # Redis鍵前綴
        self.SESSION_PREFIX = "mgfd:session:"
        self.SLOTS_PREFIX = "mgfd:slots:"
        self.HISTORY_PREFIX = "mgfd:history:"
        self.RECOMMENDATIONS_PREFIX = "mgfd:recommendations:"
    
    def _convert_numpy_types(self, obj: Any) -> Any:
        """
        遞歸轉換 numpy 類型為 Python 原生類型以支持 JSON 序列化
        
        Args:
            obj: 可能包含 numpy 類型的對象
            
        Returns:
            轉換後的對象
        """
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._convert_numpy_types(item) for item in obj]
        else:
            return obj
    
    def load_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        從Redis載入會話狀態
        
        Args:
            session_id: 會話ID
            
        Returns:
            會話狀態字典，如果不存在則返回None
        """
        try:
            session_key = f"{self.SESSION_PREFIX}{session_id}"
            session_data = self.redis_client.get(session_key)
            
            if not session_data:
                return None
            
            # 解析會話數據 - 智能處理bytes和string類型
            if isinstance(session_data, bytes):
                session_state = json.loads(session_data.decode('utf-8'))
            else:
                session_state = json.loads(session_data)
            
            # 載入槽位信息
            slots_key = f"{self.SLOTS_PREFIX}{session_id}"
            slots_data = self.redis_client.get(slots_key)
            if slots_data:
                if isinstance(slots_data, bytes):
                    session_state["filled_slots"] = json.loads(slots_data.decode('utf-8'))
                else:
                    session_state["filled_slots"] = json.loads(slots_data)
            else:
                session_state["filled_slots"] = {}
            
            # 載入對話歷史
            history_key = f"{self.HISTORY_PREFIX}{session_id}"
            history_data = self.redis_client.lrange(history_key, 0, -1)
            if history_data:
                session_state["chat_history"] = []
                for msg in history_data:
                    if isinstance(msg, bytes):
                        session_state["chat_history"].append(json.loads(msg.decode('utf-8')))
                    else:
                        session_state["chat_history"].append(json.loads(msg))
            else:
                session_state["chat_history"] = []
            
            # 載入推薦記錄
            recommendations_key = f"{self.RECOMMENDATIONS_PREFIX}{session_id}"
            recommendations_data = self.redis_client.get(recommendations_key)
            if recommendations_data:
                if isinstance(recommendations_data, bytes):
                    session_state["recommendations"] = json.loads(recommendations_data.decode('utf-8'))
                else:
                    session_state["recommendations"] = json.loads(recommendations_data)
            else:
                session_state["recommendations"] = []
            
            self.logger.info(f"載入會話狀態: {session_id}")
            return session_state
            
        except Exception as e:
            self.logger.error(f"載入會話狀態失敗: {e}")
            return None
    
    def save_session_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        """
        保存會話狀態到Redis
        
        Args:
            session_id: 會話ID
            state: 會話狀態
            
        Returns:
            是否保存成功
        """
        try:
            # 轉換 numpy 類型
            state = self._convert_numpy_types(state)
            
            # 更新時間戳
            state["last_updated"] = datetime.now().isoformat()
            
            # 保存基本會話信息
            session_key = f"{self.SESSION_PREFIX}{session_id}"
            session_data = {
                "session_id": state.get("session_id"),
                "current_stage": state.get("current_stage", "awareness"),
                "created_at": state.get("created_at"),
                "last_updated": state["last_updated"],
                "user_preferences": state.get("user_preferences", {})
            }
            
            self.redis_client.setex(
                session_key,
                self.session_timeout,
                json.dumps(session_data, ensure_ascii=False)
            )
            
            # 保存槽位信息
            slots_key = f"{self.SLOTS_PREFIX}{session_id}"
            filled_slots = state.get("filled_slots", {})
            self.redis_client.setex(
                slots_key,
                self.session_timeout,
                json.dumps(filled_slots, ensure_ascii=False)
            )
            
            # 保存對話歷史
            history_key = f"{self.HISTORY_PREFIX}{session_id}"
            chat_history = state.get("chat_history", [])
            
            # 清除舊的歷史記錄
            self.redis_client.delete(history_key)
            
            # 添加新的歷史記錄
            for message in chat_history:
                cleaned_message = self._convert_numpy_types(message)
                self.redis_client.rpush(history_key, json.dumps(cleaned_message, ensure_ascii=False))
            
            # 設置歷史記錄的過期時間
            self.redis_client.expire(history_key, self.session_timeout)
            
            # 保存推薦記錄
            recommendations_key = f"{self.RECOMMENDATIONS_PREFIX}{session_id}"
            recommendations = state.get("recommendations", [])
            self.redis_client.setex(
                recommendations_key,
                self.session_timeout,
                json.dumps(recommendations, ensure_ascii=False)
            )
            
            self.logger.info(f"保存會話狀態: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存會話狀態失敗: {e}")
            return False
    
    def update_slots(self, session_id: str, slots: Dict[str, Any]) -> bool:
        """
        更新槽位狀態
        
        Args:
            session_id: 會話ID
            slots: 新的槽位信息
            
        Returns:
            是否更新成功
        """
        try:
            # 載入當前槽位
            current_slots = self.get_slots(session_id)
            
            # 合併新槽位
            updated_slots = {**current_slots, **slots}
            
            # 轉換 numpy 類型
            updated_slots = self._convert_numpy_types(updated_slots)
            
            # 保存更新後的槽位
            slots_key = f"{self.SLOTS_PREFIX}{session_id}"
            self.redis_client.setex(
                slots_key,
                self.session_timeout,
                json.dumps(updated_slots, ensure_ascii=False)
            )
            
            self.logger.info(f"更新槽位: {session_id} - {slots}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新槽位失敗: {e}")
            return False
    
    def get_slots(self, session_id: str) -> Dict[str, Any]:
        """
        獲取會話的槽位信息
        
        Args:
            session_id: 會話ID
            
        Returns:
            槽位信息字典
        """
        try:
            slots_key = f"{self.SLOTS_PREFIX}{session_id}"
            slots_data = self.redis_client.get(slots_key)
            
            if slots_data:
                return json.loads(slots_data.decode('utf-8'))
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"獲取槽位失敗: {e}")
            return {}
    
    def add_message_to_history(self, session_id: str, message: Dict[str, Any]) -> bool:
        """
        添加消息到對話歷史
        
        Args:
            session_id: 會話ID
            message: 消息內容
            
        Returns:
            是否添加成功
        """
        try:
            history_key = f"{self.HISTORY_PREFIX}{session_id}"
            
            # 添加時間戳
            message["timestamp"] = datetime.now().isoformat()
            
            # 轉換 numpy 類型
            cleaned_message = self._convert_numpy_types(message)
            
            # 添加到歷史記錄
            self.redis_client.rpush(history_key, json.dumps(cleaned_message, ensure_ascii=False))
            
            # 設置過期時間
            self.redis_client.expire(history_key, self.session_timeout)
            
            self.logger.info(f"添加消息到歷史: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加消息到歷史失敗: {e}")
            return False
    
    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        獲取對話歷史
        
        Args:
            session_id: 會話ID
            limit: 返回的消息數量限制
            
        Returns:
            對話歷史列表
        """
        try:
            history_key = f"{self.HISTORY_PREFIX}{session_id}"
            history_data = self.redis_client.lrange(history_key, -limit, -1)
            
            return [
                json.loads(msg.decode('utf-8')) for msg in history_data
            ]
            
        except Exception as e:
            self.logger.error(f"獲取對話歷史失敗: {e}")
            return []
    
    def add_recommendation(self, session_id: str, recommendation: Dict[str, Any]) -> bool:
        """
        添加推薦記錄
        
        Args:
            session_id: 會話ID
            recommendation: 推薦信息
            
        Returns:
            是否添加成功
        """
        try:
            recommendations_key = f"{self.RECOMMENDATIONS_PREFIX}{session_id}"
            
            # 載入當前推薦記錄
            current_recommendations = self.get_recommendations(session_id)
            
            # 轉換 numpy 類型
            cleaned_recommendation = self._convert_numpy_types(recommendation)
            
            # 添加新推薦
            current_recommendations.append(cleaned_recommendation)
            
            # 保存更新後的推薦記錄
            self.redis_client.setex(
                recommendations_key,
                self.session_timeout,
                json.dumps(current_recommendations, ensure_ascii=False)
            )
            
            self.logger.info(f"添加推薦記錄: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加推薦記錄失敗: {e}")
            return False
    
    def get_recommendations(self, session_id: str) -> List[Dict[str, Any]]:
        """
        獲取推薦記錄
        
        Args:
            session_id: 會話ID
            
        Returns:
            推薦記錄列表
        """
        try:
            recommendations_key = f"{self.RECOMMENDATIONS_PREFIX}{session_id}"
            recommendations_data = self.redis_client.get(recommendations_key)
            
            if recommendations_data:
                return json.loads(recommendations_data.decode('utf-8'))
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"獲取推薦記錄失敗: {e}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """
        刪除會話
        
        Args:
            session_id: 會話ID
            
        Returns:
            是否刪除成功
        """
        try:
            # 刪除所有相關的鍵
            keys_to_delete = [
                f"{self.SESSION_PREFIX}{session_id}",
                f"{self.SLOTS_PREFIX}{session_id}",
                f"{self.HISTORY_PREFIX}{session_id}",
                f"{self.RECOMMENDATIONS_PREFIX}{session_id}"
            ]
            
            self.redis_client.delete(*keys_to_delete)
            
            self.logger.info(f"刪除會話: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"刪除會話失敗: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        清理過期的會話
        
        Returns:
            清理的會話數量
        """
        try:
            # 獲取所有會話鍵
            session_keys = self.redis_client.keys(f"{self.SESSION_PREFIX}*")
            cleaned_count = 0
            
            for key in session_keys:
                session_id = key.decode('utf-8').replace(self.SESSION_PREFIX, '')
                
                # 檢查會話是否過期
                if not self.redis_client.exists(key):
                    self.delete_session(session_id)
                    cleaned_count += 1
            
            self.logger.info(f"清理過期會話: {cleaned_count} 個")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"清理過期會話失敗: {e}")
            return 0
