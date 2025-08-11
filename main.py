# 導入必要的 Python 標準庫模組
import os
import sys
from pathlib import Path

# 導入 FastAPI 相關模組
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# 導入環境變數管理模組
from dotenv import load_dotenv

# 導入日誌記錄模組
import logging

# 將專案根目錄添加到 Python 路徑中，確保可以導入專案內的其他模組
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 從 config.py 導入配置常數
from config import STATIC_DIR, TEMPLATES_DIR, APP_HOST, APP_PORT

# 載入 .env 檔案中的環境變數
load_dotenv()

# 設定日誌記錄的基本配置
logging.basicConfig(
    level=logging.INFO,  # 設定日誌級別為 INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 設定日誌格式
    handlers=[logging.StreamHandler()]  # 設定日誌輸出到控制台
)

# 初始化 FastAPI 應用程式實例
app = FastAPI(title="SalesRAG Integration System")

# 添加 CORS 中間件，允許跨域請求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源
    allow_credentials=True,  # 允許攜帶認證資訊
    allow_methods=["*"],  # 允許所有 HTTP 方法
    allow_headers=["*"],  # 允許所有 HTTP 標頭
)

# 掛載靜態檔案目錄，讓前端可以存取 CSS、JavaScript 等靜態資源
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 設定 Jinja2 模板引擎，用於渲染 HTML 頁面
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# 導入 API 路由模組（稍後會建立）
try:
    # 嘗試導入各種 API 路由模組
    from api import sales_routes, specs_routes, history_routes, import_data_routes
    
    # 將各個路由模組註冊到主應用程式中
    app.include_router(sales_routes.router, prefix="/api/sales", tags=["sales"])  # 銷售相關 API
    app.include_router(specs_routes.router, prefix="/api/specs", tags=["specs"])  # 規格相關 API
    app.include_router(history_routes.router, prefix="/api/history", tags=["history"])  # 歷史記錄相關 API
    app.include_router(import_data_routes.router, prefix="/api", tags=["import"])  # 資料匯入相關 API
except ImportError as e:
    # 如果某些 API 路由模組無法導入，記錄警告訊息
    logging.warning(f"Some API routes not yet available: {e}")

# 導入 MGFD (Multi-turn Guided Funnel Dialogue) 路由模組
try:
    from api import mgfd_routes
    # 將 MGFD 路由註冊到主應用程式中
    app.include_router(mgfd_routes.router, prefix="/api/mgfd_cursor", tags=["mgfd"])
except ImportError as e:
    # 如果 MGFD 路由模組無法導入，記錄警告訊息
    logging.warning(f"MGFD routes not available: {e}")

# 定義根路徑 "/" 的處理函數，返回主要的整合介面
@app.get("/", response_class=HTMLResponse)
async def main_interface(request: Request):
    """主要整合介面"""
    return templates.TemplateResponse("index.html", {"request": request})

# 定義 "/mgfd_cursor" 路徑的處理函數，返回 MGFD 介面
@app.get("/mgfd_cursor", response_class=HTMLResponse)
async def mgfd_interface(request: Request):
    """MGFD 介面"""
    return templates.TemplateResponse("mgfd_interface.html", {"request": request})

# 定義健康檢查端點，用於監控服務狀態
@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "service": "SalesRAG Integration"}

# 主程式進入點
if __name__ == "__main__":
    # 導入 uvicorn ASGI 伺服器
    import uvicorn
    
    # 啟動 uvicorn 伺服器，使用配置檔案中指定的主機和埠號
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)