#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD API 路由
"""

import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# 添加項目根目錄到路徑
import sys
from pathlib import Path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from libs.mgfd_cursor import MGFDDialogueManager, create_notebook_sales_graph

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter()

# 初始化MGFD組件
mgfd_state_machine = create_notebook_sales_graph()
mgfd_dialogue_manager = mgfd_state_machine.dialogue_manager

# Pydantic模型
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str
    action_type: str
    filled_slots: Dict[str, Any]
    current_stage: str
    recommendations: Optional[list] = None

class SessionRequest(BaseModel):
    user_id: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    message: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_mgfd(request: ChatRequest):
    """
    與MGFD系統對話
    
    Args:
        request: 聊天請求
        
    Returns:
        聊天回應
    """
    try:
        # 檢查會話ID
        session_id = request.session_id
        if not session_id:
            # 創建新會話
            session_id = mgfd_dialogue_manager.create_session()
            logger.info(f"創建新會話: {session_id}")
        
        # 處理用戶輸入
        result = mgfd_state_machine.process_user_input(session_id, request.message)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # 構建回應
        response = ChatResponse(
            session_id=result["session_id"],
            response=result["response"],
            action_type=result["action_type"],
            filled_slots=result["filled_slots"],
            current_stage=result["current_stage"],
            recommendations=result.get("recommendations")
        )
        
        logger.info(f"會話 {session_id} 處理完成，行動類型: {result['action_type']}")
        return response
        
    except Exception as e:
        logger.error(f"處理聊天請求失敗: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務錯誤: {str(e)}")

@router.post("/chat/stream")
async def chat_with_mgfd_stream(request: ChatRequest):
    """
    與MGFD系統對話（串流版本）
    
    Args:
        request: 聊天請求
        
    Returns:
        串流聊天回應
    """
    async def generate_response():
        try:
            # 檢查會話ID
            session_id = request.session_id
            if not session_id:
                # 創建新會話
                session_id = mgfd_dialogue_manager.create_session()
                logger.info(f"創建新會話: {session_id}")
            
            # 處理用戶輸入
            result = mgfd_state_machine.process_user_input(session_id, request.message)
            
            if "error" in result:
                error_response = {
                    "error": result["error"],
                    "session_id": session_id
                }
                yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"
                return
            
            # 串流返回結果
            response_data = {
                "session_id": result["session_id"],
                "response": result["response"],
                "action_type": result["action_type"],
                "filled_slots": result["filled_slots"],
                "current_stage": result["current_stage"],
                "recommendations": result.get("recommendations")
            }
            
            yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"處理串流聊天請求失敗: {e}")
            error_response = {
                "error": f"內部服務錯誤: {str(e)}",
                "session_id": request.session_id or "unknown"
            }
            yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@router.post("/session/create", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    """
    創建新的MGFD會話
    
    Args:
        request: 會話創建請求
        
    Returns:
        會話創建回應
    """
    try:
        session_id = mgfd_dialogue_manager.create_session(request.user_id)
        
        welcome_message = (
            "您好！我是您的筆記型電腦購物助手。"
            "讓我幫您找到最適合的筆電。"
            "請告訴我您主要會用這台筆電做什麼？"
        )
        
        response = SessionResponse(
            session_id=session_id,
            message=welcome_message
        )
        
        logger.info(f"創建新會話: {session_id}")
        return response
        
    except Exception as e:
        logger.error(f"創建會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建會話失敗: {str(e)}")

@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """
    獲取會話信息
    
    Args:
        session_id: 會話ID
        
    Returns:
        會話信息
    """
    try:
        session = mgfd_dialogue_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="會話不存在")
        
        return {
            "session_id": session_id,
            "current_stage": session["current_stage"],
            "filled_slots": session["filled_slots"],
            "chat_history_length": len(session["chat_history"]),
            "created_at": session["created_at"].isoformat(),
            "last_updated": session["last_updated"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取會話信息失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取會話信息失敗: {str(e)}")

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    刪除會話
    
    Args:
        session_id: 會話ID
        
    Returns:
        刪除結果
    """
    try:
        session = mgfd_dialogue_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="會話不存在")
        
        # 從活躍會話中移除
        if session_id in mgfd_dialogue_manager.active_sessions:
            del mgfd_dialogue_manager.active_sessions[session_id]
        
        logger.info(f"刪除會話: {session_id}")
        return {"message": "會話已刪除", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"刪除會話失敗: {str(e)}")

@router.get("/stats")
async def get_mgfd_stats():
    """
    獲取MGFD系統統計信息
    
    Returns:
        系統統計信息
    """
    try:
        stats = mgfd_dialogue_manager.get_session_stats()
        return {
            "system_stats": stats,
            "message": "MGFD系統運行正常"
        }
        
    except Exception as e:
        logger.error(f"獲取統計信息失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取統計信息失敗: {str(e)}")

@router.post("/cleanup")
async def cleanup_expired_sessions():
    """
    清理過期會話
    
    Returns:
        清理結果
    """
    try:
        before_count = len(mgfd_dialogue_manager.active_sessions)
        mgfd_dialogue_manager.cleanup_expired_sessions()
        after_count = len(mgfd_dialogue_manager.active_sessions)
        
        cleaned_count = before_count - after_count
        
        return {
            "message": f"清理完成，清理了 {cleaned_count} 個過期會話",
            "before_count": before_count,
            "after_count": after_count,
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        logger.error(f"清理過期會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"清理過期會話失敗: {str(e)}")

@router.get("/products")
async def get_available_products():
    """
    獲取可用產品列表
    
    Returns:
        產品列表
    """
    try:
        products = mgfd_dialogue_manager.notebook_kb.products
        return {
            "products": products,
            "total_count": len(products)
        }
        
    except Exception as e:
        logger.error(f"獲取產品列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取產品列表失敗: {str(e)}")

@router.get("/products/search")
async def search_products(query: str):
    """
    搜索產品
    
    Args:
        query: 搜索查詢
        
    Returns:
        搜索結果
    """
    try:
        results = mgfd_dialogue_manager.notebook_kb.semantic_search(query)
        return {
            "query": query,
            "results": results,
            "total_count": len(results)
        }
        
    except Exception as e:
        logger.error(f"搜索產品失敗: {e}")
        raise HTTPException(status_code=500, detail=f"搜索產品失敗: {str(e)}")
