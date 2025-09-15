# api/import_data_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import re

from .csv_processor2 import CSVProcessor2
from .db_ingestor import DBIngestor

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class ProcessRequest(BaseModel):
    text_content: str
    custom_rules: Optional[Dict] = None
    temp_regex: Optional[List[str]] = None
    file_name: Optional[str] = None
    user_modeltype: Optional[str] = None

class ProcessResponse(BaseModel):
    status: str = "success"
    filename: Optional[str] = None
    stats: Optional[Dict] = None
    preview: Optional[List[Dict]] = None
    data: Optional[List[Dict]] = None  # 保留用於後續處理
    require_modeltype_input: bool = False

class IngestRequest(BaseModel):
    data: List[Dict[str, str]]

class IngestResponse(BaseModel):
    success: bool
    message: str
    duckdb_rows_added: int
    milvus_entities_added: int

def validate_regex_patterns(patterns):
    """Validate regex patterns for safety"""
    if not patterns:
        return True
    
    for pattern in patterns:
        if not pattern.strip():
            continue
        try:
            re.compile(pattern)
        except re.error:
            return False
    return True

@router.post("/process", response_model=ProcessResponse, tags=["Import"])
def process_csv_content(request: ProcessRequest):
    """
    處理 CSV 內容並返回解析結果 (使用 CSVProcessor2 strategy pattern)
    支援三階段 modeltype 判斷：檔名→內容→用戶輸入
    """
    try:
        # 驗證輸入
        if not request.text_content.strip():
            raise HTTPException(status_code=400, detail="CSV content cannot be empty.")
        if request.temp_regex and not validate_regex_patterns(request.temp_regex):
            raise HTTPException(status_code=400, detail="Invalid regex patterns provided.")
        
        processor = CSVProcessor2()
        result = processor.process_csv_content(
            csv_content=request.text_content,
            custom_rules=request.custom_rules
        )
        
        # 三階段 modeltype 判斷
        modeltype = None
        # 1. 檔名
        if request.file_name:
            modeltype = processor.detect_modeltype(request.file_name, result)
        # 2. 內容
        if not modeltype:
            modeltype = processor.detect_modeltype("", result)
        # 3. 用戶輸入
        if not modeltype and request.user_modeltype:
            modeltype = request.user_modeltype.strip()
        
        # 若仍無法判斷，嘗試使用檔名作為預設值
        if not modeltype and request.file_name:
            base_name = re.sub(r'\.(csv|CSV)$', '', request.file_name)
            if base_name and 1 <= len(base_name) <= 15 and re.match(r'^[A-Za-z0-9_-]+$', base_name):
                modeltype = base_name
                logger.info(f"使用檔名作為預設 modeltype: {modeltype}")
        
        # 最後手段：要求前端輸入
        if not modeltype:
            # 即使需要輸入 modeltype，也要提供統計資料讓前端顯示
            stats = {
                "total_rows": len(result),
                "total_columns": len(result[0].keys()) if result else 0,
                "columns": list(result[0].keys()) if result else []
            }
            preview_data = result[:10] if result else []
            
            return ProcessResponse(
                require_modeltype_input=True, 
                data=result,
                filename=request.file_name,
                stats=stats,
                preview=preview_data
            )
        
        # 補齊所有資料的 modeltype 欄位
        for row in result:
            if isinstance(row, dict):
                row["modeltype"] = modeltype
        
        # 生成與原始 lcj_business_ai 相容的回應格式
        stats = {
            "total_rows": len(result),
            "total_columns": len(result[0].keys()) if result else 0,
            "columns": list(result[0].keys()) if result else []
        }
        
        # 預覽資料（前10行）
        preview_data = result[:10] if result else []
        
        return ProcessResponse(
            status="success",
            filename=request.file_name,
            stats=stats,
            preview=preview_data,
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CSV processing failed: {str(e)}")

@router.post("/ingest-to-db", response_model=IngestResponse, tags=["Import"])
def ingest_data_to_db(request: IngestRequest):
    """
    將解析後的資料匯入到 DuckDB 和 Milvus 資料庫
    """
    if not request.data:
        raise HTTPException(status_code=400, detail="data cannot be empty.")
    
    try:
        ingestor = DBIngestor()
        duckdb_count, milvus_count = ingestor.ingest(request.data)
        
        return IngestResponse(
            success=True,
            message="Data ingestion successful.",
            duckdb_rows_added=duckdb_count,
            milvus_entities_added=milvus_count
        )
    except Exception as e:
        logger.error(f"Data ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/parser-info", tags=["Import"])
def get_parser_info():
    """
    獲取解析器配置資訊
    """
    try:
        processor = CSVProcessor2()
        return processor.get_parser_info()
    except Exception as e:
        logger.error(f"Failed to get parser info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get parser info: {str(e)}")

@router.get("/health", tags=["Import"])
def health_check():
    """
    Import routes health check
    """
    return {
        "status": "healthy",
        "service": "MLINFO Data Import Integration",
        "endpoints": ["/process", "/ingest-to-db", "/parser-info"]
    }