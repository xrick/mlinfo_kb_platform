#!/bin/bash

# SalesRAG 整合系統安裝腳本
# 使用方法: ./scripts/install.sh [dev|prod]

# 設定顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 設定變數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_MIN_VERSION="3.8"
INSTALL_MODE="dev"

# 顯示歡迎訊息
show_welcome() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}    SalesRAG 整合系統安裝程式${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo -e "${GREEN}專案目錄: $PROJECT_DIR${NC}"
    echo -e "${GREEN}安裝模式: $INSTALL_MODE${NC}"
    echo ""
}

# 檢查作業系統
check_os() {
    echo -e "${YELLOW}檢查作業系統...${NC}"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="Linux"
        DISTRO=$(lsb_release -si 2>/dev/null || echo "Unknown")
        echo -e "${GREEN}作業系統: $OS ($DISTRO)${NC}"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
        echo -e "${GREEN}作業系統: $OS${NC}"
    else
        echo -e "${RED}警告: 不支援的作業系統 $OSTYPE${NC}"
        echo -e "${YELLOW}建議在 Linux 或 macOS 環境下運行${NC}"
    fi
    
    echo ""
}

# 檢查 Python 版本
check_python() {
    echo -e "${YELLOW}檢查 Python 環境...${NC}"
    
    if ! command -v python &> /dev/null; then
        if ! command -v python3 &> /dev/null; then
            echo -e "${RED}錯誤: 未找到 Python。請先安裝 Python ${PYTHON_MIN_VERSION}+${NC}"
            echo ""
            echo "安裝建議:"
            echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
            echo "  CentOS/RHEL:   sudo yum install python3 python3-pip"
            echo "  macOS:         brew install python3"
            echo ""
            exit 1
        else
            alias python=python3
        fi
    fi
    
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    echo -e "${GREEN}Python 版本: $PYTHON_VERSION${NC}"
    
    # 檢查版本是否符合要求
    if (( PYTHON_MAJOR < 3 || (PYTHON_MAJOR == 3 && PYTHON_MINOR < 8) )); then
        echo -e "${RED}錯誤: Python 版本過低，需要 ${PYTHON_MIN_VERSION} 或更高版本${NC}"
        exit 1
    fi
    
    echo ""
}

# 檢查 pip
check_pip() {
    echo -e "${YELLOW}檢查 pip 套件管理器...${NC}"
    
    if ! command -v pip &> /dev/null; then
        if ! command -v pip3 &> /dev/null; then
            echo -e "${RED}錯誤: 未找到 pip。請先安裝 pip${NC}"
            echo ""
            echo "安裝建議:"
            echo "  Ubuntu/Debian: sudo apt-get install python3-pip"
            echo "  CentOS/RHEL:   sudo yum install python3-pip"
            echo "  macOS:         brew install python3"
            echo ""
            exit 1
        else
            alias pip=pip3
        fi
    fi
    
    PIP_VERSION=$(pip --version | awk '{print $2}')
    echo -e "${GREEN}pip 版本: $PIP_VERSION${NC}"
    
    # 升級 pip
    echo -e "${YELLOW}升級 pip...${NC}"
    pip install --upgrade pip
    
    echo ""
}

# 檢查系統依賴
check_system_deps() {
    echo -e "${YELLOW}檢查系統依賴...${NC}"
    
    # 檢查必要的系統套件
    MISSING_DEPS=()
    
    if [[ "$OS" == "Linux" ]]; then
        # Linux 系統依賴
        if ! command -v gcc &> /dev/null; then
            MISSING_DEPS+=("gcc")
        fi
        
        if ! command -v make &> /dev/null; then
            MISSING_DEPS+=("make")
        fi
        
        if ! python -c "import sqlite3" 2>/dev/null; then
            MISSING_DEPS+=("libsqlite3-dev")
        fi
        
        if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
            echo -e "${YELLOW}需要安裝以下系統依賴: ${MISSING_DEPS[*]}${NC}"
            echo ""
            echo "安裝命令:"
            echo "  Ubuntu/Debian: sudo apt-get install ${MISSING_DEPS[*]}"
            echo "  CentOS/RHEL:   sudo yum install ${MISSING_DEPS[*]}"
            echo ""
            read -p "是否現在安裝這些依賴? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                if command -v apt-get &> /dev/null; then
                    sudo apt-get update
                    sudo apt-get install -y ${MISSING_DEPS[*]}
                elif command -v yum &> /dev/null; then
                    sudo yum install -y ${MISSING_DEPS[*]}
                fi
            fi
        fi
    fi
    
    echo -e "${GREEN}系統依賴檢查完成${NC}"
    echo ""
}

