"""
EventStore - 事件溯源存儲系統
基於 Redis Streams 實現的高性能事件存儲和重播系統

主要功能：
1. 事件存儲和檢索
2. 事件重播和狀態重建
3. 事件快照管理
4. 事件流清理和維護
5. 事件查詢和過濾
"""

import logging
import json
import asyncio
import hashlib
from typing import Dict, Any, List, Optional, AsyncGenerator, Tuple
from datetime import datetime, timedelta
import redis.asyncio as redis
from dataclasses import asdict

logger = logging.getLogger(__name__)


class EventStoreError(Exception):
    """事件存儲相關錯誤"""
    pass


class EventSchemaValidator:
    """事件模式驗證器"""
    
    REQUIRED_FIELDS = [
        "session_id", "event_type", "state_from", "state_to", 
        "timestamp", "event_id"
    ]
    
    ALLOWED_EVENT_TYPES = [
        "state_transition", "user_input", "system_response", 
        "error_occurred", "session_started", "session_ended"
    ]
    
    def validate(self, event) -> Any:
        """
        驗證事件數據結構
        
        Args:
            event: 要驗證的事件對象
            
        Returns:
            驗證通過的事件對象
            
        Raises:
            EventStoreError: 驗證失敗時拋出
        """
        try:
            # 檢查必要字段
            event_dict = event.to_dict() if hasattr(event, 'to_dict') else asdict(event)
            
            for field in self.REQUIRED_FIELDS:
                if field not in event_dict or event_dict[field] is None:
                    raise EventStoreError(f"事件缺少必要字段: {field}")
            
            # 檢查事件類型
            if event_dict["event_type"] not in self.ALLOWED_EVENT_TYPES:
                raise EventStoreError(f"不支援的事件類型: {event_dict['event_type']}")
            
            # 檢查會話ID格式
            if len(event_dict["session_id"]) < 8:
                raise EventStoreError("會話ID格式不正確")
            
            # 檢查時間戳格式
            try:
                if isinstance(event_dict["timestamp"], str):
                    datetime.fromisoformat(event_dict["timestamp"].replace('Z', '+00:00'))
            except ValueError:
                raise EventStoreError("時間戳格式不正確")
            
            return event
            
        except Exception as e:
            raise EventStoreError(f"事件驗證失敗: {str(e)}")


