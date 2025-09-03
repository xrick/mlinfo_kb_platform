"""
狀態流程控制器
負責具體狀態的業務邏輯實現，每個狀態職責明確
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

from .dsm_state_enum import DSMState


# 設置日誌
logger = logging.getLogger(__name__)


class StateFlowController:
    """狀態流程控制器 - 每個狀態職責明確"""
    
    def __init__(self):
        """初始化狀態流程控制器"""
        logger.info("狀態流程控制器初始化完成")
    
    async def receive_msg(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        狀態 1: OnReceiveMsg
        職責: 接收和解析用戶消息
        
        Args:
            context: 處理上下文
            
        Returns:
            更新後的上下文
        """
        try:
            user_message = context.get("user_message", "")
            session_id = context.get("session_id", "unknown")
            
            logger.info(f"執行 OnReceiveMsg - 會話: {session_id}")
            
            # 1. 提取關鍵詞
            keywords = self._extract_keywords(user_message)
            
            # 2. 比較句子（意圖識別）
            sentence_match = self._compare_sentence(user_message)
            
            # 3. 決定流程方向（簡化分支邏輯）
            flow_direction = self._determine_flow_direction(keywords, sentence_match)
            
            result = {
                "keywords": keywords,
                "sentence_match": sentence_match,
                "flow_direction": flow_direction,
                "need_funnel_chat": flow_direction == "funnel_chat",
                "need_data_query": flow_direction == "data_query",
                "receive_msg_completed": True,
                "receive_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"OnReceiveMsg 完成 - 會話: {session_id}, 流程方向: {flow_direction}")
            return {**context, **result}
            
        except Exception as e:
            logger.error(f"OnReceiveMsg 失敗: {e}")
            return {
                **context,
                "receive_msg_completed": False,
                "error": str(e),
                "flow_direction": "fallback"
            }
    
    async def response_msg(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        狀態 2: OnResponseMsg
        職責: 生成回應和準備數據處理
        
        Args:
            context: 處理上下文
            
        Returns:
            更新後的上下文
        """
        try:
            session_id = context.get("session_id", "unknown")
            flow_direction = context.get("flow_direction", "fallback")
            
            logger.info(f"執行 OnResponseMsg - 會話: {session_id}, 流程方向: {flow_direction}")
            
            if flow_direction == "data_query":
                # 需要內部數據查詢
                result = {
                    "response_type": "data_query_required",
                    "response_message": "正在為您查詢相關信息...",
                    "need_data_query": True,
                    "need_funnel_chat": False
                }
            elif flow_direction == "funnel_chat":
                # 需要漏斗對話
                result = {
                    "response_type": "funnel_chat_required",
                    "response_message": "讓我幫您找到最適合的筆電...",
                    "need_data_query": False,
                    "need_funnel_chat": True
                }
            else:
                # 直接回應
                result = {
                    "response_type": "direct_response",
                    "response_message": "我理解您的需求，讓我為您提供幫助。",
                    "need_data_query": False,
                    "need_funnel_chat": False
                }
            
            result.update({
                "response_msg_completed": True,
                "response_timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"OnResponseMsg 完成 - 會話: {session_id}, 回應類型: {result['response_type']}")
            return {**context, **result}
            
        except Exception as e:
            logger.error(f"OnResponseMsg 失敗: {e}")
            return {
                **context,
                "response_msg_completed": False,
                "error": str(e),
                "response_type": "error"
            }
    
    async def gen_funnel_chat(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        狀態 3: OnGenFunnelChat
        職責: 生成漏斗對話引導
        
        Args:
            context: 處理上下文
            
        Returns:
            更新後的上下文
        """
        try:
            session_id = context.get("session_id", "unknown")
            keywords = context.get("keywords", [])
            
            logger.info(f"執行 OnGenFunnelChat - 會話: {session_id}")
            
            # 生成漏斗對話引導
            funnel_message = self._generate_funnel_message(keywords)
            
            result = {
                "funnel_message": funnel_message,
                "funnel_chat_generated": True,
                "funnel_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"OnGenFunnelChat 完成 - 會話: {session_id}")
            return {**context, **result}
            
        except Exception as e:
            logger.error(f"OnGenFunnelChat 失敗: {e}")
            return {
                **context,
                "funnel_chat_generated": False,
                "error": str(e)
            }
    
    async def gen_md_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        狀態 4: OnGenMDContent
        職責: 生成 Markdown 內容
        
        Args:
            context: 處理上下文
            
        Returns:
            更新後的上下文
        """
        try:
            session_id = context.get("session_id", "unknown")
            response_type = context.get("response_type", "direct_response")
            
            logger.info(f"執行 OnGenMDContent - 會話: {session_id}, 回應類型: {response_type}")
            
            if response_type == "data_query_required":
                # 生成數據查詢相關的 Markdown
                md_content = self._generate_data_query_md(context)
            elif response_type == "funnel_chat_required":
                # 生成漏斗對話相關的 Markdown
                md_content = self._generate_funnel_md(context)
            else:
                # 生成直接回應的 Markdown
                md_content = self._generate_direct_response_md(context)
            
            result = {
                "markdown_content": md_content,
                "md_content_generated": True,
                "md_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"OnGenMDContent 完成 - 會話: {session_id}")
            return {**context, **result}
            
        except Exception as e:
            logger.error(f"OnGenMDContent 失敗: {e}")
            return {
                **context,
                "md_content_generated": False,
                "error": str(e)
            }
    
    async def data_query(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        狀態 5: OnDataQuery
        職責: 執行內部數據查詢
        
        Args:
            context: 處理上下文
            
        Returns:
            更新後的上下文
        """
        try:
            session_id = context.get("session_id", "unknown")
            
            logger.info(f"執行 OnDataQuery - 會話: {session_id}")
            
            # 執行數據查詢
            query_result = await self._perform_data_query(context)
            
            result = {
                "query_result": query_result,
                "data_query_completed": True,
                "query_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"OnDataQuery 完成 - 會話: {session_id}")
            return {**context, **result}
            
        except Exception as e:
            logger.error(f"OnDataQuery 失敗: {e}")
            return {
                **context,
                "data_query_completed": False,
                "error": str(e)
            }
    
    async def queried_data_processing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        狀態 6: OnQueriedDataProcessing
        職責: 處理查詢數據
        
        Args:
            context: 處理上下文
            
        Returns:
            更新後的上下文
        """
        try:
            session_id = context.get("session_id", "unknown")
            query_result = context.get("query_result", {})
            
            logger.info(f"執行 OnQueriedDataProcessing - 會話: {session_id}")
            
            # 處理查詢數據
            processed_data = self._process_query_data(query_result)
            
            # 更新 Markdown 內容
            updated_md = self._update_markdown_with_data(context.get("markdown_content", ""), processed_data)
            
            result = {
                "processed_data": processed_data,
                "updated_markdown": updated_md,
                "data_processing_completed": True,
                "processing_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"OnQueriedDataProcessing 完成 - 會話: {session_id}")
            return {**context, **result}
            
        except Exception as e:
            logger.error(f"OnQueriedDataProcessing 失敗: {e}")
            return {
                **context,
                "data_processing_completed": False,
                "error": str(e)
            }
    
    async def send_front(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        狀態 7: OnSendFront
        職責: 發送數據到前端
        
        Args:
            context: 處理上下文
            
        Returns:
            更新後的上下文
        """
        try:
            session_id = context.get("session_id", "unknown")
            
            logger.info(f"執行 OnSendFront - 會話: {session_id}")
            
            # 準備發送到前端的數據
            frontend_data = self._prepare_frontend_data(context)
            
            # 發送到前端
            send_result = await self._send_to_frontend(frontend_data, session_id)
            
            result = {
                "frontend_data": frontend_data,
                "send_result": send_result,
                "send_front_completed": True,
                "send_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"OnSendFront 完成 - 會話: {session_id}")
            return {**context, **result}
            
        except Exception as e:
            logger.error(f"OnSendFront 失敗: {e}")
            return {
                **context,
                "send_front_completed": False,
                "error": str(e)
            }
    
    async def wait_msg(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        狀態 8: OnWaitMsg
        職責: 等待下一個消息
        
        Args:
            context: 處理上下文
            
        Returns:
            更新後的上下文
        """
        try:
            session_id = context.get("session_id", "unknown")
            
            logger.info(f"執行 OnWaitMsg - 會話: {session_id}")
            
            # 準備等待下一個消息
            wait_result = self._prepare_for_next_message(context)
            
            result = {
                "wait_prepared": True,
                "ready_for_next_message": True,
                "wait_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"OnWaitMsg 完成 - 會話: {session_id}")
            return {**context, **result}
            
        except Exception as e:
            logger.error(f"OnWaitMsg 失敗: {e}")
            return {
                **context,
                "wait_prepared": False,
                "error": str(e)
            }
    
    # ==================== 輔助方法 ====================
    
    def _extract_keywords(self, message: str) -> List[str]:
        """提取關鍵詞"""
        keywords = []
        if "筆電" in message or "laptop" in message.lower():
            keywords.append("laptop")
        if "推薦" in message or "建議" in message:
            keywords.append("recommendation")
        if "價格" in message or "預算" in message:
            keywords.append("price")
        if "規格" in message or "配置" in message:
            keywords.append("specs")
        return keywords
    
    def _compare_sentence(self, message: str) -> Dict[str, Any]:
        """比較句子（意圖識別）"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["你好", "hello", "hi"]):
            return {"intent": "greeting", "confidence": 0.9}
        elif any(word in message_lower for word in ["推薦", "建議", "找"]):
            return {"intent": "recommendation", "confidence": 0.8}
        elif any(word in message_lower for word in ["比較", "對比"]):
            return {"intent": "comparison", "confidence": 0.7}
        else:
            return {"intent": "general", "confidence": 0.5}
    
    def _determine_flow_direction(self, keywords: List[str], sentence_match: Dict[str, Any]) -> str:
        """
        決定流程方向 - 簡化分支邏輯
        
        Args:
            keywords: 提取的關鍵詞
            sentence_match: 句子匹配結果
            
        Returns:
            流程方向: "data_query", "funnel_chat", "direct_response"
        """
        intent = sentence_match.get("intent", "general")
        
        # 簡化的決策邏輯
        if intent in ["recommendation", "comparison"]:
            return "data_query"
        elif keywords and intent == "general":
            return "funnel_chat"
        else:
            return "direct_response"
    
    def _generate_funnel_message(self, keywords: List[str]) -> str:
        """生成漏斗對話引導"""
        if "laptop" in keywords:
            return "請告訴我您主要會用這台筆電來做什麼？例如工作、學習、遊戲或創作？"
        elif "price" in keywords:
            return "請告訴我您的預算大概是多少呢？"
        else:
            return "請告訴我您對筆電有什麼具體需求？"
    
    def _generate_data_query_md(self, context: Dict[str, Any]) -> str:
        """生成數據查詢相關的 Markdown"""
        return "# 正在查詢\n\n正在為您查詢相關信息，請稍候..."
    
    def _generate_funnel_md(self, context: Dict[str, Any]) -> str:
        """生成漏斗對話相關的 Markdown"""
        funnel_msg = context.get("funnel_message", "請告訴我您的需求...")
        return f"# 需求收集\n\n{funnel_msg}"
    
    def _generate_direct_response_md(self, context: Dict[str, Any]) -> str:
        """生成直接回應的 Markdown"""
        response_msg = context.get("response_message", "我理解您的需求...")
        return f"# 回應\n\n{response_msg}"
    
    async def _perform_data_query(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """執行數據查詢"""
        # 模擬數據查詢
        await asyncio.sleep(0.1)
        return {"query_result": "sample_data", "timestamp": datetime.now().isoformat()}
    
    def _process_query_data(self, query_result: Any) -> Any:
        """處理查詢數據"""
        return {"processed": "processed_data", "timestamp": datetime.now().isoformat()}
    
    def _update_markdown_with_data(self, original_md: str, processed_data: Any) -> str:
        """更新 Markdown 內容"""
        return f"{original_md}\n\n## 查詢結果\n\n基於查詢結果的內容..."
    
    def _prepare_frontend_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """準備前端數據"""
        md_content = context.get("updated_markdown") or context.get("markdown_content", "")
        return {
            "message": md_content,
            "session_id": context.get("session_id", ""),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _send_to_frontend(self, frontend_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """發送到前端"""
        # 模擬發送
        await asyncio.sleep(0.05)
        return {"success": True, "session_id": session_id}
    
    def _prepare_for_next_message(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """準備下一個消息"""
        return {"status": "ready", "timestamp": datetime.now().isoformat()}


# 導出主要類別
__all__ = ['StateFlowController']
