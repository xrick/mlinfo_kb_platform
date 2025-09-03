"""
StateManagementHandler - 核心狀態管理處理器
基於事件溯源架構和標準動作合約模式的智能狀態管理系統

實作功能：
1. 事件驅動狀態管理
2. 智能狀態轉換預測
3. 表驅動狀態機架構
4. Redis 狀態持久化
5. 標準動作合約遵循
"""

import logging
import json
import asyncio
import hashlib
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import redis.asyncio as redis

from .EventStore import EventStore
from .StateTransition import StateTransition, StateResolver
from .StateStrategyFactory import StateStrategyFactory
from .TransitionPredictor import TransitionPredictor
from .StateValidator import StateValidator

# 新增：簡化 DSM 系統導入
from .simplified_dsm import (
    DSMState, 
    DSMStateInfo, 
    SimplifiedStateMachine, 
    StateFlowController, 
    LinearFlowExecutor
)
from .action_hub import FlowExecutor, FlowValidator

logger = logging.getLogger(__name__)


class StateType(Enum):
    """狀態類型枚舉"""
    INIT = "INIT"
    FUNNEL_START = "FUNNEL_START"
    FUNNEL_QUESTION = "FUNNEL_QUESTION"
    ELICITATION = "ELICITATION"
    RECOMMENDATION_PREPARATION = "RECOMMENDATION_PREPARATION"
    RECOMMENDATION_PRESENTATION = "RECOMMENDATION_PRESENTATION"
    PRODUCT_QA = "PRODUCT_QA"
    PURCHASE_GUIDANCE = "PURCHASE_GUIDANCE"
    END = "END"
    ERROR = "ERROR"