class EventStore:
    """
    事件存儲系統
    
    使用 Redis Streams 實現事件溯源存儲，支援：
    - 高性能事件追加
    - 事件流重播
    - 自動清理和維護
    - 事件查詢和過濾
    """
    
    def __init__(
        self, 
        redis_client: redis.Redis,
        max_stream_length: int = 10000,
        snapshot_interval: int = 100
    ):
        """
        初始化事件存儲
        
        Args:
            redis_client: Redis 客戶端
            max_stream_length: 最大流長度
            snapshot_interval: 快照間隔（事件數量）
        """
        self.redis = redis_client
        self.max_stream_length = max_stream_length
        self.snapshot_interval = snapshot_interval
        self.validator = EventSchemaValidator()
        
        # 事件統計
        self.metrics = {
            "total_events": 0,
            "events_per_session": {},
            "event_types": {},
            "errors": 0
        }
        
        logger.info("EventStore 初始化完成")
    
    async def append_event(self, event) -> Dict[str, Any]:
        """
        追加事件到事件流
        
        Args:
            event: 事件對象
            
        Returns:
            追加結果字典
        """
        try:
            # 驗證事件
            validated_event = self.validator.validate(event)
            event_dict = validated_event.to_dict()
            
            # 構建流鍵
            session_id = event_dict["session_id"]
            stream_key = f"state_events:{session_id}"
            
            # 準備事件數據（Redis Streams 需要字符串鍵值對）
            event_data = {}
            for key, value in event_dict.items():
                if isinstance(value, (dict, list)):
                    event_data[key] = json.dumps(value)
                else:
                    event_data[key] = str(value)
            
            # 追加到 Redis Streams
            event_id = await self.redis.xadd(
                stream_key,
                event_data,
                maxlen=self.max_stream_length,
                approximate=True  # 允許近似修剪以提升性能
            )
            
            # 更新統計信息
            await self._update_metrics(event_dict)
            
            # 檢查是否需要創建快照
            await self._check_snapshot_needed(session_id)
            
            logger.debug(f"事件已追加: {event_id} (會話: {session_id})")
            
            return {
                "success": True,
                "event_id": event_id.decode() if isinstance(event_id, bytes) else event_id,
                "stream_key": stream_key,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"追加事件失敗: {e}", exc_info=True)
            self.metrics["errors"] += 1
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def replay_events(
        self, 
        session_id: str,
        from_event_id: str = "0",
        to_event_id: str = "+",
        max_events: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        重播事件以重建狀態
        
        Args:
            session_id: 會話ID
            from_event_id: 起始事件ID
            to_event_id: 結束事件ID
            max_events: 最大事件數量
            
        Returns:
            事件列表
        """
        try:
            stream_key = f"state_events:{session_id}"
            
            # 從 Redis Streams 讀取事件
            events_data = await self.redis.xrange(
                stream_key, 
                min=from_event_id, 
                max=to_event_id,
                count=max_events
            )
            
            events = []
            for event_id, event_fields in events_data:
                # 解析事件數據
                parsed_event = self._parse_event_fields(event_fields)
                parsed_event["redis_event_id"] = event_id.decode() if isinstance(event_id, bytes) else event_id
                events.append(parsed_event)
            
            logger.info(f"重播了 {len(events)} 個事件 (會話: {session_id})")
            return events
            
        except Exception as e:
            logger.error(f"重播事件失敗: {e}", exc_info=True)
            return []
    
    async def get_events_since(
        self, 
        session_id: str, 
        since_timestamp: datetime
    ) -> List[Dict[str, Any]]:
        """
        獲取指定時間後的事件
        
        Args:
            session_id: 會話ID
            since_timestamp: 起始時間
            
        Returns:
            事件列表
        """
        try:
            events = await self.replay_events(session_id)
            
            # 過濾時間
            filtered_events = []
            for event in events:
                try:
                    event_time = datetime.fromisoformat(
                        event["timestamp"].replace('Z', '+00:00')
                    )
                    if event_time >= since_timestamp:
                        filtered_events.append(event)
                except (KeyError, ValueError):
                    continue
            
            return filtered_events
            
        except Exception as e:
            logger.error(f"獲取時間範圍事件失敗: {e}")
            return []
    
    async def get_latest_event(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取會話的最新事件
        
        Args:
            session_id: 會話ID
            
        Returns:
            最新事件或 None
        """
        try:
            stream_key = f"state_events:{session_id}"
            
            # 獲取最後一個事件
            events_data = await self.redis.xrevrange(
                stream_key, 
                count=1
            )
            
            if not events_data:
                return None
            
            event_id, event_fields = events_data[0]
            parsed_event = self._parse_event_fields(event_fields)
            parsed_event["redis_event_id"] = event_id.decode() if isinstance(event_id, bytes) else event_id
            
            return parsed_event
            
        except Exception as e:
            logger.error(f"獲取最新事件失敗: {e}")
            return None
    
    async def create_snapshot(self, session_id: str) -> Dict[str, Any]:
        """
        創建狀態快照
        
        Args:
            session_id: 會話ID
            
        Returns:
            快照創建結果
        """
        try:
            # 獲取所有事件
            events = await self.replay_events(session_id)
            
            if not events:
                return {"success": False, "error": "無事件可快照"}
            
            # 重建狀態
            reconstructed_state = await self._reconstruct_state_from_events(events)
            
            # 存儲快照
            snapshot_key = f"snapshot:{session_id}:{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            snapshot_data = {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "events_count": len(events),
                "latest_event_id": events[-1]["redis_event_id"],
                "reconstructed_state": json.dumps(reconstructed_state)
            }
            
            await self.redis.hset(snapshot_key, mapping=snapshot_data)
            await self.redis.expire(snapshot_key, 86400 * 7)  # 7天過期
            
            # 更新快照索引
            snapshot_index_key = f"snapshots:{session_id}"
            await self.redis.zadd(
                snapshot_index_key, 
                {snapshot_key: datetime.now().timestamp()}
            )
            await self.redis.expire(snapshot_index_key, 86400 * 7)
            
            return {
                "success": True,
                "snapshot_key": snapshot_key,
                "events_count": len(events),
                "created_at": snapshot_data["created_at"]
            }
            
        except Exception as e:
            logger.error(f"創建快照失敗: {e}")
            return {"success": False, "error": str(e)}
    
    async def restore_from_snapshot(
        self, 
        session_id: str, 
        snapshot_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        從快照恢復狀態
        
        Args:
            session_id: 會話ID
            snapshot_key: 快照鍵（如果不提供則使用最新快照）
            
        Returns:
            恢復結果
        """
        try:
            if not snapshot_key:
                # 獲取最新快照
                snapshot_index_key = f"snapshots:{session_id}"
                latest_snapshots = await self.redis.zrevrange(
                    snapshot_index_key, 0, 0, withscores=True
                )
                
                if not latest_snapshots:
                    return {"success": False, "error": "找不到快照"}
                
                snapshot_key = latest_snapshots[0][0].decode() if isinstance(latest_snapshots[0][0], bytes) else latest_snapshots[0][0]
            
            # 載入快照數據
            snapshot_data = await self.redis.hgetall(snapshot_key)
            
            if not snapshot_data:
                return {"success": False, "error": "快照不存在"}
            
            # 解析重建狀態
            reconstructed_state = json.loads(
                snapshot_data[b"reconstructed_state"].decode() if isinstance(snapshot_data[b"reconstructed_state"], bytes) 
                else snapshot_data["reconstructed_state"]
            )
            
            return {
                "success": True,
                "snapshot_key": snapshot_key,
                "reconstructed_state": reconstructed_state,
                "snapshot_created_at": snapshot_data[b"created_at"].decode() if isinstance(snapshot_data[b"created_at"], bytes) else snapshot_data["created_at"],
                "events_count": int(snapshot_data[b"events_count"] if isinstance(snapshot_data[b"events_count"], bytes) else snapshot_data["events_count"])
            }
            
        except Exception as e:
            logger.error(f"從快照恢復失敗: {e}")
            return {"success": False, "error": str(e)}
    
    async def cleanup_old_events(
        self, 
        session_id: str, 
        keep_recent_hours: int = 24
    ) -> Dict[str, Any]:
        """
        清理舊事件
        
        Args:
            session_id: 會話ID
            keep_recent_hours: 保留最近幾小時的事件
            
        Returns:
            清理結果
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=keep_recent_hours)
            cutoff_timestamp = int(cutoff_time.timestamp() * 1000)
            
            stream_key = f"state_events:{session_id}"
            
            # 獲取要刪除的事件ID範圍
            old_events = await self.redis.xrange(
                stream_key, 
                min="0",
                max=f"{cutoff_timestamp}-0"
            )
            
            if not old_events:
                return {
                    "success": True,
                    "cleaned_count": 0,
                    "message": "沒有需要清理的舊事件"
                }
            
            # 刪除舊事件
            event_ids = [event_id for event_id, _ in old_events]
            deleted_count = await self.redis.xdel(stream_key, *event_ids)
            
            logger.info(f"清理了 {deleted_count} 個舊事件 (會話: {session_id})")
            
            return {
                "success": True,
                "cleaned_count": deleted_count,
                "cutoff_time": cutoff_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"清理舊事件失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_event_fields(self, event_fields: Dict) -> Dict[str, Any]:
        """解析事件字段"""
        parsed = {}
        
        for key, value in event_fields.items():
            # 處理字節串
            if isinstance(key, bytes):
                key = key.decode()
            if isinstance(value, bytes):
                value = value.decode()
            
            # 嘗試解析 JSON
            if key in ["context_data"] and value:
                try:
                    parsed[key] = json.loads(value)
                except json.JSONDecodeError:
                    parsed[key] = value
            else:
                parsed[key] = value
        
        return parsed
    
    async def _update_metrics(self, event_dict: Dict[str, Any]):
        """更新統計指標"""
        self.metrics["total_events"] += 1
        
        session_id = event_dict["session_id"]
        event_type = event_dict["event_type"]
        
        # 更新會話事件計數
        if session_id not in self.metrics["events_per_session"]:
            self.metrics["events_per_session"][session_id] = 0
        self.metrics["events_per_session"][session_id] += 1
        
        # 更新事件類型計數
        if event_type not in self.metrics["event_types"]:
            self.metrics["event_types"][event_type] = 0
        self.metrics["event_types"][event_type] += 1
    
    async def _check_snapshot_needed(self, session_id: str):
        """檢查是否需要創建快照"""
        events_count = self.metrics["events_per_session"].get(session_id, 0)
        
        if events_count % self.snapshot_interval == 0:
            logger.info(f"創建自動快照 (會話: {session_id}, 事件數: {events_count})")
            await self.create_snapshot(session_id)
    
    async def _reconstruct_state_from_events(
        self, 
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """從事件重建狀態"""
        reconstructed_state = {
            "current_state": "INIT",
            "slots": {},
            "history": [],
            "user_profile": {},
            "session_started_at": None,
            "last_user_message": "",
            "intent_history": []
        }
        
        for event in events:
            try:
                # 更新當前狀態
                if event.get("state_to"):
                    reconstructed_state["current_state"] = event["state_to"]
                
                # 更新上下文數據
                context_data = event.get("context_data", {})
                if isinstance(context_data, dict):
                    if "user_message" in context_data:
                        reconstructed_state["last_user_message"] = context_data["user_message"]
                    
                    if "intent" in context_data:
                        reconstructed_state["intent_history"].append({
                            "intent": context_data["intent"],
                            "confidence": context_data.get("confidence", 0.0),
                            "timestamp": event.get("timestamp")
                        })
                
                # 記錄歷史
                reconstructed_state["history"].append({
                    "event_id": event.get("event_id"),
                    "state": event.get("state_to"),
                    "timestamp": event.get("timestamp"),
                    "event_type": event.get("event_type")
                })
                
                # 設置會話開始時間
                if not reconstructed_state["session_started_at"] and event.get("timestamp"):
                    reconstructed_state["session_started_at"] = event["timestamp"]
                    
            except Exception as e:
                logger.warning(f"重建狀態時跳過事件: {e}")
                continue
        
        return reconstructed_state
    
    def get_metrics(self) -> Dict[str, Any]:
        """獲取事件存儲統計指標"""
        return {
            **self.metrics,
            "active_sessions": len(self.metrics["events_per_session"]),
            "error_rate": self.metrics["errors"] / max(self.metrics["total_events"], 1),
            "timestamp": datetime.now().isoformat()
        }