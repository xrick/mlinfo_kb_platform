# MGFDSYS Routes - MGFDSYS Integration System API Routes
# This module handles MGFDSYS (Manufacturing Guided Funnel Dialogue System) related routes
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
import sys
import os
import json
from pathlib import Path
import logging

# Add libs to path
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))

try:
    from libs.service_manager import ServiceManager
except ImportError as e:
    logging.error(f"Failed to import ServiceManager: {e}")
    ServiceManager = None

router = APIRouter()

# Initialize service manager
service_manager = ServiceManager() if ServiceManager else None

@router.get("/services")
async def get_services():
    """獲取可用的服務列表"""
    if not service_manager:
        return {"error": "Service manager not available"}
    
    try:
        services = service_manager.list_services()
        return {"services": services}
    except Exception as e:
        logging.error(f"Error getting services: {e}")
        return {"error": str(e)}

@router.post("/chat-stream")
async def chat_stream(request: Request):
    """處理聊天請求並返回流式響應"""
    if not service_manager:
        return JSONResponse(status_code=500, content={"error": "Service manager not available"})
    
    try:
        data = await request.json()
        query = data.get("query")
        service_name = data.get("service_name", "sales_assistant")
        
        # Extract additional parameters for funnel handling
        funnel_choice = data.get("funnel_choice")
        session_id = data.get("session_id")

        if not query:
            return JSONResponse(status_code=400, content={"error": "Query cannot be empty"})

        service = service_manager.get_service(service_name)
        if not service:
            return JSONResponse(status_code=404, content={"error": f"Service '{service_name}' not found"})

        # Pass additional parameters as kwargs to the service
        kwargs = {}
        if funnel_choice:
            kwargs["funnel_choice"] = funnel_choice
        if session_id:
            kwargs["session_id"] = session_id

        # 返回一個流式響應，從服務的 chat_stream 方法獲取內容
        return StreamingResponse(service.chat_stream(query, **kwargs), media_type="text/event-stream")

    except Exception as e:
        logging.error(f"Error in chat_stream: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

@router.post("/chat")
async def chat(request: Request):
    """處理聊天請求並返回 JSON 響應"""
    if not service_manager:
        return JSONResponse(status_code=500, content={"error": "Service manager not available"})
    
    try:
        data = await request.json()
        query = data.get("query")
        service_name = data.get("service_name", "sales_assistant")

        if not query:
            return JSONResponse(status_code=400, content={"error": "Query cannot be empty"})

        service = service_manager.get_service(service_name)
        if not service:
            return JSONResponse(status_code=404, content={"error": f"Service '{service_name}' not found"})

        # 獲取服務響應
        if hasattr(service, 'chat_stream'):
            # 如果服務支援串流，使用chat_stream
            response_gen = service.chat_stream(query)
            # 收集所有串流回應
            response_parts = []
            async for part in response_gen:
                if part.startswith('data: '):
                    try:
                        data = json.loads(part[6:])
                        response_parts.append(data)
                    except json.JSONDecodeError:
                        pass
            return {"response": response_parts}
        else:
            # 回退到process_query
            response = service.process_query(query)
            return {"response": response}

    except Exception as e:
        logging.error(f"Error in chat: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

@router.post("/multichat")
async def multichat_response(request: Request):
    """處理多輪對話回應"""
    if not service_manager:
        return JSONResponse(status_code=500, content={"error": "Service manager not available"})
    
    try:
        data = await request.json()
        session_id = data.get("session_id")
        user_choice = data.get("user_choice")
        user_input = data.get("user_input", "")
        service_name = data.get("service_name", "sales_assistant")

        if not session_id or not user_choice:
            return JSONResponse(status_code=400, content={"error": "session_id and user_choice are required"})

        service = service_manager.get_service(service_name)
        if not service:
            return JSONResponse(status_code=404, content={"error": f"Service '{service_name}' not found"})

        # 檢查服務是否支援多輪對話
        if not hasattr(service, 'process_multichat_response'):
            return JSONResponse(status_code=400, content={"error": "Service does not support multichat"})

        # 處理多輪對話回應
        result = await service.process_multichat_response(session_id, user_choice, user_input)
        return result

    except Exception as e:
        logging.error(f"Error in multichat: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

@router.post("/multichat-all")
async def multichat_all_questions(request: Request):
    """處理所有問題的一次性回答提交"""
    if not service_manager:
        return JSONResponse(status_code=500, content={"error": "Service manager not available"})
    
    try:
        data = await request.json()
        answers = data.get("answers", {})
        service_name = data.get("service_name", "sales_assistant")

        if not answers:
            return JSONResponse(status_code=400, content={"error": "answers are required"})

        service = service_manager.get_service(service_name)
        if not service:
            return JSONResponse(status_code=404, content={"error": f"Service '{service_name}' not found"})

        # 檢查服務是否支援process_all_questions_response方法
        if not hasattr(service, 'process_all_questions_response'):
            return JSONResponse(status_code=400, content={"error": "Service does not support multichat-all"})

        # 處理所有問題的回答
        result = await service.process_all_questions_response(answers)
        return result

    except Exception as e:
        logging.error(f"Error in multichat-all: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

@router.post("/funnel-choice")
async def funnel_choice(request: Request):
    """處理 Funnel Conversation 的選項選擇"""
    if not service_manager:
        return JSONResponse(status_code=500, content={"error": "Service manager not available"})
    
    try:
        data = await request.json()
        session_id = data.get("session_id")
        choice_id = data.get("choice_id")
        service_name = data.get("service_name", "sales_assistant")

        if not session_id or not choice_id:
            return JSONResponse(status_code=400, content={"error": "session_id and choice_id are required"})

        service = service_manager.get_service(service_name)
        if not service:
            return JSONResponse(status_code=404, content={"error": f"Service '{service_name}' not found"})

        # 檢查服務是否支援 Funnel Conversation
        if not hasattr(service, 'process_funnel_choice'):
            return JSONResponse(status_code=400, content={"error": "Service does not support funnel conversation"})

        # 處理 Funnel 選項選擇
        result = await service.process_funnel_choice(session_id, choice_id)
        return result

    except Exception as e:
        logging.error(f"Error in funnel-choice: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

@router.post("/specialized-flow")
async def specialized_flow(request: Request):
    """執行專業化流程（系列比較或用途推薦）"""
    if not service_manager:
        return JSONResponse(status_code=500, content={"error": "Service manager not available"})
    
    try:
        data = await request.json()
        flow_type = data.get("flow_type")
        original_query = data.get("original_query")
        user_choice = data.get("user_choice")
        service_name = data.get("service_name", "sales_assistant")

        if not flow_type or not original_query or not user_choice:
            return JSONResponse(status_code=400, content={"error": "flow_type, original_query, and user_choice are required"})

        service = service_manager.get_service(service_name)
        if not service:
            return JSONResponse(status_code=404, content={"error": f"Service '{service_name}' not found"})

        # 檢查服務是否支援專業化流程
        if not hasattr(service, 'execute_specialized_flow'):
            return JSONResponse(status_code=400, content={"error": "Service does not support specialized flows"})

        # 執行專業化流程
        result = await service.execute_specialized_flow(flow_type, original_query, user_choice)
        return result

    except Exception as e:
        logging.error(f"Error in specialized-flow: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

@router.post("/funnel-question")
async def funnel_question(request: Request):
    """獲取 Funnel Conversation 的問題"""
    if not service_manager:
        return JSONResponse(status_code=500, content={"error": "Service manager not available"})
    
    try:
        data = await request.json()
        query = data.get("query")
        service_name = data.get("service_name", "sales_assistant")

        if not query:
            return JSONResponse(status_code=400, content={"error": "query is required"})

        service = service_manager.get_service(service_name)
        if not service:
            return JSONResponse(status_code=404, content={"error": f"Service '{service_name}' not found"})

        # 檢查服務是否支援 Funnel Conversation
        if not hasattr(service, 'get_funnel_question'):
            return JSONResponse(status_code=400, content={"error": "Service does not support funnel questions"})

        # 獲取 Funnel 問題
        result = await service.get_funnel_question(query)
        return result

    except Exception as e:
        logging.error(f"Error in funnel-question: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

@router.get("/mfgdsys_route")
async def mfgdsys_route():
    """MGFDSYS 主要路由處理函數"""
    try:
        return {
            "status": "success",
            "message": "MGFDSYS route is working",
            "service": "MGFDSYS Integration System",
            "version": "1.0.0"
        }
    except Exception as e:
        logging.error(f"Error in mfgdsys_route: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})