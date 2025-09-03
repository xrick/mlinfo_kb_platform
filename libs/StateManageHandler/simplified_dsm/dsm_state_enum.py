"""
DSM 狀態機的狀態枚舉定義
保持原有的 8 個狀態，實現簡單的線性流程和清晰的職責分工
"""

from enum import Enum
from typing import Dict, Any


class DSMState(Enum):
    """DSM 狀態機的 8 個狀態（保持原有數量）"""
    ON_RECEIVE_MSG = "OnReceiveMsg"                    # 接收消息
    ON_RESPONSE_MSG = "OnResponseMsg"                  # 回應消息
    ON_GEN_FUNNEL_CHAT = "OnGenFunnelChat"            # 生成漏斗對話
    ON_GEN_MD_CONTENT = "OnGenMDContent"              # 生成 Markdown 內容
    ON_DATA_QUERY = "OnDataQuery"                      # 執行數據查詢
    ON_QUERIED_DATA_PROCESSING = "OnQueriedDataProcessing"  # 處理查詢數據
    ON_SEND_FRONT = "OnSendFront"                      # 發送到前端
    ON_WAIT_MSG = "OnWaitMsg"                          # 等待下一個消息


class DSMStateInfo:
    """DSM 狀態信息類別，提供狀態的詳細信息"""
    
    @staticmethod
    def get_state_info() -> Dict[DSMState, Dict[str, Any]]:
        """獲取所有狀態的詳細信息"""
        return {
            DSMState.ON_RECEIVE_MSG: {
                "state_name": "接收消息",
                "description": "接收和解析用戶消息，提取關鍵詞和意圖",
                "execution_order": 1,
                "main_responsibility": "消息接收和意圖識別"
            },
            DSMState.ON_RESPONSE_MSG: {
                "state_name": "回應消息",
                "description": "根據流程方向生成回應和準備數據處理",
                "execution_order": 2,
                "main_responsibility": "回應生成和流程準備"
            },
            DSMState.ON_GEN_FUNNEL_CHAT: {
                "state_name": "生成漏斗對話",
                "description": "生成漏斗對話引導，收集用戶需求",
                "execution_order": 3,
                "main_responsibility": "需求收集引導"
            },
            DSMState.ON_GEN_MD_CONTENT: {
                "state_name": "生成 Markdown 內容",
                "description": "根據回應類型生成相應的 Markdown 內容",
                "execution_order": 4,
                "main_responsibility": "內容生成"
            },
            DSMState.ON_DATA_QUERY: {
                "state_name": "執行數據查詢",
                "description": "執行內部數據查詢，獲取相關信息",
                "execution_order": 5,
                "main_responsibility": "數據查詢"
            },
            DSMState.ON_QUERIED_DATA_PROCESSING: {
                "state_name": "處理查詢數據",
                "description": "處理查詢結果，更新 Markdown 內容",
                "execution_order": 6,
                "main_responsibility": "數據處理和內容更新"
            },
            DSMState.ON_SEND_FRONT: {
                "state_name": "發送到前端",
                "description": "將處理後的數據發送到前端瀏覽器",
                "execution_order": 7,
                "main_responsibility": "前端數據發送"
            },
            DSMState.ON_WAIT_MSG: {
                "state_name": "等待下一個消息",
                "description": "準備接收下一個用戶消息",
                "execution_order": 8,
                "main_responsibility": "消息等待準備"
            }
        }
    
    @staticmethod
    def get_state_by_order(order: int) -> DSMState:
        """根據執行順序獲取狀態"""
        state_info = DSMStateInfo.get_state_info()
        for state, info in state_info.items():
            if info["execution_order"] == order:
                return state
        raise ValueError(f"無效的執行順序: {order}")
    
    @staticmethod
    def get_next_state(current_state: DSMState) -> DSMState:
        """獲取下一個狀態（線性流程）"""
        state_info = DSMStateInfo.get_state_info()
        current_order = state_info[current_state]["execution_order"]
        
        if current_order == 8:  # 最後一個狀態
            return DSMState.ON_RECEIVE_MSG  # 循環回到第一個狀態
        else:
            return DSMStateInfo.get_state_by_order(current_order + 1)
    
    @staticmethod
    def get_linear_execution_order() -> list[DSMState]:
        """獲取線性執行順序"""
        return [
            DSMState.ON_RECEIVE_MSG,
            DSMState.ON_RESPONSE_MSG,
            DSMState.ON_GEN_FUNNEL_CHAT,
            DSMState.ON_GEN_MD_CONTENT,
            DSMState.ON_DATA_QUERY,
            DSMState.ON_QUERIED_DATA_PROCESSING,
            DSMState.ON_SEND_FRONT,
            DSMState.ON_WAIT_MSG
        ]


# 導出主要類別
__all__ = ['DSMState', 'DSMStateInfo']
