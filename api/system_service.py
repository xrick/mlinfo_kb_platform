import os
import time
import duckdb
from typing import Dict, Any, List
from pymilvus import connections, utility, Collection
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SystemService:
    """
    系統狀態和統計服務
    """
    
    def __init__(self):
        self.MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
        self.MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
        self.DUCKDB_FILE = "all_nbinfo_v3.db"
        self.COLLECTION_NAME = "sales_notebook_specs"
        
        # 簡單的查詢統計存儲 (生產環境應使用 Redis 或數據庫)
        self.query_stats = {
            "total_queries": 0,
            "popular_queries": []
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """獲取系統健康狀態"""
        try:
            # 檢查 DuckDB 狀態
            duckdb_status = self._check_duckdb_health()
            
            # 檢查 Milvus 狀態
            milvus_status = self._check_milvus_health()
            
            # 獲取總記錄數
            total_records = self._get_total_records()
            
            # 獲取最後更新時間
            last_update = self._get_last_update()
            
            # 判斷總體狀態
            overall_status = "healthy" if (duckdb_status == "healthy" and milvus_status == "healthy") else "degraded"
            
            return {
                "status": overall_status,
                "duckdb_status": duckdb_status,
                "milvus_status": milvus_status,
                "total_records": total_records,
                "last_update": last_update
            }
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {str(e)}")
            return {
                "status": "error",
                "duckdb_status": "error",
                "milvus_status": "error",
                "total_records": 0,
                "last_update": None
            }
    
    def _check_duckdb_health(self) -> str:
        """檢查 DuckDB 健康狀態"""
        try:
            if not os.path.exists(self.DUCKDB_FILE):
                return "missing"
            
            with duckdb.connect(database=self.DUCKDB_FILE, read_only=True) as con:
                # 檢查表是否存在
                table_check = con.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'specs'").fetchone()
                if not table_check:
                    return "no_table"
                
                # 檢查是否有資料
                count = con.execute("SELECT COUNT(*) FROM specs").fetchone()[0]
                if count == 0:
                    return "empty"
                
                return "healthy"
                
        except Exception as e:
            logger.error(f"DuckDB 健康檢查失敗: {str(e)}")
            return "error"
    
    def _check_milvus_health(self) -> str:
        """檢查 Milvus 健康狀態"""
        try:
            # 嘗試連接
            connections.connect("default", host=self.MILVUS_HOST, port=self.MILVUS_PORT)
            
            # 檢查集合是否存在
            if not utility.has_collection(self.COLLECTION_NAME):
                return "no_collection"
            
            # 檢查集合狀態
            collection = Collection(self.COLLECTION_NAME)
            collection.load()
            
            # 檢查記錄數
            count = collection.num_entities
            if count == 0:
                return "empty"
            
            return "healthy"
            
        except Exception as e:
            logger.error(f"Milvus 健康檢查失敗: {str(e)}")
            return "error"
    
    def _get_total_records(self) -> int:
        """獲取總記錄數"""
        try:
            with duckdb.connect(database=self.DUCKDB_FILE, read_only=True) as con:
                table_check = con.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'specs'").fetchone()
                if table_check:
                    count = con.execute("SELECT COUNT(*) FROM specs").fetchone()[0]
                    return count
            return 0
        except Exception as e:
            logger.error(f"獲取記錄數失敗: {str(e)}")
            return 0
    
    def _get_last_update(self) -> str:
        """獲取最後更新時間"""
        try:
            if os.path.exists(self.DUCKDB_FILE):
                mtime = os.path.getmtime(self.DUCKDB_FILE)
                return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
            return None
        except Exception as e:
            logger.error(f"獲取更新時間失敗: {str(e)}")
            return None
    
    def get_system_stats(self) -> Dict[str, Any]:
        """獲取系統統計資訊"""
        try:
            # 獲取基本統計
            total_records = self._get_total_records()
            database_size = self._get_database_size()
            
            # 獲取查詢統計
            total_queries = self.query_stats["total_queries"]
            popular_queries = self.query_stats["popular_queries"]
            
            # 獲取資料分布統計
            data_distribution = self._get_data_distribution()
            
            return {
                "total_queries": total_queries,
                "total_records": total_records,
                "database_size": database_size,
                "popular_queries": popular_queries,
                "data_distribution": data_distribution,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"獲取系統統計失敗: {str(e)}")
            return {
                "total_queries": 0,
                "total_records": 0,
                "database_size": "0 MB",
                "popular_queries": [],
                "data_distribution": {},
                "success": False
            }
    
    def _get_database_size(self) -> str:
        """獲取資料庫大小"""
        try:
            if os.path.exists(self.DUCKDB_FILE):
                size_bytes = os.path.getsize(self.DUCKDB_FILE)
                # 轉換為 MB
                size_mb = size_bytes / (1024 * 1024)
                return f"{size_mb:.2f} MB"
            return "0 MB"
        except Exception as e:
            logger.error(f"獲取資料庫大小失敗: {str(e)}")
            return "Unknown"
    
    def _get_data_distribution(self) -> Dict[str, Any]:
        """獲取資料分布統計"""
        try:
            with duckdb.connect(database=self.DUCKDB_FILE, read_only=True) as con:
                table_check = con.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'specs'").fetchone()
                if not table_check:
                    return {}
                
                # 統計不同型號的數量
                modeltype_stats = con.execute("""
                    SELECT modeltype, COUNT(*) as count 
                    FROM specs 
                    WHERE modeltype IS NOT NULL AND modeltype != ''
                    GROUP BY modeltype 
                    ORDER BY count DESC 
                    LIMIT 10
                """).fetchdf()
                
                # 統計 CPU 品牌分布
                cpu_stats = con.execute("""
                    SELECT 
                        CASE 
                            WHEN cpu LIKE '%Intel%' THEN 'Intel'
                            WHEN cpu LIKE '%AMD%' THEN 'AMD'
                            ELSE 'Other'
                        END as cpu_brand,
                        COUNT(*) as count
                    FROM specs 
                    WHERE cpu IS NOT NULL AND cpu != ''
                    GROUP BY cpu_brand
                    ORDER BY count DESC
                """).fetchdf()
                
                return {
                    "modeltype_distribution": modeltype_stats.to_dict('records') if not modeltype_stats.empty else [],
                    "cpu_brand_distribution": cpu_stats.to_dict('records') if not cpu_stats.empty else []
                }
                
        except Exception as e:
            logger.error(f"獲取資料分布失敗: {str(e)}")
            return {}
    
    def record_query(self, query: str):
        """記錄查詢統計"""
        try:
            self.query_stats["total_queries"] += 1
            
            # 更新熱門查詢
            popular_queries = self.query_stats["popular_queries"]
            
            # 查找是否已存在相似查詢
            found = False
            for pq in popular_queries:
                if pq["query"] == query:
                    pq["count"] += 1
                    found = True
                    break
            
            if not found:
                popular_queries.append({"query": query, "count": 1})
            
            # 保持只有前 10 個熱門查詢
            popular_queries.sort(key=lambda x: x["count"], reverse=True)
            self.query_stats["popular_queries"] = popular_queries[:10]
            
        except Exception as e:
            logger.error(f"記錄查詢統計失敗: {str(e)}")
    
    def clean_all_data(self) -> Dict[str, Any]:
        """清理所有資料"""
        try:
            results = {"duckdb": False, "milvus": False}
            
            # 清理 DuckDB
            try:
                with duckdb.connect(database=self.DUCKDB_FILE, read_only=False) as con:
                    con.execute("DROP TABLE IF EXISTS specs")
                    results["duckdb"] = True
                    logger.info("DuckDB 資料清理成功")
            except Exception as e:
                logger.error(f"DuckDB 資料清理失敗: {str(e)}")
            
            # 清理 Milvus
            try:
                connections.connect("default", host=self.MILVUS_HOST, port=self.MILVUS_PORT)
                if utility.has_collection(self.COLLECTION_NAME):
                    collection = Collection(self.COLLECTION_NAME)
                    collection.drop()
                    results["milvus"] = True
                    logger.info("Milvus 資料清理成功")
            except Exception as e:
                logger.error(f"Milvus 資料清理失敗: {str(e)}")
            
            return {
                "success": results["duckdb"] and results["milvus"],
                "details": results,
                "message": "資料清理完成"
            }
            
        except Exception as e:
            logger.error(f"資料清理失敗: {str(e)}")
            return {
                "success": False,
                "details": {"duckdb": False, "milvus": False},
                "message": f"資料清理失敗: {str(e)}"
            }