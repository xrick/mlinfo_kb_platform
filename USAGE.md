# ⚠️ 執行環境說明

**請務必於 conda 虛擬環境 `salseragenv` 下執行本專案，所有依賴（如 prettytable、langchain_community 等）也需安裝於此環境。**

啟動方式：

```bash
conda activate salseragenv
```

# SalesRAG 整合系統使用文件

## 系統簡介

SalesRAG 整合系統提供了統一的界面，結合銷售助手 AI 功能和筆記型電腦規格資料處理能力。

## 安裝說明

### 系統需求

- Python 3.8+
- pip package manager
- 建議使用 Linux 或 macOS 系統

### 步驟 1: 進入專案目錄

```bash
cd /home/mapleleaf/LCJRepos/projects/SalesRAG/salesrag
```

### 步驟 2: 安裝相依套件

```bash
# 安裝所有必要的 Python 套件
pip install -r requirements.txt

# 或者使用 conda 環境（推薦）
conda activate dpenv  # 如果您有 conda 環境
pip install -r requirements.txt
```

### 步驟 3: 檢查安裝

```bash
# 檢查 Python 版本
python --version

# 檢查主要套件是否正確安裝
python -c "import fastapi, uvicorn, duckdb, pymilvus, pandas; print('All packages installed successfully')"
```

## 服務管理

### 啟動服務

#### 方法 1: 直接啟動（開發模式）

```bash
# 進入 salesrag 目錄
cd /home/mapleleaf/LCJRepos/projects/SalesRAG/salesrag

# 啟動應用程式
python main.py
```

#### 方法 2: 使用 Uvicorn（生產模式）

```bash
# 進入 salesrag 目錄
cd /home/mapleleaf/LCJRepos/projects/SalesRAG/salesrag

# 啟動 Uvicorn 服務器
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

#### 方法 3: 背景執行

```bash
# 使用 nohup 在背景執行
nohup python main.py > salesrag.log 2>&1 &

# 檢查背景程序
ps aux | grep python | grep main.py
```

### 停止服務

#### 方法 1: 前台服務停止

```bash
# 如果服務在前台執行，使用 Ctrl+C 停止
Ctrl + C
```

#### 方法 2: 背景服務停止

```bash
# 查找服務程序 ID
ps aux | grep "python main.py" | grep -v grep

# 使用 kill 命令停止（替換 PID 為實際程序 ID）
kill <PID>

# 或者強制停止
kill -9 <PID>
```

#### 方法 3: 使用 pkill

```bash
# 停止所有相關的 Python 程序
pkill -f "python main.py"

# 或者更具體的命令
pkill -f "salesrag"
```

### 檢查服務狀態

#### 檢查服務是否運行

```bash
# 檢查埠口是否被使用
netstat -tulpn | grep :8001
# 或者
lsof -i :8001

# 檢查程序是否存在
ps aux | grep "python main.py" | grep -v grep
```

#### 檢查服務健康狀態

```bash
# 使用 curl 測試健康端點
curl http://localhost:8001/health

# 或者使用 wget
wget -qO- http://localhost:8001/health
```

## 使用說明

### 1. 啟動服務後訪問

```bash
# 啟動服務
python main.py

# 在瀏覽器中打開
http://localhost:8001
```

### 2. 使用 Sales-AI 功能

1. 點擊左側邊欄的 **Sales-AI** 按鈕
2. 在聊天界面輸入問題
3. 查看 AI 回應和規格比較表格
4. 使用預設問題快速開始

### 3. 使用 Add Specifications 功能

1. 點擊左側邊欄的 **Add Specifications** 按鈕
2. 上傳 `.xlsx`, `.xls`, 或 `.csv` 格式的規格檔案
3. 預覽資料內容
4. 確認上傳並處理資料
5. 查看處理結果

### 4. 查看資料歷史

- 左側邊欄的 **已匯入檔案列表** 顯示所有成功處理的資料
- 包含時間戳記、檔案名稱、處理狀態
- 點擊項目查看詳細資訊

## 常用命令

### 開發相關

```bash
# 開發模式啟動（自動重載）
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# 檢查程式語法
python -m py_compile main.py

# 查看應用程式日誌
tail -f salesrag.log
```

### 資料庫相關

```bash
# 檢查資料庫檔案
ls -la db/

# 檢查 DuckDB 資料庫
python -c "import duckdb; conn = duckdb.connect('db/sales_specs.db'); print(conn.execute('SHOW TABLES').fetchall())"

# 檢查歷史資料庫
python -c "import sqlite3; conn = sqlite3.connect('db/history.db'); print(conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall())"
```

### 系統監控

```bash
# 監控系統資源使用
top -p $(pgrep -f "python main.py")

# 檢查記憶體使用
ps aux | grep "python main.py" | awk '{print $6}'

# 檢查網路連接
netstat -an | grep :8001
```

## 故障排除

### 常見問題

#### 1. 無法啟動服務

```bash
# 檢查埠口是否被占用
lsof -i :8001

# 更換埠口啟動
python main.py --port 8002
```

#### 2. 套件安裝失敗

```bash
# 升級 pip
pip install --upgrade pip

# 清除快取重新安裝
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

#### 3. 資料庫連接問題

```bash
# 檢查資料庫檔案權限
ls -la db/
chmod 644 db/*.db

# 重新初始化資料庫
rm -f db/history.db
python main.py  # 會自動重新建立
```

#### 4. 服務無回應

```bash
# 查看錯誤日誌
cat salesrag.log

# 重新啟動服務
pkill -f "python main.py"
python main.py
```

## 設定檔案

### config.py

主要設定檔案，包含：

- 資料庫路徑
- 應用程式設定
- 服務設定

### requirements.txt

包含所有必要的 Python 套件依賴

## API 端點

### 主要端點

- `GET /` - 主頁面
- `GET /health` - 健康檢查
- `POST /api/sales/chat-stream` - 聊天串流
- `POST /api/specs/upload` - 檔案上傳
- `GET /api/history/` - 歷史記錄

### 測試 API

```bash
# 測試健康端點
curl http://localhost:8001/health

# 測試服務列表
curl http://localhost:8001/api/sales/services

# 測試歷史記錄
curl http://localhost:8001/api/history/
```

## 維護建議

### 日常維護

1. 定期檢查日誌檔案
2. 監控系統資源使用
3. 備份重要資料庫檔案
4. 更新相依套件

### 備份

```bash
# 備份資料庫
cp db/sales_specs.db backup/
cp db/history.db backup/

# 備份設定檔案
cp config.py backup/
```

### 更新

```bash
# 更新套件
pip install --upgrade -r requirements.txt

# 檢查更新
pip list --outdated
```

## 支援

如有問題或需要協助，請：

1. 查看日誌檔案 `salesrag.log`
2. 檢查系統資源使用狀況
3. 確認網路連接正常
4. 驗證資料庫檔案完整性

---

*最後更新：2025-07-17*
