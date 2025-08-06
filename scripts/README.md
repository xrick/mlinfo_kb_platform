# 
    SalesRAG 腳本說明

本目錄包含 SalesRAG 整合系統的管理腳本。

## 腳本列表

### 1. install.sh - 安裝腳本

自動化安裝 SalesRAG 系統和所有依賴。

```bash
# 開發模式安裝（建立虛擬環境）
./scripts/install.sh dev

# 生產模式安裝（系統級安裝）
./scripts/install.sh prod

# 查看幫助
./scripts/install.sh help
```

**功能：**

- 檢查系統環境和依賴
- 安裝 Python 套件
- 建立必要目錄
- 初始化資料庫
- 設定檔案權限
- 建立快速啟動腳本

### 2. start_service.sh - 啟動服務腳本

啟動 SalesRAG 服務的腳本。

```bash
# 開發模式啟動（前台執行）
./scripts/start_service.sh dev

# 生產模式啟動（背景執行）
./scripts/start_service.sh prod
```

**功能：**

- 檢查 Python 環境和依賴
- 檢查埠口可用性
- 建立必要目錄
- 啟動服務（dev 或 prod 模式）
- 健康狀態檢查

### 3. stop_service.sh - 停止服務腳本

停止 SalesRAG 服務的腳本。

```bash
# 優雅停止服務
./scripts/stop_service.sh

# 強制停止服務
./scripts/stop_service.sh force

# 查看服務狀態
./scripts/stop_service.sh status

# 清理資源
./scripts/stop_service.sh clean
```

**功能：**

- 優雅停止服務
- 強制停止服務
- 查看服務狀態
- 清理臨時檔案

## 使用範例

### 完整安裝和啟動流程

```bash
# 1. 安裝系統（開發模式）
./scripts/install.sh dev

# 2. 啟動服務（開發模式）
./scripts/start_service.sh dev

# 3. 停止服務
./scripts/stop_service.sh
```

### 生產環境部署

```bash
# 1. 安裝系統（生產模式）
./scripts/install.sh prod

# 2. 啟動服務（生產模式）
./scripts/start_service.sh prod

# 3. 查看服務狀態
./scripts/stop_service.sh status

# 4. 停止服務
./scripts/stop_service.sh
```

### 維護操作

```bash
# 查看服務狀態
./scripts/stop_service.sh status

# 清理資源
./scripts/stop_service.sh clean

# 強制重啟服務
./scripts/stop_service.sh force
./scripts/start_service.sh prod
```

## 注意事項

1. **執行權限**：腳本需要執行權限，安裝後會自動設定
2. **系統依賴**：Linux 系統可能需要安裝 gcc, make 等編譯工具
3. **Python 版本**：需要 Python 3.8 或更高版本
4. **埠口**：預設使用 8001 埠口，確保該埠口未被占用
5. **權限**：某些系統依賴安裝可能需要 sudo 權限

## 故障排除

### 常見問題

1. **腳本沒有執行權限**

```bash
chmod +x scripts/*.sh
```

2. **Python 版本過低**

```bash
# 升級 Python 或使用虛擬環境
python --version
```

3. **依賴安裝失敗**

```bash
# 清除快取重新安裝
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

4. **埠口被占用**

```bash
# 查看占用情況
lsof -i :8001
# 停止占用的程序
kill -9 <PID>
```

5. **服務無法啟動**

```bash
# 查看日誌
cat salesrag.log
# 檢查依賴
python -c "import fastapi, uvicorn"
```

## 日誌檔案

腳本運行時會產生以下日誌檔案：

- `salesrag.log` - 服務運行日誌
- `salesrag.pid` - 服務程序 ID 檔案

## 自訂設定

如需修改預設設定，可以編輯以下檔案：

- `config.py` - 應用程式設定
- 腳本中的變數（如埠口、路徑等）

## 版本資訊

這些腳本適用於：

- SalesRAG 整合系統 v1.0
- Python 3.8+
- Linux/macOS 系統

---

*更多詳細說明請參考上層目錄的 USAGE.md 檔案*
