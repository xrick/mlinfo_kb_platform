"""
MGFD系統主控制器
整合所有模組並提供統一的接口
"""

import logging
import json
import redis
from typing import Dict, Any, Optional, List
from datetime import datetime

from ....libs.mgfd_modules.user_input_handler import UserInputHandler
from .redis_state_manager import RedisStateManager
from .llm_manager import MGFDLLMManager
from .dialogue_manager import DialogueManager
from .action_executor import ActionExecutor
from .response_generator import ResponseGenerator
from .config_loader import ConfigLoader


class MGFDSystem:
    """
    MGFD系統主控制器
    負責協調所有模組的工作流程
    """
    
    def __init__(self, redis_client: redis.Redis, config_path: str = "libs/mgfd_cursor/humandata/"):
        """
        初始化MGFD系統
        
        Args:
            redis_client: Redis客戶端
            config_path: 配置檔案路徑
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("初始化MGFD系統...")
        
        # 初始化配置載入器
        self.config_loader = ConfigLoader(config_path)
        
        # 初始化LLM管理器
        self.llm_manager = MGFDLLMManager()
        
        # 載入槽位模式
        self.slot_schema = self.config_loader.load_slot_schema()
        
        # 初始化所有模組
        self.state_manager = RedisStateManager(redis_client)
        self.user_input_handler = UserInputHandler(self.llm_manager, self.slot_schema)
        self.dialogue_manager = DialogueManager(notebook_kb_path=None)
        self.action_executor = ActionExecutor(self.llm_manager, self.config_loader)
        self.response_generator = ResponseGenerator(self.config_loader)
        
        self.logger.info("MGFD系統初始化完成")
    
    def process_message(self, session_id: str, user_message: str, 
                       stream: bool = False) -> Dict[str, Any]:
        """
        處理用戶消息的主要入口點
        
        Args:
            session_id: 會話ID
            user_message: 用戶消息
            stream: 是否使用串流回應
            
        Returns:
            處理結果字典
        """
        try:
            self.logger.info(f"處理會話 {session_id} 的消息: {user_message[:50]}...")
            
            # 步驟1: 處理用戶輸入
            input_result = self.user_input_handler.process_user_input(
                user_message, session_id, self.state_manager
            )
            
            if not input_result.get("success", False):
                return self._handle_error("用戶輸入處理失敗", input_result.get("error"))
            
            # 步驟2: 路由決策 (Think階段)
            decision = self.dialogue_manager.route_action(input_result["state"], user_message)
            
            # DialogueAction 對象不需要檢查 success，直接使用
            if not decision:
                return self._handle_error("對話決策失敗", "無法生成決策")
            
            # 步驟3: 執行動作 (Act階段)
            # 將 DialogueAction 轉換為 ActionExecutor 期望的格式
            command = {
                "action": decision.action_type.value,
                "target_slot": decision.target_slot,
                "message": decision.message,
                "confidence": decision.confidence
            }
            action_result = self.action_executor.execute_action(
                command, input_result["state"]
            )
            
            if not action_result.get("success", False):
                return self._handle_error("動作執行失敗", action_result.get("error"))
            
            # 步驟4: 生成回應
            response_json = self.response_generator.generate_response(action_result["result"])
            # 解析JSON回應為對象，以便前端處理
            try:
                response_obj = json.loads(response_json)
                # 提取content作為主要回應文字
                response = response_obj.get("content", response_json)
            except json.JSONDecodeError:
                # 如果解析失敗，使用原始回應
                response = response_json
            
            # 步驟5: 更新狀態
            self._update_final_state(session_id, input_result["state"], action_result["result"])
            
            # 步驟6: 格式化回應
            result = {
                "success": True,
                "response": response,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "action_type": decision.action_type.value,
                "filled_slots": input_result["state"].get("filled_slots", {}),
                "dialogue_stage": input_result["state"].get("current_stage", "awareness")
            }
            
            # 添加前端需要的額外信息
            try:
                response_obj = json.loads(response_json)
                if "suggestions" in response_obj:
                    result["suggestions"] = response_obj["suggestions"]
                if "recommendations" in response_obj:
                    result["recommendations"] = response_obj["recommendations"]
            except (json.JSONDecodeError, KeyError):
                pass
            
            # 添加串流支援
            if stream:
                result["stream_response"] = self.response_generator.generate_stream_response(action_result["result"])
            
            self.logger.info(f"會話 {session_id} 處理完成，動作類型: {result['action_type']}")
            return result
            
        except Exception as e:
            self.logger.error(f"處理消息時發生錯誤: {e}", exc_info=True)
            return self._handle_error("系統內部錯誤", str(e))
    
    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """
        獲取會話狀態
        
        Args:
            session_id: 會話ID
            
        Returns:
            會話狀態字典
        """
        try:
            state = self.state_manager.load_session_state(session_id)
            if state:
                return {
                    "success": True,
                    "state": state,
                    "dialogue_stage": state.get("current_stage", "awareness"),
                    "filled_slots": state.get("filled_slots", {}),
                    "chat_history": state.get("chat_history", [])
                }
            else:
                return {
                    "success": False,
                    "error": "會話不存在",
                    "state": None
                }
        except Exception as e:
            self.logger.error(f"獲取會話狀態失敗: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "state": None
            }
    
    def reset_session(self, session_id: str) -> Dict[str, Any]:
        """
        重置會話
        
        Args:
            session_id: 會話ID
            
        Returns:
            重置結果
        """
        try:
            success = self.state_manager.delete_session(session_id)
            if success:
                return {
                    "success": True,
                    "message": "會話重置成功",
                    "session_id": session_id
                }
            else:
                return {
                    "success": False,
                    "error": "會話重置失敗"
                }
        except Exception as e:
            self.logger.error(f"重置會話失敗: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        獲取系統狀態
        
        Returns:
            系統狀態信息
        """
        try:
            # 檢查Redis連接
            redis_status = "connected" if self.state_manager.redis_client.ping() else "disconnected"
            
            # 檢查LLM連接
            llm_status = "available" if self.llm_manager else "unavailable"
            
            # 清理過期會話
            cleaned_sessions = self.state_manager.cleanup_expired_sessions()
            
            return {
                "success": True,
                "system_status": {
                    "redis": redis_status,
                    "llm": llm_status,
                    "modules": {
                        "user_input_handler": "active",
                        "dialogue_manager": "active", 
                        "action_executor": "active",
                        "response_generator": "active",
                        "state_manager": "active"
                    },
                    "cleaned_sessions": cleaned_sessions,
                    "timestamp": datetime.now().isoformat()
                }
            }
        except Exception as e:
            self.logger.error(f"獲取系統狀態失敗: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_error(self, message: str, error: str = None) -> Dict[str, Any]:
        """
        處理錯誤並生成錯誤回應
        
        Args:
            message: 錯誤消息
            error: 詳細錯誤信息
            
        Returns:
            錯誤回應字典
        """
        error_response = {
            "success": False,
            "error": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if error:
            error_response["details"] = error
        
        self.logger.error(f"錯誤處理: {message} - {error}")
        return error_response
    
    def _update_final_state(self, session_id: str, state: Dict[str, Any], 
                           action_result: Dict[str, Any]) -> None:
        """
        更新最終狀態
        
        Args:
            session_id: 會話ID
            state: 當前狀態
            action_result: 動作執行結果
        """
        try:
            # 添加系統回應到對話歷史
            if action_result.get("response"):
                system_message = {
                    "role": "assistant",
                    "content": action_result["response"],
                    "timestamp": datetime.now().isoformat(),
                    "action_type": action_result.get("action_type", "UNKNOWN")
                }
                self.state_manager.add_message_to_history(session_id, system_message)
            
            # 保存最終狀態
            self.state_manager.save_session_state(session_id, state)
            
        except Exception as e:
            self.logger.error(f"更新最終狀態失敗: {e}", exc_info=True)
    
    def get_chat_history(self, session_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        獲取對話歷史
        
        Args:
            session_id: 會話ID
            limit: 歷史記錄限制
            
        Returns:
            對話歷史
        """
        try:
            history = self.state_manager.get_chat_history(session_id, limit)
            formatted_history = self.response_generator.format_chat_history(history)
            
            return {
                "success": True,
                "chat_history": formatted_history,
                "session_id": session_id,
                "count": len(formatted_history)
            }
        except Exception as e:
            self.logger.error(f"獲取對話歷史失敗: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "chat_history": []
            }
