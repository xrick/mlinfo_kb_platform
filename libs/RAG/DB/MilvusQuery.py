# libs/RAG/DB/MilvusQuery.py
from pymilvus import connections, utility, Collection
from langchain_community.embeddings import HuggingFaceEmbeddings
from .DatabaseQuery import DatabaseQuery
from logging import Logger

class MilvusQuery(DatabaseQuery):
    def __init__(self, host="localhost", port="19530", collection_name=None):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.collection = None
        
        # 使用與 KnowledgeManager 一致的嵌入模型
        self.embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.connect()
        if self.collection_name:
            # 指定新的 collection 名稱
            self.set_collection(collection_name if collection_name else "product_semantic_chunks")

    def connect(self):
        try:
            connections.connect("default", host=self.host, port=self.port)
            print(f"成功連接到 Milvus at {self.host}:{self.port}")
        except Exception as e:
            print(f"連接 Milvus 失敗: {e}")

    def set_collection(self, collection_name: str):
        
        # try:
            # Logger.info(f"^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n{utility.list_collections()}\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        if utility.has_collection(collection_name):
            self.collection = Collection(collection_name)
            self.collection.load()
            self.collection_name = collection_name
            print(f"成功設定並載入 Collection: {collection_name}")
        else:
            print(f"錯誤: Collection '{collection_name}' 不存在。")
            self.collection = None
        # except Exception as e:
        #     print(f"設定 Collection 失敗: {e}")

    def search(self, query_text: str, top_k=5):
        if not self.collection:
            print("錯誤: 未設定 Collection。")
            return []

        # 1. 將查詢文本向量化
        query_vector = self.embedding_model.embed_query(query_text)

        # 2. 定義要從 Milvus 回傳的欄位
        #    這些欄位名稱必須與 ingest_data.py 中建立的 Schema 完全對應
        # output_fields = [
        #     'Product', 'Segment', 'Model_Year', 'KB_Language', 'OS', 
        #     'Processor', 'Memory', 'Storage', 'Screen_Spec', 'Touch', 
        #     'Color', 'Communication', 'Camera', 'Graphics', 'Audio', 
        #     'Adapter', 'Battery', 'Finger_Print', 'TPM', 'Card_Reader', 
        #     'Backlit', 'Pen', 'Weight', 'DimensionWDH'
        # ]
        # Use the actual fields that exist in the current collection schema
        output_fields = [
            'product_id', 'chunk_type', 'semantic_group', 'content'
        ]

        # 3. 執行向量搜尋
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = self.collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=output_fields # ★ 修改點：使用新的欄位列表
        )

        # 4. 整理並回傳結果
        #    回傳的格式現在是一個包含所有查詢欄位的字典
        hits = results[0]
        formatted_results = []
        for hit in hits:
            # ★ 修改點：動態地從 hit.entity 中提取所有請求的欄位
            entity_data = {field: hit.entity.get(field) for field in output_fields}
            
            # 加上 id 和 distance 資訊
            entity_data['id'] = hit.id
            entity_data['distance'] = hit.distance
            
            # 將單筆結果加入列表
            formatted_results.append(entity_data)
            
        return formatted_results

    def query(self, *args, **kwargs):
        # 在這個類別中，我們使用 search 方法進行主要操作
        if 'query_text' in kwargs:
            return self.search(kwargs['query_text'], kwargs.get('top_k', 5))
        return "請提供 'query_text' 參數。"

    def disconnect(self):
        try:
            connections.disconnect("default")
            print("已斷開 Milvus 連接。")
        except Exception as e:
            print(f"斷開 Milvus 連接失敗: {e}")