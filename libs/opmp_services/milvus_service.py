#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Milvus Collection Viewer 服務
提供 Milvus 資料庫查看和管理功能
"""

import logging
from typing import List, Dict, Any, Optional
from pymilvus import connections, utility, Collection, DataType
from config import MILVUS_HOST, MILVUS_PORT

logger = logging.getLogger(__name__)


class MilvusService:
    """Milvus 服務類，提供集合查看和資料存取功能"""
    
    def __init__(self, host: str = None, port: str = None):
        """初始化 Milvus 服務
        
        Args:
            host: Milvus 主機位址，預設使用配置檔案中的設定
            port: Milvus 連接埠，預設使用配置檔案中的設定
        """
        self.host = host or MILVUS_HOST
        self.port = port or MILVUS_PORT
        self.connection_alias = "milvus_viewer"
        self._is_connected = False
        
    def connect(self) -> bool:
        """連接到 Milvus 服務
        
        Returns:
            bool: 連接是否成功
        """
        try:
            # 如果已經連接，先斷開
            if self._is_connected:
                self.disconnect()
                
            connections.connect(
                alias=self.connection_alias,
                host=self.host,
                port=self.port
            )
            self._is_connected = True
            logger.info(f"成功連接到 Milvus: {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"連接 Milvus 失敗: {e}")
            self._is_connected = False
            return False
    
    def disconnect(self):
        """斷開 Milvus 連接"""
        try:
            if self._is_connected:
                connections.disconnect(self.connection_alias)
                self._is_connected = False
                logger.info("已斷開 Milvus 連接")
        except Exception as e:
            logger.warning(f"斷開 Milvus 連接時發生錯誤: {e}")
    
    def is_connected(self) -> bool:
        """檢查是否已連接到 Milvus
        
        Returns:
            bool: 連接狀態
        """
        return self._is_connected
    
    def get_databases(self) -> List[str]:
        """獲取所有可用的資料庫
        
        Returns:
            List[str]: 資料庫名稱列表
        """
        try:
            if not self._is_connected:
                self.connect()
                
            # Milvus 預設只有一個資料庫 "default"
            # 這個方法為未來多資料庫支援做準備
            return ["default"]
            
        except Exception as e:
            logger.error(f"獲取資料庫列表失敗: {e}")
            return []
    
    def get_collections(self) -> List[Dict[str, Any]]:
        """獲取當前資料庫中的所有集合
        
        Returns:
            List[Dict]: 集合資訊列表，包含名稱和基本統計
        """
        try:
            if not self._is_connected:
                if not self.connect():
                    return []
            
            collection_names = utility.list_collections(using=self.connection_alias)
            collections_info = []
            
            for name in collection_names:
                try:
                    collection = Collection(name, using=self.connection_alias)
                    # 獲取集合基本資訊
                    row_count = collection.num_entities
                    
                    # 獲取集合狀態
                    status = "loaded" if collection.has_index() else "not_loaded"
                    
                    collections_info.append({
                        "name": name,
                        "row_count": row_count,
                        "status": status,
                        "description": collection.schema.description or ""
                    })
                    
                except Exception as e:
                    logger.warning(f"獲取集合 {name} 資訊時發生錯誤: {e}")
                    collections_info.append({
                        "name": name,
                        "row_count": 0,
                        "status": "error",
                        "description": f"錯誤: {str(e)}"
                    })
            
            return collections_info
            
        except Exception as e:
            logger.error(f"獲取集合列表失敗: {e}")
            return []
    
    def get_collection_schema(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """獲取指定集合的 Schema 資訊
        
        Args:
            collection_name: 集合名稱
            
        Returns:
            Dict: Schema 資訊，如果失敗則返回 None
        """
        try:
            if not self._is_connected:
                if not self.connect():
                    return None
            
            if not utility.has_collection(collection_name, using=self.connection_alias):
                logger.warning(f"集合 {collection_name} 不存在")
                return None
            
            collection = Collection(collection_name, using=self.connection_alias)
            schema = collection.schema
            
            # 轉換 Schema 為可序列化的格式
            fields_info = []
            for field in schema.fields:
                field_info = {
                    "name": field.name,
                    "data_type": self._datatype_to_string(field.dtype),
                    "is_primary": field.is_primary,
                    "description": field.description or ""
                }
                
                # 如果是向量欄位，添加維度資訊
                if field.dtype in [DataType.FLOAT_VECTOR, DataType.BINARY_VECTOR]:
                    field_info["dimension"] = field.params.get("dim", "未知")
                
                fields_info.append(field_info)
            
            # 獲取索引資訊
            indexes_info = []
            try:
                indexes = collection.indexes
                for index in indexes:
                    indexes_info.append({
                        "field_name": index.field_name,
                        "index_type": index.params.get("index_type", "未知"),
                        "metric_type": index.params.get("metric_type", "未知")
                    })
            except Exception as e:
                logger.warning(f"獲取集合索引資訊失敗: {e}")
            
            return {
                "collection_name": collection_name,
                "description": schema.description or "",
                "fields": fields_info,
                "indexes": indexes_info
            }
            
        except Exception as e:
            logger.error(f"獲取集合 Schema 失敗: {e}")
            return None
    
    def get_collection_data(self, collection_name: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """獲取集合中的資料（分頁）
        
        Args:
            collection_name: 集合名稱
            limit: 每頁資料數量
            offset: 偏移量
            
        Returns:
            Dict: 包含資料和分頁資訊的字典
        """
        try:
            if not self._is_connected:
                if not self.connect():
                    return {"data": [], "total": 0, "has_more": False}
            
            if not utility.has_collection(collection_name, using=self.connection_alias):
                return {"data": [], "total": 0, "has_more": False}
            
            collection = Collection(collection_name, using=self.connection_alias)
            
            # 確保集合已載入
            if not collection.has_index():
                collection.load()
            
            # 獲取總記錄數
            total_count = collection.num_entities
            
            # 獲取非向量欄位（向量欄位太大，不適合直接顯示）
            schema = collection.schema
            output_fields = []
            vector_fields = []
            primary_key_field = None

            for field in schema.fields:
                if field.dtype in [DataType.FLOAT_VECTOR, DataType.BINARY_VECTOR]:
                    vector_fields.append({
                        "name": field.name,
                        "dimension": field.params.get("dim", "未知")
                    })
                elif not field.is_primary:  # 主鍵欄位會自動包含
                    output_fields.append(field.name)
                else:
                    # 找到主鍵欄位
                    primary_key_field = field

            # 執行查詢（限制條件查詢，因為 Milvus 不直接支援 OFFSET）
            # 這裡使用一個簡單的策略：查詢前 offset + limit 條記錄，然後在應用層做分頁
            query_limit = min(offset + limit, 16384)  # Milvus 查詢限制

            # 構造查詢表達式（根據實際主鍵類型動態構建）
            expr = None
            if primary_key_field:
                if primary_key_field.dtype in [DataType.INT8, DataType.INT16, DataType.INT32, DataType.INT64]:
                    # 整數型主鍵
                    expr = f"{primary_key_field.name} >= 0"
                elif primary_key_field.dtype in [DataType.VARCHAR, DataType.STRING]:
                    # 字串型主鍵，使用不等於空字串的表達式
                    expr = f'{primary_key_field.name} != ""'
                else:
                    logger.warning(f"不支援的主鍵類型: {primary_key_field.dtype}")
                    expr = None
            else:
                logger.warning("找不到主鍵欄位")
                expr = None
            
            try:
                if expr:
                    # 嘗試使用查詢
                    results = collection.query(
                        expr=expr,
                        output_fields=output_fields,
                        limit=query_limit
                    )

                    # 應用分頁
                    paginated_results = results[offset:offset + limit] if offset < len(results) else []
                else:
                    logger.warning("無法構造查詢表達式，無法獲取資料")
                    paginated_results = []

            except Exception as query_error:
                logger.warning(f"查詢失敗，嘗試使用搜尋方法: {query_error}")
                # 如果查詢失敗，提供基本資訊
                paginated_results = []
            
            # 處理結果
            processed_data = []
            for record in paginated_results:
                processed_record = {}
                for key, value in record.items():
                    # 處理特殊資料類型
                    if isinstance(value, (list, tuple)) and len(value) > 10:
                        processed_record[key] = f"[陣列，長度: {len(value)}]"
                    else:
                        processed_record[key] = value
                processed_data.append(processed_record)
            
            return {
                "data": processed_data,
                "total": total_count,
                "has_more": (offset + limit) < total_count,
                "vector_fields": vector_fields,
                "current_page": offset // limit + 1,
                "page_size": limit
            }
            
        except Exception as e:
            logger.error(f"獲取集合資料失敗: {e}")
            return {"data": [], "total": 0, "has_more": False, "error": str(e)}
    
    def get_collection_statistics(self, collection_name: str) -> Dict[str, Any]:
        """獲取集合的統計資訊
        
        Args:
            collection_name: 集合名稱
            
        Returns:
            Dict: 統計資訊
        """
        try:
            if not self._is_connected:
                if not self.connect():
                    return {}
            
            if not utility.has_collection(collection_name, using=self.connection_alias):
                return {"error": "集合不存在"}
            
            collection = Collection(collection_name, using=self.connection_alias)
            
            # 獲取更多詳細資訊
            schema = collection.schema
            
            return {
                "collection_name": collection_name,
                "row_count": collection.num_entities,
                "field_count": len(schema.fields),
                "description": schema.description or "",
                "is_loaded": collection.has_index(),
                "raw_stats": {"row_count": collection.num_entities}
            }
            
        except Exception as e:
            logger.error(f"獲取集合統計資訊失敗: {e}")
            return {"error": str(e)}
    
    def _datatype_to_string(self, datatype) -> str:
        """將 Milvus 資料類型轉換為字串
        
        Args:
            datatype: Milvus DataType
            
        Returns:
            str: 資料類型字串
        """
        type_mapping = {
            DataType.BOOL: "Boolean",
            DataType.INT8: "Int8",
            DataType.INT16: "Int16", 
            DataType.INT32: "Int32",
            DataType.INT64: "Int64",
            DataType.FLOAT: "Float",
            DataType.DOUBLE: "Double",
            DataType.STRING: "String",
            DataType.VARCHAR: "VarChar",
            DataType.FLOAT_VECTOR: "FloatVector",
            DataType.BINARY_VECTOR: "BinaryVector",
        }
        return type_mapping.get(datatype, str(datatype))
    
    def __enter__(self):
        """上下文管理器進入"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()