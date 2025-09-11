from pymilvus import connections, utility, Collection
from langchain_community.embeddings import HuggingFaceEmbeddings
from .DatabaseQuery import DatabaseQuery
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ParentChildMilvusQuery(DatabaseQuery):
    """
    Parent-Child Milvus 查詢類別
    支持 Parent-Child Chunking 架構的向量搜索
    """
    
    def __init__(self, host="localhost", port="19530", 
                 parent_collection_name=None, child_collection_name=None):
        self.host = host
        self.port = port
        self.parent_collection_name = parent_collection_name
        self.child_collection_name = child_collection_name
        self.parent_collection = None
        self.child_collection = None
        
        # 使用與 KnowledgeManager 一致的嵌入模型
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        self.connect()
        if parent_collection_name and child_collection_name:
            self.set_collections(parent_collection_name, child_collection_name)

    def connect(self):
        """連接到 Milvus"""
        try:
            connections.connect("default", host=self.host, port=self.port)
            logger.info(f"成功連接到 Milvus at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"連接 Milvus 失敗: {e}")

    def set_collections(self, parent_collection_name: str, child_collection_name: str):
        """設定 Parent 和 Child 集合"""
        try:
            # 設定 Parent 集合
            if utility.has_collection(parent_collection_name):
                self.parent_collection = Collection(parent_collection_name)
                self.parent_collection.load()
                self.parent_collection_name = parent_collection_name
                logger.info(f"成功設定並載入 Parent Collection: {parent_collection_name}")
            else:
                logger.error(f"Parent Collection '{parent_collection_name}' 不存在")
                self.parent_collection = None
                
            # 設定 Child 集合
            if utility.has_collection(child_collection_name):
                self.child_collection = Collection(child_collection_name)
                self.child_collection.load()
                self.child_collection_name = child_collection_name
                logger.info(f"成功設定並載入 Child Collection: {child_collection_name}")
            else:
                logger.error(f"Child Collection '{child_collection_name}' 不存在")
                self.child_collection = None
                
        except Exception as e:
            logger.error(f"設定 Collections 失敗: {e}")

    def search_parent(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索 Parent 集合"""
        if not self.parent_collection:
            logger.error("Parent Collection 未設定")
            return []

        try:
            # 將查詢文本向量化
            query_vector = self.embedding_model.embed_query(query_text)

            # 定義輸出欄位
            output_fields = [
                'id', 'text', 'source_file', 'row_index', 
                'modeltype', 'modelname', 'version', 'child_count'
            ]

            # 執行搜索
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            results = self.parent_collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=output_fields
            )

            # 格式化結果
            hits = results[0] if results and len(results) > 0 else []
            formatted_results = []
            
            for hit in hits:
                entity_data = {field: hit.entity.get(field) for field in output_fields}
                entity_data['id'] = hit.id
                entity_data['similarity_score'] = hit.score
                entity_data['chunk_type'] = 'parent'
                formatted_results.append(entity_data)
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"Parent 搜索失敗: {e}")
            return []

    def search_child(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索 Child 集合"""
        if not self.child_collection:
            logger.error("Child Collection 未設定")
            return []

        try:
            # 將查詢文本向量化
            query_vector = self.embedding_model.embed_query(query_text)

            # 定義輸出欄位
            output_fields = [
                'id', 'parent_id', 'text', 'field_group', 'chunk_index',
                'source_file', 'row_index', 'modeltype', 'modelname'
            ]

            # 執行搜索
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            results = self.child_collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=output_fields
            )

            # 格式化結果
            hits = results[0] if results and len(results) > 0 else []
            formatted_results = []
            
            for hit in hits:
                entity_data = {field: hit.entity.get(field) for field in output_fields}
                entity_data['id'] = hit.id
                entity_data['similarity_score'] = hit.score
                entity_data['chunk_type'] = 'child'
                formatted_results.append(entity_data)
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"Child 搜索失敗: {e}")
            return []

    def search(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """統一的搜索接口，返回 Child 結果（更精確）"""
        return self.search_child(query_text, top_k)

    def parent_child_search(self, query_text: str, 
                          child_top_k: int = 10, 
                          parent_top_k: int = 3) -> Dict[str, Any]:
        """
        Parent-Child 聯合搜索
        
        Args:
            query_text: 查詢文本
            child_top_k: Child 結果數量
            parent_top_k: Parent 結果數量
            
        Returns:
            包含 child 和 parent 結果的字典
        """
        try:
            # 搜索 Child chunks
            child_results = self.search_child(query_text, child_top_k)
            
            # 搜索 Parent documents
            parent_results = self.search_parent(query_text, parent_top_k)
            
            return {
                "query": query_text,
                "child_chunks": child_results,
                "parent_documents": parent_results,
                "total_child_chunks": len(child_results),
                "total_parent_docs": len(parent_results)
            }
            
        except Exception as e:
            logger.error(f"Parent-Child 搜索失敗: {e}")
            return {
                "query": query_text,
                "child_chunks": [],
                "parent_documents": [],
                "total_child_chunks": 0,
                "total_parent_docs": 0,
                "error": str(e)
            }

    def query(self, *args, **kwargs):
        """實現 DatabaseQuery 接口"""
        if 'query_text' in kwargs:
            return self.search(kwargs['query_text'], kwargs.get('top_k', 5))
        return "請提供 'query_text' 參數。"

    def disconnect(self):
        """斷開連接"""
        try:
            connections.disconnect("default")
            logger.info("已斷開 Milvus 連接")
        except Exception as e:
            logger.warning(f"斷開連接時發生錯誤: {e}")
