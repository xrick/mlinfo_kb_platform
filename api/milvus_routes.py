#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Milvus Collection Viewer API 路由
提供 Milvus 資料庫管理和查看的 RESTful API
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional

# 導入 Milvus 服務
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from libs.services.milvus_service import MilvusService

# 設定日誌
logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter()

# 全域 Milvus 服務實例
milvus_service = None


def get_milvus_service() -> MilvusService:
    """獲取 Milvus 服務實例（單例模式）"""
    global milvus_service
    if milvus_service is None:
        milvus_service = MilvusService()
    return milvus_service


@router.get("/health")
async def milvus_health_check():
    """Milvus 健康檢查端點"""
    try:
        service = get_milvus_service()
        is_connected = service.connect()
        
        if is_connected:
            service.disconnect()  # 檢查完畢後斷開連接
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "status": "healthy",
                    "message": "Milvus 服務連接正常"
                }
            )
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "status": "unhealthy", 
                    "message": "無法連接到 Milvus 服務"
                }
            )
    except Exception as e:
        logger.error(f"Milvus 健康檢查失敗: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "status": "error",
                "message": f"健康檢查失敗: {str(e)}"
            }
        )


@router.get("/databases")
async def get_databases():
    """獲取所有可用的資料庫
    
    Returns:
        JSONResponse: 包含資料庫列表的響應
    """
    try:
        service = get_milvus_service()
        
        with service:  # 使用上下文管理器自動處理連接
            databases = service.get_databases()
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "databases": databases,
                        "default_database": "default"
                    }
                }
            )
    except Exception as e:
        logger.error(f"獲取資料庫列表失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取資料庫列表失敗: {str(e)}"
        )


@router.get("/collections")
async def get_collections():
    """獲取當前資料庫中的所有集合
    
    Returns:
        JSONResponse: 包含集合列表和基本統計的響應
    """
    try:
        service = get_milvus_service()
        
        with service:
            collections = service.get_collections()
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "collections": collections,
                        "total_count": len(collections)
                    }
                }
            )
    except Exception as e:
        logger.error(f"獲取集合列表失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取集合列表失敗: {str(e)}"
        )


@router.get("/collection/{collection_name}/schema")
async def get_collection_schema(collection_name: str):
    """獲取指定集合的 Schema 資訊
    
    Args:
        collection_name: 集合名稱
        
    Returns:
        JSONResponse: 包含 Schema 詳細資訊的響應
    """
    try:
        service = get_milvus_service()
        
        with service:
            schema_info = service.get_collection_schema(collection_name)
            
            if schema_info is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"集合 '{collection_name}' 不存在或無法讀取"
                )
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": schema_info
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取集合 Schema 失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取集合 Schema 失敗: {str(e)}"
        )


@router.get("/collection/{collection_name}/data")
async def get_collection_data(
    collection_name: str,
    page: int = Query(1, ge=1, description="頁碼，從 1 開始"),
    page_size: int = Query(50, ge=1, le=500, description="每頁資料數量，最大 500")
):
    """獲取集合中的資料（分頁）
    
    Args:
        collection_name: 集合名稱
        page: 頁碼（從 1 開始）
        page_size: 每頁資料數量
        
    Returns:
        JSONResponse: 包含分頁資料的響應
    """
    try:
        service = get_milvus_service()
        
        # 計算偏移量
        offset = (page - 1) * page_size
        
        with service:
            data_result = service.get_collection_data(
                collection_name=collection_name,
                limit=page_size,
                offset=offset
            )
            
            if "error" in data_result:
                raise HTTPException(
                    status_code=500,
                    detail=f"讀取資料失敗: {data_result['error']}"
                )
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "collection_name": collection_name,
                        "records": data_result["data"],
                        "pagination": {
                            "current_page": page,
                            "page_size": page_size,
                            "total_records": data_result["total"],
                            "has_more": data_result["has_more"],
                            "total_pages": (data_result["total"] + page_size - 1) // page_size
                        },
                        "vector_fields": data_result.get("vector_fields", [])
                    }
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取集合資料失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取集合資料失敗: {str(e)}"
        )


@router.get("/collection/{collection_name}/statistics")
async def get_collection_statistics(collection_name: str):
    """獲取集合的詳細統計資訊
    
    Args:
        collection_name: 集合名稱
        
    Returns:
        JSONResponse: 包含統計資訊的響應
    """
    try:
        service = get_milvus_service()
        
        with service:
            stats = service.get_collection_statistics(collection_name)
            
            if "error" in stats:
                raise HTTPException(
                    status_code=404 if "不存在" in stats["error"] else 500,
                    detail=stats["error"]
                )
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": stats
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取集合統計資訊失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取集合統計資訊失敗: {str(e)}"
        )


@router.get("/connection/status")
async def get_connection_status():
    """獲取當前 Milvus 連接狀態
    
    Returns:
        JSONResponse: 連接狀態資訊
    """
    try:
        service = get_milvus_service()
        
        # 測試連接
        can_connect = service.connect()
        if can_connect:
            service.disconnect()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "can_connect": can_connect,
                    "host": service.host,
                    "port": service.port,
                    "connection_alias": service.connection_alias
                }
            }
        )
    except Exception as e:
        logger.error(f"檢查連接狀態失敗: {e}")
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "can_connect": False,
                    "error": str(e),
                    "host": service.host if 'service' in locals() else "unknown",
                    "port": service.port if 'service' in locals() else "unknown"
                }
            }
        )


# 應用程式關閉時清理資源
@router.on_event("shutdown")
async def cleanup_milvus_service():
    """應用程式關閉時清理 Milvus 服務資源"""
    global milvus_service
    if milvus_service:
        try:
            milvus_service.disconnect()
            logger.info("Milvus 服務已清理")
        except Exception as e:
            logger.warning(f"清理 Milvus 服務時發生錯誤: {e}")


# 添加路由標籤和描述
router.tags = ["Milvus Viewer"]