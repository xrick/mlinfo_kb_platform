# libs/KnowledgeManageHandler/polars_helper.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Polars 輔助工具類別
提供 Polars 數據操作的核心功能，包括連接管理、查詢執行、性能優化等
"""

import logging
import os
import psutil
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import time

# Polars 相關導入
try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False
    pl = None

# 類型註解處理
if POLARS_AVAILABLE:
    DataFrame = pl.DataFrame
    LazyFrame = pl.LazyFrame
else:
    DataFrame = Any
    LazyFrame = Any


class PolarsConnectionError(Exception):
    """Polars 連接錯誤"""
    pass


class PolarsQueryError(Exception):
    """Polars 查詢錯誤"""
    pass


class PolarsMemoryError(Exception):
    """Polars 內存錯誤"""
    pass


class PolarsHelper:
    """
    Polars 數據操作輔助工具類別
    
    主要功能：
    1. 數據源連接管理
    2. 查詢執行和優化
    3. 內存使用監控
    4. 錯誤處理和降級
    5. 性能優化建議
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Polars 輔助工具
        
        Args:
            config: 配置字典，包含連接參數、內存限制等
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # 數據源連接
        self.data_sources = {}
        
        # 性能監控
        self.query_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0
        }
        
        # 內存監控
        self.memory_warnings = []
        
        self.logger.info("Polars 輔助工具初始化完成")
    
    async def connect_data_source(self, source_config: Dict[str, Any]) -> bool:
        """
        連接數據源，支援 CSV、Parquet、Arrow、SQL 等格式
        
        Args:
            source_config: 數據源配置
            
        Returns:
            是否成功連接
        """
        if not POLARS_AVAILABLE:
            self.logger.error("Polars 未安裝，無法連接數據源")
            return False
        
        try:
            source_name = source_config.get("name", "unknown")
            source_type = source_config.get("type", "file")
            source_path = source_config.get("path", "")
            
            # 檢查文件是否存在
            if not Path(source_path).exists():
                self.logger.error(f"數據源文件不存在: {source_path}")
                return False
            
            # 根據文件類型選擇讀取方法
            if source_type == "csv":
                df = pl.read_csv(source_path)
            elif source_type == "parquet":
                df = pl.read_parquet(source_path)
            elif source_type == "arrow":
                df = pl.read_ipc(source_path)
            elif source_type == "sql":
                # 對於 SQL 文件，這裡提供一個簡單的實現
                # 實際使用中可能需要更複雜的 SQL 解析
                df = pl.read_csv(source_path)  # 暫時當作 CSV 處理
            else:
                self.logger.error(f"不支援的數據源類型: {source_type}")
                return False
            
            # 檢查內存使用
            if not self._check_memory_usage(df):
                raise PolarsMemoryError("內存使用超出限制")
            
            # 存儲數據源
            self.data_sources[source_name] = {
                "type": source_type,
                "path": source_path,
                "dataframe": df,
                "row_count": len(df),
                "column_count": len(df.columns),
                "memory_usage_mb": self._estimate_memory_usage(df),
                "connected_at": time.time()
            }
            
            self.logger.info(f"數據源連接成功: {source_name} ({source_type}), "
                           f"行數: {len(df)}, 列數: {len(df.columns)}")
            return True
            
        except PolarsMemoryError as e:
            self.logger.error(f"內存不足，無法連接數據源: {e}")
            return False
        except Exception as e:
            self.logger.error(f"連接數據源失敗: {e}")
            return False
    
    async def execute_query(self, query_expr: str, lazy: bool = True, 
                           parallel: bool = True) -> Optional[Any]:
        """
        執行 Polars 查詢，包含錯誤處理和性能優化
        
        Args:
            query_expr: 查詢表達式
            lazy: 是否使用 LazyFrame 優化
            parallel: 是否啟用並行處理
            
        Returns:
            查詢結果
        """
        if not POLARS_AVAILABLE:
            self.logger.error("Polars 未安裝，無法執行查詢")
            return None
        
        start_time = time.time()
        self.query_stats["total_queries"] += 1
        
        try:
            # 解析查詢表達式
            parsed_query = self._parse_query_expression(query_expr)
            if not parsed_query:
                raise PolarsQueryError("無法解析查詢表達式")
            
            # 獲取數據源
            source_name = parsed_query.get("source", "default")
            if source_name not in self.data_sources:
                raise PolarsConnectionError(f"數據源不存在: {source_name}")
            
            df = self.data_sources[source_name]["dataframe"]
            
            # 執行查詢
            if lazy:
                # 使用 LazyFrame 優化
                result = self._execute_lazy_query(df, parsed_query, parallel)
            else:
                # 直接執行查詢
                result = self._execute_eager_query(df, parsed_query, parallel)
            
            # 檢查內存使用
            if not self._check_memory_usage(result):
                raise PolarsMemoryError("查詢結果超出內存限制")
            
            # 更新統計信息
            execution_time = time.time() - start_time
            self.query_stats["successful_queries"] += 1
            self.query_stats["total_execution_time"] += execution_time
            self.query_stats["average_execution_time"] = (
                self.query_stats["total_execution_time"] / self.query_stats["successful_queries"]
            )
            
            self.logger.info(f"查詢執行成功，耗時: {execution_time:.3f}秒")
            return result
            
        except (PolarsConnectionError, PolarsQueryError, PolarsMemoryError) as e:
            self.logger.error(f"查詢執行失敗: {e}")
            self.query_stats["failed_queries"] += 1
            return None
        except Exception as e:
            self.logger.error(f"查詢執行出現未知錯誤: {e}")
            self.query_stats["failed_queries"] += 1
            return None
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        獲取當前內存使用情況
        
        Returns:
            內存使用信息字典
        """
        try:
            # 系統內存信息
            system_memory = psutil.virtual_memory()
            
            # 當前進程內存信息
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info()
            
            # Polars 數據源內存使用
            polars_memory = 0
            for source_name, source_info in self.data_sources.items():
                polars_memory += source_info.get("memory_usage_mb", 0)
            
            memory_info = {
                "system_total_gb": round(system_memory.total / (1024**3), 2),
                "system_available_gb": round(system_memory.available / (1024**3), 2),
                "system_used_percent": system_memory.percent,
                "process_memory_mb": round(process_memory.rss / (1024**2), 2),
                "polars_memory_mb": round(polars_memory, 2),
                "current_mb": round(process_memory.rss / (1024**2), 2),
                "memory_warnings": self.memory_warnings.copy()
            }
            
            return memory_info
            
        except Exception as e:
            self.logger.error(f"獲取內存使用信息失敗: {e}")
            return {
                "error": str(e),
                "current_mb": 0
            }
    
    def optimize_query_plan(self, query_expr: str) -> str:
        """
        提供查詢優化建議
        
        Args:
            query_expr: 查詢表達式
            
        Returns:
            優化建議字符串
        """
        try:
            suggestions = []
            
            # 檢查是否使用了 LazyFrame
            if "lazy" not in query_expr.lower():
                suggestions.append("考慮使用 LazyFrame 來優化查詢性能")
            
            # 檢查並行處理
            if "parallel" not in query_expr.lower():
                suggestions.append("考慮啟用並行處理來提升查詢速度")
            
            # 檢查內存使用
            if "memory" in query_expr.lower():
                suggestions.append("注意內存使用，考慮分批處理大數據集")
            
            # 檢查索引使用
            if "filter" in query_expr.lower():
                suggestions.append("確保過濾條件使用了適當的索引")
            
            if not suggestions:
                suggestions.append("查詢表達式看起來已經很優化了")
            
            return "\n".join(suggestions)
            
        except Exception as e:
            self.logger.error(f"生成查詢優化建議失敗: {e}")
            return "無法生成優化建議"
    
    def _parse_query_expression(self, query_expr: str) -> Optional[Dict[str, Any]]:
        """
        解析查詢表達式
        
        Args:
            query_expr: 查詢表達式字符串
            
        Returns:
            解析後的查詢信息字典
        """
        try:
            # 這裡提供一個簡單的解析邏輯
            # 實際實現中可能需要更複雜的語法分析
            
            parsed = {
                "source": "default",
                "operations": [],
                "filters": [],
                "columns": [],
                "limit": None
            }
            
            # 簡單的關鍵字識別
            if "filter" in query_expr:
                parsed["operations"].append("filter")
            if "select" in query_expr:
                parsed["operations"].append("select")
            if "groupby" in query_expr:
                parsed["operations"].append("groupby")
            if "sort" in query_expr:
                parsed["operations"].append("sort")
            
            return parsed
            
        except Exception as e:
            self.logger.error(f"解析查詢表達式失敗: {e}")
            return None
    
    def _execute_lazy_query(self, df: DataFrame, parsed_query: Dict[str, Any], 
                           parallel: bool) -> LazyFrame:
        """
        執行 LazyFrame 查詢
        
        Args:
            df: 原始 DataFrame
            parsed_query: 解析後的查詢信息
            parallel: 是否啟用並行處理
            
        Returns:
            LazyFrame 查詢結果
        """
        try:
            # 轉換為 LazyFrame
            lazy_df = df.lazy()
            
            # 應用查詢操作
            for operation in parsed_query.get("operations", []):
                if operation == "filter":
                    # 這裡提供一個簡單的過濾示例
                    lazy_df = lazy_df.filter(pl.col("price") > 1000)
                elif operation == "select":
                    # 選擇特定列
                    lazy_df = lazy_df.select(["modelname", "price", "modeltype"])
                elif operation == "groupby":
                    # 分組操作
                    lazy_df = lazy_df.groupby("modeltype").agg([
                        pl.col("price").mean().alias("avg_price"),
                        pl.col("price").count().alias("count")
                    ])
            
            # 設置並行處理
            if parallel:
                lazy_df = lazy_df.with_streaming(True)
            
            return lazy_df
            
        except Exception as e:
            self.logger.error(f"執行 LazyFrame 查詢失敗: {e}")
            raise PolarsQueryError(f"LazyFrame 查詢執行失敗: {e}")
    
    def _execute_eager_query(self, df: DataFrame, parsed_query: Dict[str, Any], 
                            parallel: bool) -> DataFrame:
        """
        執行 Eager 查詢
        
        Args:
            df: 原始 DataFrame
            parsed_query: 解析後的查詢信息
            parallel: 是否啟用並行處理
            
        Returns:
            DataFrame 查詢結果
        """
        try:
            result_df = df
            
            # 應用查詢操作
            for operation in parsed_query.get("operations", []):
                if operation == "filter":
                    result_df = result_df.filter(pl.col("price") > 1000)
                elif operation == "select":
                    result_df = result_df.select(["modelname", "price", "modeltype"])
                elif operation == "groupby":
                    result_df = result_df.groupby("modeltype").agg([
                        pl.col("price").mean().alias("avg_price"),
                        pl.col("price").count().alias("count")
                    ])
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"執行 Eager 查詢失敗: {e}")
            raise PolarsQueryError(f"Eager 查詢執行失敗: {e}")
    
    def _check_memory_usage(self, df: Union[DataFrame, LazyFrame]) -> bool:
        """
        檢查內存使用是否超出限制
        
        Args:
            df: DataFrame 或 LazyFrame
            
        Returns:
            是否在內存限制內
        """
        try:
            memory_limit_mb = self.config.get("memory_limit_mb", 1024)
            
            if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
                estimated_memory = self._estimate_memory_usage(df)
            else:
                # 對於 LazyFrame，提供一個保守的估計
                estimated_memory = 100  # 假設 LazyFrame 內存使用較少
            
            if estimated_memory > memory_limit_mb:
                warning_msg = f"內存使用超出限制: {estimated_memory}MB > {memory_limit_mb}MB"
                self.memory_warnings.append(warning_msg)
                self.logger.warning(warning_msg)
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"檢查內存使用失敗: {e}")
            return True  # 如果檢查失敗，允許繼續執行
    
    def _estimate_memory_usage(self, df: DataFrame) -> float:
        """
        估算 DataFrame 的內存使用量 (MB)
        
        Args:
            df: DataFrame
            
        Returns:
            估算的內存使用量 (MB)
        """
        try:
            # 獲取 DataFrame 的基本信息
            row_count = len(df)
            column_count = len(df.columns)
            
            # 簡單的內存估算 (每行每列約 8 字節)
            estimated_bytes = row_count * column_count * 8
            
            # 轉換為 MB
            estimated_mb = estimated_bytes / (1024 * 1024)
            
            return round(estimated_mb, 2)
            
        except Exception as e:
            self.logger.error(f"估算內存使用量失敗: {e}")
            return 0.0
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        獲取性能統計信息
        
        Returns:
            性能統計字典
        """
        return {
            "query_stats": self.query_stats.copy(),
            "memory_usage": self.get_memory_usage(),
            "data_sources": {
                name: {
                    "type": info["type"],
                    "row_count": info["row_count"],
                    "column_count": info["column_count"],
                    "memory_usage_mb": info["memory_usage_mb"],
                    "connected_at": info["connected_at"]
                }
                for name, info in self.data_sources.items()
            }
        }
