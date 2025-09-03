"""
流程執行引擎
根據 JSON 配置自動執行狀態轉換
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from .flow_validator import FlowValidator, ValidationResult
from ...simplified_dsm import StateFlowController


# 設置日誌
logger = logging.getLogger(__name__)


class FlowExecutor:
    """JSON 流程定義執行引擎"""
    
    def __init__(self, flow_definition_path: str = None):
        """
        初始化流程執行引擎
        
        Args:
            flow_definition_path: 流程定義檔案路徑
        """
        self.flow_definition = None
        self.flow_validator = FlowValidator()
        self.flow_controller = StateFlowController()
        
        if flow_definition_path:
            self.load_flow_definition(flow_definition_path)
        
        logger.info("流程執行引擎初始化完成")
    
    def load_flow_definition(self, file_path: str) -> bool:
        """
        載入流程定義檔案
        
        Args:
            file_path: 流程定義檔案路徑
            
        Returns:
            是否成功載入
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.flow_definition = json.load(f)
            
            # 驗證流程定義
            validation_result = self.flow_validator.validate(self.flow_definition)
            if not validation_result.is_valid:
                logger.error(f"流程定義驗證失敗: {validation_result.errors}")
                return False
            
            logger.info(f"流程定義載入成功: {self.flow_definition.get('flow_metadata', {}).get('flow_name', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"載入流程定義失敗: {e}")
            return False
    
    def get_flow_metadata(self) -> Dict[str, Any]:
        """獲取流程元數據"""
        if self.flow_definition:
            return self.flow_definition.get("flow_metadata", {})
        return {}
    
    def get_available_states(self) -> List[str]:
        """獲取可用的狀態列表"""
        if self.flow_definition and "states" in self.flow_definition:
            return list(self.flow_definition["states"].keys())
        return []
    
    def get_state_info(self, state_id: str) -> Dict[str, Any]:
        """獲取狀態信息"""
        if self.flow_definition and "states" in self.flow_definition:
            return self.flow_definition["states"].get(state_id, {})
        return {}
    
    async def execute_flow(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行完整流程
        
        Args:
            initial_context: 初始處理上下文
            
        Returns:
            處理結果
        """
        if not self.flow_definition:
            raise ValueError("流程定義未載入，請先載入流程定義檔案")
        
        # 驗證流程定義
        validation_result = self.flow_validator.validate(self.flow_definition)
        if not validation_result.is_valid:
            raise ValueError(f"流程定義驗證失敗: {validation_result.errors}")
        
        # 初始化執行上下文
        execution_context = self._initialize_execution_context(initial_context)
        session_id = execution_context.get("session_id", "unknown")
        
        logger.info(f"開始執行流程 - 會話: {session_id}")
        
        # 開始執行監控
        execution_start_time = datetime.now()
        execution_results = {}
        
        # 按順序執行所有狀態
        linear_sequence = self.flow_definition["flow_transitions"]["linear_sequence"]
        
        for state_id in linear_sequence:
            state_start_time = datetime.now()
            logger.info(f"執行狀態: {state_id} - 會話: {session_id}")
            
            try:
                # 執行狀態
                execution_context = await self._execute_single_state(state_id, execution_context)
                
                # 計算執行時間
                state_execution_time = (datetime.now() - state_start_time).total_seconds() * 1000
                
                # 記錄執行結果
                execution_results[state_id] = {
                    "completed": execution_context.get(f"{state_id.lower()}_completed", False),
                    "timestamp": execution_context.get(f"{state_id.lower()}_timestamp", ""),
                    "execution_time_ms": state_execution_time,
                    "error": execution_context.get("error", None),
                    "success": execution_context.get(f"{state_id.lower()}_completed", False)
                }
                
                # 檢查是否有錯誤
                if execution_context.get("error"):
                    logger.warning(f"狀態 {state_id} 執行時出現錯誤: {execution_context.get('error')}")
                
            except Exception as e:
                logger.error(f"狀態 {state_id} 執行失敗: {e}")
                execution_results[state_id] = {
                    "completed": False,
                    "timestamp": datetime.now().isoformat(),
                    "execution_time_ms": 0,
                    "error": str(e),
                    "success": False
                }
                execution_context["error"] = str(e)
                execution_context["error_state"] = state_id
        
        # 計算總執行時間
        total_execution_time = (datetime.now() - execution_start_time).total_seconds() * 1000
        
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
            "final_context": execution_context,
            "flow_metadata": self.get_flow_metadata()
        }
        
        logger.info(f"流程執行完成 - 會話: {session_id}, "
                   f"成功狀態: {successful_states}, 失敗狀態: {failed_states}, "
                   f"總執行時間: {total_execution_time:.2f}ms")
        
        return final_result
    
    def _initialize_execution_context(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """初始化執行上下文"""
        execution_context = initial_context.copy()
        
        # 確保有 session_id
        if "session_id" not in execution_context or not execution_context["session_id"]:
            execution_context["session_id"] = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 添加流程執行信息
        execution_context.update({
            "flow_start_time": datetime.now().isoformat(),
            "flow_name": self.get_flow_metadata().get("flow_name", "Unknown"),
            "flow_version": self.get_flow_metadata().get("version", "Unknown")
        })
        
        return execution_context
    
    async def _execute_single_state(self, state_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """執行單個狀態"""
        try:
            # 獲取狀態配置
            state_config = self.get_state_info(state_id)
            if not state_config:
                raise ValueError(f"找不到狀態配置: {state_id}")
            
            # 獲取動作函數名稱
            action_function = state_config.get("action_function")
            if not action_function:
                raise ValueError(f"狀態 {state_id} 缺少 action_function")
            
            # 執行對應的動作函數
            if action_function == "receive_msg":
                result = await self.flow_controller.receive_msg(context)
            elif action_function == "response_msg":
                result = await self.flow_controller.response_msg(context)
            elif action_function == "gen_funnel_chat":
                result = await self.flow_controller.gen_funnel_chat(context)
            elif action_function == "gen_md_content":
                result = await self.flow_controller.gen_md_content(context)
            elif action_function == "data_query":
                result = await self.flow_controller.data_query(context)
            elif action_function == "queried_data_processing":
                result = await self.flow_controller.queried_data_processing(context)
            elif action_function == "send_front":
                result = await self.flow_controller.send_front(context)
            elif action_function == "wait_msg":
                result = await self.flow_controller.wait_msg(context)
            else:
                raise ValueError(f"未知的動作函數: {action_function}")
            
            return result
            
        except Exception as e:
            logger.error(f"執行狀態 {state_id} 時發生錯誤: {e}")
            # 返回錯誤上下文
            error_context = context.copy()
            error_context.update({
                f"{state_id.lower()}_completed": False,
                f"{state_id.lower()}_timestamp": datetime.now().isoformat(),
                "error": str(e),
                "error_state": state_id
            })
            return error_context
    
    async def execute_single_state(self, state_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行單個狀態
        
        Args:
            state_id: 狀態 ID
            context: 處理上下文
            
        Returns:
            處理結果
        """
        if not self.flow_definition:
            raise ValueError("流程定義未載入")
        
        return await self._execute_single_state(state_id, context)
    
    def get_flow_status(self) -> Dict[str, Any]:
        """獲取流程狀態信息"""
        return {
            "flow_loaded": self.flow_definition is not None,
            "flow_metadata": self.get_flow_metadata(),
            "available_states": self.get_available_states(),
            "total_states": len(self.get_available_states()),
            "execution_mode": self.flow_definition.get("flow_configuration", {}).get("execution_mode", "unknown") if self.flow_definition else "unknown",
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_flow(self):
        """重置流程"""
        # 這裡可以添加流程重置邏輯
        logger.info("流程已重置")
    
    def validate_current_flow(self) -> ValidationResult:
        """驗證當前載入的流程定義"""
        if not self.flow_definition:
            return ValidationResult(
                is_valid=False,
                errors=["流程定義未載入"],
                warnings=[]
            )
        
        return self.flow_validator.validate(self.flow_definition)


# 導出主要類別
__all__ = ['FlowExecutor']
