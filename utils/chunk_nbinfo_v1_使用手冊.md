<!-- utils/chunk_nbinfo_v1_使用手冊.md -->

# Parent-Child Chunking 系統使用手冊

## 📖 目錄

1. [系統概述](#系統概述)
2. [環境準備](#環境準備)
3. [基本使用方法](#基本使用方法)
4. [進階功能](#進階功能)
5. [Collection 管理](#collection-管理)
6. [錯誤處理與除錯](#錯誤處理與除錯)
7. [最佳實務](#最佳實務)
8. [API 參考](#api-參考)

## 系統概述

本系統是一個專為筆記型電腦規格資料設計的 Parent-Child Chunking 向量化處理系統，主要功能包括：

### 🎯 核心特色

- **階層式資料結構**: 每個筆記型電腦規格為 parent chunk，語義欄位群組為 child chunks
- **記憶體優化**: 支援流式處理，可處理大型資料集而不耗盡記憶體
- **多種搜索策略**: 提供四種不同的檢索策略，適應不同查詢需求
- **安全的 Collection 管理**: 自動備份、防意外刪除、詳細日誌記錄

### 🏗️ 系統架構

```
CSV 檔案 → Parent Chunks (完整規格) → Milvus Parent Collection
            ↓
         Child Chunks (語義欄位群組) → Milvus Child Collection
                                          ↓
                               HierarchicalRetriever (多種搜索策略)
```

## 環境準備

### 1. 套件安裝

```bash
pip install sentence-transformers pymilvus pandas numpy psutil
```

### 2. Milvus 服務啟動

```bash
# 使用 Docker 啟動 Milvus
docker run -d --name milvus-standalone \
  -p 19530:19530 -p 9091:9091 \
  -v milvus_data:/var/lib/milvus \
  milvusdb/milvus:latest
```

### 3. 確認環境

```python
from utils.chunk_nbinfo_v1_20250910 import MilvusParentChildManager

# 測試連線
manager = MilvusParentChildManager()
if manager.initialize():
    print("✅ 環境準備完成")
    manager.disconnect()
else:
    print("❌ Milvus 連接失敗，請檢查服務是否啟動")
```

## 基本使用方法

### 1. 快速開始 - 一鍵建立完整系統

```python
from utils.chunk_nbinfo_v1_20250910 import create_complete_parent_child_system

# 使用最簡單的方式建立完整系統
system_result = create_complete_parent_child_system(
    csv_file_path="您的CSV檔案目錄路徑",
    collection_prefix="laptop_specs"
)

if system_result["status"] == "success":
    print("✅ 系統建立成功!")
    retriever = system_result["retriever"]
  
    # 立即開始搜索
    results = retriever.hybrid_search("gaming laptop", parent_k=3, child_k=5)
    print(f"找到 {len(results.get('reranked_results', []))} 個相關結果")
else:
    print(f"❌ 系統建立失敗: {system_result.get('error', '未知錯誤')}")
```

### 2. 標準處理模式（適合小型資料集）

```python
from utils.chunk_nbinfo_v1_20250910 import 


result = embed_all_nbinfo_to_collection(
    csv_directory="data/laptop_specs",
    collection_name="laptop_specs_standard",
    chunk_size=512,
    chunk_overlap=50
)

print(f"處理結果: {result}")
```

### 3. 流式處理模式（推薦用於大型資料集）

```python
from utils.chunk_nbinfo_v1_20250910 import embed_all_nbinfo_to_collection_streaming

result = embed_all_nbinfo_to_collection_streaming(
    csv_directory="data/laptop_specs",
    collection_name="laptop_specs_stream",
    chunk_size=512,
    chunk_overlap=50,
    batch_size=100,
    milvus_host="localhost",
    milvus_port="19530"
)

print(f"流式處理結果: {result}")
print(f"記憶體峰值使用: {result.get('statistics', {}).get('memory_peak_mb', 0)} MB")
```

## 進階功能

### 1. 安全的 Collection 創建

#### 防意外刪除模式

```python
from utils.chunk_nbinfo_v1_20250910 import MilvusParentChildManager

manager = MilvusParentChildManager()
manager.initialize()

# 如果 collection 已存在，會拋出錯誤而非刪除
result = manager.create_parent_child_collections(
    "important_data",
    overwrite=False  # 設為 False 防止意外刪除
)

if "error" in result:
    print(f"⚠️ Collection 已存在: {result['error']}")
```

#### 自動備份模式

```python
# 刪除前自動備份既有資料
result = manager.create_parent_child_collections(
    "laptop_specs",
    overwrite=True,
    backup_before_drop=True  # 啟用自動備份
)

print(f"Collection 創建結果: {result}")
# 備份檔案會儲存在 backups/ 目錄下
```

### 2. 四種搜索策略

```python
from utils.chunk_nbinfo_v1_20250910 import HierarchicalRetriever

# 初始化檢索器
manager = MilvusParentChildManager()
manager.initialize()
retriever = HierarchicalRetriever(manager)

# 策略 1: Parent-first 搜索（先找父節點再找子節點）
parent_results = retriever.parent_first_search(
    query="高效能遊戲筆電",
    k=5
)

# 策略 2: Child-first 搜索（直接搜索子節點）
child_results = retriever.child_first_search(
    query="NVIDIA RTX 顯示卡",
    k=8
)

# 策略 3: Hybrid 搜索（混合搜索 + 重新排序）- 推薦使用
hybrid_results = retriever.hybrid_search(
    query="輕薄商務筆電",
    parent_k=3,
    child_k=6,
    rerank=True
)

# 策略 4: Semantic Field 搜索（針對特定語義欄位）
semantic_results = retriever.semantic_field_search(
    query="CPU 效能跑分",
    field_groups=["system_specs", "connectivity"],
    k=5
)
```

### 3. 系統統計與監控

```python
# 獲取 collection 統計資訊
stats = retriever.get_collection_stats()
print(f"父節點數量: {stats['parent_collection']['count']}")
print(f"子節點數量: {stats['child_collection']['count']}")
print(f"平均每個父節點的子節點數: {stats['average_children_per_parent']:.1f}")

# 測試所有搜索策略的效果
test_results = retriever.test_search_strategies("gaming laptop with RTX 4080")
for strategy, result in test_results["strategies"].items():
    print(f"{strategy}: {result.get('result_count', 0)} 個結果")
```

## Collection 管理

### 1. 列出現有 Collections

```python
manager = MilvusParentChildManager()
manager.initialize()

# 列出所有 collections
all_collections = manager.list_existing_collections()
if all_collections["success"]:
    print(f"總共有 {all_collections['total_collections']} 個 collections:")
    for collection in all_collections["collections"]:
        print(f"  📊 {collection['name']}: {collection['entity_count']} 筆資料")

# 只列出特定前綴的 collections
filtered_collections = manager.list_existing_collections(prefix_filter="laptop_")
```

### 2. 獲取詳細資訊

```python
# 獲取特定 collection 的詳細資訊
collection_info = manager.get_collection_info("laptop_specs_parent")
if collection_info["success"]:
    print(f"Collection 名稱: {collection_info['collection_name']}")
    print(f"資料筆數: {collection_info['entity_count']}")
    print(f"欄位數量: {len(collection_info['schema']['fields'])}")
    print(f"是否有索引: {collection_info['has_index']}")
    print(f"是否為 parent-child 系統: {collection_info['is_parent_child']}")
```

### 3. 批量清理 Collections

```python
# 安全檢查 - 先查看會刪除哪些 collections
cleanup_preview = manager.cleanup_collections("test_", confirm=False)
print(f"預覽清理結果: {cleanup_preview}")

# 確認執行清理（會自動備份）
cleanup_result = manager.cleanup_collections("test_", confirm=True)
print(f"清理完成:")
print(f"  刪除數量: {cleanup_result['deleted_count']}")
print(f"  失敗數量: {cleanup_result['failed_count']}")
```

## 錯誤處理與除錯

### 1. 常見問題診斷

```python
# 健康檢查函數
def health_check():
    try:
        manager = MilvusParentChildManager()
        if manager.initialize():
            print("✅ Milvus 連接正常")
            stats = HierarchicalRetriever(manager).get_collection_stats()
            if stats.get("total_chunks", 0) > 0:
                print("✅ 資料已載入")
                return True
            else:
                print("⚠️ 尚未載入資料")
                return False
        else:
            print("❌ Milvus 連接失敗")
            return False
    except Exception as e:
        print(f"❌ 健康檢查失敗: {e}")
        return False

# 執行健康檢查
health_check()
```

### 2. 系統驗證

```python
from utils.chunk_nbinfo_v1_20250910 import validate_parent_child_system

# 完整系統驗證
validation_result = validate_parent_child_system(
    csv_directory="您的測試資料目錄",
    collection_prefix="validation_test",
    test_mode="streaming"
)

print(f"驗證狀態: {validation_result['overall_status']}")
print(f"測試時間: {validation_result.get('performance', {}).get('total_duration_seconds', 0):.2f} 秒")

# 查看詳細測試結果
for test_name, test_result in validation_result["tests"].items():
    print(f"- {test_name}: {test_result['status']}")
```

### 3. 錯誤處理最佳實務

```python
def robust_collection_creation(collection_name, csv_directory):
    """穩健的 collection 創建函數"""
    try:
        manager = MilvusParentChildManager()
      
        # Step 1: 初始化檢查
        if not manager.initialize():
            return {"error": "無法連接到 Milvus 服務"}
      
        # Step 2: 安全創建 collections
        result = manager.create_parent_child_collections(
            collection_name,
            overwrite=False,  # 先嘗試不覆蓋
            backup_before_drop=True
        )
      
        if "error" in result and "already exists" in result["error"]:
            # 如果已存在，詢問使用者是否要覆蓋
            user_input = input(f"Collection '{collection_name}' 已存在，是否要覆蓋？(y/N): ")
            if user_input.lower() == 'y':
                result = manager.create_parent_child_collections(
                    collection_name,
                    overwrite=True,
                    backup_before_drop=True
                )
            else:
                return {"error": "使用者取消操作"}
      
        if result.get("parent") and result.get("child"):
            # Step 3: 處理資料
            processing_result = embed_all_nbinfo_to_collection_streaming(
                csv_directory=csv_directory,
                collection_name=collection_name,
                overwrite=True,
                backup_before_drop=True
            )
            return processing_result
        else:
            return {"error": f"Collection 創建失敗: {result}"}
          
    except Exception as e:
        return {"error": f"未預期的錯誤: {str(e)}"}
    finally:
        if 'manager' in locals():
            manager.disconnect()

# 使用範例
result = robust_collection_creation("my_laptops", "data/laptop_specs")
print(f"執行結果: {result}")
```

## 最佳實務

### 1. 效能優化

#### 記憶體優化配置

```python
# 針對大型資料集的最佳配置
streaming_config = {
    "batch_size": 50,        # 較小的批次減少記憶體使用
    "chunk_size": 256,       # 較小的塊大小
    "chunk_overlap": 25      # 較小的重疊
}

result = embed_all_nbinfo_to_collection_streaming(
    csv_directory="large_dataset",
    collection_name="large_collection",
    **streaming_config
)
```

#### 搜索策略選擇指南

```python
def choose_search_strategy(query_type, query_text):
    """根據查詢類型選擇最佳搜索策略"""
  
    if "比較" in query_text or "vs" in query_text.lower():
        # 需要比較時使用 hybrid search
        return "hybrid"
    elif any(spec in query_text for spec in ["CPU", "GPU", "記憶體", "電池"]):
        # 特定規格查詢使用 semantic field search
        return "semantic_field"
    elif "型號" in query_text or "model" in query_text.lower():
        # 型號查詢使用 parent-first search
        return "parent_first"
    else:
        # 一般查詢使用 child-first search
        return "child_first"

# 使用範例
query = "請比較 RTX 4080 遊戲效能"
strategy = choose_search_strategy("comparison", query)
print(f"建議使用策略: {strategy}")
```

### 2. 安全性建議

#### 重要資料的保護策略

```python
def secure_data_processing(csv_directory, collection_name):
    """安全的資料處理流程"""
  
    # 1. 先做備份檢查
    manager = MilvusParentChildManager()
    manager.initialize()
  
    existing_collections = manager.list_existing_collections(
        prefix_filter=collection_name
    )
  
    if existing_collections.get("filtered_collections", 0) > 0:
        print("⚠️ 發現現有資料，將自動備份")
  
    # 2. 使用最安全的設定
    result = embed_all_nbinfo_to_collection_streaming(
        csv_directory=csv_directory,
        collection_name=collection_name,
        overwrite=True,
        backup_before_drop=True  # 一定要備份
    )
  
    # 3. 驗證結果
    if result.get("success"):
        validation = validate_parent_child_system(
            csv_directory, 
            collection_name
        )
        if validation["overall_status"] == "passed":
            print("✅ 資料處理並驗證成功")
        else:
            print("⚠️ 資料處理成功但驗證有問題")
  
    return result
```

### 3. 監控與維護

#### 定期系統檢查

```python
def system_maintenance():
    """系統維護檢查清單"""
    print("🔧 系統維護檢查開始")
  
    manager = MilvusParentChildManager()
    if not manager.initialize():
        print("❌ 無法連接 Milvus")
        return
  
    try:
        # 1. 檢查所有 collections
        collections = manager.list_existing_collections()
        print(f"📊 目前有 {collections['total_collections']} 個 collections")
      
        # 2. 識別 parent-child 系統
        pc_collections = [c for c in collections["collections"] 
                         if c.get("is_parent_child", False)]
        print(f"🏗️ 其中 {len(pc_collections)} 個屬於 parent-child 系統")
      
        # 3. 檢查資料量異常的 collections
        for collection in collections["collections"]:
            count = collection.get("entity_count", 0)
            if count == 0:
                print(f"⚠️ {collection['name']} 沒有資料")
            elif count > 100000:
                print(f"📈 {collection['name']} 資料量很大: {count:,} 筆")
      
        # 4. 清理建議
        test_collections = [c for c in collections["collections"] 
                           if c["name"].startswith(("test_", "demo_"))]
        if test_collections:
            print(f"🧹 建議清理 {len(test_collections)} 個測試用 collections")
            for tc in test_collections:
                print(f"  - {tc['name']}")
  
    finally:
        manager.disconnect()

# 執行維護檢查
system_maintenance()
```

## API 參考

### MilvusParentChildManager 類別

#### 初始化方法

```python
manager = MilvusParentChildManager(
    host="localhost",           # Milvus 主機
    port="19530",              # Milvus 埠號
    embedding_model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
```

#### 主要方法

| 方法名稱                              | 參數                                                         | 返回值   | 說明                          |
| ------------------------------------- | ------------------------------------------------------------ | -------- | ----------------------------- |
| `initialize()`                      | 無                                                           | `bool` | 初始化連接和嵌入模型          |
| `create_parent_child_collections()` | `collection_prefix`, `overwrite`, `backup_before_drop` | `Dict` | 創建 parent-child collections |
| `list_existing_collections()`       | `prefix_filter`                                            | `Dict` | 列出現有 collections          |
| `get_collection_info()`             | `collection_name`                                          | `Dict` | 獲取 collection 詳細資訊      |
| `cleanup_collections()`             | `prefix_filter`, `confirm`                               | `Dict` | 批量清理 collections          |
| `disconnect()`                      | 無                                                           | 無       | 斷開連接                      |

### HierarchicalRetriever 類別

#### 搜索方法

| 方法名稱                    | 參數                                             | 返回值         | 適用場景             |
| --------------------------- | ------------------------------------------------ | -------------- | -------------------- |
| `parent_first_search()`   | `query`, `k`                                 | `List[Dict]` | 需要完整上下文的查詢 |
| `child_first_search()`    | `query`, `k`                                 | `List[Dict]` | 針對特定屬性的查詢   |
| `hybrid_search()`         | `query`, `parent_k`, `child_k`, `rerank` | `Dict`       | 一般推薦使用         |
| `semantic_field_search()` | `query`, `field_groups`, `k`               | `List[Dict]` | 特定欄位群組查詢     |

### 處理函數

#### embed_all_nbinfo_to_collection_streaming()

**參數說明:**

- `csv_directory` (str): CSV 檔案目錄路徑
- `collection_name` (str): Collection 名稱
- `chunk_size` (int): 子塊最大大小，預設 512
- `chunk_overlap` (int): 子塊重疊大小，預設 50
- `batch_size` (int): 批次處理大小，預設 100
- `milvus_host` (str): Milvus 主機，預設 "localhost"
- `milvus_port` (str): Milvus 埠號，預設 "19530"
- `overwrite` (bool): 是否覆蓋現有 collection，預設 True
- `backup_before_drop` (bool): 刪除前是否備份，預設 False

**返回值:**

```python
{
    "success": bool,
    "collection_name": str,
    "processing_mode": "streaming",
    "statistics": {
        "parent_chunks_processed": int,
        "child_chunks_processed": int,
        "files_processed": int,
        "memory_peak_mb": float,
        "processing_time_seconds": float
    }
}
```

### 語義欄位群組

系統預設的欄位分組：

```python
field_groups = {
    "basic_info": ["modeltype", "version", "modelname", "mainboard"],
    "development": ["devtime", "pm", "structconfig"],
    "display": ["lcd", "touchpanel", "lcdconnector"],
    "io_peripherals": ["iointerface", "ledind", "powerbutton", "keyboard", "webcamera", "touchpad", "fingerprint"],
    "system_specs": ["cpu", "gpu", "memory", "storage", "battery"],
    "connectivity": ["wireless", "lan", "lte", "bluetooth", "wifislot"],
    "security_features": ["tpm", "rtc", "thermal"],
    "software_config": ["softwareconfig", "ai", "accessory", "certifications"],
    "audio": ["audio"]
}
```

---

## 📞 支援與協助

如果您在使用過程中遇到問題：

1. **檢查系統健康**: 執行 `health_check()` 函數
2. **查看日誌**: 系統會詳細記錄所有操作和錯誤資訊
3. **驗證環境**: 確認 Milvus 服務正常運行
4. **參考範例**: 查看本手冊中的完整範例程式碼

### 常見錯誤代碼

| 錯誤訊息                    | 原因                | 解決方法                              |
| --------------------------- | ------------------- | ------------------------------------- |
| "Connection refused"        | Milvus 服務未啟動   | 檢查 Docker 容器狀態                  |
| "Collection already exists" | Collection 名稱衝突 | 使用不同名稱或設定 `overwrite=True` |
| "Memory error"              | 記憶體不足          | 使用流式處理並調小 `batch_size`     |
| "Empty CSV directory"       | 找不到 CSV 檔案     | 檢查檔案路徑和權限                    |

---

*最後更新: 2025年1月*
*版本: v1.0*
