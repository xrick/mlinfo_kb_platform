from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import io
import logging
from typing import Dict, Any
from pathlib import Path
import sqlite3
from datetime import datetime

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_specs_file(file: UploadFile = File(...)):
    """上傳規格檔案並進行初步處理"""
    try:
        # 驗證檔案類型
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(status_code=400, detail="不支援的檔案格式")
        
        # 讀取檔案內容
        contents = await file.read()
        
        # 根據檔案類型處理
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # 基本資料驗證
        if df.empty:
            raise HTTPException(status_code=400, detail="檔案內容為空")
        
        # 預覽資料（前10行）
        preview_data = df.head(10).to_dict('records')
        
        # 基本統計信息
        stats = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": df.columns.tolist(),
            "missing_values": df.isnull().sum().to_dict()
        }
        
        return {
            "status": "success",
            "filename": file.filename,
            "stats": stats,
            "preview": preview_data
        }
        
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"檔案處理失敗: {str(e)}")

@router.post("/process")
async def process_specs_data(data: Dict[Any, Any]):
    """處理規格資料並存入資料庫"""
    try:
        filename = data.get("filename")
        specs_data = data.get("data")
        
        if not filename or not specs_data:
            raise HTTPException(status_code=400, detail="缺少必要的資料")
        
        # 模擬資料處理流程
        processed_count = 0
        success_count = 0
        error_count = 0
        
        # 這裡應該包含實際的資料處理邏輯
        # 例如：驗證資料格式、轉換資料、存入資料庫等
        
        for item in specs_data:
            try:
                processed_count += 1
                # 模擬資料驗證和處理
                if validate_spec_item(item):
                    # 存入資料庫
                    save_spec_to_database(item)
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Error processing item: {e}")
                error_count += 1
        
        # 如果成功處理了資料，記錄到歷史
        if success_count > 0:
            await record_to_history(filename, success_count, error_count)
        
        return {
            "status": "completed",
            "processed": processed_count,
            "success": success_count,
            "errors": error_count
        }
        
    except Exception as e:
        logger.error(f"Error processing specs data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"資料處理失敗: {str(e)}")

def validate_spec_item(item: Dict[Any, Any]) -> bool:
    """驗證規格項目"""
    # 基本驗證邏輯
    required_fields = ['modelname', 'cpu', 'memory', 'storage']
    
    for field in required_fields:
        if field not in item or not item[field]:
            return False
    
    return True

def save_spec_to_database(item: Dict[Any, Any]):
    """將規格項目存入資料庫"""
    # 這裡應該包含實際的資料庫操作
    # 暫時跳過實際的資料庫操作
    pass

async def record_to_history(filename: str, success_count: int, error_count: int):
    """記錄到歷史資料庫"""
    try:
        # 這裡應該調用歷史 API 或直接操作資料庫
        from .history_routes import add_history_record
        await add_history_record({
            "filename": filename,
            "data_type": "specifications",
            "record_count": success_count,
            "error_count": error_count,
            "status": "success" if error_count == 0 else "partial"
        })
    except Exception as e:
        logger.error(f"Failed to record to history: {e}")

@router.get("/template")
async def get_template():
    """獲取規格資料模板"""
    template_columns = [
        'modeltype', 'version', 'modelname', 'mainboard', 'devtime',
        'pm', 'structconfig', 'lcd', 'touchpanel', 'iointerface', 
        'ledind', 'powerbutton', 'keyboard', 'webcamera', 'touchpad', 
        'fingerprint', 'audio', 'battery', 'cpu', 'gpu', 'memory', 
        'lcdconnector', 'storage', 'wifislot', 'thermal', 'tpm', 'rtc', 
        'wireless', 'lan', 'bluetooth', 'softwareconfig', 'ai', 'accessory', 
        'certifications', 'otherfeatures'
    ]
    
    return {
        "columns": template_columns,
        "description": "筆記型電腦規格資料模板",
        "example": {col: f"範例{col}" for col in template_columns[:5]}
    }