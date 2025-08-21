#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試Milvus連接和基本功能
"""

from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Milvus配置
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "new_nb_pc_v1"
OLD_COLLECTION_NAME = "new_pc_v2"

def test_milvus_connection():
    """測試Milvus連接"""
    try:
        logger.info(f"嘗試連接到Milvus: {MILVUS_HOST}:{MILVUS_PORT}")
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
        logger.info("✅ 成功連接到Milvus")
        return True
    except Exception as e:
        logger.error(f"❌ 連接Milvus失敗: {e}")
        return False

def check_and_drop_old_collection():
    """檢查並刪除舊的collection"""
    try:
        if utility.has_collection(OLD_COLLECTION_NAME):
            logger.info(f"發現舊collection: {OLD_COLLECTION_NAME}")
            logger.info("正在刪除舊collection...")
            utility.drop_collection(OLD_COLLECTION_NAME)
            logger.info(f"✅ 成功刪除collection: {OLD_COLLECTION_NAME}")
        else:
            logger.info(f"✅ 未發現舊collection: {OLD_COLLECTION_NAME}")
        return True
    except Exception as e:
        logger.error(f"❌ 刪除舊collection失敗: {e}")
        return False

def test_collection_creation():
    """測試collection建立功能"""
    try:
        # 定義schema
        fields = [
            FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="doc_id", dtype=DataType.INT64),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="parent_text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="query_vector", dtype=DataType.FLOAT_VECTOR, dim=384)
        ]
        
        schema = CollectionSchema(fields, "Notebook specs with parent-child chunking")
        
        # 建立collection
        logger.info(f"正在建立collection: {COLLECTION_NAME}")
        collection = Collection(COLLECTION_NAME, schema)
        
        # 建立索引
        logger.info("正在建立向量索引...")
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        collection.create_index("query_vector", index_params)
        
        logger.info(f"✅ 成功建立collection: {COLLECTION_NAME}")
        
        # 清理測試collection
        logger.info("清理測試collection...")
        utility.drop_collection(COLLECTION_NAME)
        logger.info("✅ 測試完成，collection已清理")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 建立collection失敗: {e}")
        return False

def main():
    """主函數"""
    logger.info("🧪 開始測試Milvus連接和基本功能")
    logger.info("=" * 60)
    
    # 測試1: 連接Milvus
    logger.info("\n1️⃣ 測試Milvus連接")
    if not test_milvus_connection():
        logger.error("無法連接到Milvus，測試終止")
        return
    
    # 測試2: 檢查並刪除舊collection
    logger.info("\n2️⃣ 檢查並刪除舊collection")
    if not check_and_drop_old_collection():
        logger.error("刪除舊collection失敗")
        return
    
    # 測試3: 測試collection建立
    logger.info("\n3️⃣ 測試collection建立功能")
    if not test_collection_creation():
        logger.error("建立collection測試失敗")
        return
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 所有測試通過！Milvus環境準備就緒")
    logger.info("\n💡 下一步：執行parent-child chunking和資料匯入")

if __name__ == "__main__":
    main()

