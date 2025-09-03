"""
簡化 DSM 系統測試檔案
測試 DSM 簡化狀態機、流程控制器和線性流程執行器的功能
"""

import asyncio
import logging
from datetime import datetime

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 導入簡化 DSM 系統
from simplified_dsm import (
    DSMState, 
    DSMStateInfo, 
    SimplifiedStateMachine, 
    StateFlowController, 
    LinearFlowExecutor
)

from action_hub import FlowExecutor, FlowValidator


async def test_dsm_state_enum():
    """測試 DSM 狀態枚舉"""
    logger.info("=== 測試 DSM 狀態枚舉 ===")
    
    # 測試狀態枚舉
    assert len(DSMState) == 8, f"期望 8 個狀態，實際 {len(DSMState)}"
    logger.info(f"狀態枚舉測試通過，共 {len(DSMState)} 個狀態")
    
    # 測試狀態信息
    state_info = DSMStateInfo.get_state_info()
    assert len(state_info) == 8, f"期望 8 個狀態信息，實際 {len(state_info)}"
    logger.info("狀態信息測試通過")
    
    # 測試線性執行順序
    linear_order = DSMStateInfo.get_linear_execution_order()
    assert len(linear_order) == 8, f"期望 8 個執行順序，實際 {len(linear_order)}"
    logger.info("線性執行順序測試通過")
    
    logger.info("✅ DSM 狀態枚舉測試完成\n")


async def test_simplified_state_machine():
    """測試簡化狀態機"""
    logger.info("=== 測試簡化狀態機 ===")
    
    # 創建狀態機實例
    state_machine = SimplifiedStateMachine()
    
    # 測試狀態轉換
    transitions = state_machine.get_all_transitions()
    assert len(transitions) == 8, f"期望 8 個狀態轉換，實際 {len(transitions)}"
    logger.info("狀態轉換測試通過")
    
    # 測試狀態驗證
    assert state_machine.validate_transition(DSMState.ON_RECEIVE_MSG, DSMState.ON_RESPONSE_MSG), "狀態轉換驗證失敗"
    logger.info("狀態驗證測試通過")
    
    # 測試機器狀態
    machine_status = state_machine.get_machine_status()
    assert machine_status["machine_initialized"], "狀態機初始化檢查失敗"
    logger.info("機器狀態測試通過")
    
    logger.info("✅ 簡化狀態機測試完成\n")


async def test_state_flow_controller():
    """測試狀態流程控制器"""
    logger.info("=== 測試狀態流程控制器 ===")
    
    # 創建流程控制器實例
    flow_controller = StateFlowController()
    
    # 測試上下文驗證
    test_context = {
        "session_id": "test_session_001",
        "user_message": "你好，我想買一台筆電"
    }
    
    # 測試接收消息狀態
    result = await flow_controller.receive_msg(test_context)
    assert result["receive_msg_completed"], "接收消息狀態執行失敗"
    assert "keywords" in result, "關鍵詞提取失敗"
    assert "flow_direction" in result, "流程方向判斷失敗"
    logger.info("接收消息狀態測試通過")
    
    # 測試回應消息狀態
    result = await flow_controller.response_msg(result)
    assert result["response_msg_completed"], "回應消息狀態執行失敗"
    assert "response_type" in result, "回應類型生成失敗"
    logger.info("回應消息狀態測試通過")
    
    logger.info("✅ 狀態流程控制器測試完成\n")


async def test_linear_flow_executor():
    """測試線性流程執行器"""
    logger.info("=== 測試線性流程執行器 ===")
    
    # 創建線性流程執行器實例
    linear_executor = LinearFlowExecutor()
    
    # 測試流程狀態
    flow_status = linear_executor.get_flow_status()
    assert flow_status["executor_initialized"], "執行器初始化檢查失敗"
    logger.info("流程狀態測試通過")
    
    # 測試可用狀態
    available_states = linear_executor.get_available_states()
    assert len(available_states) == 8, f"期望 8 個可用狀態，實際 {len(available_states)}"
    logger.info("可用狀態測試通過")
    
    # 測試上下文驗證
    test_context = {"user_message": "測試消息"}
    validation_result = linear_executor.validate_context(test_context)
    assert validation_result["is_valid"], "上下文驗證失敗"
    assert "session_id" in test_context, "自動生成 session_id 失敗"
    logger.info("上下文驗證測試通過")
    
    logger.info("✅ 線性流程執行器測試完成\n")


async def test_flow_validator():
    """測試流程驗證器"""
    logger.info("=== 測試流程驗證器 ===")
    
    # 創建流程驗證器實例
    flow_validator = FlowValidator()
    
    # 測試基本驗證
    test_flow = {
        "flow_metadata": {"name": "test"},
        "states": {},
        "flow_transitions": {}
    }
    
    validation_result = flow_validator.validate(test_flow)
    assert not validation_result.is_valid, "基本驗證應該失敗"
    logger.info("基本驗證測試通過")
    
    logger.info("✅ 流程驗證器測試完成\n")


async def test_integration():
    """測試整合功能"""
    logger.info("=== 測試整合功能 ===")
    
    # 創建完整的 DSM 系統
    state_machine = SimplifiedStateMachine()
    flow_controller = StateFlowController()
    
    # 測試完整流程執行
    test_context = {
        "session_id": "integration_test_001",
        "user_message": "推薦一台適合工作的筆電"
    }
    
    try:
        result = await state_machine.execute_simplified_flow(test_context, flow_controller)
        assert result["flow_completed"], "完整流程執行失敗"
        assert result["successful_states"] > 0, "沒有成功執行的狀態"
        logger.info(f"整合測試通過，成功執行 {result['successful_states']} 個狀態")
        
    except Exception as e:
        logger.error(f"整合測試失敗: {e}")
        raise
    
    logger.info("✅ 整合功能測試完成\n")


async def main():
    """主測試函數"""
    logger.info("🚀 開始測試簡化 DSM 系統")
    start_time = datetime.now()
    
    try:
        # 執行所有測試
        await test_dsm_state_enum()
        await test_simplified_state_machine()
        await test_state_flow_controller()
        await test_linear_flow_executor()
        await test_flow_validator()
        await test_integration()
        
        # 測試完成
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("🎉 所有測試完成！")
        logger.info(f"⏱️  總測試時間: {duration:.2f} 秒")
        logger.info("✅ 簡化 DSM 系統功能正常")
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        raise


if __name__ == "__main__":
    # 運行測試
    asyncio.run(main())
