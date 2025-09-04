
from pymilvus import connections, Collection

# 連接到 Milvus 伺服器
connections.connect(host="localhost", port="19530")


# 指定要查詢的 collection 名稱
collection_name = "product_semantic_chunks"

# 加載指定的 collection
collection = Collection(collection_name)

# 獲取 schema（結構）
schema = collection.schema

# 輸出每個欄位的資訊
for field in schema.fields:
    print(f"欄位名稱: {field.name}, 類型: {field.dtype}, 是否主鍵: {field.is_primary}, 是否可為空: {field.nullable}")