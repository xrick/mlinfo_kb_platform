<!-- utils/chunk_nbinfo_v2_usage_guide.md -->
<!-- claudedocs/chunk_nbinfo_v2_usage_guide.md -->
# Chunk NBInfo v2 使用指南

## 概覽

`chunk_nbinfo_v2_20250915.py` 是一個強大的筆記型電腦規格資料處理工具，提供從 CSV 檔案處理到向量化搜尋的完整解決方案。該工具支援 DuckDB 資料庫存儲、Milvus 向量搜尋，以及先進的父子分塊技術。

## 主要功能

- **資料庫管理**: 將多個 CSV 檔案合併並存儲到 DuckDB 資料庫
- **向量化嵌入**: 將規格資料轉換為向量嵌入並存儲到 Milvus
- **父子分塊**: 實現階層式分塊策略以提高檢索精度
- **搜尋系統**: 提供語義搜尋和混合檢索功能
- **資料驗證**: 自動驗證資料完整性和一致性

## 安裝需求

### 必要依賴套件

```bash
# 核心資料處理
pip install pandas numpy

# 資料庫支援
pip install duckdb sqlite3

# 向量搜尋和機器學習
pip install pymilvus sentence-transformers

# 檔案處理和工具
pip install pathlib hashlib json
```

### 系統需求

- **Python**: 3.8 或以上版本
- **Milvus**: 2.0+ (本地或遠端部署)
- **記憶體**: 建議 8GB 以上 (大型資料集處理)
- **硬碟空間**: 根據資料集大小，建議預留充足空間

### 環境設定

1. **Milvus 服務設定**
```bash
# 使用 Docker 啟動 Milvus (推薦)
docker-compose up -d milvus-standalone

# 或使用 Milvus Lite (輕量版)
pip install milvus-lite
```

2. **資料目錄結構**
```
project/
├── data/
│   └── raw/
│       └── EM_New TTL_241104_AllModelsParsed/
│           ├── model1.csv
│           ├── model2.csv
│           └── ...
├── db/
│   └── (資料庫檔案將自動建立)
└── utils/
    └── chunk_nbinfo_v2_20250915.py
```

## 核心函式說明

### 1. `gen_all_nbinfo_tb()` - 資料庫建立

**功能**: 將所有 CSV 檔案合併到 DuckDB 資料庫，並管理 Milvus collection

**參數**:
- `csv_directory` (str): CSV 檔案目錄路徑
  - 預設: `'data/raw/EM_New TTL_241104_AllModelsParsed'`
- `db_path` (str): DuckDB 資料庫檔案路徑
  - 預設: `'all_nbinfo_v2.db'`
- `collection_name` (str): Milvus collection 名稱
  - 預設: `'nbtypes_collection'`

**返回值**: `bool` - 操作成功與否

**特性**:
- 自動刪除現有資料庫檔案
- 驗證 CSV 檔案結構一致性
- 建立效能索引
- 管理 Milvus collection 生命週期

### 2. `embed_all_nbinfo_to_collection()` - 向量化嵌入

**功能**: 將 CSV 資料進行向量化嵌入並存儲到 Milvus

**參數**:
- `csv_directory` (str): CSV 檔案目錄
- `collection_name` (str): 目標 collection 名稱
- `chunk_size` (int): 分塊大小 (預設: 512)
- `chunk_overlap` (int): 分塊重疊 (預設: 50)

**返回值**: `Dict[str, Any]` - 包含處理統計資訊

### 3. `create_complete_parent_child_system()` - 完整系統建立

**功能**: 建立完整的父子分塊檢索系統

**參數**:
- `csv_file_path` (str): 單一 CSV 檔案路徑
- `milvus_host` (str): Milvus 主機 (預設: "localhost")
- `milvus_port` (str): Milvus 埠口 (預設: "19530")
- `collection_prefix` (str): Collection 前綴 (預設: "nb_specs_demo")

**返回值**: `Dict[str, Any]` - 系統設定結果和檢索器實例

### 4. `validate_parent_child_system()` - 系統驗證

**功能**: 驗證父子分塊系統的完整性和效能

**參數**:
- `csv_directory` (str): 資料目錄
- `collection_prefix` (str): Collection 前綴
- `test_queries` (List[str]): 測試查詢列表

## 使用範例

### 基本使用流程

```python
from utils.chunk_nbinfo_v2_20250915 import (
    gen_all_nbinfo_tb,
    embed_all_nbinfo_to_collection,
    create_complete_parent_child_system
)

# 1. 建立資料庫和基礎 collection
success = gen_all_nbinfo_tb(
    csv_directory='data/raw/EM_New TTL_241104_AllModelsParsed',
    db_path='notebooks.db',
    collection_name='nb_specs'
)

if success:
    print("資料庫建立成功！")
    
    # 2. 進行向量化嵌入
    results = embed_all_nbinfo_to_collection(
        csv_directory='data/raw/EM_New TTL_241104_AllModelsParsed',
        collection_name='nb_specs_vectors',
        chunk_size=512,
        chunk_overlap=50
    )
    
    print(f"嵌入完成: {results}")
```

### 高級使用：父子分塊系統

