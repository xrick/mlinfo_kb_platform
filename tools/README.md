# 工具說明文件 (Tools Documentation)

本目錄包含了用於管理和維護 SalesRAG Integration System 的各種命令列工具。

## 📋 工具列表

### 1. DuckDB 資料庫管理工具

#### `duckdb_query_cli.py` - DuckDB 查詢工具
用於查看和查詢 DuckDB 資料庫中的筆電規格資料。

**主要功能：**
- 查看資料庫資訊和表格結構
- 搜尋和過濾資料
- 執行自訂 SQL 查詢
- 匯出查詢結果

**使用方法：**
```bash
# 查看資料庫基本資訊
python tools/duckdb_query_cli.py info

# 查看表格結構
python tools/duckdb_query_cli.py schema specs

# 列出所有記錄
python tools/duckdb_query_cli.py list specs

# 搜尋特定型號
python tools/duckdb_query_cli.py search specs --column modelname --value "AG958"

# 執行自訂 SQL 查詢
python tools/duckdb_query_cli.py sql "SELECT modeltype, COUNT(*) FROM specs GROUP BY modeltype"

# 匯出查詢結果
python tools/duckdb_query_cli.py export specs --format csv --output laptops.csv
```

#### `clean_modelname.py` - 資料清理工具
用於清理 modelname 欄位中的 "Model Name:" 前綴。

**使用方法：**
```bash
python tools/clean_modelname.py
```

### 2. Sales Assistant 配置管理工具

#### `entity_manager.py` - 實體模式管理工具
管理 `entity_patterns.json` 檔案，用於配置實體識別的正則表達式模式。

**主要功能：**
- 查看和管理實體類型
- 新增、修改、刪除實體模式
- 測試正則表達式模式
- 驗證配置檔案

**使用方法：**
```bash
# 列出所有實體類型
python tools/entity_manager.py list

# 查看特定實體類型
python tools/entity_manager.py show MODEL_TYPE

# 新增實體類型
python tools/entity_manager.py add NEW_ENTITY "新實體描述" "\\\\b(?:pattern1|pattern2)\\\\b" --examples "example1" "example2"

# 更新實體描述
python tools/entity_manager.py update MODEL_TYPE description "更新的描述"

# 新增模式到現有實體
python tools/entity_manager.py add-pattern MODEL_TYPE "\\\\b(?:new_pattern)\\\\b"

# 移除模式
python tools/entity_manager.py remove-pattern MODEL_TYPE "\\\\b(?:old_pattern)\\\\b"

# 新增範例
python tools/entity_manager.py add-example MODEL_TYPE "新範例"

# 測試正則表達式
python tools/entity_manager.py test "\\\\b(?:958|819)\\\\b" "請比較958系列的筆電"

# 驗證配置檔案
python tools/entity_manager.py validate

# 刪除實體類型
python tools/entity_manager.py delete OLD_ENTITY
```

#### `keywords_manager.py` - 查詢關鍵字管理工具
管理 `query_keywords.json` 檔案，用於配置查詢意圖識別的關鍵字。

**主要功能：**
- 查看和管理意圖類型
- 新增、修改、刪除關鍵字
- 搜尋和測試關鍵字匹配
- 匯出關鍵字列表

**使用方法：**
```bash
# 列出所有意圖
python tools/keywords_manager.py list

# 查看特定意圖
python tools/keywords_manager.py show comparison

# 新增意圖
python tools/keywords_manager.py add price "價格相關查詢" "價格" "price" "貴" "便宜" "多少錢"

# 更新意圖描述
python tools/keywords_manager.py update comparison description "比較功能相關查詢"

# 新增關鍵字到現有意圖
python tools/keywords_manager.py add-keyword comparison "對比"

# 移除關鍵字
python tools/keywords_manager.py remove-keyword comparison "vs"

# 搜尋關鍵字
python tools/keywords_manager.py search "比較"

# 測試查詢意圖識別
python tools/keywords_manager.py test "請比較958和819系列的筆電"

# 匯出關鍵字
python tools/keywords_manager.py export --intent comparison --format txt

# 驗證配置檔案
python tools/keywords_manager.py validate

# 刪除意圖
python tools/keywords_manager.py delete old_intent
```

#### `config_manager.py` - 統一配置管理工具
提供統一的配置檔案管理介面，包括備份、還原、同步等功能。