@dataclass
class StateEvent:
    """狀態事件資料結構"""
    session_id: str
    event_type: str
    state_from: str
    state_to: str
    context_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: hashlib.md5(
        f"{datetime.now().isoformat()}{id(object())}".encode()
    ).hexdigest())
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "session_id": self.session_id,
            "event_type": self.event_type,
            "state_from": self.state_from,
            "state_to": self.state_to,
            "context_data": json.dumps(self.context_data),
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateEvent':
        """從字典創建事件"""
        return cls(
            session_id=data["session_id"],
            event_type=data["event_type"],
            state_from=data["state_from"],
            state_to=data["state_to"],
            context_data=json.loads(data["context_data"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_id=data["event_id"]
        )


class StateManagementHandler:
    """
    核心狀態管理處理器
    
    提供完整的狀態管理功能，包括：
    - 事件溯源狀態管理
    - 智能狀態轉換
    - 表驅動狀態機
    - Redis 持久化
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        初始化狀態管理處理器
        
        Args:
            redis_client: Redis 客戶端實例
        """
        self.redis_client = redis_client
        self.event_store = EventStore(redis_client) if redis_client else None
        self.state_strategies = StateStrategyFactory()
        self.transition_predictor = TransitionPredictor()
        self.state_validator = StateValidator()
        
        # 載入狀態轉換表
        self.state_transitions = self._load_state_transitions()
        
        # 新增：初始化簡化 DSM 系統
        self.dsm_state_machine = SimplifiedStateMachine()
        self.dsm_flow_controller = StateFlowController()
        self.dsm_linear_executor = LinearFlowExecutor()
        
        # 新增：初始化 JSON 流程定義系統
        self.flow_executor = None
        self.flow_validator = FlowValidator()
        
        # 性能監控
        self.metrics = {
            "total_transitions": 0,
            "average_transition_time": 0.0,
            "error_count": 0,
            "prediction_accuracy": 0.0
        }
        
        logger.info("StateManagementHandler 初始化完成，包含簡化 DSM 系統")
    
    def _load_state_transitions(self) -> Dict[str, StateTransition]:
        """載入狀態轉換表"""
        # 這個方法會在後續實作中填入完整的 STATE_TRANSITIONS
        return {}
    
    # =================== 標準動作合約介面 ===================
    
    async def process_state(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        主要狀態處理入口點 - 遵循標準動作合約
        
        Args:
            context: 當前處理上下文
            
        Returns:
            狀態處理結果字典
        """
        start_time = datetime.now()
        session_id = context.get('session_id', 'unknown')
        
        try:
            logger.info(f"開始處理狀態 - 會話: {session_id}")
            
            # 1. 驗證輸入上下文
            validation_result = await self._validate_context(context)
            if not validation_result['is_valid']:
                return self._create_error_result(
                    "上下文驗證失敗", 
                    validation_result['errors']
                )
            
            # 2. 獲取當前狀態
            current_state = context.get('stage', StateType.INIT.value)
            
            # 3. 創建狀態事件
            state_event = self._create_state_event(context, current_state)
            
            # 4. 記錄事件到事件存儲
            if self.event_store:
                await self.event_store.append_event(state_event)
            
            # 5. 選擇處理策略
            strategy = self.state_strategies.get_strategy(context)
            
            # 6. 執行狀態轉換
            transition_result = await self._execute_state_transition(
                current_state, context, strategy
            )
            
            # 7. 預測下一步狀態
            next_predictions = await self.transition_predictor.predict_next_states(
                transition_result
            )
            
            # 8. 更新性能指標
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(execution_time, True)
            
            # 9. 組裝回應結果
            result = {
                **transition_result,
                "predicted_next_states": next_predictions,
                "strategy_used": strategy.name if strategy else "default",
                "event_id": state_event.event_id,
                "execution_time_ms": execution_time * 1000,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"狀態處理完成 - 會話: {session_id}, 執行時間: {execution_time:.3f}秒")
            return result
            
        except Exception as e:
            logger.error(f"狀態處理時發生錯誤 - 會話: {session_id}: {e}", exc_info=True)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(execution_time, False)
            
            return self._create_error_result(
                f"狀態處理失敗: {str(e)}",
                {"session_id": session_id, "execution_time": execution_time}
            )
    
    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """
        獲取會話狀態 - 標準動作合約
        
        Args:
            session_id: 會話識別碼
            
        Returns:
            會話狀態字典
        """
        try:
            if not self.redis_client:
                return self._create_error_result("Redis 客戶端未初始化")
            
            # 從 Redis 獲取當前狀態
            current_state_key = f"session:{session_id}:current"
            state_data = await self.redis_client.hgetall(current_state_key)
            
            if not state_data:
                # 會話不存在，返回初始狀態
                return {
                    "success": True,
                    "session_id": session_id,
                    "current_state": StateType.INIT.value,
                    "state_data": {},
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "is_new_session": True
                }
            
            # 解析狀態數據
            parsed_state_data = {}
            for key, value in state_data.items():
                try:
                    parsed_state_data[key.decode() if isinstance(key, bytes) else key] = \
                        json.loads(value.decode() if isinstance(value, bytes) else value)
                except (json.JSONDecodeError, AttributeError):
                    parsed_state_data[key.decode() if isinstance(key, bytes) else key] = \
                        value.decode() if isinstance(value, bytes) else value
            
            return {
                "success": True,
                "session_id": session_id,
                "current_state": parsed_state_data.get("current_state", StateType.INIT.value),
                "state_data": parsed_state_data,
                "last_updated": parsed_state_data.get("last_updated", datetime.now().isoformat()),
                "is_new_session": False
            }
            
        except Exception as e:
            logger.error(f"獲取會話狀態時發生錯誤 - 會話: {session_id}: {e}", exc_info=True)
            return self._create_error_result(f"獲取會話狀態失敗: {str(e)}")
    
    async def update_session_state(
        self, 
        session_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新會話狀態 - 標準動作合約
        
        Args:
            session_id: 會話識別碼
            context: 會話上下文數據
            
        Returns:
            更新結果字典
        """
        try:
            if not self.redis_client:
                return self._create_error_result("Redis 客戶端未初始化")
            
            # 準備狀態數據
            state_data = {
                "session_id": session_id,
                "current_state": context.get("stage", StateType.INIT.value),
                "slots": json.dumps(context.get("slots", {})),
                "history": json.dumps(context.get("history", [])),
                "user_profile": json.dumps(context.get("user_profile", {})),
                "last_updated": datetime.now().isoformat(),
                "last_user_message": context.get("user_message", ""),
                "intent": context.get("intent", ""),
                "confidence": str(context.get("confidence", 0.0))
            }
            
            # 使用 Redis Pipeline 批量操作
            pipeline = self.redis_client.pipeline()
            
            # 1. 更新當前狀態
            current_state_key = f"session:{session_id}:current"
            pipeline.hset(current_state_key, mapping=state_data)
            pipeline.expire(current_state_key, 3600)  # 1小時過期
            
            # 2. 添加到狀態歷史
            history_key = f"session:{session_id}:history"
            history_entry = json.dumps({
                "timestamp": datetime.now().isoformat(),
                "state": context.get("stage", StateType.INIT.value),
                "user_message": context.get("user_message", ""),
                "intent": context.get("intent", ""),
                "slots_count": len(context.get("slots", {}))
            })
            pipeline.lpush(history_key, history_entry)
            pipeline.ltrim(history_key, 0, 99)  # 保留最近100個記錄
            pipeline.expire(history_key, 86400)  # 24小時過期
            
            # 3. 更新用戶會話索引
            user_id = context.get("user_id")
            if user_id:
                user_sessions_key = f"user:{user_id}:sessions"
                pipeline.sadd(user_sessions_key, session_id)
                pipeline.expire(user_sessions_key, 86400)
            
            # 執行批量操作
            await pipeline.execute()
            
            return {
                "success": True,
                "session_id": session_id,
                "updated_at": datetime.now().isoformat(),
                "current_state": context.get("stage", StateType.INIT.value)
            }
            
        except Exception as e:
            logger.error(f"更新會話狀態時發生錯誤 - 會話: {session_id}: {e}", exc_info=True)
            return self._create_error_result(f"更新會話狀態失敗: {str(e)}")
    
    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        刪除會話 - 標準動作合約
        
        Args:
            session_id: 會話識別碼
            
        Returns:
            刪除結果字典
        """
        try:
            if not self.redis_client:
                return self._create_error_result("Redis 客戶端未初始化")
            
            # 獲取相關的 Redis 鍵
            keys_to_delete = [
                f"session:{session_id}:current",
                f"session:{session_id}:history",
                f"state_events:{session_id}"
            ]
            
            # 批量刪除
            deleted_count = await self.redis_client.delete(*keys_to_delete)
            
            return {
                "success": True,
                "session_id": session_id,
                "deleted_keys": deleted_count,
                "deleted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"刪除會話時發生錯誤 - 會話: {session_id}: {e}", exc_info=True)
            return self._create_error_result(f"刪除會話失敗: {str(e)}")
    
    # =================== 內部實作方法 ===================
    
    async def _validate_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """驗證上下文數據"""
        errors = []
        
        # 檢查必要字段
        required_fields = ["session_id"]
        for field in required_fields:
            if field not in context or not context[field]:
                errors.append(f"缺少必要字段: {field}")
        
        # 檢查會話ID格式
        session_id = context.get("session_id", "")
        if len(session_id) < 8:
            errors.append("session_id 長度不足")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    def _create_state_event(
        self, 
        context: Dict[str, Any], 
        current_state: str
    ) -> StateEvent:
        """創建狀態事件"""
        return StateEvent(
            session_id=context.get("session_id", ""),
            event_type="state_transition",
            state_from=current_state,
            state_to=context.get("next_state", current_state),
            context_data={
                "user_message": context.get("user_message", ""),
                "intent": context.get("intent", ""),
                "confidence": context.get("confidence", 0.0),
                "slots_count": len(context.get("slots", {}))
            }
        )
    
    async def _execute_state_transition(
        self,
        current_state: str,
        context: Dict[str, Any],
        strategy: Optional[Any] = None
    ) -> Dict[str, Any]:
        """執行狀態轉換"""
        # 獲取狀態轉換配置
        transition_config = self.state_transitions.get(current_state)
        
        if not transition_config:
            logger.warning(f"找不到狀態轉換配置: {current_state}")
            return {
                "current_state": current_state,
                "next_state": current_state,
                "message": f"狀態 {current_state} 無可用轉換"
            }
        
        # 執行轉換動作
        if hasattr(transition_config, 'actions'):
            for action in transition_config.actions:
                try:
                    if callable(action):
                        action_result = await action(context)
                        context.update(action_result)
                except Exception as e:
                    logger.error(f"執行狀態動作時發生錯誤: {e}")
        
        # 決定下一個狀態
        next_state = current_state  # 預設保持當前狀態
        if hasattr(transition_config, 'next_state_resolver'):
            try:
                next_state = await transition_config.next_state_resolver.resolve_next_state(context)
            except Exception as e:
                logger.error(f"解析下一個狀態時發生錯誤: {e}")
        
        return {
            "current_state": current_state,
            "next_state": next_state,
            "context_updates": context,
            "transition_successful": True
        }
    
    def _update_metrics(self, execution_time: float, success: bool):
        """更新性能指標"""
        self.metrics["total_transitions"] += 1
        
        # 更新平均執行時間
        current_avg = self.metrics["average_transition_time"]
        total_transitions = self.metrics["total_transitions"]
        self.metrics["average_transition_time"] = (
            (current_avg * (total_transitions - 1) + execution_time) / total_transitions
        )
        
        if not success:
            self.metrics["error_count"] += 1
    
    def _create_error_result(
        self, 
        error_message: str, 
        additional_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """創建錯誤結果"""
        result = {
            "success": False,
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }
        
        if additional_info:
            result.update(additional_info)
        
        return result
    
    def get_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        return {
            **self.metrics,
            "error_rate": (
                self.metrics["error_count"] / max(self.metrics["total_transitions"], 1)
            ),
            "uptime": datetime.now().isoformat()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            "module_name": "StateManagementHandler",
            "status": "active",
            "redis_connected": self.redis_client is not None,
            "event_store_enabled": self.event_store is not None,
            "total_state_transitions": len(self.state_transitions),
            "metrics": self.get_metrics(),
            "timestamp": datetime.now().isoformat()
        }
    
    # =================== 簡化 DSM 系統方法 ===================
    
    async def execute_dsm_flow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行 DSM 簡化流程
        
        Args:
            context: 處理上下文
            
        Returns:
            流程執行結果
        """
        try:
            logger.info(f"開始執行 DSM 簡化流程 - 會話: {context.get('session_id', 'unknown')}")
            
            # 使用線性流程執行器執行流程
            result = await self.dsm_linear_executor.execute_linear_flow(context)
            
            logger.info(f"DSM 簡化流程執行完成 - 會話: {context.get('session_id', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"執行 DSM 流程失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def load_dsm_flow_definition(self, flow_definition_path: str) -> bool:
        """
        載入 DSM 流程定義檔案
        
        Args:
            flow_definition_path: 流程定義檔案路徑
            
        Returns:
            是否成功載入
        """
        try:
            from .action_hub import FlowExecutor
            self.flow_executor = FlowExecutor(flow_definition_path)
            logger.info(f"DSM 流程定義載入成功: {flow_definition_path}")
            return True
            
        except Exception as e:
            logger.error(f"載入 DSM 流程定義失敗: {e}")
            return False
    
    async def execute_dsm_flow_from_json(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        根據 JSON 流程定義執行 DSM 流程
        
        Args:
            context: 處理上下文
            
        Returns:
            流程執行結果
        """
        if not self.flow_executor:
            return {
                "success": False,
                "error": "流程定義未載入，請先調用 load_dsm_flow_definition",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            logger.info(f"開始執行 JSON 定義的 DSM 流程 - 會話: {context.get('session_id', 'unknown')}")
            
            # 使用流程執行引擎執行流程
            result = await self.flow_executor.execute_flow(context)
            
            logger.info(f"JSON 定義的 DSM 流程執行完成 - 會話: {context.get('session_id', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"執行 JSON 定義的 DSM 流程失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_dsm_status(self) -> Dict[str, Any]:
        """獲取 DSM 系統狀態"""
        return {
            "dsm_state_machine_initialized": self.dsm_state_machine is not None,
            "dsm_flow_controller_initialized": self.dsm_flow_controller is not None,
            "dsm_linear_executor_initialized": self.dsm_linear_executor is not None,
            "flow_executor_loaded": self.flow_executor is not None,
            "flow_validator_initialized": self.flow_validator is not None,
            "available_dsm_states": [state.value for state in DSMState],
            "dsm_linear_flow": DSMStateInfo.get_linear_execution_order(),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_dsm_state_info(self, state_id: str) -> Dict[str, Any]:
        """獲取 DSM 狀態信息"""
        try:
            state = DSMState(state_id)
            return DSMStateInfo.get_state_info().get(state, {})
        except ValueError:
            return {"error": f"無效的狀態 ID: {state_id}"}
    
    def reset_dsm_system(self):
        """重置 DSM 系統"""
        if self.dsm_state_machine:
            self.dsm_state_machine.reset_state_machine()
        
        if self.dsm_linear_executor:
            self.dsm_linear_executor.reset_flow()
        
        logger.info("DSM 系統已重置")
    
    def validate_dsm_flow_definition(self, flow_definition_path: str) -> Dict[str, Any]:
        """
        驗證 DSM 流程定義檔案
        
        Args:
            flow_definition_path: 流程定義檔案路徑
            
        Returns:
            驗證結果
        """
        try:
            validation_result = self.flow_validator.validate_flow_file(flow_definition_path)
            
            return {
                "is_valid": validation_result.is_valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "timestamp": validation_result.timestamp
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }