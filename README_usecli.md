# Milvus Collection CLI 使用說明

## 📖 概述

`milvus_cli.py` 是一個強大的命令行工具，用於查看、搜尋和管理 Milvus 中的筆電規格 collection。該工具提供了多種功能來探索和分析已建立的 `new_nb_pc_v1` collection。

## 🚀 快速開始

### 基本語法

```bash
python scripts/milvus_cli.py [選項] [參數]
```

### 顯示幫助

```bash
python scripts/milvus_cli.py --help
```

## 🔧 功能選項

### 1. 顯示 Collection 基本資訊

```bash
python scripts/milvus_cli.py --info
```

**功能說明：**
- 顯示 collection 名稱和實體數量
- 顯示完整的 schema 結構
- 顯示索引資訊和參數

**輸出範例：**
```
============================================================
📊 Collection基本資訊
============================================================
名稱: new_nb_pc_v1
實體數量: 115
Schema: CollectionSchema(fields=[...])

🔍 索引資訊:
  欄位: query_vector
  索引類型: {'metric_type': 'L2', 'index_type': 'IVF_FLAT', 'params': {'nlist': 1024}}
```

### 2. 顯示 Chunk 統計資訊

```bash
python scripts/milvus_cli.py --stats
```

**功能說明：**
- 統計 parent 和 child chunks 數量
- 顯示各型號的 chunks 分布
- 提供整體資料概覽

**輸出範例：**
```
============================================================
📈 Chunk統計資訊
============================================================
Parent Chunks: 23
Child Chunks: 92
總Chunks: 115

📋 各型號統計:
  17: 5 chunks
  27: 25 chunks
  326: 5 chunks
  ...
```

### 3. 顯示範例資料

```bash
# 顯示前5筆資料（預設）
python scripts/milvus_cli.py --sample

# 顯示前10筆資料
python scripts/milvus_cli.py --sample 10
```

**功能說明：**
- 顯示指定數量的資料範例
- 包含完整的 chunk 資訊
- 自動截斷過長的內容

**輸出範例：**
```
============================================================
📋 前5筆資料範例
============================================================

1. PK: 460256333946479506
   DocID: 1
   Type: parent
   Product: AC01
   Model: AC01
   Source: AC01_result.csv
   Content: 型號系列: AC01 | 產品名稱: AC01...
```

### 4. 語義搜尋

```bash
python scripts/milvus_cli.py --search "AMD Ryzen processor"
```

**功能說明：**
- 使用 embedding 模型進行語義搜尋
- 返回最相關的 chunks
- 顯示相似度分數

**輸出範例：**
```
============================================================
🔍 語義搜尋: 'AMD Ryzen processor'
============================================================

結果 1:
  ID: 460256333946479549
  距離: 4.7788
  類型: performance
  產品: APX27
  型號: 17
  來源: data_17.csv
  內容: CPU: AMD Ryzen 7 5800H | GPU: AMD Radeon Graphics...
```

### 5. 型號搜尋

```bash
python scripts/milvus_cli.py --modeltype "27"
```

**功能說明：**
- 根據特定型號搜尋所有相關 chunks
- 支援精確匹配
- 顯示該型號的所有資料

### 6. Chunk 類型搜尋

```bash
python scripts/milvus_cli.py --chunk-type "performance"
```

**功能說明：**
- 搜尋特定類型的 chunks
- 支援的類型：`parent`, `performance`, `design`, `connectivity`, `business`
- 顯示該類型的所有 chunks

### 7. 顯示所有資訊

```bash
python scripts/milvus_cli.py --all
```

**功能說明：**
- 一次性顯示所有基本資訊
- 包含統計資訊和範例資料
- 適合快速概覽

## 📋 使用場景

### 場景1：快速了解 Collection 狀態
```bash
python scripts/milvus_cli.py --info --stats
```

### 場景2：探索特定型號的產品
```bash
python scripts/milvus_cli.py --modeltype "27" --sample 20
```

### 場景3：搜尋特定功能的產品
```bash
python scripts/milvus_cli.py --search "touch screen"
```

### 場景4：分析效能相關的 chunks
```bash
python scripts/milvus_cli.py --chunk-type "performance" --sample 15
```

### 場景5：完整資料概覽
```bash
python scripts/milvus_cli.py --all
```

## ⚠️ 注意事項

### 1. 環境要求
- 確保 Milvus 服務正在運行
- 確保 `new_nb_pc_v1` collection 已建立
- 安裝必要的 Python 套件：
  ```bash
  pip install pymilvus sentence-transformers
  ```

### 2. 連接設定
- 預設連接：`localhost:19530`
- 如需修改連接設定，請編輯 `milvus_cli.py` 中的配置變數

### 3. 效能考量
- 語義搜尋需要載入 embedding 模型，首次執行較慢
- 大量資料查詢時建議使用適當的 limit 參數
- 搜尋結果按相似度排序

## 🔍 進階用法

### 組合查詢
```bash
# 搜尋特定型號的效能 chunks
python scripts/milvus_cli.py --modeltype "27" --chunk-type "performance"
```

### 批量操作
```bash
# 檢查多個型號
for model in "17" "27" "326"; do
    echo "=== 型號 $model ==="
    python scripts/milvus_cli.py --modeltype "$model" --sample 3
done
```

### 輸出重導向
```bash
# 將結果保存到檔案
python scripts/milvus_cli.py --all > collection_report.txt

# 只顯示錯誤訊息
python scripts/milvus_cli.py --info 2> errors.log
```

## 🛠️ 故障排除

### 常見問題

1. **連接失敗**
   ```
   ❌ 連接Milvus失敗: Connection refused
   ```
   **解決方案：** 檢查 Milvus 服務是否運行，確認主機和端口設定

2. **Collection 不存在**
   ```
   Collection 'new_nb_pc_v1' 不存在
   ```
   **解決方案：** 先執行資料匯入腳本建立 collection

3. **Embedding 模型載入失敗**
   ```
   ❌ 載入embedding模型失敗: Model not found
   ```
   **解決方案：** 檢查網路連接，確保能下載模型檔案

### 除錯模式
```bash
# 啟用詳細日誌
export PYTHONPATH=.
python -u scripts/milvus_cli.py --info
```

## 📚 相關文件

- [Milvus 官方文件](https://milvus.io/docs)
- [Parent-Child Chunking 說明](docs/MGFD_System_Design/)
- [資料匯入腳本](scripts/import_to_milvus.py)

## 🤝 支援

如有問題或建議，請：
1. 檢查本文件的故障排除部分
2. 查看腳本的錯誤日誌
3. 確認環境設定正確

---

**版本：** 1.0  
**更新日期：** 2025-08-21  
**維護者：** AI Assistant

