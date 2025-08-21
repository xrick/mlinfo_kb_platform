#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驗證Milvus Collection的內容和功能
"""

from pymilvus import connections, Collection
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "new_nb_pc_v1"

def connect_to_milvus():
    """連接到Milvus"""
    try:
        logger.info(f"連接到Milvus: {MILVUS_HOST}:{MILVUS_PORT}")
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
        logger.info("✅ 成功連接到Milvus")
        return True
    except Exception as e:
        logger.error(f"❌ 連接Milvus失敗: {e}")
        return False

def verify_collection():
    """驗證collection的內容"""
    try:
        # 載入collection
        collection = Collection(COLLECTION_NAME)
        collection.load()
        
        # 獲取collection統計資訊
        logger.info(f"Collection名稱: {COLLECTION_NAME}")
        logger.info(f"實體數量: {collection.num_entities}")
        
        # 查詢前5筆資料
        logger.info("\n📋 前5筆資料:")
        results = collection.query(
            expr="pk >= 0",
            output_fields=["pk", "doc_id", "chunk_type", "product_id", "modeltype", "source"],
            limit=5
        )
        
        for i, result in enumerate(results, 1):
            logger.info(f"  {i}. PK: {result['pk']}, DocID: {result['doc_id']}, "
                      f"Type: {result['chunk_type']}, Product: {result['product_id']}, "
                      f"Model: {result['modeltype']}, Source: {result['source']}")
        
        # 統計各類型chunks數量
        logger.info("\n📊 Chunk類型統計:")
        parent_results = collection.query(
            expr="chunk_type == 'parent'",
            output_fields=["pk"],
            limit=1000
        )
        child_results = collection.query(
            expr="chunk_type != 'parent'",
            output_fields=["pk"],
            limit=1000
        )
        
        logger.info(f"  Parent Chunks: {len(parent_results)}")
        logger.info(f"  Child Chunks: {len(child_results)}")
        
        # 統計各型號的chunks數量
        logger.info("\n📊 各型號統計:")
        model_results = collection.query(
            expr="pk >= 0",
            output_fields=["modeltype"],
            limit=1000
        )
        
        model_counts = {}
        for result in model_results:
            modeltype = result['modeltype']
            if modeltype:
                model_counts[modeltype] = model_counts.get(modeltype, 0) + 1
        
        for modeltype, count in sorted(model_counts.items()):
            logger.info(f"  {modeltype}: {count} chunks")
        
        # 測試向量搜尋
        logger.info("\n🔍 測試向量搜尋:")
        test_query = "AMD Ryzen processor"
        
        # 執行向量搜尋
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        search_results = collection.search(
            data=[[0.1] * 384],  # 測試向量
            anns_field="query_vector",
            param=search_params,
            limit=3,
            output_fields=["chunk_type", "product_id", "chunk_text"]
        )
        
        logger.info(f"搜尋查詢: '{test_query}'")
        for i, hit in enumerate(search_results[0]):
            logger.info(f"  結果 {i+1}: ID={hit.id}, Distance={hit.distance:.4f}, "
                      f"Type={hit.entity.get('chunk_type')}, Product={hit.entity.get('product_id')}")
            chunk_text = hit.entity.get('chunk_text', '')[:100]
            logger.info(f"    Text: {chunk_text}...")
        
        logger.info("✅ Collection驗證完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ Collection驗證失敗: {e}")
        return False

def main():
    """主函數"""
    logger.info("🔍 開始驗證Milvus Collection")
    logger.info("=" * 60)
    
    # 連接Milvus
    if not connect_to_milvus():
        return
    
    try:
        # 驗證collection
        success = verify_collection()
        
        if success:
            logger.info("🎉 Collection驗證成功！")
        else:
            logger.error("❌ Collection驗證失敗")
            
    except Exception as e:
        logger.error(f"執行失敗: {e}")
        raise
    
    finally:
        # 清理連接
        connections.disconnect("default")
        logger.info("已斷開Milvus連接")

if __name__ == "__main__":
    main()

