import os
import sys
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 添加專案根目錄到 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from sales_rag_app.libs.service_manager import ServiceManager 
import logging

###setup debug
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# from libs.service_manager import ServiceManager

# 載入環境變數
load_dotenv()

# 初始化 FastAPI 應用
app = FastAPI()

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發時允許所有來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載靜態檔案目錄 - 修正路徑
app.mount("/static", StaticFiles(directory="sales_rag_app/static"), name="static")

# 設定模板目錄 - 修正路徑
# 設定模板目錄 - 修正路徑
templates = Jinja2Templates(directory="sales_rag_app/templates")

# 初始化服務管理器
service_manager = ServiceManager()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """渲染主頁面"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/test", response_class=HTMLResponse)
async def test_interface(request: Request):
    """渲染測試介面"""
    return templates.TemplateResponse("test_interface.html", {"request": request})

@app.get("/api/get-services", response_class=JSONResponse)
async def get_services():
    """獲取可用的服務列表"""
    services = service_manager.list_services()
    return {"services": services}

@app.post("/api/chat-stream")
async def chat_stream(request: Request):
    """處理聊天請求並返回流式響應"""
    try:
        data = await request.json()
        query = data.get("query")
        service_name = data.get("service_name", "sales_assistant") # 預設使用銷售助理

        if not query:
            return JSONResponse(status_code=400, content={"error": "Query cannot be empty"})

        service = service_manager.get_service(service_name)
        if not service:
             return JSONResponse(status_code=404, content={"error": f"Service '{service_name}' not found"})

        # 返回一個流式響應，從服務的 chat_stream 方法獲取內容
        return StreamingResponse(service.chat_stream(query), media_type="text/event-stream")

    except Exception as e:
        print(f"Error in chat_stream: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

@app.post("/api/clarification-response")
async def handle_clarification_response(request: Request):
    """處理澄清對話回應"""
    try:
        data = await request.json()
        conversation_id = data.get("conversation_id")
        user_choice = data.get("user_choice")
        user_input = data.get("user_input", "")
        service_name = data.get("service_name", "sales_assistant")

        if not conversation_id or not user_choice:
            return JSONResponse(
                status_code=400, 
                content={"error": "conversation_id and user_choice are required"}
            )

        service = service_manager.get_service(service_name)
        if not service:
            return JSONResponse(
                status_code=404, 
                content={"error": f"Service '{service_name}' not found"}
            )

        # 檢查服務是否支援澄清對話處理
        if not hasattr(service, 'process_clarification_response'):
            return JSONResponse(
                status_code=501, 
                content={"error": "Service does not support clarification responses"}
            )

        # 處理澄清回應
        result = await service.process_clarification_response(conversation_id, user_choice, user_input)
        
        return JSONResponse(content=result)

    except Exception as e:
        logging.error(f"Error in handle_clarification_response: {e}")
        return JSONResponse(
            status_code=500, 
            content={"error": f"Internal Server Error: {str(e)}"}
        )

@app.post("/api/smart-clarification-response")
async def handle_smart_clarification_response(request: Request):
    """處理智能澄清對話回應"""
    try:
        data = await request.json()
        original_query = data.get("original_query")
        question_id = data.get("question_id")
        user_choice = data.get("user_choice")
        user_input = data.get("user_input", "")
        service_name = data.get("service_name", "sales_assistant")

        if not original_query or not question_id or not user_choice:
            return JSONResponse(
                status_code=400, 
                content={"error": "original_query, question_id and user_choice are required"}
            )

        service = service_manager.get_service(service_name)
        if not service:
            return JSONResponse(
                status_code=404, 
                content={"error": f"Service '{service_name}' not found"}
            )

        # 檢查服務是否支援智能澄清處理
        if not hasattr(service, 'process_smart_clarification_response'):
            return JSONResponse(
                status_code=501, 
                content={"error": "Service does not support smart clarification responses"}
            )

        # 處理智能澄清回應
        result = await service.process_smart_clarification_response(
            original_query, question_id, user_choice, user_input
        )
        
        return JSONResponse(content=result)

    except Exception as e:
        logging.error(f"Error in handle_smart_clarification_response: {e}")
        return JSONResponse(
            status_code=500, 
            content={"error": f"Internal Server Error: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)