# 建立虛擬環境
create_venv() {
    echo -e "${YELLOW}建立 Python 虛擬環境...${NC}"
    
    VENV_DIR="$PROJECT_DIR/venv"
    
    if [ -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}虛擬環境已存在，跳過建立${NC}"
    else
        python -m venv "$VENV_DIR"
        echo -e "${GREEN}虛擬環境建立完成: $VENV_DIR${NC}"
    fi
    
    # 啟用虛擬環境
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}虛擬環境已啟用${NC}"
    
    # 升級 pip
    pip install --upgrade pip
    
    echo ""
}

# 安裝 Python 依賴
install_python_deps() {
    echo -e "${YELLOW}安裝 Python 依賴套件...${NC}"
    
    cd "$PROJECT_DIR"
    
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}錯誤: 找不到 requirements.txt 檔案${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}從 requirements.txt 安裝套件...${NC}"
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Python 依賴安裝成功${NC}"
    else
        echo -e "${RED}Python 依賴安裝失敗${NC}"
        exit 1
    fi
    
    echo ""
}

# 建立必要目錄
create_directories() {
    echo -e "${YELLOW}建立必要目錄...${NC}"
    
    DIRS=(
        "$PROJECT_DIR/db"
        "$PROJECT_DIR/logs"
        "$PROJECT_DIR/uploads"
        "$PROJECT_DIR/backups"
    )
    
    for dir in "${DIRS[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            echo -e "${GREEN}建立目錄: $dir${NC}"
        fi
    done
    
    echo ""
}

# 設定檔案權限
set_permissions() {
    echo -e "${YELLOW}設定檔案權限...${NC}"
    
    # 設定腳本執行權限
    chmod +x "$PROJECT_DIR/scripts/"*.sh
    
    # 設定資料庫目錄權限
    chmod 755 "$PROJECT_DIR/db"
    
    # 設定日誌目錄權限
    chmod 755 "$PROJECT_DIR/logs"
    
    echo -e "${GREEN}檔案權限設定完成${NC}"
    echo ""
}