**主要功能：**
- 查看配置檔案狀態
- 同步資料庫資料到配置檔案
- 備份和還原配置
- 驗證所有配置檔案
- 匯出配置摘要

**使用方法：**
```bash
# 查看配置狀態
python tools/config_manager.py status

# 同步資料庫中的 modeltype 到配置檔案
python tools/config_manager.py sync

# 驗證所有配置檔案
python tools/config_manager.py validate

# 備份所有配置檔案
python tools/config_manager.py backup

# 列出備份檔案
python tools/config_manager.py list-backups

# 從備份還原配置
python tools/config_manager.py restore entity_patterns_20250729_143022.json

# 顯示配置摘要
python tools/config_manager.py summary

# 匯出完整配置
python tools/config_manager.py export --format json
python tools/config_manager.py export --format summary
```

## 🔧 常見使用場景

### 場景1：新增支援的筆電系列
當資料庫中新增了新的筆電系列（如 777 系列）時：

```bash
# 1. 同步資料庫中的 modeltype 到配置檔案
python tools/config_manager.py sync

# 2. 驗證配置是否正確
python tools/config_manager.py validate

# 3. 測試新的實體識別
python tools/entity_manager.py test "\\\\b(?:819|839|928|958|960|AC01|777)\\\\b" "請比較777系列的筆電"
```

### 場景2：新增查詢意圖
當需要支援新的查詢類型（如價格查詢）時：

```bash
# 1. 新增價格相關意圖
python tools/keywords_manager.py add price "價格相關查詢" "價格" "price" "貴" "便宜" "多少錢" "成本" "預算"

# 2. 測試新意圖的識別
python tools/keywords_manager.py test "這款筆電價格如何？"

# 3. 驗證配置
python tools/keywords_manager.py validate
```

### 場景3：資料清理和維護
定期維護資料庫資料品質：

```bash
# 1. 查看資料庫狀態
python tools/duckdb_query_cli.py info

# 2. 檢查資料品質
python tools/duckdb_query_cli.py sql "SELECT modelname FROM specs WHERE modelname LIKE '%Model Name:%'"

# 3. 清理資料（如有需要）
python tools/clean_modelname.py

# 4. 備份配置
python tools/config_manager.py backup
```

### 場景4：問題診斷
當系統無法識別某些查詢時：

```bash
# 1. 測試實體識別
python tools/entity_manager.py test "\\\\b(?:819|839|928|958|960|AC01)\\\\b" "請比較656系列的筆電"

# 2. 測試意圖識別
python tools/keywords_manager.py test "請比較656系列的筆電"

# 3. 查看配置狀態
python tools/config_manager.py status

# 4. 驗證配置
python tools/config_manager.py validate
```

## 📁 檔案結構

```
tools/
├── README.md                 # 本說明文件
├── duckdb_query_cli.py      # DuckDB 查詢工具
├── clean_modelname.py       # 資料清理工具
├── entity_manager.py        # 實體模式管理工具
├── keywords_manager.py      # 查詢關鍵字管理工具
├── config_manager.py        # 統一配置管理工具
└── backups/                 # 配置檔案備份目錄
    ├── entity_patterns_*.json
    └── query_keywords_*.json
```

## ⚠️ 注意事項

1. **備份重要性**：修改配置檔案前建議先建立備份
2. **正則表達式**：在 JSON 檔案中，反斜線需要雙重轉義（`\\\\b` 而不是 `\\b`）
3. **權限設定**：確保工具檔案有執行權限（`chmod +x tools/*.py`）
4. **路徑依賴**：工具需要在專案根目錄下執行
5. **資料庫連接**：確保 DuckDB 資料庫檔案存在且可存取

## 🚀 快速開始

1. **驗證環境**：
   ```bash
   python tools/config_manager.py status
   ```

2. **同步配置**：
   ```bash
   python tools/config_manager.py sync
   ```

3. **驗證配置**：
   ```bash
   python tools/config_manager.py validate
   ```

4. **查看資料**：
   ```bash
   python tools/duckdb_query_cli.py info
   ```

## 📞 支援

如果在使用過程中遇到問題，請：
1. 檢查配置檔案狀態：`python tools/config_manager.py status`
2. 驗證配置：`python tools/config_manager.py validate`
3. 查看備份：`python tools/config_manager.py list-backups`
4. 從備份還原（如有需要）

---

*最後更新：2025-07-29*
*版本：v1.0.0*