"""
MGFD系統主控制器
整合所有模組並提供統一的接口
"""

import logging
import json
import redis
from typing import Dict, Any, Optional, List
from datetime import datetime

from .user_input_handler import UserInputHandler
from .redis_state_manager import RedisStateManager
from .llm_manager import MGFDLLMManager
from .response_generator import ResponseGenerator
from .knowledge_base import NotebookKnowledgeBase
from .question_manager import QuestionManager


class MGFDSystem:
    """
    MGFD系統主控制器
    負責協調所有模組的工作流程
    """
    
    def __init__(self, redis_client: redis.Redis, config_path: str = "libs/mgfd_cursor/humandata/"):
        """
        初始化MGFD系統 - 簡化版for Case-1
        
        Args:
            redis_client: Redis客戶端
            config_path: 配置檔案路徑
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("初始化MGFD系統 (簡化版)...")
        
        self.config_path = config_path
        
        # 初始化LLM管理器
        self.llm_manager = MGFDLLMManager()
        
        # 載入槽位配置 - 直接載入enhanced配置
        self.slot_schema = self._load_slot_schema()
        
        # 初始化核心模組
        self.state_manager = RedisStateManager(redis_client)
        self.user_input_handler = UserInputHandler(self.llm_manager, self.slot_schema)
        self.question_manager = QuestionManager(f"{config_path}/default_slots_questions.json")
        self.response_generator = ResponseGenerator()
        self.knowledge_base = NotebookKnowledgeBase()
        
        # Prompt風格控制
        self.use_prompt_style = True
        self.current_prompt_step = 1
        
        self.logger.info("MGFD系統初始化完成 (簡化版)")
    
    def _load_slot_schema(self) -> Dict[str, Any]:
        """載入槽位配置"""
        try:
            import os
            config_file = os.path.join(self.config_path, "default_slots_enhanced.json")
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("slot_definitions", {})
        except Exception as e:
            self.logger.error(f"載入槽位配置失敗: {e}")
            return {}
    
    def process_message(self, session_id: str, user_message: str, 
                       stream: bool = False) -> Dict[str, Any]:
        """
        處理用戶消息 - 簡化版Case-1流程
        
        Args:
            session_id: 會話ID
            user_message: 用戶消息
            stream: 是否使用串流回應
            
        Returns:
            處理結果字典
        """
        try:
            self.logger.info(f"========== 開始處理會話 {session_id} 的消息: {user_message[:50]}... ==========")
            
            # 步驟1: 處理用戶輸入並提取槽位
            input_result = self.user_input_handler.process_user_input(
                user_message, session_id, self.state_manager
            )
            
            if not input_result.get("success", False):
                return self._handle_error("用戶輸入處理失敗", input_result.get("error"))
            
            current_state = input_result["state"]
            current_slots = current_state.get("filled_slots", {})
            
            # 調試：輸出當前狀態
            self.logger.info(f"DEBUG - 當前狀態檢查:")
            self.logger.info(f"  - filled_slots: {current_slots}")
            self.logger.info(f"  - awaiting_prompt_response: {current_state.get('awaiting_prompt_response', False)}")
            self.logger.info(f"  - current_prompt_step: {current_state.get('current_prompt_step', 'None')}")
            self.logger.info(f"  - funnel_mode: {current_state.get('funnel_mode', False)}")
            self.logger.info(f"  - current_stage: {current_state.get('current_stage', 'None')}")

            # 優先處理：等待回覆模式（避免重覆同題）
            if current_state.get("awaiting_prompt_response", False):
                try:
                    step = int(current_state.get("current_prompt_step", 1))
                except Exception:
                    step = 1

                self.logger.info(f"等待回覆模式命中：step={step}, slots={current_slots}")
                
                # 修復：先檢查用戶回應是否有效，而不是槽位是否改變
                is_valid_response = self._was_response_successfully_processed(step, user_message, current_slots)
                
                if is_valid_response:
                    # 用戶提供了有效回應 → 處理槽位並前進到下一步
                    updated_slots = self.question_manager.process_prompt_response(step, user_message, current_slots)
                    
                    # 應用智能推斷增強槽位信息
                    inferred_slots = self.question_manager.auto_infer_slots(updated_slots)
                    
                    # 記錄處理結果
                    if updated_slots != current_slots:
                        self.logger.info(f"DEBUG - 槽位有更新: {current_slots} -> {updated_slots}")
                    else:
                        self.logger.info(f"DEBUG - 槽位無變化但用戶回應有效: {current_slots}")
                    
                    if inferred_slots != updated_slots:
                        self.logger.info(f"DEBUG - 智能推斷增強槽位: {updated_slots} -> {inferred_slots}")
                    
                    # 更新狀態並前進到下一步
                    current_state["filled_slots"] = inferred_slots
                    current_state["awaiting_prompt_response"] = False
                    current_state["current_prompt_step"] = step + 1
                    self.logger.info(f"DEBUG - 狀態更新: awaiting_prompt_response=False, current_prompt_step={step + 1}")
                    self.state_manager.save_session_state(session_id, current_state)
                    self.logger.info(f"DEBUG - 狀態已保存到 Redis")

                    # 若已可直接搜尋，則跳過剩餘問題
                    if self.question_manager.should_skip_to_search(updated_slots) or self.question_manager.is_collection_complete(updated_slots):
                        return self._handle_product_search(session_id, current_state)

                    # 否則進入下一題
                    next_step = int(current_state.get("current_prompt_step", step + 1))
                    next_question = self.question_manager.get_prompt_style_question(next_step, updated_slots)
                    if next_question:
                        # 修復：設定等待回應狀態並保存
                        current_state["awaiting_prompt_response"] = True
                        current_state["current_prompt_step"] = next_step
                        current_state["current_question_slot"] = next_question["slot_name"]
                        self.state_manager.save_session_state(session_id, current_state)
                        self.logger.info(f"DEBUG - 設定下一題等待狀態: awaiting_prompt_response=True, step={next_step}")
                        
                        question_text = self.question_manager.format_question_with_options(next_question, inferred_slots)
                        return {
                            "success": True,
                            "response": question_text,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat(),
                            "action_type": "ask_prompt_question",
                            "question_info": next_question,
                            "filled_slots": updated_slots,
                            "dialogue_stage": current_state.get("current_stage", "awareness"),
                            "funnel_mode": True,
                            "prompt_step": next_step
                        }
                    # 若無下一題則進入搜尋
                    return self._handle_product_search(session_id, current_state)
                else:
                    # 用戶回應無效，提示用法並重送當前題
                    active_question = self.question_manager.get_prompt_style_question(step, current_slots)
                    tip = "\n\n提示：請回覆選項字母 (如 A、B、C...) 或完整選項文字。"
                    question_text = self.question_manager.format_question_with_options(active_question, current_slots) + tip if active_question else "請回覆有效選項。"
                    return {
                        "success": True,
                        "response": question_text,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "action_type": "ask_prompt_question",
                        "question_info": active_question,
                        "filled_slots": current_slots,
                        "dialogue_stage": current_state.get("current_stage", "awareness"),
                        "funnel_mode": True,
                        "prompt_step": step
                    }
            
            # 步驟2: 檢查是否需要觸發funnel chat (Case-1核心邏輯)
            self.logger.info(f"DEBUG - 檢查是否觸發 funnel chat")
            should_trigger = self._should_trigger_funnel_chat(user_message, current_slots)
            self.logger.info(f"DEBUG - _should_trigger_funnel_chat 結果: {should_trigger}")
            
            if should_trigger:
                # 觸發funnel chat模式
                current_state["funnel_mode"] = True
                current_state["current_question_order"] = 0
                self.logger.info("DEBUG - 觸發funnel chat模式，設置 funnel_mode=True")
            
            # 步驟3: 決定下一步動作
            self.logger.info(f"DEBUG - 決定下一步動作，funnel_mode: {current_state.get('funnel_mode', False)}")
            
            if current_state.get("funnel_mode", False):
                # 在funnel chat模式中
                is_complete = self.question_manager.is_collection_complete(current_slots)
                self.logger.info(f"DEBUG - 槽位收集完成檢查: {is_complete}")
                
                if is_complete:
                    # 槽位收集完成，進行產品搜索
                    self.logger.info("DEBUG - 進入產品搜索")
                    return self._handle_product_search(session_id, current_state)
                else:
                    # 繼續收集槽位
                    self.logger.info("DEBUG - 繼續收集槽位")
                    return self._handle_slot_collection(session_id, current_state)
            else:
                # 一般對話模式 (簡化處理)
                self.logger.info("DEBUG - 進入一般對話模式")
                return self._handle_general_query(session_id, current_state, user_message)
            
        except Exception as e:
            self.logger.error(f"處理消息時發生錯誤: {e}", exc_info=True)
            return self._handle_error("系統內部錯誤", str(e))
    
    def _should_trigger_funnel_chat(self, user_message: str, current_slots: Dict[str, Any]) -> bool:
        """
        判斷是否應該觸發funnel chat模式
        
        Args:
            user_message: 用戶消息
            current_slots: 當前槽位
            
        Returns:
            是否觸發funnel chat
        """
        # Case-1觸發條件: "請介紹目前新出的筆電" 等類似查詢
        trigger_keywords = [
            "請介紹", "推薦", "新出", "筆電", "laptop", "筆記型電腦",
            "想要", "需要", "找", "買"
        ]
        
        # 檢查是否包含觸發關鍵詞
        for keyword in trigger_keywords:
            if keyword in user_message:
                self.logger.info(f"觸發關鍵詞: {keyword}")
                return True
        
        # 如果已經有部分槽位但不完整，也觸發funnel chat
        if current_slots and not self.question_manager.is_collection_complete(current_slots):
            return True
        
        return False
    
    def _handle_slot_collection(self, session_id: str, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理槽位收集流程 - 整合Prompt風格
        
        Args:
            session_id: 會話ID
            current_state: 當前狀態
            
        Returns:
            處理結果
        """
        try:
            current_slots = current_state.get("filled_slots", {})
            current_prompt_step = current_state.get("current_prompt_step", 1)
            
            self.logger.info(f"DEBUG - _handle_slot_collection:")
            self.logger.info(f"  - current_slots: {current_slots}")
            self.logger.info(f"  - current_prompt_step: {current_prompt_step}")
            self.logger.info(f"  - use_prompt_style: {self.use_prompt_style}")
            
            # 檢查是否應該跳過到搜尋
            should_skip = self.question_manager.should_skip_to_search(current_slots)
            self.logger.info(f"DEBUG - should_skip_to_search: {should_skip}")
            
            if should_skip:
                return self._handle_product_search(session_id, current_state)
            
            # 使用Prompt風格獲取下一個問題
            if self.use_prompt_style and current_prompt_step <= 6:
                self.logger.info(f"DEBUG - 使用Prompt風格，獲取步驟 {current_prompt_step} 的問題")
                next_question = self.question_manager.get_prompt_style_question(current_prompt_step, current_slots)
                
                if next_question:
                    self.logger.info(f"DEBUG - 獲取到問題: {next_question}")
                    # 格式化問題文字
                    question_text = self.question_manager.format_question_with_options(next_question, current_state.get("filled_slots", {}))
                    self.logger.info(f"DEBUG - 格式化問題文字: {question_text[:100]}...")
                    
                    # 更新狀態
                    current_state["current_prompt_step"] = current_prompt_step
                    current_state["current_question_slot"] = next_question["slot_name"]
                    current_state["awaiting_prompt_response"] = True
                    self.logger.info(f"DEBUG - 更新狀態設置: awaiting_prompt_response=True, current_prompt_step={current_prompt_step}")
                    self.state_manager.save_session_state(session_id, current_state)
                    self.logger.info(f"DEBUG - 狀態已保存完成")
                    
                    return {
                        "success": True,
                        "response": question_text,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "action_type": "ask_prompt_question",
                        "question_info": next_question,
                        "filled_slots": current_slots,
                        "dialogue_stage": current_state.get("current_stage", "awareness"),
                        "funnel_mode": True,
                        "prompt_step": current_prompt_step
                    }
            
            # 後備方案：使用傳統問題管理
            current_order = current_state.get("current_question_order", 0)
            next_question = self.question_manager.get_next_question(current_slots, current_order)
            
            if next_question:
                # 有下一個問題，生成詢問回應
                question_text = next_question.get("primary_question", "")
                examples = next_question.get("examples", [])
                
                # 更新問題順序
                current_state["current_question_order"] = next_question.get("order", 0)
                self.state_manager.save_session_state(session_id, current_state)
                
                # 生成回應
                response_content = f"{question_text}\n\n可選項目："
                for i, example in enumerate(examples[:5], 1):  # 只顯示前5個選項
                    response_content += f"\n{i}. {example}"
                
                return {
                    "success": True,
                    "response": response_content,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "action_type": "elicit_information",
                    "filled_slots": current_slots,
                    "dialogue_stage": current_state.get("current_stage", "awareness"),
                    "funnel_mode": True,
                    "progress": self.question_manager.get_progress_info(current_slots)
                }
            else:
                # 沒有更多問題，進入產品搜索
                return self._handle_product_search(session_id, current_state)
                
        except Exception as e:
            self.logger.error(f"處理槽位收集失敗: {e}")
            return self._handle_error("槽位收集失敗", str(e))
    
    def _handle_product_search(self, session_id: str, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理產品搜索
        
        Args:
            session_id: 會話ID
            current_state: 當前狀態
            
        Returns:
            處理結果
        """
        try:
            current_slots = current_state.get("filled_slots", {})
            
            # 使用整合chunking的知識庫搜索產品
            self.logger.info(f"使用chunking搜尋引擎進行產品搜尋，槽位: {current_slots}")
            search_results = self.knowledge_base.search_products(current_slots)
            
            if search_results:
                # 生成增強的產品推薦回應
                response_content = "根據您的需求，我為您推薦以下筆電：\n\n"
                
                for i, product in enumerate(search_results[:3], 1):  # 只顯示前3個結果
                    response_content += f"{i}. **{product.get('modelname', 'Unknown')}**\n"
                    response_content += f"   - 型號：{product.get('modeltype', 'N/A')}\n"
                    response_content += f"   - CPU：{product.get('cpu', 'N/A')}\n"
                    response_content += f"   - GPU：{product.get('gpu', 'N/A')}\n"
                    response_content += f"   - 記憶體：{product.get('memory', 'N/A')}\n"
                    response_content += f"   - 螢幕：{product.get('lcd', 'N/A')}\n"
                    
                    # 添加相似度資訊（如果有的話）
                    if 'similarity_score' in product:
                        response_content += f"   - 匹配度：{product['similarity_score']:.2%}\n"
                    
                    # 添加匹配原因（如果有的話）
                    if 'match_reasons' in product:
                        reasons = ", ".join(product['match_reasons'])
                        response_content += f"   - 推薦原因：{reasons}\n"
                    
                    response_content += "\n"
                
                # 退出funnel模式
                current_state["funnel_mode"] = False
                self.state_manager.save_session_state(session_id, current_state)
                
                return {
                    "success": True,
                    "response": response_content,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "action_type": "recommend_products",
                    "filled_slots": current_slots,
                    "recommendations": search_results[:3],
                    "dialogue_stage": current_state.get("current_stage", "awareness"),
                    "funnel_mode": False
                }
            else:
                return {
                    "success": True,
                    "response": "很抱歉，根據您的需求沒有找到合適的筆電。請調整您的條件再試一次。",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "action_type": "no_results",
                    "filled_slots": current_slots,
                    "dialogue_stage": current_state.get("current_stage", "awareness"),
                    "funnel_mode": False
                }
                
        except Exception as e:
            self.logger.error(f"處理產品搜索失敗: {e}")
            return self._handle_error("產品搜索失敗", str(e))
    
    def _handle_general_query(self, session_id: str, current_state: Dict[str, Any], user_message: str) -> Dict[str, Any]:
        """
        處理一般查詢 (非funnel chat模式)
        
        Args:
            session_id: 會話ID
            current_state: 當前狀態
            user_message: 用戶消息
            
        Returns:
            處理結果
        """
        try:
            # 簡單的一般回應
            response_content = "您好！我是筆電推薦助手。如果您需要筆電推薦，請告訴我您的需求，我會為您提供個人化的建議。\n\n您可以說：「請介紹一個適合工作的筆電」或「推薦一台遊戲筆電」。"
            
            return {
                "success": True,
                "response": response_content,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "action_type": "general_response",
                "filled_slots": current_state.get("filled_slots", {}),
                "dialogue_stage": current_state.get("current_stage", "awareness"),
                "funnel_mode": False
            }
            
        except Exception as e:
            self.logger.error(f"處理一般查詢失敗: {e}")
            return self._handle_error("一般查詢失敗", str(e))

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
    
    def _was_response_successfully_processed(self, step: int, user_message: str, current_slots: Dict[str, Any]) -> bool:
        """
        判斷用戶回應是否被成功處理（不依賴槽位是否改變）
        
        Args:
            step: 當前步驟
            user_message: 用戶消息
            current_slots: 當前槽位
            
        Returns:
            是否成功處理
        """
        try:
            # 檢查是否為有效的選項回應
            step_key = f"step_{step}"
            normalized_upper = user_message.strip().upper()
            
            # 1. 檢查字母選項是否有效
            if self.question_manager.slot_mapper.validate_prompt_response(step_key, normalized_upper):
                self.logger.info(f"用戶回應 '{user_message}' 在步驟 {step} 中有效")
                return True
            
            # 2. 檢查完整選項文字是否有效
            options = []
            if step == 1:
                options = self.question_manager.slot_mapper.get_prompt_options_for_slot("usage_purpose")
            elif step == 2:
                options = self.question_manager.slot_mapper.get_prompt_options_for_slot("budget_range")
            elif step == 3:
                options = self.question_manager.slot_mapper.get_prompt_options_for_slot("portability")
            elif step == 4:
                options = self.question_manager.slot_mapper.get_prompt_options_for_slot("screen_size")
            elif step == 5:
                options = self.question_manager.slot_mapper.get_prompt_options_for_slot("brand_preference")
            elif step == 6:
                options = self.question_manager.slot_mapper.get_prompt_options_for_slot("special_requirement")
            
            # 檢查是否匹配完整選項文字
            user_message_lower = user_message.strip().lower()
            for opt in options:
                if (opt.get("value", "").lower() == user_message_lower or 
                    opt.get("text", "").lower() == user_message_lower):
                    self.logger.info(f"用戶回應 '{user_message}' 匹配完整選項文字")
                    return True
            
            self.logger.warning(f"用戶回應 '{user_message}' 在步驟 {step} 中無效")
            return False
            
        except Exception as e:
            self.logger.error(f"判斷回應處理狀態失敗: {e}")
            return False

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