# 初始化資料庫
init_database() {
    echo -e "${YELLOW}初始化資料庫...${NC}"
    
    cd "$PROJECT_DIR"
    
    # 檢查資料庫檔案
    if [ -f "db/sales_specs.db" ]; then
        echo -e "${GREEN}DuckDB 資料庫已存在${NC}"
    else
        echo -e "${YELLOW}DuckDB 資料庫將在首次啟動時建立${NC}"
    fi
    
    # 測試資料庫連接
    python -c "
import sys
sys.path.append('.')
try:
    from utils.database import DatabaseManager
    from config import DB_PATH, HISTORY_DB_PATH
    
    config = {
        'db_path': str(DB_PATH),
        'history_db_path': str(HISTORY_DB_PATH)
    }
    
    db_manager = DatabaseManager(config)
    results = db_manager.test_connections()
    
    if results.get('duckdb', False):
        print('DuckDB 連接測試: 成功')
    else:
        print('DuckDB 連接測試: 失敗')
    
    if results.get('history', False):
        print('歷史資料庫連接測試: 成功')
    else:
        print('歷史資料庫連接測試: 失敗')
        
except Exception as e:
    print(f'資料庫測試失敗: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}資料庫初始化完成${NC}"
    else
        echo -e "${RED}資料庫初始化失敗${NC}"
        exit 1
    fi
    
    echo ""
}

# 驗證安裝
verify_installation() {
    echo -e "${YELLOW}驗證安裝...${NC}"
    
    cd "$PROJECT_DIR"
    
    # 測試導入主要模組
    python -c "
import sys
sys.path.append('.')
try:
    import main
    from config import *
    from api import sales_routes, specs_routes, history_routes
    print('模組導入測試: 成功')
except Exception as e:
    print(f'模組導入測試失敗: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}安裝驗證通過${NC}"
    else
        echo -e "${RED}安裝驗證失敗${NC}"
        exit 1
    fi
    
    echo ""
}

# 建立啟動腳本
create_shortcuts() {
    echo -e "${YELLOW}建立啟動腳本...${NC}"
    
    # 建立啟動腳本
    cat > "$PROJECT_DIR/start.sh" << 'EOF'
#!/bin/bash
# SalesRAG 快速啟動腳本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 啟用虛擬環境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 啟動服務
python main.py
EOF

    chmod +x "$PROJECT_DIR/start.sh"
    
    # 建立停止腳本
    cat > "$PROJECT_DIR/stop.sh" << 'EOF'
#!/bin/bash
# SalesRAG 快速停止腳本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/scripts/stop_service.sh"
EOF

    chmod +x "$PROJECT_DIR/stop.sh"
    
    echo -e "${GREEN}啟動腳本建立完成${NC}"
    echo ""
}

# 顯示安裝完成訊息
show_completion() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}    安裝完成！${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo -e "${GREEN}安裝摘要:${NC}"
    echo -e "${GREEN}  - Python 版本: $PYTHON_VERSION${NC}"
    echo -e "${GREEN}  - 專案目錄: $PROJECT_DIR${NC}"
    echo -e "${GREEN}  - 安裝模式: $INSTALL_MODE${NC}"
    echo ""
    echo -e "${YELLOW}快速啟動命令:${NC}"
    echo -e "${YELLOW}  開發模式: ./start.sh${NC}"
    echo -e "${YELLOW}  生產模式: ./scripts/start_service.sh prod${NC}"
    echo -e "${YELLOW}  停止服務: ./stop.sh${NC}"
    echo ""
    echo -e "${YELLOW}詳細說明請參考: USAGE.md${NC}"
    echo ""
    echo -e "${GREEN}立即啟動服務:${NC}"
    echo -e "${GREEN}  cd $PROJECT_DIR && ./start.sh${NC}"
    echo ""
}

# 顯示使用說明
show_usage() {
    echo "使用方法: $0 [dev|prod]"
    echo ""
    echo "安裝模式:"
    echo "  dev  - 開發模式 (建立虛擬環境)"
    echo "  prod - 生產模式 (系統級安裝)"
    echo ""
    echo "範例:"
    echo "  $0 dev      # 開發模式安裝"
    echo "  $0 prod     # 生產模式安裝"
    echo ""
}

# 主程式
main() {
    # 檢查參數
    if [ $# -gt 0 ]; then
        case $1 in
            "dev")
                INSTALL_MODE="dev"
                ;;
            "prod")
                INSTALL_MODE="prod"
                ;;
            "help"|"-h"|"--help")
                show_usage
                exit 0
                ;;
            *)
                echo -e "${RED}錯誤: 不支援的安裝模式 '$1'${NC}"
                show_usage
                exit 1
                ;;
        esac
    fi
    
    # 執行安裝步驟
    show_welcome
    check_os
    check_python
    check_pip
    check_system_deps
    
    if [ "$INSTALL_MODE" = "dev" ]; then
        create_venv
    fi
    
    install_python_deps
    create_directories
    set_permissions
    init_database
    verify_installation
    create_shortcuts
    show_completion
}

# 執行主程式
main "$@"