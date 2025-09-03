"""
線性流程執行器
負責高層次的流程協調和執行，使用標記位控制流程方向
"""

import logging
from datetime import datetime
from typing import Dict, Any

from .simplified_state_machine import SimplifiedStateMachine
from .state_flow_controller import StateFlowController


# 設置日誌
logger = logging.getLogger(__name__)


class LinearFlowExecutor:
    """線性流程執行器 - 高層次的流程協調和執行"""
    
    def __init__(self):
        """初始化線性流程執行器"""
        self.state_machine = SimplifiedStateMachine()
        self.flow_controller = StateFlowController()
        logger.info("線性流程執行器初始化完成")
    
    async def execute_linear_flow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行線性流程 - 簡化分支邏輯
        
        Args:
            context: 處理上下文
            
        Returns:
            處理結果
        """
        session_id = context.get("session_id", "unknown")
        logger.info(f"開始執行 DSM 線性流程 - 會話: {session_id}")
        
        # 使用簡化狀態機執行流程
        result = await self.state_machine.execute_simplified_flow(context, self.flow_controller)
        
        logger.info(f"DSM 線性流程執行完成 - 會話: {session_id}")
        return result
    
    async def execute_single_state(self, state_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行單個狀態
        
        Args:
            state_name: 狀態名稱
            context: 處理上下文
            
        Returns:
            處理結果
        """
        session_id = context.get("session_id", "unknown")
        logger.info(f"執行單個狀態: {state_name} - 會話: {session_id}")
        
        try:
            # 根據狀態名稱執行對應的處理
            if state_name == "OnReceiveMsg":
                result = await self.flow_controller.receive_msg(context)
            elif state_name == "OnResponseMsg":
                result = await self.flow_controller.response_msg(context)
            elif state_name == "OnGenFunnelChat":
                result = await self.flow_controller.gen_funnel_chat(context)
            elif state_name == "OnGenMDContent":
                result = await self.flow_controller.gen_md_content(context)
            elif state_name == "OnDataQuery":
                result = await self.flow_controller.data_query(context)
            elif state_name == "OnQueriedDataProcessing":
                result = await self.flow_controller.queried_data_processing(context)
            elif state_name == "OnSendFront":
                result = await self.flow_controller.send_front(context)
            elif state_name == "OnWaitMsg":
                result = await self.flow_controller.wait_msg(context)
            else:
                raise ValueError(f"未知狀態: {state_name}")
            
            logger.info(f"單個狀態 {state_name} 執行完成 - 會話: {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"執行單個狀態 {state_name} 失敗: {e}")
            return {
                **context,
                "error": str(e),
                "error_state": state_name,
                f"{state_name.lower()}_completed": False
            }
    
    def get_flow_status(self) -> Dict[str, Any]:
        """獲取流程狀態信息"""
        return {
            "executor_initialized": True,
            "state_machine_status": self.state_machine.get_machine_status(),
            "flow_controller_initialized": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_flow(self):
        """重置流程"""
        self.state_machine.reset_state_machine()
        logger.info("線性流程已重置")
    
    def get_available_states(self) -> list[str]:
        """獲取可用的狀態列表"""
        return [
            "OnReceiveMsg",
            "OnResponseMsg",
            "OnGenFunnelChat",
            "OnGenMDContent",
            "OnDataQuery",
            "OnQueriedDataProcessing",
            "OnSendFront",
            "OnWaitMsg"
        ]
    
    def validate_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證上下文數據的完整性
        
        Args:
            context: 處理上下文
            
        Returns:
            驗證結果
        """
        validation_result = {
            "is_valid": True,
            "missing_fields": [],
            "warnings": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # 檢查必需字段
        required_fields = ["session_id"]
        for field in required_fields:
            if field not in context or not context[field]:
                validation_result["missing_fields"].append(field)
                validation_result["is_valid"] = False
        
        # 檢查建議字段
        suggested_fields = ["user_message"]
        for field in suggested_fields:
            if field not in context:
                validation_result["warnings"].append(f"建議提供字段: {field}")
        
        # 如果缺少必需字段，設置默認值
        if not validation_result["is_valid"]:
            if "session_id" not in context or not context["session_id"]:
                context["session_id"] = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                validation_result["warnings"].append("已自動生成 session_id")
                validation_result["is_valid"] = True
        
        return validation_result


# 導出主要類別
__all__ = ['LinearFlowExecutor']
