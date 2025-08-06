#!/bin/bash

# SalesRAG 服務啟動腳本
# 使用方法: ./scripts/start_service.sh [dev|prod]

# 設定顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 設定變數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/salesrag.log"
PID_FILE="$PROJECT_DIR/salesrag.pid"
PORT=8001
HOST="0.0.0.0"

# 檢查 Python 環境
check_python() {
    if ! command -v python &> /dev/null; then
        echo -e "${RED}錯誤: 未找到 Python。請確保 Python 已安裝且在 PATH 中。${NC}"
        exit 1
    fi
    
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}Python 版本: $PYTHON_VERSION${NC}"
}

# 檢查相依套件
check_dependencies() {
    echo -e "${YELLOW}檢查相依套件...${NC}"
    
    python -c "import fastapi, uvicorn, duckdb, pymilvus, pandas" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${RED}錯誤: 部分套件未安裝。請執行 'pip install -r requirements.txt'${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}所有套件檢查通過${NC}"
}

# 檢查埠口是否被占用
check_port() {
    if lsof -i :$PORT > /dev/null 2>&1; then
        echo -e "${RED}錯誤: 埠口 $PORT 已被占用${NC}"
        echo "請使用以下命令查看占用的程序:"
        echo "lsof -i :$PORT"
        exit 1
    fi
}

# 建立必要目錄
create_directories() {
    mkdir -p "$PROJECT_DIR/db"
    mkdir -p "$PROJECT_DIR/logs"
    
    # 設定日誌檔案
    touch "$LOG_FILE"
    
    echo -e "${GREEN}目錄結構已建立${NC}"
}

# 開發模式啟動
start_dev() {
    echo -e "${YELLOW}啟動開發模式...${NC}"
    
    cd "$PROJECT_DIR"
    python main.py
}

# 生產模式啟動
start_prod() {
    echo -e "${YELLOW}啟動生產模式...${NC}"
    
    cd "$PROJECT_DIR"
    
    # 使用 nohup 在背景執行
    nohup uvicorn main:app --host $HOST --port $PORT --workers 4 > "$LOG_FILE" 2>&1 &
    
    # 取得程序 ID
    PID=$!
    echo $PID > "$PID_FILE"
    
    echo -e "${GREEN}服務已在背景啟動${NC}"
    echo "程序 ID: $PID"
    echo "日誌檔案: $LOG_FILE"
    echo "PID 檔案: $PID_FILE"
    
    # 等待服務啟動
    sleep 3
    
    # 檢查服務狀態
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}服務健康檢查通過${NC}"
        echo "服務網址: http://localhost:$PORT"
    else
        echo -e "${RED}警告: 服務可能未正常啟動，請查看日誌${NC}"
    fi
}

# 顯示使用說明
show_usage() {
    echo "使用方法: $0 [dev|prod]"
    echo ""
    echo "模式說明:"
    echo "  dev  - 開發模式 (前台執行，自動重載)"
    echo "  prod - 生產模式 (背景執行，多個 worker)"
    echo ""
    echo "範例:"
    echo "  $0 dev      # 開發模式啟動"
    echo "  $0 prod     # 生產模式啟動"
    echo ""
}

# 主程式
main() {
    echo -e "${GREEN}=== SalesRAG 服務啟動程式 ===${NC}"
    echo ""
    
    # 檢查參數
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi
    
    MODE=$1
    
    case $MODE in
        "dev")
            echo -e "${YELLOW}模式: 開發模式${NC}"
            ;;
        "prod")
            echo -e "${YELLOW}模式: 生產模式${NC}"
            ;;
        *)
            echo -e "${RED}錯誤: 不支援的模式 '$MODE'${NC}"
            show_usage
            exit 1
            ;;
    esac
    
    # 執行檢查
    check_python
    check_dependencies
    check_port
    create_directories
    
    # 啟動服務
    if [ "$MODE" = "dev" ]; then
        start_dev
    else
        start_prod
    fi
}

# 執行主程式
main "$@"