from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import sqlite3
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, Any, List
import json

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "db" / "history.db"

def init_history_database():
    """初始化歷史資料庫"""
    try:
        # 確保資料庫目錄存在
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # 創建歷史記錄表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                data_type TEXT NOT NULL,
                record_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("History database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize history database: {e}")

@router.on_event("startup")
async def startup_event():
    """應用啟動時初始化資料庫"""
    init_history_database()

@router.get("/")
async def get_history():
    """獲取資料歷史記錄"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # 獲取歷史記錄，按時間倒序
        cursor.execute('''
            SELECT id, filename, data_type, record_count, error_count, 
                   status, timestamp, metadata
            FROM data_history
            ORDER BY timestamp DESC
            LIMIT 50
        ''')
        
        records = cursor.fetchall()
        conn.close()
        
        # 轉換為字典格式
        history_list = []
        for record in records:
            history_item = {
                "id": record[0],
                "filename": record[1],
                "data_type": record[2],
                "record_count": record[3],
                "error_count": record[4],
                "status": record[5],
                "timestamp": record[6],
                "metadata": json.loads(record[7]) if record[7] else {}
            }
            history_list.append(history_item)
        
        return {"history": history_list}
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=f"獲取歷史記錄失敗: {str(e)}")

@router.post("/")
async def add_history_record(data: Dict[Any, Any]):
    """新增歷史記錄"""
    try:
        filename = data.get("filename")
        data_type = data.get("data_type", "unknown")
        record_count = data.get("record_count", 0)
        error_count = data.get("error_count", 0)
        status = data.get("status", "unknown")
        metadata = data.get("metadata", {})
        
        if not filename:
            raise HTTPException(status_code=400, detail="檔案名稱不能為空")
        
        # 只記錄成功的資料
        if status in ["success", "partial"] and record_count > 0:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO data_history 
                (filename, data_type, record_count, error_count, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (filename, data_type, record_count, error_count, status, json.dumps(metadata)))
            
            conn.commit()
            record_id = cursor.lastrowid
            conn.close()
            
            return {
                "status": "success",
                "record_id": record_id,
                "message": "歷史記錄已新增"
            }
        else:
            return {
                "status": "skipped",
                "message": "未記錄到歷史（資料未成功處理）"
            }
        
    except Exception as e:
        logger.error(f"Error adding history record: {e}")
        raise HTTPException(status_code=500, detail=f"新增歷史記錄失敗: {str(e)}")

@router.delete("/{record_id}")
async def delete_history_record(record_id: int):
    """刪除歷史記錄"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM data_history WHERE id = ?', (record_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="記錄不存在")
        
        conn.commit()
        conn.close()
        
        return {"status": "success", "message": "記錄已刪除"}
        
    except Exception as e:
        logger.error(f"Error deleting history record: {e}")
        raise HTTPException(status_code=500, detail=f"刪除記錄失敗: {str(e)}")

@router.get("/stats")
async def get_history_stats():
    """獲取歷史統計資訊"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # 總記錄數
        cursor.execute('SELECT COUNT(*) FROM data_history')
        total_records = cursor.fetchone()[0]
        
        # 成功記錄數
        cursor.execute('SELECT COUNT(*) FROM data_history WHERE status = "success"')
        success_records = cursor.fetchone()[0]
        
        # 總處理的資料筆數
        cursor.execute('SELECT SUM(record_count) FROM data_history')
        total_processed = cursor.fetchone()[0] or 0
        
        # 按資料類型分組
        cursor.execute('''
            SELECT data_type, COUNT(*), SUM(record_count)
            FROM data_history
            GROUP BY data_type
        ''')
        type_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_records": total_records,
            "success_records": success_records,
            "total_processed": total_processed,
            "type_stats": {
                row[0]: {"count": row[1], "processed": row[2]}
                for row in type_stats
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting history stats: {e}")
        raise HTTPException(status_code=500, detail=f"獲取統計資訊失敗: {str(e)}")

# 工具函數供其他模組使用
async def record_success_to_history(filename: str, data_type: str, count: int, metadata: Dict = None):
    """記錄成功的資料處理到歷史"""
    try:
        await add_history_record({
            "filename": filename,
            "data_type": data_type,
            "record_count": count,
            "error_count": 0,
            "status": "success",
            "metadata": metadata or {}
        })
    except Exception as e:
        logger.error(f"Failed to record success to history: {e}")