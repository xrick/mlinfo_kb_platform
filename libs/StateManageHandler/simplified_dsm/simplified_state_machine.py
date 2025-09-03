"""
DSM 簡化狀態機
保持 8 個狀態，但簡化流程，實現線性執行和清晰的職責分工
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

from .dsm_state_enum import DSMState, DSMStateInfo


# 設置日誌
logger = logging.getLogger(__name__)


class SimplifiedStateMachine:
    """簡化 DSM 狀態機 - 保持 8 個狀態，但簡化流程"""
    
    def __init__(self):
        """初始化簡化狀態機"""
        self.current_state = DSMState.ON_RECEIVE_MSG
        
        # 簡化後的狀態轉換表
        self.simplified_transitions = {
            DSMState.ON_RECEIVE_MSG: {
                "next_state": DSMState.ON_RESPONSE_MSG,
                "description": "接收消息後直接轉向回應消息",
                "condition": "always"
            },
            DSMState.ON_RESPONSE_MSG: {
                "next_state": DSMState.ON_GEN_FUNNEL_CHAT,
                "description": "回應消息後轉向生成漏斗對話",
                "condition": "always"
            },
            DSMState.ON_GEN_FUNNEL_CHAT: {
                "next_state": DSMState.ON_GEN_MD_CONTENT,
                "description": "生成漏斗對話後轉向生成 Markdown 內容",
                "condition": "always"
            },
            DSMState.ON_GEN_MD_CONTENT: {
                "next_state": DSMState.ON_DATA_QUERY,
                "description": "生成 Markdown 內容後轉向數據查詢",
                "condition": "always"
            },
            DSMState.ON_DATA_QUERY: {
                "next_state": DSMState.ON_QUERIED_DATA_PROCESSING,
                "description": "數據查詢後轉向數據處理",
                "condition": "always"
            },
            DSMState.ON_QUERIED_DATA_PROCESSING: {
                "next_state": DSMState.ON_SEND_FRONT,
                "description": "數據處理後轉向發送前端",
                "condition": "always"
            },
            DSMState.ON_SEND_FRONT: {
                "next_state": DSMState.ON_WAIT_MSG,
                "description": "發送前端後轉向等待消息",
                "condition": "always"
            },
            DSMState.ON_WAIT_MSG: {
                "next_state": DSMState.ON_RECEIVE_MSG,
                "description": "等待消息後轉向接收消息",
                "condition": "always"
            }
        }
        
        logger.info("DSM 簡化狀態機初始化完成")
    
    def get_current_state(self) -> DSMState:
        """獲取當前狀態"""
        return self.current_state
    
    def get_next_state(self, current_state: DSMState) -> DSMState:
        """獲取下一個狀態"""
        if current_state in self.simplified_transitions:
            return self.simplified_transitions[current_state]["next_state"]
        else:
            raise ValueError(f"未知狀態: {current_state}")
    
    def get_transition_info(self, state: DSMState) -> Dict[str, Any]:
        """獲取狀態轉換信息"""
        if state in self.simplified_transitions:
            return self.simplified_transitions[state]
        else:
            return {}
    
    def get_all_transitions(self) -> Dict[DSMState, Dict[str, Any]]:
        """獲取所有狀態轉換信息"""
        return self.simplified_transitions.copy()
    
    def validate_transition(self, from_state: DSMState, to_state: DSMState) -> bool:
        """驗證狀態轉換是否有效"""
        if from_state in self.simplified_transitions:
            expected_next = self.simplified_transitions[from_state]["next_state"]
            return expected_next == to_state
        return False
    
    async def execute_simplified_flow(self, context: Dict[str, Any], 
                                    flow_controller: Any) -> Dict[str, Any]:
        """
        執行簡化流程 - 線性執行所有狀態
        
        Args:
            context: 處理上下文
            flow_controller: 流程控制器實例
            
        Returns:
            處理結果
        """
        session_id = context.get("session_id", "unknown")
        logger.info(f"開始執行 DSM 簡化流程 - 會話: {session_id}")
        
        # 線性執行所有狀態
        states_execution_order = DSMStateInfo.get_linear_execution_order()
        
        execution_results = {}
        start_time = datetime.now()
        
        for state in states_execution_order:
            state_start_time = datetime.now()
            logger.info(f"執行狀態: {state.value} - 會話: {session_id}")
            
            try:
                # 執行對應的狀態處理
                context = await self._execute_single_state(state, context, flow_controller)
                
                # 計算執行時間
                state_execution_time = (datetime.now() - state_start_time).total_seconds() * 1000
                
                # 記錄執行結果
                execution_results[state.value] = {
                    "completed": context.get(f"{state.value.lower()}_completed", False),
                    "timestamp": context.get(f"{state.value.lower()}_timestamp", ""),
                    "execution_time_ms": state_execution_time,
                    "error": context.get("error", None),
                    "success": context.get(f"{state.value.lower()}_completed", False)
                }
                
                # 檢查是否有錯誤
                if context.get("error"):
                    logger.warning(f"狀態 {state.value} 執行時出現錯誤: {context.get('error')}")
                
                # 更新當前狀態
                self.current_state = state
                
            except Exception as e:
                logger.error(f"狀態 {state.value} 執行失敗: {e}")
                execution_results[state.value] = {
                    "completed": False,
                    "timestamp": datetime.now().isoformat(),
                    "execution_time_ms": 0,
                    "error": str(e),
                    "success": False
                }
                context["error"] = str(e)
                context["error_state"] = state.value
        
        # 計算總執行時間
        total_execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # 準備最終結果
        successful_states = sum(1 for result in execution_results.values() if result["success"])
        failed_states = len(execution_results) - successful_states
        
        final_result = {
            "success": failed_states == 0,
            "session_id": session_id,
            "flow_completed": True,
            "completion_timestamp": datetime.now().isoformat(),
            "total_execution_time_ms": total_execution_time,
            "successful_states": successful_states,
            "failed_states": failed_states,
            "execution_summary": execution_results,
            "final_context": context,
            "current_state": self.current_state.value
        }
        
        logger.info(f"DSM 簡化流程執行完成 - 會話: {session_id}, "
                   f"成功狀態: {successful_states}, 失敗狀態: {failed_states}, "
                   f"總執行時間: {total_execution_time:.2f}ms")
        
        return final_result
    
    async def _execute_single_state(self, state: DSMState, context: Dict[str, Any], 
                                  flow_controller: Any) -> Dict[str, Any]:
        """執行單個狀態"""
        try:
            if state == DSMState.ON_RECEIVE_MSG:
                return await flow_controller.receive_msg(context)
            elif state == DSMState.ON_RESPONSE_MSG:
                return await flow_controller.response_msg(context)
            elif state == DSMState.ON_GEN_FUNNEL_CHAT:
                return await flow_controller.gen_funnel_chat(context)
            elif state == DSMState.ON_GEN_MD_CONTENT:
                return await flow_controller.gen_md_content(context)
            elif state == DSMState.ON_DATA_QUERY:
                return await flow_controller.data_query(context)
            elif state == DSMState.ON_QUERIED_DATA_PROCESSING:
                return await flow_controller.queried_data_processing(context)
            elif state == DSMState.ON_SEND_FRONT:
                return await flow_controller.send_front(context)
            elif state == DSMState.ON_WAIT_MSG:
                return await flow_controller.wait_msg(context)
            else:
                raise ValueError(f"未知狀態: {state}")
        except Exception as e:
            logger.error(f"執行狀態 {state.value} 時發生錯誤: {e}")
            # 返回錯誤上下文
            error_context = context.copy()
            error_context.update({
                f"{state.value.lower()}_completed": False,
                f"{state.value.lower()}_timestamp": datetime.now().isoformat(),
                "error": str(e),
                "error_state": state.value
            })
            return error_context
    
    def reset_state_machine(self):
        """重置狀態機到初始狀態"""
        self.current_state = DSMState.ON_RECEIVE_MSG
        logger.info("DSM 狀態機已重置到初始狀態")
    
    def get_machine_status(self) -> Dict[str, Any]:
        """獲取狀態機狀態信息"""
        return {
            "current_state": self.current_state.value,
            "current_state_info": DSMStateInfo.get_state_info().get(self.current_state, {}),
            "total_states": len(DSMState.ON_RECEIVE_MSG),
            "linear_execution_order": [state.value for state in DSMStateInfo.get_linear_execution_order()],
            "machine_initialized": True
        }


# 導出主要類別
__all__ = ['SimplifiedStateMachine']
