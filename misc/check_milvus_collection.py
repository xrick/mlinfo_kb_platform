#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 Milvus 資料庫中是否存在 product_semantic_chunks 集合
"""

from pymilvus import connections, utility, Collection
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Milvus 配置
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "product_semantic_chunks"

def connect_to_milvus():
    """連接到 Milvus"""
    try:
        logger.info(f"嘗試連接到 Milvus: {MILVUS_HOST}:{MILVUS_PORT}")
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
        logger.info("✅ 成功連接到 Milvus")
        return True
    except Exception as e:
        logger.error(f"❌ 連接 Milvus 失敗: {e}")
        return False

def check_collection_exists():
    """檢查集合是否存在"""
    try:
        if utility.has_collection(COLLECTION_NAME):
            logger.info(f"✅ 集合 '{COLLECTION_NAME}' 存在")
            
            # 獲取集合詳細資訊
            collection = Collection(COLLECTION_NAME)
            schema = collection.schema
            
            logger.info(f"集合名稱: {collection.name}")
            logger.info(f"集合描述: {schema.description}")
            logger.info(f"字段數量: {len(schema.fields)}")
            
            # 顯示字段資訊
            logger.info("字段詳情:")
            for field in schema.fields:
                logger.info(f"  - {field.name}: {field.dtype} (主鍵: {field.is_primary})")
            
            # 獲取集合統計資訊
            stats = collection.get_statistics()
            logger.info(f"集合統計: {stats}")
            
            return True
        else:
            logger.warning(f"❌ 集合 '{COLLECTION_NAME}' 不存在")
            return False
            
    except Exception as e:
        logger.error(f"檢查集合時發生錯誤: {e}")
        return False

def list_all_collections():
    """列出所有集合"""
    try:
        collections = utility.list_collections()
        logger.info(f"Milvus 中的所有集合: {collections}")
        return collections
    except Exception as e:
        logger.error(f"列出集合時發生錯誤: {e}")
        return []

def main():
    """主函數"""
    logger.info("=== 檢查 Milvus 集合 ===")
    
    # 連接到 Milvus
    if not connect_to_milvus():
        return
    
    # 列出所有集合
    logger.info("--- 列出所有集合 ---")
    all_collections = list_all_collections()
    
    # 檢查目標集合
    logger.info(f"--- 檢查集合 '{COLLECTION_NAME}' ---")
    exists = check_collection_exists()
    
    # 總結
    logger.info("=== 檢查結果 ===")
    if exists:
        logger.info(f"✅ 集合 '{COLLECTION_NAME}' 存在於 Milvus 中")
    else:
        logger.info(f"❌ 集合 '{COLLECTION_NAME}' 不存在於 Milvus 中")
        if all_collections:
            logger.info(f"可用的集合: {all_collections}")
    
    # 斷開連接
    connections.disconnect("default")
    logger.info("已斷開 Milvus 連接")

if __name__ == "__main__":
    main()
