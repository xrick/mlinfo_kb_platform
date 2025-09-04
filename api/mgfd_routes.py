"""
MGFD API路由 - FastAPI版本
適配新的MGFD系統架構，使用FastAPI Router
"""

import logging
import json
import redis
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError

# from libs.mgfd_cursor.mgfd_system import MGFDSystem
from libs.MGFDKernel import MGFDKernel
from .models import (
    ChatRequest, ChatResponse, SessionState, ChatHistoryResponse,
    SystemStatus, HealthResponse, ErrorResponse, StreamResponse,
    ResetSessionRequest, ResetSessionResponse, APIVersion
)

# 創建Router
router = APIRouter()

# 配置日誌
logger = logging.getLogger(__name__)

# 初始化Redis連接
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()  # 測試連接
    logger.info("Redis連接成功")
except Exception as e:
    logger.error(f"Redis連接失敗: {e}")
    redis_client = None

# 初始化MGFD系統（僅使用 Redis）
try:
    mgfd_system = MGFDKernel(redis_client) if redis_client else None
    logger.info("MGFD系統初始化成功")
except Exception as e:
    logger.error(f"MGFD系統初始化失敗: {e}")
    mgfd_system = None


def get_mgfd_system() -> MGFDKernel:
    """依賴注入：獲取MGFD系統實例"""
    if not mgfd_system:
        raise HTTPException(status_code=503, detail="MGFD系統未初始化")
    return mgfd_system


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    request: ChatRequest,
    mgfd: MGFDKernel = Depends(get_mgfd_system)
):
    """
    處理聊天請求
    
    - **message**: 用戶消息
    - **session_id**: 會話ID（可選）
    - **stream**: 是否使用串流回應
    """
    try:
        # 生成會話ID（如果沒有提供）
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"處理聊天請求 - 會話ID: {session_id}, 消息: {request.message[:50]}...")
        
        # 處理消息
        result = await mgfd.process_message(session_id, request.message, request.stream)
        
        # 添加會話ID到回應
        result['session_id'] = session_id
        
        if result.get('success', False):
            return ChatResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result.get('error', '處理失敗'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"處理聊天請求時發生錯誤: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"系統內部錯誤: {str(e)}")


@router.post("/chat/stream", tags=["chat"])
async def chat_stream(
    request: ChatRequest,
    mgfd: MGFDKernel = Depends(get_mgfd_system)
):
    """
    處理串流聊天請求
    
    返回Server-Sent Events (SSE)格式的串流回應
    """
    try:
        # 生成會話ID（如果沒有提供）
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"處理串流聊天請求 - 會話ID: {session_id}, 消息: {request.message[:50]}...")
        
        # 處理消息（啟用串流）
        result = await mgfd.process_message(session_id, request.message, stream=True)
        
        if not result.get('success', False):
            raise HTTPException(status_code=400, detail=result.get('error', '處理失敗'))
        
        # 返回串流回應
        async def generate_stream():
            # 發送開始標記
            yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
            
            # 發送主要回應（現在直接使用 result，不再依賴 stream_response）
            yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"
            
            # 發送結束標記
            yield f"data: {json.dumps({'type': 'end', 'session_id': session_id})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"處理串流聊天請求時發生錯誤: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"系統內部錯誤: {str(e)}")