```python
# 建立完整的父子分塊檢索系統
system_results = create_complete_parent_child_system(
    csv_file_path='data/raw/EM_New TTL_241104_AllModelsParsed/model_specs.csv',
    milvus_host='localhost',
    milvus_port='19530',
    collection_prefix='advanced_nb_search'
)

# 取得檢索器
retriever = system_results.get('retriever')

if retriever:
    # 執行搜尋
    query = "找出配備 RTX 4060 顯卡的筆記型電腦"
    results = retriever.search(query, top_k=5)
    
    for result in results:
        print(f"模型: {result.get('modelname')}")
        print(f"分數: {result.get('score')}")
        print(f"規格: {result.get('content')}")
        print("---")
```

### 批次處理和驗證

```python
from utils.chunk_nbinfo_v2_20250915 import (
    validate_parent_child_system,
    run_comprehensive_tests
)

# 運行綜合測試
test_results = run_comprehensive_tests()
print(f"測試結果: {test_results}")

# 驗證特定系統
validation_results = validate_parent_child_system(
    csv_directory='data/raw/EM_New TTL_241104_AllModelsParsed',
    collection_prefix='nb_specs_demo',
    test_queries=[
        "高效能遊戲筆電",
        "輕薄商務筆記型電腦",
        "RTX 4070 顯示卡"
    ]
)

print(f"驗證結果: {validation_results}")
```

## 進階配置

### Milvus 連線設定

```python
# 自訂 Milvus 連線
from pymilvus import connections

connections.connect(
    "default",
    host="your-milvus-host",
    port="19530",
    user="username",      # 如果需要認證
    password="password"   # 如果需要認證
)
```

### 效能調優建議

1. **分塊大小調整**
   - 小分塊 (256-512): 更精確的檢索
   - 大分塊 (1024-2048): 更好的上下文理解

2. **索引優化**
   - 使用適當的 Milvus 索引類型 (IVF_FLAT, HNSW)
   - 根據資料量調整索引參數

3. **記憶體管理**
   - 大型資料集建議使用串流處理
   - 定期清理暫存向量資料

### 自訂分塊策略

```python
# 自訂分塊參數以適應不同需求
results = embed_all_nbinfo_to_collection(
    csv_directory='your_data_path',
    collection_name='custom_collection',
    chunk_size=1024,        # 更大的分塊以保留更多上下文
    chunk_overlap=100       # 增加重疊以改善連續性
)
```

## 故障排除

### 常見問題和解決方案

#### 1. Milvus 連線失敗
**錯誤訊息**: `Connection failed`
**解決方案**:
```bash
# 檢查 Milvus 服務狀態
docker ps | grep milvus

# 重啟 Milvus 服務
docker-compose restart milvus-standalone
```

#### 2. CSV 檔案格式錯誤
**錯誤訊息**: `Column mismatch in file`
**解決方案**:
- 確保所有 CSV 檔案具有相同的欄位結構
- 檢查檔案編碼 (建議使用 UTF-8)
- 驗證欄位名稱一致性

#### 3. 記憶體不足
**錯誤訊息**: `MemoryError` 或效能緩慢
**解決方案**:
```python
# 使用串流處理版本
results = embed_all_nbinfo_to_collection_streaming(
    csv_directory='your_data',
    collection_name='streaming_collection',
    batch_size=100  # 降低批次大小
)
```

#### 4. DuckDB 檔案鎖定
**錯誤訊息**: `database is locked`
**解決方案**:
- 確保沒有其他程序正在使用資料庫
- 手動刪除資料庫檔案後重新執行

#### 5. 向量維度不匹配
**錯誤訊息**: `Vector dimension mismatch`
**解決方案**:
- 確保使用一致的 sentence-transformer 模型
- 檢查 Milvus collection schema 中的向量維度設定

### 日誌和除錯

啟用詳細日誌：
```python
import logging

# 設定日誌級別
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 在執行前檢查設定
logger.info("開始處理資料...")
```

### 效能監控

```python
import time

start_time = time.time()

# 執行處理
results = gen_all_nbinfo_tb(csv_directory='your_data')

end_time = time.time()
print(f"處理時間: {end_time - start_time:.2f} 秒")
print(f"處理結果: {results}")
```

## 最佳實踐

### 1. 資料預處理
- 在處理前驗證 CSV 檔案格式
- 清理重複和無效資料
- 統一資料編碼格式

### 2. 系統監控
- 定期檢查 Milvus 服務狀態
- 監控資料庫檔案大小和效能
- 追蹤向量嵌入品質

### 3. 備份策略
- 定期備份 DuckDB 資料庫檔案
- 保存 Milvus collection 快照
- 維護原始 CSV 檔案的備份

### 4. 擴展性考量
- 對於大型資料集，考慮分散式 Milvus 部署
- 使用索引分區以提高查詢效能
- 實施適當的快取策略

## 支援和維護

如遇到問題或需要協助，請：

1. 檢查本文件的故障排除章節
2. 啟用詳細日誌以獲取錯誤資訊
3. 確認所有依賴套件版本相容性
4. 驗證資料格式和系統設定

## 版本資訊

- **當前版本**: v2 (2025-09-15)
- **主要更新**: DuckDB 支援、Milvus collection 管理、父子分塊系統
- **相容性**: Python 3.8+, Milvus 2.0+, DuckDB 0.8+