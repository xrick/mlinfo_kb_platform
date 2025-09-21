# utils/ do_db_build.py
from utils.chunk_nbinfo_v2_20250915 import (
    gen_all_nbinfo_tb,
    embed_all_nbinfo_to_collection,
    create_complete_parent_child_system
)

# 1. 建立資料庫和基礎 collection
success = gen_all_nbinfo_tb(
    csv_directory='data/raw/EM_New TTL_241104_AllModelsParsed',
    db_path='db/all_nbinfo_v2.db',
    collection_name='nbtypes'
)

if success:
    print("資料庫建立成功！")
    
    # 2. 進行向量化嵌入
    results = embed_all_nbinfo_to_collection(
        csv_directory='data/raw/EM_New TTL_241104_AllModelsParsed',
        collection_name='product_semantic_chunks',
        chunk_size=512,
        chunk_overlap=50
    )
    
    print(f"嵌入完成: {results}")