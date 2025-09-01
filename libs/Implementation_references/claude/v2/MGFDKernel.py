"""
MGFD 核心控制器 - 系統大腦及對外唯一介面
負責協調五大模組，管理對話流程，處理前端請求
"""

import logging
import json
import redis
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

# 導入其他模組（待實作）
# from .UserInputHandler import UserInputHandler
# from .StateManagementHandler import StateManagementHandler
# from .PromptManagementHandler import PromptManagementHandler
# from .KnowledgeManagementHandler import KnowledgeManagementHandler
# from .ResponseGenHandler import ResponseGenHandler

logger = logging.getLogger(__name__)


class MGFDKernel:
    """
    MGFD 系統核心控制器
    職責：協調五大模組，管理對話流程，處理前端請求
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        """
        初始化 MGFD 核心控制器
        
        Args:
            redis_client: Redis 客戶端實例，用於會話狀態持久化
        """
        self.redis_client = redis_client
        self.config = self._load_config()
        self.slot_schema = self._load_slot_schema()
        
        # 初始化五大模組（暫時使用 None，待實作）
        self.user_input_handler = None  # UserInputHandler()
        self.prompt_manager = None      # PromptManagementHandler()
        self.knowledge_manager = None   # KnowledgeManagementHandler()
        self.response_generator = None  # ResponseGenHandler()
        self.state_manager = None       # StateManagementHandler(redis_client)
        
        logger.info("MGFDKernel 初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """載入系統配置"""
        try:
            config_path = Path(__file__).parent / "config" / "system_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 使用預設配置
                return {
                    "max_session_duration": 3600,  # 1小時
                    "max_slots_per_session": 20,
                    "default_response_timeout": 30,
                    "enable_streaming": True,
                    "log_level": "INFO"
                }
        except Exception as e:
            logger.error(f"載入配置失敗: {e}")
            return {}
    
    def _load_slot_schema(self) -> Dict[str, str]:
        """載入槽位架構定義"""
        try:
            # 基於 default_slots.json 的槽位映射
            slot_mapping = {
                "用途": "usage_purpose",
                "價格區間": "price_range",
                "推出時間": "release_time",
                "CPU效能": "cpu_performance",
                "GPU效能": "gpu_performance",
                "重量": "weight",
                "攜帶性": "portability",
                "開關機速度": "boot_speed",
                "螢幕尺寸": "screen_size",
                "品牌": "brand",
                "觸控螢幕": "touch_screen"
            }
            return slot_mapping
        except Exception as e:
            logger.error(f"載入槽位架構失敗: {e}")
            return {}
    
    async def process_message(
        self, 
        session_id: str, 
        message: str, 
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        處理用戶消息 - 主要入口點
        
        Args:
            session_id: 會話識別碼
            message: 用戶輸入消息
            stream: 是否使用串流回應
            
        Returns:
            包含回應內容的字典，格式對齊 mgfd_ai.js 期望
        """
        try:
            logger.info(f"處理消息 - 會話: {session_id}, 消息: {message[:50]}...")
            
            # 檢查模組是否已初始化
            if not self._check_modules_initialized():
                return self._create_error_response("系統模組未初始化")
            
            # 處理消息
            result = await self._process_message_internal(session_id, message)
            
            # 添加會話ID到回應
            result['session_id'] = session_id
            result['timestamp'] = datetime.now().isoformat()
            
            logger.info(f"消息處理完成 - 會話: {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"處理消息時發生錯誤: {e}", exc_info=True)
            return self._create_error_response(f"系統內部錯誤: {str(e)}")
    
    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """
        獲取會話狀態
        
        Args:
            session_id: 會話識別碼
            
        Returns:
            會話狀態字典
        """
        try:
            if not self.state_manager:
                return self._create_error_response("狀態管理器未初始化")
            
            # 暫時返回基本狀態，待 StateManagementHandler 實作
            return {
                "success": True,
                "session_id": session_id,
                "current_stage": "unknown",
                "filled_slots": {},
                "chat_history": [],
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"獲取會話狀態時發生錯誤: {e}", exc_info=True)
            return self._create_error_response(f"獲取會話狀態失敗: {str(e)}")
    
    async def reset_session(self, session_id: str) -> Dict[str, Any]:
        """
        重置會話
        
        Args:
            session_id: 會話識別碼
            
        Returns:
            重置結果字典
        """
        try:
            logger.info(f"重置會話: {session_id}")
            
            if not self.state_manager:
                return self._create_error_response("狀態管理器未初始化")
            
            # 暫時返回成功，待 StateManagementHandler 實作
            return {
                "success": True,
                "session_id": session_id,
                "message": "會話重置成功",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"重置會話時發生錯誤: {e}", exc_info=True)
            return self._create_error_response(f"重置會話失敗: {str(e)}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        獲取系統狀態
        
        Returns:
            系統狀態字典
        """
        try:
            modules_status = {
                "user_input_handler": self.user_input_handler is not None,
                "prompt_manager": self.prompt_manager is not None,
                "knowledge_manager": self.knowledge_manager is not None,
                "response_generator": self.response_generator is not None,
                "state_manager": self.state_manager is not None
            }
            
            redis_status = "connected" if self.redis_client and self.redis_client.ping() else "disconnected"
            
            return {
                "success": True,
                "system_status": {
                    "redis": redis_status,
                    "modules": modules_status,
                    "timestamp": datetime.now().isoformat(),
                    "version": "v2.0.0"
                }
            }
            
        except Exception as e:
            logger.error(f"獲取系統狀態時發生錯誤: {e}", exc_info=True)
            return self._create_error_response(f"獲取系統狀態失敗: {str(e)}")
    
    async def _process_message_internal(
        self, 
        session_id: str, 
        message: str
    ) -> Dict[str, Any]:
        """
        內部消息處理流程
        
        Args:
            session_id: 會話識別碼
            message: 用戶輸入消息
            
        Returns:
            處理結果字典
        """
        # Step 1: 建立 context
        context = await self._build_context(session_id, message)
        
        # Step 2: 解析輸入（UserInputHandler）
        if self.user_input_handler:
            input_result = await self.user_input_handler.parse(message, context)
            context.update(input_result)
        else:
            # 暫時使用基本解析
            context.update({
                "intent": "unknown",
                "slots_update": {},
                "control": {},
                "errors": [],
                "confidence": 0.0
            })
        
        # Step 3: 狀態機驅動（StateManager）
        if self.state_manager:
            state_result = await self.state_manager.process_state(context)
            context.update(state_result)
        else:
            # 暫時使用基本狀態處理
            context.update({
                "stage": "INIT",
                "needs_knowledge_search": False
            })
        
        # Step 4: 知識查詢（如需要）
        if context.get('needs_knowledge_search') and self.knowledge_manager:
            knowledge_result = await self.knowledge_manager.search(context)
            context.update(knowledge_result)
        
        # Step 5: 生成回應（ResponseGenerator）
        if self.response_generator:
            response_result = await self.response_generator.generate(context)
            context.update(response_result)
        else:
            # 暫時使用基本回應
            context.update({
                "response_type": "general",
                "response_message": "系統正在處理您的請求..."
            })
        
        # Step 6: 更新狀態
        if self.state_manager:
            await self.state_manager.update_session(session_id, context)
        
        return self._format_frontend_response(context)
    
    async def _build_context(
        self, 
        session_id: str, 
        message: str
    ) -> Dict[str, Any]:
        """
        建立處理上下文
        
        Args:
            session_id: 會話識別碼
            message: 用戶輸入消息
            
        Returns:
            上下文字典
        """
        # 獲取現有會話狀態
        session_state = {}
        if self.state_manager:
            session_state = await self.state_manager.get_session(session_id) or {}
        
        context = {
            "session_id": session_id,
            "user_message": message,
            "timestamp": datetime.now().isoformat(),
            "stage": session_state.get("stage", "INIT"),
            "slots": session_state.get("slots", {}),
            "history": session_state.get("history", []),
            "control": {},
            "errors": [],
            "slot_schema": self.slot_schema,
            "config": self.config
        }
        
        return context
    
    def _format_frontend_response(
        self, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        格式化前端回應
        
        Args:
            context: 處理上下文
            
        Returns:
            格式化後的回應字典
        """
        stage = context.get('stage', 'unknown')
        response_type = context.get('response_type', 'general')
        
        # 根據階段和回應類型格式化
        if stage == 'FUNNEL_START':
            return {
                "type": "funnel_start",
                "message": context.get('funnel_intro', '歡迎使用筆電購物助手！'),
                "session_id": context.get('session_id')
            }
        elif stage == 'FUNNEL_QUESTION':
            return {
                "type": "funnel_question",
                "question": context.get('current_question'),
                "options": context.get('question_options', []),
                "session_id": context.get('session_id'),
                "message": context.get('question_message', '')
            }
        elif stage == 'RECOMMENDATION':
            return {
                "type": "recommendation",
                "recommendations": context.get('recommendations', []),
                "comparison_table": context.get('comparison_table'),
                "summary": context.get('recommendation_summary'),
                "session_id": context.get('session_id')
            }
        elif stage == 'ELICITATION':
            return {
                "type": "elicitation",
                "message": context.get('elicitation_message'),
                "slots_needed": context.get('slots_needed', []),
                "session_id": context.get('session_id')
            }
        else:
            return {
                "type": "general",
                "message": context.get('response_message', ''),
                "session_id": context.get('session_id')
            }
    
    def _check_modules_initialized(self) -> bool:
        """檢查模組是否已初始化"""
        # 只需要 UserInputHandler 已初始化即可進行基本處理
        return self.user_input_handler is not None
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """創建錯誤回應"""
        return {
            "success": False,
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }
    
    def set_user_input_handler(self, handler):
        """設置用戶輸入處理器"""
        self.user_input_handler = handler
        logger.info("UserInputHandler 已設置")
    
    def set_prompt_manager(self, manager):
        """設置提示管理器"""
        self.prompt_manager = manager
        logger.info("PromptManagementHandler 已設置")
    
    def set_knowledge_manager(self, manager):
        """設置知識管理器"""
        self.knowledge_manager = manager
        logger.info("KnowledgeManagementHandler 已設置")
    
    def set_response_generator(self, generator):
        """設置回應生成器"""
        self.response_generator = generator
        logger.info("ResponseGenHandler 已設置")
    
    def set_state_manager(self, manager):
        """設置狀態管理器"""
        self.state_manager = manager
        logger.info("StateManagementHandler 已設置")
