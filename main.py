# 導入必要的 Python 標準庫模組
import os
import sys
import uuid
from pathlib import Path

# 導入 FastAPI 相關模組
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

# 導入環境變數管理模組
from dotenv import load_dotenv

# 導入日誌記錄模組
import logging
import json
import numpy as np

# 將專案根目錄添加到 Python 路徑中，確保可以導入專案內的其他模組
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 從 config.py 導入配置常數
from api import mgfdsys_routes_deprecated
from config import STATIC_DIR, TEMPLATES_DIR, APP_HOST, APP_PORT

# 載入 .env 檔案中的環境變數
load_dotenv()

# 自定義JSON編碼器處理numpy類型
class NumpyJSONEncoder(json.JSONEncoder):
    """自定義JSON編碼器，支持numpy類型序列化"""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)

# 設定日誌記錄的基本配置
logging.basicConfig(
    level=logging.INFO,  # 設定日誌級別為 INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 設定日誌格式
    handlers=[logging.StreamHandler()]  # 設定日誌輸出到控制台
)

# 初始化 FastAPI 應用程式實例
app = FastAPI(
    title="MGFD SalesRAG Integration System",
    description="智能對話系統 - 基於FastAPI的現代化實現",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置FastAPI使用自定義JSON編碼器
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse as StarletteJSONResponse

class CustomJSONResponse(StarletteJSONResponse):
    """自定義JSONResponse，支持numpy類型"""
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            cls=NumpyJSONEncoder
        ).encode('utf-8')

# 設置默認響應類
app.default_response_class = CustomJSONResponse

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

# 導入 API 路由模組
try:
    # 嘗試導入各種 API 路由模組
    # from api import mgfd_routes,sales_routes, specs_routes, history_routes, import_data_routes
    from api import mgfd_routes, specs_routes, history_routes, milvus_routes #import_data_routes
    
    # 將各個路由模組註冊到主應用程式中
    # 導入 MGFD (Multi-turn Guided Funnel Dialogue) 路由模組
    app.include_router(mgfd_routes.router, prefix="/api/mgfd", tags=["mgfd"])
    # app.include_router(sales_routes.router, prefix="/api/sales", tags=["sales"])  # 銷售相關 API
    app.include_router(specs_routes.router, prefix="/api/specs", tags=["specs"])  # 規格相關 API
    app.include_router(history_routes.router, prefix="/api/history", tags=["history"])  # 歷史記錄相關 API
    app.include_router(milvus_routes.router, prefix="/api/milvus", tags=["milvus"])  # Milvus Viewer 相關 API
    # app.include_router(import_data_routes.router, prefix="/api", tags=["import"])  # 資料匯入相關 API
    # app.include_router(mgfdsys_routes_deprecated.router, prefix="/api/mgfdsys", tags=["mgfdsys"])  # MGFDSYS 相關 API
except ImportError as e:
    # 如果某些 API 路由模組無法導入，記錄警告訊息
    logging.warning(f"Some API routes not yet available: {e}")



# 自定義OpenAPI文檔
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="MGFD SalesRAG Integration System",
        version="2.0.0",
        description="智能對話系統API - 基於FastAPI的現代化實現",
        routes=app.routes,
    )
    
    # 添加自定義文檔信息
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    # 添加服務器信息
    openapi_schema["servers"] = [
        {
            "url": f"http://{APP_HOST}:{APP_PORT}",
            "description": "開發服務器"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

###　原本的根路徑定義
# 定義根路徑 "/" 的處理函數，返回主要的整合介面
# @app.get("/", response_class=HTMLResponse)
# async def main_interface(request: Request):
#     """主要整合介面"""
#     return templates.TemplateResponse("index.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
async def main_interface(request: Request):
    """主要整合介面"""
    return templates.TemplateResponse("index.html", {"request": request})

# 定義 "/mgfd_cursor" 路徑的處理函數，返回 MGFD 介面
# @app.get("/mgfd_cursor", response_class=HTMLResponse)
# async def mgfd_interface(request: Request):
#     """MGFD 介面"""
#     return templates.TemplateResponse("mgfd_interface.html", {"request": request})

# 定義健康檢查端點，用於監控服務狀態
@app.get("/health", tags=["system"])
async def health_check():
    """健康檢查端點"""
    try:
        # 檢查MGFD系統狀態
        from api.mgfd_routes import mgfd_system
        if mgfd_system:
            mgfd_status = "initialized"
        else:
            mgfd_status = "not_initialized"
        
        return {
            "status": "healthy",
            "service": "MGFD SalesRAG Integration",
            "version": "2.0.0",
            "mgfd_system": mgfd_status,
            "timestamp": "2025-01-27T19:30:00"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-01-27T19:30:00"
        }

# 定義系統狀態端點
@app.get("/status", tags=["system"])
async def system_status():
    """系統狀態端點"""
    try:
        # 檢查MGFD系統狀態
        from api.mgfd_routes import mgfd_system
        if mgfd_system:
            mgfd_status = mgfd_system.get_system_status()
        else:
            mgfd_status = {"success": False, "error": "MGFD系統未初始化"}
        
        return {
            "status": "running",
            "version": "2.0.0",
            "services": {
                "mgfd_system": mgfd_status
            },
            "timestamp": "2025-09-02T19:30:00"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"系統狀態檢查失敗: {str(e)}")

# 全局異常處理器
from fastapi.exceptions import RequestValidationError

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP異常處理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "error_code": exc.status_code,
            "timestamp": "2025-01-27T19:30:00"
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """請求驗證錯誤處理器"""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "輸入驗證失敗",
            "details": exc.errors(),
            "timestamp": "2025-01-27T19:30:00"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用異常處理器"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "系統內部錯誤",
            "details": str(exc),
            "timestamp": "2025-01-27T19:30:00"
        }
    )

# 中間件：添加請求處理時間
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加請求處理時間中間件"""
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 中間件：添加請求ID
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """添加請求ID中間件"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# 啟動事件
@app.on_event("startup")
async def startup_event():
    """應用程式啟動事件"""
    logging.info("🚀 MGFD SalesRAG Integration System 啟動中...")
    logging.info(f"📖 API文檔: http://{APP_HOST}:{APP_PORT}/docs")
    logging.info(f"🔍 ReDoc文檔: http://{APP_HOST}:{APP_PORT}/redoc")
    logging.info("✅ 系統啟動完成")

# 關閉事件
@app.on_event("shutdown")
async def shutdown_event():
    """應用程式關閉事件"""
    logging.info("🛑 MGFD SalesRAG Integration System 關閉中...")

# 主程式進入點
if __name__ == "__main__":
    # 導入 uvicorn ASGI 伺服器
    import uvicorn
    
    # 啟動 uvicorn 伺服器，使用配置檔案中指定的主機和埠號
    uvicorn.run(
        "main:app",
        host=APP_HOST, 
        port=APP_PORT,
        reload=True,  # 開發模式：自動重載
        log_level="info"
    )