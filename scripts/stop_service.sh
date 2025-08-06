#!/bin/bash

# SalesRAG 服務停止腳本
# 使用方法: ./scripts/stop_service.sh [force]

# 設定顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 設定變數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_DIR/salesrag.pid"
LOG_FILE="$PROJECT_DIR/salesrag.log"
PORT=8001

# 檢查服務狀態
check_service_status() {
    # 方法 1: 檢查 PID 檔案
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}找到服務程序 (PID: $PID)${NC}"
            return 0
        else
            echo -e "${YELLOW}PID 檔案存在但程序不存在，清除過時的 PID 檔案${NC}"
            rm -f "$PID_FILE"
        fi
    fi
    
    # 方法 2: 檢查埠口使用情況
    if lsof -i :$PORT > /dev/null 2>&1; then
        PID=$(lsof -ti :$PORT)
        echo -e "${YELLOW}找到使用埠口 $PORT 的程序 (PID: $PID)${NC}"
        return 0
    fi
    
    # 方法 3: 檢查程序名稱
    PID=$(pgrep -f "python main.py" | head -1)
    if [ -n "$PID" ]; then
        echo -e "${YELLOW}找到 Python 主程序 (PID: $PID)${NC}"
        return 0
    fi
    
    echo -e "${GREEN}沒有找到運行中的服務${NC}"
    return 1
}

# 優雅停止服務
graceful_stop() {
    echo -e "${YELLOW}嘗試優雅停止服務...${NC}"
    
    # 從 PID 檔案獲取程序 ID
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "發送 SIGTERM 信號給程序 $PID"
            kill $PID
            
            # 等待程序結束
            for i in {1..30}; do
                if ! ps -p $PID > /dev/null 2>&1; then
                    echo -e "${GREEN}程序已優雅停止${NC}"
                    rm -f "$PID_FILE"
                    return 0
                fi
                sleep 1
            done
            
            echo -e "${YELLOW}優雅停止超時，將強制停止${NC}"
            kill -9 $PID
            rm -f "$PID_FILE"
            return 0
        else
            echo -e "${YELLOW}PID 檔案中的程序不存在，清除檔案${NC}"
            rm -f "$PID_FILE"
        fi
    fi
    
    # 停止使用指定埠口的程序
    PID=$(lsof -ti :$PORT)
    if [ -n "$PID" ]; then
        echo "停止使用埠口 $PORT 的程序 (PID: $PID)"
        kill $PID
        sleep 2
        
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}強制停止程序${NC}"
            kill -9 $PID
        fi
        return 0
    fi
    
    # 停止所有相關的 Python 程序
    PIDS=$(pgrep -f "python main.py")
    if [ -n "$PIDS" ]; then
        echo "停止所有相關的 Python 程序: $PIDS"
        for PID in $PIDS; do
            kill $PID
            sleep 1
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID
            fi
        done
        return 0
    fi
    
    echo -e "${GREEN}沒有找到需要停止的服務${NC}"
    return 1
}

# 強制停止服務
force_stop() {
    echo -e "${YELLOW}強制停止所有相關服務...${NC}"
    
    # 強制停止所有相關程序
    pkill -9 -f "python main.py"
    pkill -9 -f "uvicorn main:app"
    pkill -9 -f "salesrag"
    
    # 釋放埠口
    if lsof -i :$PORT > /dev/null 2>&1; then
        PID=$(lsof -ti :$PORT)
        echo "強制停止占用埠口 $PORT 的程序 (PID: $PID)"
        kill -9 $PID
    fi
    
    # 清理檔案
    rm -f "$PID_FILE"
    
    echo -e "${GREEN}強制停止完成${NC}"
}

# 清理資源
cleanup() {
    echo -e "${YELLOW}清理資源...${NC}"
    
    # 清理 PID 檔案
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ! ps -p $PID > /dev/null 2>&1; then
            rm -f "$PID_FILE"
            echo "清理過時的 PID 檔案"
        fi
    fi
    
    # 清理臨時檔案
    find "$PROJECT_DIR" -name "*.pyc" -delete
    find "$PROJECT_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
    
    echo -e "${GREEN}清理完成${NC}"
}

# 顯示服務狀態
show_status() {
    echo -e "${YELLOW}=== 服務狀態檢查 ===${NC}"
    
    # 檢查程序
    if check_service_status; then
        echo -e "${YELLOW}服務狀態: 運行中${NC}"
        
        # 顯示程序資訊
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            echo "PID 檔案: $PID_FILE"
            echo "程序 ID: $PID"
        fi
        
        # 顯示埠口使用情況
        if lsof -i :$PORT > /dev/null 2>&1; then
            echo "埠口 $PORT: 使用中"
        fi
        
        # 顯示記憶體使用
        if [ -n "$PID" ]; then
            MEM=$(ps -p $PID -o rss= 2>/dev/null)
            if [ -n "$MEM" ]; then
                echo "記憶體使用: ${MEM}KB"
            fi
        fi
        
    else
        echo -e "${GREEN}服務狀態: 已停止${NC}"
    fi
    
    # 檢查日誌檔案
    if [ -f "$LOG_FILE" ]; then
        LOG_SIZE=$(du -h "$LOG_FILE" | cut -f1)
        echo "日誌檔案: $LOG_FILE ($LOG_SIZE)"
    fi
    
    echo ""
}

# 顯示使用說明
show_usage() {
    echo "使用方法: $0 [force|status|clean]"
    echo ""
    echo "選項說明:"
    echo "  (無參數) - 優雅停止服務"
    echo "  force     - 強制停止所有相關服務"
    echo "  status    - 顯示服務狀態"
    echo "  clean     - 清理資源和臨時檔案"
    echo ""
    echo "範例:"
    echo "  $0         # 優雅停止服務"
    echo "  $0 force   # 強制停止服務"
    echo "  $0 status  # 查看服務狀態"
    echo "  $0 clean   # 清理資源"
    echo ""
}

# 主程式
main() {
    echo -e "${GREEN}=== SalesRAG 服務停止程式 ===${NC}"
    echo ""
    
    # 檢查參數
    ACTION=${1:-"stop"}
    
    case $ACTION in
        "stop")
            if check_service_status; then
                graceful_stop
            fi
            ;;
        "force")
            force_stop
            ;;
        "status")
            show_status
            ;;
        "clean")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}錯誤: 不支援的操作 '$ACTION'${NC}"
            show_usage
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}操作完成${NC}"
}

# 執行主程式
main "$@"