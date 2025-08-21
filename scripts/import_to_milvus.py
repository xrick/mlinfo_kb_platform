#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
將筆電規格資料匯入到Milvus
使用Parent-Child Chunking技術
"""

import os
import csv
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection
from sentence_transformers import SentenceTransformer

# 導入chunking引擎
from parent_child_chunking import NotebookParentChildChunker

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/milvus_import.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "new_nb_pc_v1"
CSV_DIR = "data/raw/EM_New TTL_241104_AllTransformedToGoogleSheet"
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
DIMENSION = 384

class MilvusNotebookImporter:
    """Milvus筆電規格資料匯入器"""
    
    def __init__(self):
        self.connection = None
        self.collection = None
        self.embedding_model = None
        self.chunker = NotebookParentChildChunker()
        
        # 統計資訊
        self.stats = {
            'files_processed': 0,
            'total_products': 0,
            'total_chunks': 0,
            'parent_chunks': 0,
            'child_chunks': 0,
            'milvus_inserts': 0,
            'errors': 0
        }
    
    def connect_to_milvus(self):
        """連接到Milvus"""
        try:
            logger.info(f"連接到Milvus: {MILVUS_HOST}:{MILVUS_PORT}")
            connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
            logger.info("✅ 成功連接到Milvus")
            return True
        except Exception as e:
            logger.error(f"❌ 連接Milvus失敗: {e}")
            return False
    
    def setup_collection(self):
        """建立或設定collection"""
        try:
            # 檢查collection是否存在
            if utility.has_collection(COLLECTION_NAME):
                logger.info(f"Collection '{COLLECTION_NAME}' 已存在，正在刪除...")
                utility.drop_collection(COLLECTION_NAME)
            
            # 定義schema
            fields = [
                FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="doc_id", dtype=DataType.INT64),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="parent_text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=1000),
                FieldSchema(name="query_vector", dtype=DataType.FLOAT_VECTOR, dim=DIMENSION),
                FieldSchema(name="chunk_type", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="product_id", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="modeltype", dtype=DataType.VARCHAR, max_length=100)
            ]
            
            schema = CollectionSchema(fields, "Notebook specs with parent-child chunking")
            
            # 建立collection
            logger.info(f"建立collection: {COLLECTION_NAME}")
            self.collection = Collection(COLLECTION_NAME, schema)
            
            # 建立索引
            logger.info("建立向量索引...")
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            self.collection.create_index("query_vector", index_params)
            
            logger.info("✅ Collection建立完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 建立collection失敗: {e}")
            return False
    
    def load_embedding_model(self):
        """載入embedding模型"""
        try:
            logger.info(f"載入embedding模型: {EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info("✅ Embedding模型載入完成")
            return True
        except Exception as e:
            logger.error(f"❌ 載入embedding模型失敗: {e}")
            return False
    
    def generate_embedding(self, text: str) -> List[float]:
        """生成文本的embedding向量"""
        try:
            if not self.embedding_model:
                raise ValueError("Embedding模型未載入")
            
            # 清理文本
            cleaned_text = text.strip()
            if not cleaned_text:
                return [0.0] * DIMENSION
            
            # 生成embedding
            embedding = self.embedding_model.encode(cleaned_text)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"生成embedding失敗: {e}")
            return [0.0] * DIMENSION
    
    def process_csv_file(self, csv_file: Path) -> List[Dict[str, Any]]:
        """處理單個CSV檔案"""
        try:
            logger.info(f"處理檔案: {csv_file.name}")
            
            # 讀取CSV
            df = pd.read_csv(csv_file, dtype={'modeltype': str})
            
            # 添加來源檔案資訊
            df['source_file'] = csv_file.name
            
            # 轉換為字典列表
            products = df.to_dict('records')
            
            logger.info(f"檔案 {csv_file.name} 包含 {len(products)} 個產品")
            return products
            
        except Exception as e:
            logger.error(f"處理檔案 {csv_file.name} 失敗: {e}")
            return []
    
    def create_chunks_with_embeddings(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """為產品建立chunks並生成embeddings"""
        try:
            logger.info(f"開始為 {len(products)} 個產品建立chunks")
            
            # 使用chunking引擎建立chunks
            parent_chunks, child_chunks = self.chunker.batch_create_chunks(products)
            
            all_chunks = []
            chunk_id_counter = 0
            
            # 處理parent chunks
            for parent_chunk in parent_chunks:
                chunk_id_counter += 1
                
                # 生成embedding
                embedding = self.generate_embedding(parent_chunk['content'])
                
                # 準備Milvus插入資料
                milvus_chunk = {
                    'doc_id': chunk_id_counter,
                    'source': parent_chunk.get('source', ''),
                    'parent_text': parent_chunk['content'],
                    'chunk_text': parent_chunk['content'],
                    'query_vector': embedding,
                    'chunk_type': 'parent',
                    'product_id': parent_chunk.get('product_id', ''),
                    'modeltype': parent_chunk.get('modeltype', '')
                }
                
                all_chunks.append(milvus_chunk)
                self.stats['parent_chunks'] += 1
            
            # 處理child chunks
            for child_chunk in child_chunks:
                if not child_chunk or not child_chunk.get('content'):
                    continue
                
                chunk_id_counter += 1
                
                # 生成embedding
                embedding = self.generate_embedding(child_chunk['content'])
                
                # 準備Milvus插入資料
                milvus_chunk = {
                    'doc_id': chunk_id_counter,
                    'source': child_chunk.get('source', ''),
                    'parent_text': '',  # child chunks沒有parent_text
                    'chunk_text': child_chunk['content'],
                    'query_vector': embedding,
                    'chunk_type': child_chunk['chunk_type'],
                    'product_id': child_chunk.get('product_id', ''),
                    'modeltype': child_chunk.get('modeltype', '')
                }
                
                all_chunks.append(milvus_chunk)
                self.stats['child_chunks'] += 1
            
            self.stats['total_chunks'] = len(all_chunks)
            logger.info(f"成功建立 {len(all_chunks)} 個chunks")
            
            return all_chunks
            
        except Exception as e:
            logger.error(f"建立chunks失敗: {e}")
            return []
    
    def insert_to_milvus(self, chunks: List[Dict[str, Any]]):
        """將chunks插入到Milvus"""
        try:
            if not chunks:
                logger.warning("沒有chunks需要插入")
                return
            
            logger.info(f"開始插入 {len(chunks)} 個chunks到Milvus")
            
            # 準備插入資料 - 按照schema欄位順序
            doc_ids = []
            sources = []
            parent_texts = []
            chunk_texts = []
            query_vectors = []
            chunk_types = []
            product_ids = []
            modeltypes = []
            
            for chunk in chunks:
                doc_ids.append(chunk['doc_id'])
                sources.append(chunk['source'])
                parent_texts.append(chunk['parent_text'])
                chunk_texts.append(chunk['chunk_text'])
                query_vectors.append(chunk['query_vector'])
                chunk_types.append(chunk['chunk_type'])
                product_ids.append(chunk['product_id'])
                modeltypes.append(chunk['modeltype'])
            
            # 按照schema欄位順序組織資料
            insert_data = [
                doc_ids,
                sources,
                parent_texts,
                chunk_texts,
                query_vectors,
                chunk_types,
                product_ids,
                modeltypes
            ]
            
            # 插入資料
            try:
                self.collection.insert(insert_data)
                logger.info(f"成功插入 {len(chunks)} 個chunks到Milvus")
                self.stats['milvus_inserts'] += len(chunks)
            except Exception as e:
                logger.error(f"插入到Milvus失敗: {e}")
                self.stats['errors'] += len(chunks)
                raise
            
            logger.info("✅ 所有chunks插入完成")
            
        except Exception as e:
            logger.error(f"插入到Milvus失敗: {e}")
            raise
    
    def process_all_files(self):
        """處理所有CSV檔案"""
        try:
            # 確保logs目錄存在
            os.makedirs('logs', exist_ok=True)
            
            # 連接到Milvus
            if not self.connect_to_milvus():
                return False
            
            # 設定collection
            if not self.setup_collection():
                return False
            
            # 載入embedding模型
            if not self.load_embedding_model():
                return False
            
            # 獲取所有CSV檔案
            csv_files = list(Path(CSV_DIR).glob('*.csv'))
            csv_files.sort()
            
            if not csv_files:
                logger.error(f"在目錄 {CSV_DIR} 中未找到CSV檔案")
                return False
            
            logger.info(f"找到 {len(csv_files)} 個CSV檔案")
            
            # 處理每個檔案
            all_products = []
            for csv_file in csv_files:
                try:
                    products = self.process_csv_file(csv_file)
                    all_products.extend(products)
                    self.stats['files_processed'] += 1
                    
                except Exception as e:
                    logger.error(f"處理檔案 {csv_file.name} 失敗: {e}")
                    continue
            
            self.stats['total_products'] = len(all_products)
            logger.info(f"總共處理 {len(all_products)} 個產品")
            
            # 建立chunks
            chunks = self.create_chunks_with_embeddings(all_products)
            
            # 插入到Milvus
            self.insert_to_milvus(chunks)
            
            # 載入collection到記憶體
            logger.info("載入collection到記憶體...")
            self.collection.load()
            
            # 刷新資料
            logger.info("刷新collection資料...")
            self.collection.flush()
            
            logger.info("✅ 所有檔案處理完成")
            return True
            
        except Exception as e:
            logger.error(f"處理檔案失敗: {e}")
            return False
        
        finally:
            # 清理連接
            if self.connection:
                connections.disconnect("default")
                logger.info("已斷開Milvus連接")
    
    def get_stats(self) -> Dict[str, Any]:
        """取得處理統計資訊"""
        return self.stats.copy()
    
    def print_stats(self):
        """顯示統計資訊"""
        stats = self.get_stats()
        logger.info("=" * 60)
        logger.info("📊 處理統計資訊:")
        logger.info(f"處理檔案數: {stats['files_processed']}")
        logger.info(f"總產品數: {stats['total_products']}")
        logger.info(f"總Chunks數: {stats['total_chunks']}")
        logger.info(f"Parent Chunks: {stats['parent_chunks']}")
        logger.info(f"Child Chunks: {stats['child_chunks']}")
        logger.info(f"Milvus插入數: {stats['milvus_inserts']}")
        logger.info(f"錯誤數: {stats['errors']}")
        logger.info("=" * 60)

def main():
    """主函數"""
    logger.info("🚀 開始執行筆電規格資料匯入到Milvus")
    logger.info("=" * 60)
    
    importer = MilvusNotebookImporter()
    
    try:
        success = importer.process_all_files()
        
        if success:
            logger.info("🎉 資料匯入成功完成！")
            importer.print_stats()
        else:
            logger.error("❌ 資料匯入失敗")
            
    except Exception as e:
        logger.error(f"執行失敗: {e}")
        raise

if __name__ == "__main__":
    main()
