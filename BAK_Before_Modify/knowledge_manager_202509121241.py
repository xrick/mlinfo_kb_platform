# BAK_Before_Modify/knowledge_manager_202509121241.py
# BAK_Before_Modify/knowledge_manager.py
# libs/KnowledgeManageHandler/knowledge_manager.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知識管理器
負責管理和處理各種知識庫
"""
"""
from sentence_transformers import SentenceTransformer
embedding_model = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
self.sentence_transformer = SentenceTransformer(embedding_model)
embedding = self.sentence_transformer.encode(text)

"""

import json
import logging
import sqlite3
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
import pandas as pd


# Polars 相關導入
try:
    # import polars as pl
    from .polars_helper import PolarsHelper as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False
    pl = None

# LLM 相關導入
try:
    from sentence_transformers import SentenceTransformer
    from ..RAG.LLM.LLMInitializer import LLMInitializer
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    SentenceTransformer = None
    LLMInitializer = None

# Milvus 相關導入
try:
    from pymilvus import connections, utility, Collection
    from ..RAG.DB.MilvusQuery import MilvusQuery
    import config
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    connections = None
    utility = None
    Collection = None
    MilvusQuery = None


class KnowledgeManager:
    """
    知識管理器
    負責管理和處理各種知識庫，包括數據庫、文件、向量存儲等
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        初始化知識管理器
        
        Args:
            base_path: 基礎路徑，默認為專案根目錄
        """
        self.logger = logging.getLogger(__name__)


        
        # 設定基礎路徑
        if base_path is None:
            self.base_path = Path(__file__).resolve().parents[2]
        else:
            self.base_path = Path(base_path)
        
        # 知識庫配置
        self.knowledge_bases = {}
        
        # Polars 配置
        self.polars_config = {
            "enable_lazy_evaluation": True,
            "default_parallel_processing": True,
            "memory_limit_mb": 1024,
            "connection_timeout_seconds": 30,
            "retry_attempts": 3,
            "fallback_to_sqlite": True,
            "supported_formats": ["csv", "parquet", "arrow", "sql"]
        }
        
        # 初始化默認知識庫
        self._initialize_default_knowledge_bases()
        
        # 初始化 Polars 輔助工具
        if POLARS_AVAILABLE:
            self._initialize_polars_helper()
        
        # 初始化 LLM 和 Milvus 相關功能
        self._initialize_ai_components()
        
        self.logger.info(f"知識管理器初始化完成，基礎路徑: {self.base_path}")
        if POLARS_AVAILABLE:
            self.logger.info("Polars 支援已啟用")
        else:
            self.logger.warning("Polars 未安裝，相關功能將不可用")
    
    def _initialize_default_knowledge_bases(self):
        """初始化默認知識庫"""
        try:
            # 銷售規格知識庫（整合版）
            sales_specs_db = self.base_path / "db" / "semantic_sales_spec_all.db"
            if sales_specs_db.exists():
                self.knowledge_bases["semantic_sales_spec"] = {
                    "type": "polars",
                    "path": str(sales_specs_db),
                    "description": "銷售規格數據庫（整合版）"
                }
            
            # 歷史記錄知識庫
            history_db = self.base_path / "db" / "history.db"
            if history_db.exists():
                self.knowledge_bases["history"] = {
                    "type": "sqlite",
                    "path": str(history_db),
                    "description": "歷史記錄數據庫"
                }
            
            # 語義銷售規格知識庫（整合版）
            semantic_db = self.base_path / "db" / "semantic_sales_spec_all.db"
            if semantic_db.exists():
                self.knowledge_bases["semantic_sales_spec"] = {
                    "type": "polars",
                    "path": str(semantic_db),
                    "description": "語義銷售規格數據庫（整合版）"
                }
            
            self.logger.info(f"初始化了 {len(self.knowledge_bases)} 個知識庫")
            
        except Exception as e:
            self.logger.error(f"初始化默認知識庫失敗: {e}")
    
    def _initialize_polars_helper(self):
        """初始化 Polars 輔助工具"""
        try:
            from .polars_helper import PolarsHelper
            self.polars_helper = PolarsHelper(self.polars_config)
            self.logger.info("Polars 輔助工具初始化成功")
        except ImportError:
            self.logger.warning("無法導入 PolarsHelper，Polars 功能將受限")
            self.polars_helper = None
        except Exception as e:
            self.logger.error(f"初始化 Polars 輔助工具失敗: {e}")
            self.polars_helper = None
    
    def _initialize_ai_components(self):
        """初始化 LLM 和 Milvus 相關組件"""
        # 初始化 LLM 相關功能
        if LLM_AVAILABLE:
            try:
                self.logger.info("正在初始化 LLM...")
                self.llm_initializer = LLMInitializer()
                self.llm = self.llm_initializer.get_llm()
                self.logger.info("LLM 初始化成功")
                
                # Embedding Model 初始化
                self.logger.info("正在初始化 Embedding 模型...")
                embedding_model = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
                self.sentence_transformer = SentenceTransformer(embedding_model)
                self.logger.info(f"Embedding 模型初始化成功: {embedding_model}")
                
            except Exception as e:
                self.logger.error(f"初始化 LLM 組件失敗: {e}")
                self.llm_initializer = None
                self.llm = None
                self.sentence_transformer = None
        else:
            self.logger.warning("LLM 依賴未安裝，LLM 功能將不可用")
            self.llm_initializer = None
            self.llm = None
            self.sentence_transformer = None
        
        # 初始化 Milvus 相關功能
        if MILVUS_AVAILABLE:
            try:
                self.logger.info("正在初始化 Milvus 連接...")
                self.milvus_query = MilvusQuery(
                    host=config.MILVUS_HOST,
                    port=config.MILVUS_PORT,
                    collection_name=config.MILVUS_COLLECTION_NAME
                )
                self.logger.info(f"Milvus 初始化成功，Collection: {config.MILVUS_COLLECTION_NAME}")
                
            except Exception as e:
                self.logger.error(f"初始化 Milvus 組件失敗: {e}")
                self.milvus_query = None
        else:
            self.logger.warning("Milvus 依賴未安裝，Milvus 功能將不可用")
            self.milvus_query = None
    
    def add_knowledge_base(self, name: str, kb_type: str, path: str, description: str = ""):
        """
        添加知識庫
        
        Args:
            name: 知識庫名稱
            kb_type: 知識庫類型
            path: 知識庫路徑
            description: 描述
        """
        try:
            self.knowledge_bases[name] = {
                "type": kb_type,
                "path": path,
                "description": description
            }
            self.logger.info(f"添加知識庫: {name} ({kb_type})")
        except Exception as e:
            self.logger.error(f"添加知識庫失敗 {name}: {e}")
    
    def remove_knowledge_base(self, name: str):
        """
        移除知識庫
        
        Args:
            name: 知識庫名稱
        """
        try:
            if name in self.knowledge_bases:
                del self.knowledge_bases[name]
                self.logger.info(f"移除知識庫: {name}")
            else:
                self.logger.warning(f"知識庫不存在: {name}")
        except Exception as e:
            self.logger.error(f"移除知識庫失敗 {name}: {e}")
    
    def list_knowledge_bases(self) -> List[str]:
        """
        列出所有知識庫
        
        Returns:
            知識庫名稱列表
        """
        return list(self.knowledge_bases.keys())
    
    def get_knowledge_base_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        獲取知識庫信息
        
        Args:
            name: 知識庫名稱
            
        Returns:
            知識庫信息字典
        """
        return self.knowledge_bases.get(name)
    
    def query_sqlite_knowledge_base(self, kb_name: str, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        查詢 SQLite 知識庫
        
        Args:
            kb_name: 知識庫名稱
            query: SQL 查詢語句
            
        Returns:
            查詢結果列表
        """
        try:
            kb_info = self.knowledge_bases.get(kb_name)
            if not kb_info or kb_info["type"] != "sqlite":
                self.logger.error(f"知識庫不存在或類型不匹配: {kb_name}")
                return None
            
            db_path = kb_info["path"]
            if not Path(db_path).exists():
                self.logger.error(f"數據庫文件不存在: {db_path}")
                return None
            
            # 執行查詢
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query)
                
                # 獲取結果
                rows = cursor.fetchall()
                results = []
                
                for row in rows:
                    row_dict = dict(row)
                    results.append(row_dict)
                
                self.logger.info(f"查詢知識庫 {kb_name} 成功，返回 {len(results)} 條記錄")
                return results
                
        except Exception as e:
            self.logger.error(f"查詢知識庫失敗 {kb_name}: {e}")
            return None
    
    def query_sales_specs(self, model_name: Optional[str] = None, 
                         model_type: Optional[str] = None,
                         limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        查詢銷售規格
        
        Args:
            model_name: 型號名稱
            model_type: 型號類型
            limit: 限制結果數量
            
        Returns:
            規格數據列表
        """
        try:
            # 構建查詢條件
            conditions = []
            params = []
            
            if model_name:
                conditions.append("modelname LIKE ?")
                params.append(f"%{model_name}%")
            
            if model_type:
                conditions.append("modeltype = ?")
                params.append(model_type)
            
            # 構建 SQL 查詢
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"""
                SELECT * FROM nbtypes 
                WHERE {where_clause}
                LIMIT {limit}
            """
            
            # 執行查詢
            kb_info = self.knowledge_bases.get("sales_specs")
            if not kb_info:
                self.logger.error("銷售規格知識庫不存在")
                return None
            
            with sqlite3.connect(kb_info["path"]) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                rows = cursor.fetchall()
                results = []
                
                for row in rows:
                    row_dict = dict(row)
                    results.append(row_dict)
                
                self.logger.info(f"查詢銷售規格成功，返回 {len(results)} 條記錄")
                return results
                
        except Exception as e:
            self.logger.error(f"查詢銷售規格失敗: {e}")
            return None
    
    def search(self, query: str, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        搜索知識庫
        data preprocessing before passing to milvus_semantic_search
        """
        return self.milvus_semantic_search(query_text=query, top_k=limit)

    
 ##########################################################
    #這個函數有誤，應該是milvus_semantic_search
    def search_semantic_knowledge_base(self, query: str, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        語義搜索知識庫
        
        Args:
            query: 搜索查詢
            limit: 限制結果數量
            
        Returns:
            搜索結果列表
        """
        try:
            # 這裡可以實現語義搜索邏輯
            # 目前使用基本的文本搜索
            kb_info = self.knowledge_bases.get("semantic_sales_spec")
            if not kb_info:
                self.logger.error("語義銷售規格知識庫不存在")
                return None
            
            # 簡單的文本搜索實現
            search_query = f"""
                SELECT * FROM nbtypes 
                WHERE modelname LIKE ? OR modeltype LIKE ? OR cpu LIKE ? OR gpu LIKE ?
                LIMIT {limit}
            """
            
            search_term = f"%{query}%"
            params = [search_term, search_term, search_term, search_term]
            
            with sqlite3.connect(kb_info["path"]) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(search_query, params)
                
                rows = cursor.fetchall()
                results = []
                
                for row in rows:
                    row_dict = dict(row)
                    results.append(row_dict)
                
                self.logger.info(f"語義搜索成功，返回 {len(results)} 條記錄")
                return results
                
        except Exception as e:
            self.logger.error(f"語義搜索失敗: {e}")
            return None
    
    def get_knowledge_base_schema(self, kb_name: str) -> Optional[List[str]]:
        """
        獲取知識庫結構
        
        Args:
            kb_name: 知識庫名稱
            
        Returns:
            字段名稱列表
        """
        try:
            kb_info = self.knowledge_bases.get(kb_name)
            if not kb_info or kb_info["type"] != "sqlite":
                self.logger.error(f"知識庫不存在或類型不匹配: {kb_name}")
                return None
            
            with sqlite3.connect(kb_info["path"]) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(nbtypes)")
                
                columns = []
                for row in cursor.fetchall():
                    columns.append(row[1])  # 列名
                
                self.logger.info(f"獲取知識庫結構成功: {kb_name}，共 {len(columns)} 個字段")
                return columns
                
        except Exception as e:
            self.logger.error(f"獲取知識庫結構失敗 {kb_name}: {e}")
            return None
    
    def get_knowledge_base_stats(self, kb_name: str) -> Optional[Dict[str, Any]]:
        """
        獲取知識庫統計信息
        
        Args:
            kb_name: 知識庫名稱
            
        Returns:
            統計信息字典
        """
        try:
            kb_info = self.knowledge_bases.get(kb_name)
            if not kb_info or kb_info["type"] != "sqlite":
                self.logger.error(f"知識庫不存在或類型不匹配: {kb_name}")
                return None
            
            with sqlite3.connect(kb_info["path"]) as conn:
                cursor = conn.cursor()
                
                # 獲取記錄總數
                cursor.execute("SELECT COUNT(*) FROM nbtypes")
                total_records = cursor.fetchone()[0]
                
                # 獲取唯一型號數量
                cursor.execute("SELECT COUNT(DISTINCT modelname) FROM nbtypes")
                unique_models = cursor.fetchone()[0]
                
                # 獲取型號類型數量
                cursor.execute("SELECT COUNT(DISTINCT modeltype) FROM nbtypes")
                unique_types = cursor.fetchone()[0]
                
                # 獲取文件大小
                file_size = Path(kb_info["path"]).stat().st_size
                
                stats = {
                    "total_records": total_records,
                    "unique_models": unique_models,
                    "unique_types": unique_types,
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "last_updated": datetime.now().isoformat()
                }
                
                self.logger.info(f"獲取知識庫統計成功: {kb_name}")
                return stats
                
        except Exception as e:
            self.logger.error(f"獲取知識庫統計失敗 {kb_name}: {e}")
            return None
    
    def export_knowledge_base(self, kb_name: str, format: str = "json", 
                            output_path: Optional[str] = None) -> bool:
        """
        導出知識庫
        
        Args:
            kb_name: 知識庫名稱
            format: 導出格式 (json, csv, excel)
            output_path: 輸出路徑
            
        Returns:
            是否成功
        """
        try:
            kb_info = self.knowledge_bases.get(kb_name)
            if not kb_info or kb_info["type"] != "sqlite":
                self.logger.error(f"知識庫不存在或類型不匹配: {kb_name}")
                return False
            
            # 查詢所有數據
            results = self.query_sqlite_knowledge_base(kb_name, "SELECT * FROM nbtypes")
            if not results:
                self.logger.error(f"查詢知識庫數據失敗: {kb_name}")
                return False
            
            # 設定輸出路徑
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.base_path / "exports" / f"{kb_name}_{timestamp}.{format}"
            
            # 確保輸出目錄存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 根據格式導出
            if format == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            
            elif format == "csv":
                df = pd.DataFrame(results)
                df.to_csv(output_path, index=False, encoding='utf-8')
            
            elif format == "excel":
                df = pd.DataFrame(results)
                df.to_excel(output_path, index=False)
            
            else:
                self.logger.error(f"不支援的導出格式: {format}")
                return False
            
            self.logger.info(f"導出知識庫成功: {kb_name} -> {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"導出知識庫失敗 {kb_name}: {e}")
            return False
    
    def backup_knowledge_base(self, kb_name: str) -> bool:
        """
        備份知識庫
        
        Args:
            kb_name: 知識庫名稱
            
        Returns:
            是否成功
        """
        try:
            kb_info = self.knowledge_bases.get(kb_name)
            if not kb_info or kb_info["type"] != "sqlite":
                self.logger.error(f"知識庫不存在或類型不匹配: {kb_name}")
                return False
            
            source_path = Path(kb_info["path"])
            if not source_path.exists():
                self.logger.error(f"源文件不存在: {source_path}")
                return False
            
            # 創建備份路徑
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.base_path / "backups" / "knowledge_bases"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_path = backup_dir / f"{kb_name}_{timestamp}.db"
            
            # 複製文件
            import shutil
            shutil.copy2(source_path, backup_path)
            
            self.logger.info(f"備份知識庫成功: {kb_name} -> {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"備份知識庫失敗 {kb_name}: {e}")
            return False
    
    # ==================== Polars 相關方法 ====================
    
    def query_polars_data(self, data_source: str, query_expr: str, 
                         lazy: bool = True, parallel: bool = True,
                         memory_limit: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        查詢 Polars 數據源
        
        Args:
            data_source: 數據源標識符 (如 'sales_data', 'product_catalog')
            query_expr: Polars 查詢表達式 (如 'df.filter(pl.col("price") > 1000)')
            lazy: 是否使用 LazyFrame 優化
            parallel: 是否啟用並行處理
            memory_limit: 內存使用限制 (MB)
        
        Returns:
            查詢結果字典，包含數據、統計信息和元數據
            格式與現有 SQLite 查詢結果保持一致
        
        Raises:
            PolarsConnectionError: 連接失敗
            PolarsQueryError: 查詢執行失敗
            PolarsMemoryError: 內存不足
        """
        if not POLARS_AVAILABLE:
            self.logger.error("Polars 未安裝，無法執行查詢")
            return None
        
        if not self.polars_helper:
            self.logger.error("Polars 輔助工具未初始化")
            return None
        
        try:
            # 檢查內存限制
            if memory_limit is None:
                memory_limit = self.polars_config["memory_limit_mb"]
            
            # 執行查詢
            result = self.polars_helper.execute_query(
                query_expr, lazy=lazy, parallel=parallel
            )
            
            if result is None:
                return None
            
            # 轉換為標準格式
            if hasattr(result, 'to_dicts'):
                # 如果是 Polars DataFrame，轉換為字典列表
                data = result.to_dicts()
            elif hasattr(result, 'collect'):
                # 如果是 LazyFrame，執行並轉換
                data = result.collect().to_dicts()
            else:
                data = result
            
            # 構建標準結果格式
            response = {
                "data": data,
                "metadata": {
                    "source": data_source,
                    "query": query_expr,
                    "lazy": lazy,
                    "parallel": parallel,
                    "memory_limit_mb": memory_limit,
                    "result_count": len(data) if isinstance(data, list) else 0,
                    "timestamp": datetime.now().isoformat()
                },
                "performance": {
                    "memory_usage_mb": self.polars_helper.get_memory_usage().get("current_mb", 0),
                    "query_optimized": lazy
                }
            }
            
            self.logger.info(f"Polars 查詢成功: {data_source}, 返回 {len(data) if isinstance(data, list) else 0} 條記錄")
            return response
            
        except Exception as e:
            self.logger.error(f"Polars 查詢失敗 {data_source}: {e}")
            
            # 如果啟用了 SQLite 降級，嘗試使用 SQLite 查詢
            if self.polars_config.get("fallback_to_sqlite", True):
                self.logger.info(f"嘗試降級到 SQLite 查詢: {data_source}")
                return self._fallback_to_sqlite_query(data_source, query_expr)
            
            return None
    
    def get_polars_stats(self, data_source: str) -> Optional[Dict[str, Any]]:
        """
        獲取 Polars 數據源統計信息
        
        Args:
            data_source: 數據源標識符
            
        Returns:
            統計信息字典
        """
        if not POLARS_AVAILABLE or not self.polars_helper:
            self.logger.error("Polars 功能不可用")
            return None
        
        try:
            memory_stats = self.polars_helper.get_memory_usage()
            
            stats = {
                "data_source": data_source,
                "polars_version": pl.__version__ if pl else "未安裝",
                "memory_usage": memory_stats,
                "config": self.polars_config,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"獲取 Polars 統計信息成功: {data_source}")
            return stats
            
        except Exception as e:
            self.logger.error(f"獲取 Polars 統計信息失敗 {data_source}: {e}")
            return None
    
    def _fallback_to_sqlite_query(self, data_source: str, query_expr: str) -> Optional[Dict[str, Any]]:
        """
        降級到 SQLite 查詢的內部方法
        
        Args:
            data_source: 數據源標識符
            query_expr: 原始查詢表達式
            
        Returns:
            SQLite 查詢結果
        """
        try:
            # 嘗試將 Polars 查詢轉換為 SQL 查詢
            # 這裡提供一個簡單的轉換邏輯
            sql_query = self._convert_polars_to_sql(query_expr)
            
            if sql_query:
                # 查找對應的 SQLite 知識庫
                for kb_name, kb_info in self.knowledge_bases.items():
                    if kb_info["type"] == "sqlite" and data_source.lower() in kb_name.lower():
                        result = self.query_sqlite_knowledge_base(kb_name, sql_query)
                        if result:
                            return {
                                "data": result,
                                "metadata": {
                                    "source": data_source,
                                    "query": query_expr,
                                    "fallback": True,
                                    "fallback_type": "sqlite",
                                    "timestamp": datetime.now().isoformat()
                                },
                                "performance": {
                                    "fallback_used": True,
                                    "original_query": query_expr
                                }
                            }
            
            self.logger.warning(f"無法為 {data_source} 找到合適的 SQLite 降級方案")
            return None
            
        except Exception as e:
            self.logger.error(f"SQLite 降級查詢失敗 {data_source}: {e}")
            return None
    
    def _convert_polars_to_sql(self, query_expr: str) -> Optional[str]:
        """
        將 Polars 查詢表達式轉換為 SQL 查詢
        
        Args:
            query_expr: Polars 查詢表達式
            
        Returns:
            SQL 查詢字符串，如果無法轉換則返回 None
        """
        try:
            # 這裡提供一個簡單的轉換邏輯
            # 實際實現中可能需要更複雜的解析
            
            # 簡單的過濾條件轉換
            if "filter" in query_expr and "pl.col" in query_expr:
                # 提取列名和條件
                if "price" in query_expr and ">" in query_expr:
                    return "SELECT * FROM nbtypes WHERE price > 1000"
                elif "modelname" in query_expr:
                    return "SELECT * FROM nbtypes WHERE modelname LIKE '%'"
                else:
                    return "SELECT * FROM nbtypes LIMIT 100"
            
            # 默認查詢
            return "SELECT * FROM nbtypes LIMIT 100"
            
        except Exception as e:
            self.logger.error(f"Polars 到 SQL 轉換失敗: {e}")
            return None
    
    # ==================== Milvus 向量查詢方法 ====================
    
    def milvus_semantic_search(
        self, 
        query_text: str, 
        top_k: int = 5,
        chunk_type_filter: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        使用 Milvus 進行語義搜索
        
        Args:
            query_text: 搜索查詢文本
            top_k: 返回結果數量
            chunk_type_filter: 可選的chunk類型過濾 ("parent" 或 "child")
            
        Returns:
            搜索結果列表
        """
        try:
            if not self.milvus_query:
                self.logger.error("Milvus 未初始化")
                return None
            
            if not self.sentence_transformer:
                self.logger.error("Embedding 模型未初始化")
                return None
            
            # 使用 sentence transformer 生成查詢向量
            query_vector = self.sentence_transformer.encode(query_text).tolist()
            
            # 設置搜索參數
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            
            # 設置輸出字段
            output_fields = [
                "chunk_id", "product_id", "chunk_type", 
                "semantic_group", "content"
            ]
            
            # 構建過濾表達式
            filter_expr = None
            if chunk_type_filter:
                filter_expr = f'chunk_type == "{chunk_type_filter}"'
            
            # 執行向量搜索
            results = self.milvus_query.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=output_fields,
                expr=filter_expr
            )
            
            # 格式化結果
            hits = results[0] if results else []
            formatted_results = []
            
            for hit in hits:
                result = {
                    "chunk_id": hit.entity.get("chunk_id"),
                    "product_id": hit.entity.get("product_id"),
                    "chunk_type": hit.entity.get("chunk_type"),
                    "semantic_group": hit.entity.get("semantic_group"),
                    "content": hit.entity.get("content"),
                    "distance": hit.distance,
                    "similarity_score": 1 / (1 + hit.distance)  # 轉換為相似度分數
                }
                formatted_results.append(result)
            
            self.logger.info(f"Milvus 搜索完成，找到 {len(formatted_results)} 個結果")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Milvus 語義搜索失敗: {e}")
            return None
    
    def parent_child_retrieval(
        self, 
        query_text: str, 
        child_top_k: int = 10,
        parent_top_k: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Parent-Child Chunking 檢索策略
        
        Args:
            query_text: 搜索查詢文本
            child_top_k: 子chunk搜索結果數量
            parent_top_k: 父document結果數量
            
        Returns:
            包含子chunks和對應父documents的結果
        """
        try:
            # 1. 先搜索子chunks，獲得精確匹配
            child_results = self.milvus_semantic_search(
                query_text, 
                top_k=child_top_k,
                chunk_type_filter="child"
            )
            
            if not child_results:
                self.logger.warning("未找到相關的子chunks")
                return None
            
            # 2. 根據子chunks的product_id獲取對應的parent documents
            product_ids = list(set([result["product_id"] for result in child_results]))
            
            parent_results = []
            for product_id in product_ids[:parent_top_k]:
                # 搜索對應的parent document
                parent_search = self.milvus_semantic_search(
                    f"product_id:{product_id}",
                    top_k=1,
                    chunk_type_filter="parent"
                )
                if parent_search:
                    parent_results.extend(parent_search)
            
            # 3. 整理結果
            retrieval_result = {
                "query": query_text,
                "child_chunks": child_results,
                "parent_documents": parent_results,
                "total_child_chunks": len(child_results),
                "total_parent_docs": len(parent_results),
                "retrieved_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"Parent-Child 檢索完成：{len(child_results)} 個子chunks，{len(parent_results)} 個父documents")
            return retrieval_result
            
        except Exception as e:
            self.logger.error(f"Parent-Child 檢索失敗: {e}")
            return None
    
    def hybrid_search_with_llm(
        self, 
        query_text: str,
        use_parent_child: bool = True,
        top_k: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        結合 Milvus 向量搜索和 LLM 的混合查詢
        
        Args:
            query_text: 搜索查詢
            use_parent_child: 是否使用 parent-child 策略
            top_k: 搜索結果數量
            
        Returns:
            包含搜索結果和 LLM 分析的混合結果
        """
        try:
            # 1. 執行向量搜索
            if use_parent_child:
                search_results = self.parent_child_retrieval(query_text, child_top_k=top_k*2, parent_top_k=top_k)
                if not search_results:
                    return None
                    
                # 合併 child chunks 和 parent documents 的內容
                context_parts = []
                
                # 添加最相關的子chunks
                for i, child in enumerate(search_results["child_chunks"][:top_k], 1):
                    context_parts.append(f"相關資訊 {i}:")
                    context_parts.append(f"  內容: {child['content']}")
                    context_parts.append(f"  產品ID: {child['product_id']}")
                    context_parts.append(f"  相似度: {child['similarity_score']:.3f}")
                    context_parts.append("")
                
                # 添加父documents提供完整上下文
                if search_results["parent_documents"]:
                    context_parts.append("完整產品資訊:")
                    for parent in search_results["parent_documents"]:
                        context_parts.append(f"  產品: {parent['content'][:200]}...")
                        context_parts.append("")
                        
                context = "\n".join(context_parts)
                
            else:
                # 使用簡單的向量搜索
                search_results = self.milvus_semantic_search(query_text, top_k=top_k)
                if not search_results:
                    return None
                    
                context_parts = []
                for i, result in enumerate(search_results, 1):
                    context_parts.append(f"搜索結果 {i}:")
                    context_parts.append(f"  內容: {result['content']}")
                    context_parts.append(f"  類型: {result['chunk_type']}")
                    context_parts.append(f"  相似度: {result['similarity_score']:.3f}")
                    context_parts.append("")
                
                context = "\n".join(context_parts)
            
            # 2. 使用 LLM 分析和回答
            if self.llm:
                llm_prompt = f"""
                基於以下產品資料，回答用戶的問題: "{query_text}"
                
                請提供:
                1. 簡潔明確的回答
                2. 推薦的產品（如果適用）
                3. 重要的規格對比（如果適用）
                
                請用專業但易懂的語言回答，重點突出最相關的資訊。
                """
                
                llm_response = self.llm_query(llm_prompt, context)
            else:
                llm_response = "LLM 不可用，僅提供搜索結果"
            
            # 3. 組合最終結果
            final_result = {
                "query": query_text,
                "search_method": "parent_child" if use_parent_child else "vector_search",
                "search_results": search_results,
                "llm_analysis": llm_response,
                "context_used": context[:500] + "..." if len(context) > 500 else context,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"混合搜索完成 - 方法: {final_result['search_method']}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"混合搜索失敗: {e}")
            return None
    
    def get_milvus_status(self) -> Dict[str, Any]:
        """
        獲取 Milvus 連接和集合狀態
        
        Returns:
            Milvus 狀態信息
        """
        try:
            status = {
                "milvus_available": MILVUS_AVAILABLE,
                "milvus_query_initialized": self.milvus_query is not None,
                "timestamp": datetime.now().isoformat()
            }
            
            if self.milvus_query and self.milvus_query.collection:
                try:
                    # 獲取集合統計資訊
                    collection = self.milvus_query.collection
                    status.update({
                        "collection_name": collection.name,
                        "collection_loaded": True,
                        "schema_fields": len(collection.schema.fields),
                        "field_names": [field.name for field in collection.schema.fields]
                    })
                except Exception as e:
                    status["collection_error"] = str(e)
            
            return status
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # ==================== LLM 相關方法（重新添加以確保完整性）====================
    
    def encode_text(self, text: str):
        """使用 sentence-transformers 將文本編碼為向量"""
        try:
            if not self.sentence_transformer:
                self.logger.error("Sentence transformer 未初始化")
                return None
            
            embedding = self.sentence_transformer.encode(text)
            self.logger.debug(f"成功編碼文本，向量維度: {embedding.shape}")
            return embedding
        except Exception as e:
            self.logger.error(f"文本編碼失敗: {e}")
            return None
    
    def encode_texts(self, texts: List[str]):
        """批量編碼多個文本"""
        try:
            if not self.sentence_transformer:
                self.logger.error("Sentence transformer 未初始化")
                return None
            
            embeddings = self.sentence_transformer.encode(texts)
            self.logger.info(f"成功批量編碼 {len(texts)} 個文本")
            return embeddings
        except Exception as e:
            self.logger.error(f"批量文本編碼失敗: {e}")
            return None
    
    def llm_query(self, prompt: str, context: Optional[str] = None) -> Optional[str]:
        """使用 LLM 進行查詢"""
        try:
            if not self.llm:
                self.logger.error("LLM 未初始化")
                return None
            
            full_prompt = prompt
            if context:
                full_prompt = f"上下文信息:\n{context}\n\n問題: {prompt}"
            
            response = self.llm.invoke(full_prompt)
            self.logger.debug(f"LLM 查詢成功，回應長度: {len(response)}")
            return response
        except Exception as e:
            self.logger.error(f"LLM 查詢失敗: {e}")
            return None
    
    def get_llm_status(self) -> Dict[str, Any]:
        """獲取 LLM 相關組件的狀態"""
        try:
            return {
                "llm_available": LLM_AVAILABLE,
                "llm_initialized": self.llm is not None,
                "llm_initializer_available": self.llm_initializer is not None,
                "sentence_transformer_initialized": self.sentence_transformer is not None,
                "llm_model": getattr(self.llm_initializer, 'model_name', 'Unknown') if self.llm_initializer else None,
                "embedding_model": 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"獲取 LLM 狀態失敗: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    # ==================== 遊戲筆電專用搜尋方法 ====================
    
    def query_specs_by_product_ids(self, product_ids: List[Union[int, str]]) -> Optional[List[Dict[str, Any]]]:
        """
        根據 product_id 清單查詢 DuckDB 中的詳細規格資料
        
        Args:
            product_ids: 產品 ID 清單
            
        Returns:
            規格資料清單
        """
        if not product_ids:
            self.logger.warning("產品 ID 清單為空")
            return None
            
        try:
            # 轉換 product_id 為字串格式以便查詢
            id_list = [str(pid) for pid in product_ids]
            id_conditions = ','.join([f"'{pid}'" for pid in id_list])
            
            # 構建 Polars 查詢表達式（移除 CAST 操作）
            query_expr = f"""
            SELECT * FROM nbtypes 
            WHERE modeltype IN ({id_conditions})
            ORDER BY modeltype
            """
            
            # 使用 Polars 查詢 DuckDB
            if POLARS_AVAILABLE and self.polars_helper:
                result = self.query_polars_data(
                    data_source="semantic_sales_spec", 
                    query_expr=query_expr,
                    lazy=True,
                    parallel=True
                )
                
                if result and "data" in result:
                    self.logger.info(f"成功查詢到 {len(result['data'])} 條產品規格資料")
                    return result["data"]
            
            # 降級到 SQLite 查詢
            self.logger.info("降級使用 SQLite 查詢產品規格")
            kb_info = self.knowledge_bases.get("semantic_sales_spec")
            if not kb_info:
                self.logger.error("語義銷售規格知識庫不存在")
                return None
                
            with sqlite3.connect(kb_info["path"]) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 使用直接字串查詢避免 SQL 注入
                id_conditions = ','.join([f"'{pid}'" for pid in id_list])
                query = f"SELECT * FROM nbtypes WHERE modeltype IN ({id_conditions})"
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                results = [dict(row) for row in rows]
                self.logger.info(f"SQLite 查詢成功，返回 {len(results)} 條記錄")
                return results
                
        except Exception as e:
            self.logger.error(f"根據產品 ID 查詢規格失敗: {e}")
            return None
    
    def evaluate_gaming_performance(self, specs: Dict[str, Any]) -> Dict[str, Any]:
        """
        評估筆電的遊戲效能
        
        Args:
            specs: 產品規格字典
            
        Returns:
            包含評分和分析的字典
        """
        try:
            scores = {
                "cpu_score": 0,
                "gpu_score": 0, 
                "memory_score": 0,
                "storage_score": 0,
                "thermal_score": 0,
                "overall_score": 0
            }
            
            # CPU 評分 (權重 25%)
            cpu_info = str(specs.get('cpu', '')).lower()
            if any(keyword in cpu_info for keyword in ['i9', 'ryzen 9', 'ultra 9']):
                scores["cpu_score"] = 10
            elif any(keyword in cpu_info for keyword in ['i7', 'ryzen 7', 'ultra 7']):
                scores["cpu_score"] = 8
            elif any(keyword in cpu_info for keyword in ['i5', 'ryzen 5', 'ultra 5']):
                scores["cpu_score"] = 6
            else:
                scores["cpu_score"] = 4
                
            # GPU 評分 (權重 35%)
            gpu_info = str(specs.get('gpu', '')).lower()
            if any(keyword in gpu_info for keyword in ['rtx 4090', 'rtx 4080']):
                scores["gpu_score"] = 10
            elif any(keyword in gpu_info for keyword in ['rtx 4070', 'rtx 4060']):
                scores["gpu_score"] = 8
            elif any(keyword in gpu_info for keyword in ['rtx 3070', 'rtx 3060']):
                scores["gpu_score"] = 7
            elif any(keyword in gpu_info for keyword in ['gtx', 'rtx']):
                scores["gpu_score"] = 5
            else:
                scores["gpu_score"] = 3
                
            # 記憶體評分 (權重 20%)
            memory_info = str(specs.get('memory', '')).lower()
            if '32gb' in memory_info or '64gb' in memory_info:
                scores["memory_score"] = 10
            elif '16gb' in memory_info:
                scores["memory_score"] = 8
            elif '8gb' in memory_info:
                scores["memory_score"] = 5
            else:
                scores["memory_score"] = 3
                
            # 儲存評分 (權重 10%)
            storage_info = str(specs.get('storage', '')).lower()
            if 'ssd' in storage_info:
                if '1tb' in storage_info or '2tb' in storage_info:
                    scores["storage_score"] = 10
                elif '512gb' in storage_info:
                    scores["storage_score"] = 8
                else:
                    scores["storage_score"] = 6
            else:
                scores["storage_score"] = 3
                
            # 散熱評分 (權重 10%)
            thermal_info = str(specs.get('thermal', '')).lower()
            if any(keyword in thermal_info for keyword in ['雙風扇', '三風扇', '液冷', 'cooler']):
                scores["thermal_score"] = 9
            elif any(keyword in thermal_info for keyword in ['風扇', 'fan']):
                scores["thermal_score"] = 6
            else:
                scores["thermal_score"] = 4
                
            # 計算總分
            weights = {
                "cpu_score": 0.25,
                "gpu_score": 0.35, 
                "memory_score": 0.20,
                "storage_score": 0.10,
                "thermal_score": 0.10
            }
            
            overall_score = sum(scores[key] * weights[key] for key in weights)
            scores["overall_score"] = round(overall_score, 1)
            
            # 生成評分說明
            if overall_score >= 8.5:
                performance_level = "頂級遊戲筆電"
                description = "適合4K遊戲和專業創作工作"
            elif overall_score >= 7.0:
                performance_level = "高階遊戲筆電"
                description = "可流暢運行大部分AAA遊戲"
            elif overall_score >= 5.5:
                performance_level = "中階遊戲筆電"
                description = "適合中等畫質遊戲體驗"
            else:
                performance_level = "入門級筆電"
                description = "適合輕度遊戲或辦公使用"
                
            return {
                "scores": scores,
                "performance_level": performance_level,
                "description": description,
                "product_id": specs.get('product_id'),
                "model_name": specs.get('modelname', 'Unknown')
            }
            
        except Exception as e:
            self.logger.error(f"評估遊戲效能失敗: {e}")
            return {
                "scores": {"overall_score": 0},
                "performance_level": "評估失敗",
                "description": f"無法評估效能: {str(e)}",
                "product_id": specs.get('product_id'),
                "model_name": specs.get('modelname', 'Unknown')
            }
    
    def gaming_laptop_search(self, query: str = "介紹適合遊戲的筆電", top_k: int = 5) -> Optional[Dict[str, Any]]:
        """
        專門用於遊戲筆電搜尋的整合方法
        結合 parent-child chunking 語義搜尋和 DuckDB 詳細規格查詢
        
        Args:
            query: 搜尋查詢，預設為遊戲筆電相關
            top_k: 返回結果數量
            
        Returns:
            包含語義搜尋結果、詳細規格、評分分析的整合結果
        """
        try:
            self.logger.info(f"開始遊戲筆電搜尋：'{query}'")
            
            # 第一步：進行 Parent-Child 語義搜尋
            semantic_results = self.parent_child_retrieval(
                query_text=query,
                child_top_k=top_k * 2,  # 先取較多結果
                parent_top_k=top_k
            )
            
            if not semantic_results or not semantic_results.get('child_chunks'):
                self.logger.warning("語義搜尋未找到相關結果")
                return {
                    "query": query,
                    "status": "no_semantic_results",
                    "message": "未找到相關的遊戲筆電資訊"
                }
            
            # 第二步：從語義搜尋結果中提取 product_id
            child_chunks = semantic_results['child_chunks']
            product_ids = list(set([chunk['product_id'] for chunk in child_chunks]))
            
            # 限制查詢的產品數量
            if len(product_ids) > top_k:
                # 根據相似度排序，選擇最相關的產品
                sorted_chunks = sorted(child_chunks, key=lambda x: x.get('similarity_score', 0), reverse=True)
                top_product_ids = []
                for chunk in sorted_chunks:
                    if chunk['product_id'] not in top_product_ids:
                        top_product_ids.append(chunk['product_id'])
                    if len(top_product_ids) >= top_k:
                        break
                product_ids = top_product_ids
            
            self.logger.info(f"找到 {len(product_ids)} 個相關產品：{product_ids}")
            
            # 第三步：查詢詳細規格
            detailed_specs = self.query_specs_by_product_ids(product_ids)
            
            if not detailed_specs:
                self.logger.warning("無法查詢到詳細規格資料")
                return {
                    "query": query,
                    "semantic_results": semantic_results,
                    "status": "no_spec_data",
                    "message": "找到相關產品但無法獲取詳細規格"
                }
            
            # 第四步：評估遊戲效能
            gaming_evaluations = []
            for spec in detailed_specs:
                evaluation = self.evaluate_gaming_performance(spec)
                evaluation['detailed_specs'] = spec
                gaming_evaluations.append(evaluation)
            
            # 按遊戲效能評分排序
            gaming_evaluations.sort(key=lambda x: x['scores']['overall_score'], reverse=True)
            
            # 第五步：使用 LLM 生成智能推薦（如果可用）
            llm_analysis = None
            if self.llm and len(gaming_evaluations) > 0:
                try:
                    # 準備給 LLM 的摘要資訊
                    top_3_laptops = gaming_evaluations[:3]
                    laptop_summary = []
                    for eval_result in top_3_laptops:
                        specs = eval_result['detailed_specs']
                        laptop_summary.append(
                            f"• {eval_result['model_name']}: "
                            f"遊戲評分 {eval_result['scores']['overall_score']}/10, "
                            f"CPU: {specs.get('cpu', 'N/A')}, "
                            f"GPU: {specs.get('gpu', 'N/A')}, "
                            f"記憶體: {specs.get('memory', 'N/A')}"
                        )
                    
                    prompt = f"""
                    用戶查詢：{query}
                    
                    根據以下遊戲筆電評估結果，請提供專業的購買建議：
                    
                    {chr(10).join(laptop_summary)}
                    
                    請以繁體中文回答，包含：
                    1. 最適合的型號推薦及原因
                    2. 各型號的優缺點分析  
                    3. 價格效能考量建議
                    4. 適用的遊戲類型
                    
                    請保持回答簡潔專業，不超過300字。
                    """
                    
                    llm_analysis = self.query_llm(prompt)
                    
                except Exception as e:
                    self.logger.warning(f"LLM 分析失敗，將跳過: {e}")
                    llm_analysis = "LLM 分析不可用，僅提供評分結果"
            
            # 整合最終結果
            final_result = {
                "query": query,
                "status": "success",
                "summary": {
                    "total_found": len(gaming_evaluations),
                    "top_gaming_score": gaming_evaluations[0]['scores']['overall_score'] if gaming_evaluations else 0,
                    "search_timestamp": datetime.now().isoformat()
                },
                "semantic_search_results": {
                    "child_chunks": semantic_results['child_chunks'][:5],  # 限制返回數量
                    "parent_documents": semantic_results.get('parent_documents', [])
                },
                "gaming_recommendations": gaming_evaluations,
                "llm_analysis": llm_analysis
            }
            
            self.logger.info(f"遊戲筆電搜尋完成，找到 {len(gaming_evaluations)} 個推薦產品")
            return final_result
            
        except Exception as e:
            self.logger.error(f"遊戲筆電搜尋失敗: {e}")
            return {
                "query": query,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # ==================== 通用產品規格搜尋方法－語義搜尋 ====================
    
    def search_product_data(self, message: str) -> Dict[str, Any]:
        """
        通用產品規格搜尋函式
        使用語義搜尋和 DuckDB 規格查詢
        
        Args:
            message: 客戶查詢字串
            
        Returns:
            JSON格式的產品規格資料
        """
        try:
            self.logger.info(f"開始產品規格搜尋：'{message}'")
            
            # 🎮 遊戲相關查詢增強處理
            enhanced_query = message
            gaming_keywords = ['遊戲', '游戲', 'gaming', 'game', '電玩', '遊戲體驗', '玩遊戲', '打遊戲']
            if any(keyword in message.lower() for keyword in gaming_keywords):
                # 為遊戲查詢添加GPU相關關鍵詞來增強語義匹配
                enhanced_query = f"{message} 專用顯卡 AMD Radeon 高效能 遊戲筆電"
                self.logger.info(f"偵測到遊戲查詢，增強搜尋詞彙: '{enhanced_query}'")
            
            # 第一步：語義搜尋
            semantic_results = self.milvus_semantic_search(
                query_text=enhanced_query,
                top_k=10
            )
            
            if not semantic_results:
                self.logger.warning("語義搜尋未找到相關結果")
                return {
                    "query": message,
                    "status": "no_results",
                    "products": []
                }
            
            # 第二步：提取 product_id，並正規化為字串做為 modeltype 比對鍵
            matched_keys = list({str(item.get('product_id', '')).strip() for item in semantic_results if str(item.get('product_id', '')).strip()})
            self.logger.info(f"Milvus 對應的 modeltype 候選（matched_keys）共 {len(matched_keys)} 個：{matched_keys}")

            if not matched_keys:
                # 有語義結果但沒有有效的 product_id（modelname 對應鍵）
                self.logger.warning("語義搜尋結果缺少可用的 product_id 作為 modelname 比對鍵")
                return {
                    "query": message,
                    "status": "no_results",
                    "products": []
                }

            # 第三步：在 DuckDB（semantic_sales_spec_all.db）查詢 nbtypes
            kb_info = self.knowledge_bases.get("semantic_sales_spec")
            if not kb_info:
                self.logger.error("語義銷售規格知識庫不存在")
                return {
                    "query": message,
                    "status": "no_database",
                    "products": []
                }

            detailed_specs = []
            try:
                # 延遲導入 duckdb，避免頂層依賴衝擊
                import duckdb  # type: ignore

                # 使用直接字串 IN 查詢，比對 modeltype（等同於 milvus product_id）
                # 只選取必要欄位以提升效能
                essential_fields = [
                    'modeltype', 'modelname', 'cpu', 'gpu', 'memory', 'storage', 
                    'lcd', 'battery', 'audio', 'wireless', 'bluetooth'
                ]
                fields_str = ', '.join(essential_fields)
                modeltype_strs = [f"'{mt}'" for mt in matched_keys]
                in_clause = ','.join(modeltype_strs)
                sql = f"""
                    SELECT {fields_str}
                    FROM nbtypes
                    WHERE modeltype IN ({in_clause})
                """

                self.logger.info(f"開始在 DuckDB 查詢 nbtypes（以 modeltype IN ({in_clause})）")
                con = duckdb.connect(kb_info["path"])  # 直接連線到 DuckDB 檔案
                try:
                    cur = con.execute(sql)
                    rows = cur.fetchall()
                    columns = [d[0] for d in cur.description] if cur.description else []
                    for r in rows:
                        # rows 為 tuple，需與欄位名稱對應成 dict
                        row_dict = {columns[i]: r[i] for i in range(len(columns))}
                        detailed_specs.append(row_dict)
                finally:
                    try:
                        con.close()
                    except Exception:
                        pass
            except Exception as duckdb_error:
                # 直接返回 error，並附上清楚訊息給呼叫端
                self.logger.error(f"DuckDB 查詢失敗: {duckdb_error}")
                return {
                    "query": message,
                    "status": "error",
                    "error": f"DuckDB query failed: {duckdb_error}",
                    "products": []
                }
                
            if not detailed_specs:
                self.logger.warning("無法查詢到詳細規格資料")
                return {
                    "query": message,
                    "status": "no_spec_data",
                    "matched_keys": matched_keys,
                    "products": []
                }
            
            # 第四步：整理回傳資料
            self.logger.info(f"成功找到 {len(detailed_specs)} 個產品規格")
            return {
                "query": message,
                "status": "success",
                "matched_keys": matched_keys,
                "count": len(detailed_specs),
                "products": detailed_specs
            }
            
        except Exception as e:
            self.logger.error(f"產品規格搜尋失敗: {e}")
            return {
                "query": message,
                "status": "error",
                "error": str(e),
                "products": []
            }

"""
backup function for search_product_data
def search_product_data(self, message: str) -> Dict[str, Any]:
        
        # 通用產品規格搜尋函式
        # 使用語義搜尋和 DuckDB 規格查詢
        
        # Args:
        #     message: 客戶查詢字串
            
        # Returns:
        #     JSON格式的產品規格資料
        
        try:
            self.logger.info(f"開始產品規格搜尋：'{message}'")
            
            # 第一步：語義搜尋
            semantic_results = self.milvus_semantic_search(
                query_text=message,
                top_k=10
            )
            
            if not semantic_results:
                self.logger.warning("語義搜尋未找到相關結果")
                return {
                    "query": message,
                    "status": "no_results",
                    "products": []
                }
            
            # 第二步：提取 product_id
            product_ids = list(set([item['product_id'] for item in semantic_results]))
            
            self.logger.info(f"找到 {len(product_ids)} 個相關產品：{product_ids}")
            
            # 第三步：查詢 DuckDB 詳細規格 (使用 SQLite 降級查詢)
            kb_info = self.knowledge_bases.get("semantic_sales_spec")
            if not kb_info:
                self.logger.error("語義銷售規格知識庫不存在")
                return {
                    "query": message,
                    "status": "no_database",
                    "products": []
                }
                
            with sqlite3.connect(kb_info["path"]) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 使用直接字串查詢
                id_conditions = ','.join([f"'{pid}'" for pid in product_ids])
                query = f"SELECT * FROM nbtypes WHERE modeltype IN ({id_conditions})"
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                detailed_specs = [dict(row) for row in rows]
                
            if not detailed_specs:
                self.logger.warning("無法查詢到詳細規格資料")
                return {
                    "query": message,
                    "status": "no_spec_data", 
                    "products": []
                }
            
            # 第四步：整理回傳資料
            self.logger.info(f"成功找到 {len(detailed_specs)} 個產品規格")
            return {
                "query": message,
                "status": "success",
                "products": detailed_specs
            }
            
        except Exception as e:
            self.logger.error(f"產品規格搜尋失敗: {e}")
            return {
                "query": message,
                "status": "error",
                "error": str(e),
                "products": []
            }
"""
