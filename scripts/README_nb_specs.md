# 筆電規格資料匯入與查詢系統

本系統提供將CSV檔案中的筆電規格資料匯入到SQLite資料庫，以及多種查詢方式的功能。

## 📁 檔案結構

```
scripts/
├── import_nb_specs.py          # 主要匯入腳本
├── test_nb_spec_import.py      # 測試腳本
├── query_nb_specs.py           # 查詢腳本
└── README_nb_specs.md          # 本說明文件
```

## 🚀 快速開始

### 1. 測試環境

在執行匯入腳本之前，建議先執行測試腳本確認環境正常：

```bash
python scripts/test_nb_spec_import.py
```

測試腳本會：
- 檢查CSV檔案是否存在
- 測試資料庫建立功能
- 測試CSV檔案讀取功能

### 2. 執行匯入

```bash
python scripts/import_nb_specs.py
```

匯入腳本會：
- 自動建立 `db/nb_spec_0250821v1.db` 資料庫
- 讀取 `data/raw/EM_New TTL_241104_AllTransformedToGoogleSheet/` 中的所有CSV檔案
- 將資料匯入到資料庫中
- 提供詳細的進度追蹤和錯誤處理
- 生成日誌檔案 `logs/nb_spec_import.log`

## 📊 資料庫結構

### 主要資料表：`notebook_specs`

包含以下欄位：
- **基本資訊**：`modeltype`, `version`, `modelname`, `mainboard`
- **開發資訊**：`devtime`, `pm`
- **硬體規格**：`cpu`, `gpu`, `memory`, `storage`, `lcd`, `touchpanel`
- **連接介面**：`iointerface`, `wireless`, `lan`, `bluetooth`
- **軟體配置**：`softwareconfig`, `ai`
- **其他**：`accessory`, `certifications`
- **系統欄位**：`source_file`, `import_timestamp`, `content_hash`

### 匯入記錄表：`import_logs`

記錄每次匯入的詳細資訊：
- `filename`: 來源CSV檔案名
- `total_rows`: 總行數
- `imported_rows`: 成功匯入行數
- `skipped_rows`: 跳過行數（重複資料）
- `error_rows`: 錯誤行數
- `status`: 匯入狀態
- `import_timestamp`: 匯入時間

## 🔍 查詢功能

### 基本查詢

```bash
# 顯示統計資訊
python scripts/query_nb_specs.py --stats

# 列出所有型號（限制數量）
python scripts/query_nb_specs.py --list --limit 20

# 根據型號類型搜尋
python scripts/query_nb_specs.py --modeltype 27

# 根據關鍵字搜尋
python scripts/query_nb_specs.py --keyword AMD

# 顯示詳細規格
python scripts/query_nb_specs.py --detail 1
```

### 查詢選項說明

- `--stats`: 顯示資料庫統計資訊
- `--list`: 列出所有型號
- `--modeltype`: 根據型號類型搜尋（如：17, 27, 958等）
- `--keyword`: 根據關鍵字搜尋（在型號、版本、名稱、CPU、GPU等欄位中搜尋）
- `--detail`: 顯示指定ID記錄的詳細規格
- `--limit`: 限制顯示數量（預設50）
- `--db`: 指定資料庫路徑（預設：`db/nb_spec_0250821v1.db`）

## 📈 匯入統計

根據最近的匯入結果：
- **總記錄數**: 23筆
- **處理檔案數**: 19個CSV檔案
- **各型號分布**:
  - 空白型號: 21筆（主要為各種筆電型號）
  - 17: 1筆
  - 531: 1筆
- **版本分布**:
  - EVT_v1.2: 3筆
  - MP_v1.0: 3筆
  - MP_v1.1: 2筆
  - Planning_v0.3: 2筆
  - 其他版本各1筆

## 🛠️ 技術特點

### 資料清理
- 自動移除BOM字元
- 清理多餘空白和換行
- 標準化資料格式

### 去重機制
- 使用內容雜湊值（MD5）進行去重
- 基於 `modeltype`, `version`, `modelname`, `content_hash` 的唯一性約束

### 錯誤處理
- 完整的異常處理機制
- 詳細的錯誤日誌記錄
- 單行錯誤不影響整體匯入

### 效能優化
- 建立適當的資料庫索引
- 批次提交（每100筆）
- 記憶體效率的資料處理

## 📝 日誌與監控

### 日誌檔案
- 位置：`logs/nb_spec_import.log`
- 格式：時間戳 - 日誌等級 - 訊息
- 內容：匯入進度、錯誤詳情、統計資訊

### 監控指標
- 檔案處理進度
- 資料匯入成功率
- 錯誤統計
- 處理時間

## 🔧 自訂與擴展

### 修改資料庫結構
在 `import_nb_specs.py` 的 `create_database()` 方法中修改資料表結構。

### 新增查詢功能
在 `query_nb_specs.py` 的 `NotebookSpecQuery` 類別中新增查詢方法。

### 支援其他資料格式
可以擴展腳本支援Excel、JSON等其他資料格式。

## ⚠️ 注意事項

1. **資料備份**: 匯入前建議備份現有資料庫
2. **編碼問題**: CSV檔案應使用UTF-8編碼
3. **磁碟空間**: 確保有足夠的磁碟空間儲存資料庫
4. **權限設定**: 確保腳本有讀取CSV檔案和寫入資料庫的權限

## 🆘 故障排除

### 常見問題

1. **CSV檔案讀取失敗**
   - 檢查檔案路徑是否正確
   - 確認檔案編碼為UTF-8
   - 檢查檔案權限

2. **資料庫建立失敗**
   - 檢查目錄權限
   - 確認SQLite3已安裝
   - 檢查磁碟空間

3. **查詢結果為空**
   - 確認資料已成功匯入
   - 檢查查詢條件是否正確
   - 使用 `--stats` 確認資料庫狀態

### 聯絡支援

如遇到問題，請檢查：
1. 日誌檔案 `logs/nb_spec_import.log`
2. 資料庫檔案 `db/nb_spec_0250821v1.db`
3. 測試腳本輸出

## 📚 相關文件

- [SQLite官方文件](https://www.sqlite.org/docs.html)
- [Python CSV模組文件](https://docs.python.org/3/library/csv.html)
- [Python SQLite3模組文件](https://docs.python.org/3/library/sqlite3.html)