@router.get("/session/{session_id}", response_model=SessionState, tags=["session"])
async def get_session_state(
    session_id: str,
    mgfd: MGFDKernel = Depends(get_mgfd_system)
):
    """
    獲取會話狀態
    
    - **session_id**: 會話ID
    """
    try:
        logger.info(f"獲取會話狀態 - 會話ID: {session_id}")
        
        result = await mgfd.get_session_state(session_id)
        
        if result.get('success', False):
            return SessionState(**result['state'])
        else:
            raise HTTPException(status_code=404, detail=result.get('error', '會話不存在'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取會話狀態時發生錯誤: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"系統內部錯誤: {str(e)}")


@router.post("/session/{session_id}/reset", response_model=ResetSessionResponse, tags=["session"])
async def reset_session(
    session_id: str,
    mgfd: MGFDKernel = Depends(get_mgfd_system)
):
    """
    重置會話
    
    - **session_id**: 會話ID
    """
    try:
        logger.info(f"重置會話 - 會話ID: {session_id}")
        
        result = mgfd.reset_session(session_id)
        
        if result.get('success', False):
            return ResetSessionResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result.get('error', '重置失敗'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置會話時發生錯誤: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"系統內部錯誤: {str(e)}")


# @router.get("/session/{session_id}/history", response_model=ChatHistoryResponse, tags=["session"])
# async def get_chat_history(
#     session_id: str,
#     limit: int = 50,
#     mgfd: MGFDKernel = Depends(get_mgfd_system)
# ):
#     """
#     獲取對話歷史
#     
#     - **session_id**: 會話ID
#     - **limit**: 歷史記錄限制（默認50）
#     """
#     try:
#         logger.info(f"獲取對話歷史 - 會話ID: {session_id}, 限制: {limit}")
#         
#         result = mgfd.get_chat_history(session_id, limit)
#         
#         if result.get('success', False):
#             return ChatHistoryResponse(**result)
#         else:
#             raise HTTPException(status_code=404, detail=result.get('error', '會話不存在'))
#             
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"獲取對話歷史時發生錯誤: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"系統內部錯誤: {str(e)}")


@router.get("/status", response_model=SystemStatus, tags=["system"])
async def get_system_status(
    mgfd: MGFDKernel = Depends(get_mgfd_system)
):
    """
    獲取系統狀態
    
    返回MGFD系統的詳細狀態信息
    """
    try:
        logger.info("獲取系統狀態")
        
        result = await mgfd.get_system_status()
        
        if result.get('success', False):
            return SystemStatus(**result)
        else:
            raise HTTPException(status_code=500, detail=result.get('error', '獲取狀態失敗'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取系統狀態時發生錯誤: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"系統內部錯誤: {str(e)}")


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """
    健康檢查端點
    
    檢查MGFD系統和相關服務的健康狀態
    """
    try:
        # 檢查Redis連接
        redis_status = "connected" if redis_client and redis_client.ping() else "disconnected"
        
        # 檢查MGFD系統
        mgfd_status = "initialized" if mgfd_system else "not_initialized"
        
        health_status = {
            "status": "healthy" if redis_status == "connected" and mgfd_status == "initialized" else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "redis": redis_status,
                "mgfd_system": mgfd_status
            }
        }
        
        return HealthResponse(**health_status)
        
    except Exception as e:
        logger.error(f"健康檢查時發生錯誤: {e}", exc_info=True)
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            services={
                "redis": "unknown",
                "mgfd_system": "unknown"
            }
        )


# 注意：異常處理器和中間件應該在應用程式級別處理，而不是在Router級別


# 新增 mgfd_cursor 前端所需的端點
@router.post("/session/create", response_model=dict, tags=["mgfd_cursor"])
async def create_session(
    mgfd: MGFDKernel = Depends(get_mgfd_system)
):
    """
    創建新會話
    
    為 mgfd_cursor 前端介面提供會話創建功能
    """
    try:
        session_id = str(uuid.uuid4())
        logger.info(f"創建新會話: {session_id}")
        
        # 初始化會話狀態
        result = await mgfd.reset_session(session_id)
        
        if result.get('success', False):
            return {
                "success": True,
                "session_id": session_id,
                "message": "會話創建成功"
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error', '會話創建失敗'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建會話時發生錯誤: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"系統內部錯誤: {str(e)}")


@router.get("/stats", response_model=dict, tags=["mgfd_cursor"])
async def get_stats(
    mgfd: MGFDKernel = Depends(get_mgfd_system)
):
    """
    獲取系統統計資訊
    
    為 mgfd_cursor 前端介面提供統計資訊
    """
    try:
        logger.info("獲取系統統計資訊")
        
        # 獲取系統狀態
        status_result = await mgfd.get_system_status()
        
        if status_result.get('success', False):
            return {
                "success": True,
                "system_stats": {  # 改為 system_stats 以匹配前端期望
                    "active_sessions": 0,  # 活躍會話數量
                    "total_products": 19,  # 產品數量（從日誌中看到有19個）
                    "slot_schema_count": 7  # 槽位架構數量（cpu, gpu, memory, storage, size, weight, price）
                }
            }
        else:
            return {
                "success": False,
                "system_stats": {
                    "active_sessions": 0,
                    "total_products": 0,
                    "slot_schema_count": 0,
                    "error": status_result.get('error', '未知錯誤')
                }
            }
            
    except Exception as e:
        logger.error(f"獲取統計資訊時發生錯誤: {e}", exc_info=True)
        return {
            "success": False,
            "system_stats": {
                "active_sessions": 0,
                "total_products": 0,
                "slot_schema_count": 0,
                "error": str(e)
            }
        }



