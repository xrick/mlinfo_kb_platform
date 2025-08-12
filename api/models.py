"""
FastAPI Pydantic模型
定義MGFD系統的請求和回應模型
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class APIVersion(str, Enum):
    """API版本枚舉"""
    v1 = "v1"
    v2 = "v2"


class ChatRequest(BaseModel):
    """聊天請求模型"""
    message: str = Field(..., description="用戶消息", min_length=1, max_length=1000)
    session_id: Optional[str] = Field(None, description="會話ID")
    stream: bool = Field(False, description="是否使用串流回應")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "我想買一台筆電",
                "session_id": "test_session_001",
                "stream": False
            }
        }


class ChatResponse(BaseModel):
    """聊天回應模型"""
    success: bool = Field(..., description="請求是否成功")
    response: str = Field(..., description="系統回應")
    session_id: str = Field(..., description="會話ID")
    timestamp: str = Field(..., description="時間戳")
    action_type: str = Field(..., description="動作類型")
    filled_slots: Dict[str, Any] = Field(default_factory=dict, description="已填寫的槽位")
    dialogue_stage: str = Field(..., description="對話階段")
    suggestions: Optional[List[str]] = Field(None, description="建議選項")
    recommendations: Optional[List[Dict[str, Any]]] = Field(None, description="推薦產品")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "response": "您好！我是您的筆電購物助手。請告訴我您主要會用這台筆電做什麼？",
                "session_id": "test_session_001",
                "timestamp": "2025-01-27T19:30:00",
                "action_type": "ELICIT_SLOT",
                "filled_slots": {},
                "dialogue_stage": "awareness"
            }
        }


class SessionState(BaseModel):
    """會話狀態模型"""
    session_id: str = Field(..., description="會話ID")
    current_stage: str = Field(..., description="當前階段")
    filled_slots: Dict[str, Any] = Field(default_factory=dict, description="已填寫的槽位")
    chat_history: List[Dict[str, Any]] = Field(default_factory=list, description="對話歷史")
    created_at: str = Field(..., description="創建時間")
    last_updated: str = Field(..., description="最後更新時間")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "test_session_001",
                "current_stage": "awareness",
                "filled_slots": {"usage_purpose": "gaming"},
                "chat_history": [
                    {"role": "user", "content": "我想買筆電", "timestamp": "2025-01-27T19:30:00"},
                    {"role": "assistant", "content": "請告訴我用途", "timestamp": "2025-01-27T19:30:01"}
                ],
                "created_at": "2025-01-27T19:30:00",
                "last_updated": "2025-01-27T19:30:01"
            }
        }


class ChatHistoryResponse(BaseModel):
    """對話歷史回應模型"""
    success: bool = Field(..., description="請求是否成功")
    chat_history: List[Dict[str, Any]] = Field(default_factory=list, description="對話歷史")
    session_id: str = Field(..., description="會話ID")
    count: int = Field(..., description="歷史記錄數量")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "chat_history": [
                    {"role": "user", "content": "我想買筆電", "timestamp": "2025-01-27T19:30:00"},
                    {"role": "assistant", "content": "請告訴我用途", "timestamp": "2025-01-27T19:30:01"}
                ],
                "session_id": "test_session_001",
                "count": 2
            }
        }


class SystemStatus(BaseModel):
    """系統狀態模型"""
    success: bool = Field(..., description="請求是否成功")
    system_status: Dict[str, Any] = Field(..., description="系統狀態信息")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "system_status": {
                    "redis": "connected",
                    "llm": "available",
                    "modules": {
                        "user_input_handler": "active",
                        "dialogue_manager": "active",
                        "action_executor": "active",
                        "response_generator": "active",
                        "state_manager": "active"
                    },
                    "cleaned_sessions": 0,
                    "timestamp": "2025-01-27T19:30:00"
                }
            }
        }


class HealthResponse(BaseModel):
    """健康檢查回應模型"""
    status: str = Field(..., description="系統狀態")
    timestamp: str = Field(..., description="時間戳")
    services: Dict[str, str] = Field(..., description="服務狀態")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-01-27T19:30:00",
                "services": {
                    "redis": "connected",
                    "mgfd_system": "initialized"
                }
            }
        }


class ErrorResponse(BaseModel):
    """錯誤回應模型"""
    success: bool = Field(False, description="請求失敗")
    error: str = Field(..., description="錯誤信息")
    timestamp: str = Field(..., description="時間戳")
    details: Optional[str] = Field(None, description="詳細錯誤信息")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": "系統內部錯誤",
                "timestamp": "2025-01-27T19:30:00",
                "details": "具體錯誤詳情"
            }
        }


class StreamResponse(BaseModel):
    """串流回應模型"""
    type: str = Field(..., description="回應類型")
    data: Dict[str, Any] = Field(..., description="回應數據")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "message",
                "data": {
                    "content": "正在處理您的請求...",
                    "session_id": "test_session_001"
                }
            }
        }


class ResetSessionRequest(BaseModel):
    """重置會話請求模型"""
    session_id: str = Field(..., description="會話ID")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "test_session_001"
            }
        }


class ResetSessionResponse(BaseModel):
    """重置會話回應模型"""
    success: bool = Field(..., description="請求是否成功")
    message: str = Field(..., description="回應消息")
    session_id: str = Field(..., description="會話ID")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "會話重置成功",
                "session_id": "test_session_001"
            }
        }


# 用於API文檔的標籤
tags_metadata = [
    {
        "name": "chat",
        "description": "聊天相關操作，包括發送消息、獲取回應等",
    },
    {
        "name": "session",
        "description": "會話管理操作，包括獲取狀態、重置會話等",
    },
    {
        "name": "system",
        "description": "系統管理操作，包括健康檢查、狀態監控等",
    },
]
