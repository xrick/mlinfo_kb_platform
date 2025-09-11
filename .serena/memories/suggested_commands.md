# 建議指令

## 安裝與設定
```bash
# 開發模式安裝
./scripts/install.sh dev

# 生產模式安裝  
./scripts/install.sh prod

# 手動安裝依賴
pip install -r requirements.txt
```

## 執行應用程式
```bash
# 開發模式 (前台執行，自動重載)
python main.py

# 生產模式 (背景執行，多worker)
./scripts/start_service.sh prod

# 停止服務
./scripts/stop_service.sh
```

## 資料庫管理
```bash
# 查看DuckDB數據
python tools/duckdb_viewer_cli.py

# 檢查Milvus集合
python check_milvus_collection.py
```

## 測試與驗證
```bash
# 健康檢查
curl http://localhost:8001/health

# 系統狀態
curl http://localhost:8001/status
```