#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD 狀態機實現
簡化版本，不依賴LangGraph
"""

import logging
from typing import Dict, Any, Optional
from .models import NotebookDialogueState, ActionType
from .dialogue_manager import DialogueManager as MGFDDialogueManager

class MGFDStateMachine:
    """MGFD狀態機"""
    
    def __init__(self, dialogue_manager: MGFDDialogueManager):
        """
        初始化狀態機
        
        Args:
            dialogue_manager: 對話管理器
        """
        self.dialogue_manager = dialogue_manager
        self.logger = logging.getLogger(__name__)
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """
        處理用戶輸入
        
        Args:
            session_id: 會話ID
            user_input: 用戶輸入
            
        Returns:
            處理結果
        """
        try:
            self.logger.info(f"處理用戶輸入 - session_id: {session_id}, input: '{user_input[:100]}...'")
            
            # 獲取會話狀態
            state = self.dialogue_manager.get_session(session_id)
            if not state:
                self.logger.warning(f"會話不存在: {session_id}")
                return {
                    "error": "會話不存在",
                    "session_id": session_id
                }
        except Exception as e:
            self.logger.error(f"獲取會話狀態失敗: {e}")
            return {
                "error": f"系統錯誤: {str(e)}",
                "session_id": session_id
            }
        
        try:
            # 添加用戶消息到歷史記錄
            user_message = {
                "role": "user",
                "content": user_input,
                "timestamp": self.dialogue_manager.active_sessions[session_id]["last_updated"]
            }
            state["chat_history"].append(user_message)
            
            # Think步驟：決定下一步行動
            self.logger.debug("開始行動路由分析...")
            action = self.dialogue_manager.route_action(state, user_input)
            self.logger.info(f"路由結果 - action_type: {action.action_type}, target_slot: {action.target_slot}")
            
            # Act步驟：執行行動
            if action.action_type == ActionType.ELICIT_INFORMATION:
                self.logger.debug("執行信息收集行動")
                return self._handle_elicitation(state, action)
            elif action.action_type == ActionType.RECOMMEND_PRODUCTS:
                self.logger.debug("執行產品推薦行動")
                return self._handle_recommendation(state, action)
            elif action.action_type == ActionType.HANDLE_INTERRUPTION:
                self.logger.debug("執行中斷處理行動")
                return self._handle_interruption(state, action)
            else:
                self.logger.warning(f"未知行動類型: {action.action_type}")
                return self._handle_unknown_action(state, action)
        except Exception as e:
            self.logger.error(f"處理用戶輸入時發生錯誤: {e}")
            return {
                "error": f"處理錯誤: {str(e)}",
                "session_id": session_id
            }
    
    def _handle_elicitation(self, state: NotebookDialogueState, action) -> Dict[str, Any]:
        """處理信息收集"""
        try:
            # 首先檢查action中是否已經有提取的槽位（來自funnel option selection或special case）
            extracted_slots = {}
            if hasattr(action, 'extracted_slots') and action.extracted_slots:
                extracted_slots = action.extracted_slots
                self.logger.info(f"使用action中的extracted_slots: {extracted_slots}")
            else:
                # 如果action中沒有，則從用戶輸入中提取槽位信息
                self.logger.debug("從用戶輸入中提取槽位")
                extracted_slots = self.dialogue_manager.extract_slots_from_input(
                    state["chat_history"][-1]["content"], 
                    state
                )
            
            # 更新已填寫的槽位
            if extracted_slots:
                old_slots = state["filled_slots"].copy()
                state["filled_slots"].update(extracted_slots)
                self.logger.info(f"槽位更新: {old_slots} -> {state['filled_slots']}")
            else:
                self.logger.debug("未提取到新槽位")
        except Exception as e:
            self.logger.error(f"處理槽位提取時發生錯誤: {e}")
            extracted_slots = {}
        
        # 新增：檢查是否需要確認提取的信息
        confirmation_message = self._generate_confirmation_message(extracted_slots, state)
        
        # 生成回應
        if confirmation_message:
            response_content = confirmation_message
        else:
            response_content = action.message
        
        response_message = {
            "role": "assistant",
            "content": response_content,
            "action_type": "elicitation",
            "target_slot": action.target_slot,
            "extracted_slots": extracted_slots
        }
        
        state["chat_history"].append(response_message)
        
        # 更新會話狀態
        self.dialogue_manager.update_session(state["session_id"], {
            "chat_history": state["chat_history"],
            "filled_slots": state["filled_slots"]
        })
        
        return {
            "session_id": state["session_id"],
            "response": response_content,
            "action_type": "elicitation",
            "target_slot": action.target_slot,
            "extracted_slots": extracted_slots,
            "filled_slots": state["filled_slots"],
            "current_stage": state["current_stage"]
        }

    def _generate_confirmation_message(self, extracted_slots: Dict[str, Any], state: NotebookDialogueState) -> str:
        """生成確認消息"""
        if not extracted_slots:
            return ""
        
        confirmations = []
        
        # 確認使用目的
        if "usage_purpose" in extracted_slots:
            purpose = extracted_slots["usage_purpose"]
            purpose_map = {
                "gaming": "遊戲",
                "business": "商務工作",
                "student": "學習",
                "creative": "創作設計", 
                "general": "一般使用"
            }
            purpose_name = purpose_map.get(purpose, purpose)
            confirmations.append(f"使用目的：{purpose_name}")
        
        # 確認性能特徵
        if "performance_features" in extracted_slots:
            features = extracted_slots["performance_features"]
            if isinstance(features, list) and features:
                feature_names = []
                for feature in features:
                    if feature == "fast":
                        feature_names.append("快速開關機")
                    elif feature == "portable":
                        feature_names.append("輕便攜帶")
                    elif feature == "performance":
                        feature_names.append("高效能")
                
                if feature_names:
                    confirmations.append(f"性能需求：{', '.join(feature_names)}")
        
        # 確認預算範圍
        if "budget_range" in extracted_slots:
            budget = extracted_slots["budget_range"]
            budget_map = {
                "budget": "平價",
                "mid_range": "中價位",
                "premium": "高價位",
                "luxury": "頂級"
            }
            budget_name = budget_map.get(budget, budget)
            confirmations.append(f"預算範圍：{budget_name}")
        
        if confirmations:
            return f"好的，我了解了：{', '.join(confirmations)}。現在讓我為您推薦最適合的筆電。"
        
        return ""
    
    def _handle_recommendation(self, state: NotebookDialogueState, action) -> Dict[str, Any]:
        """處理產品推薦"""
        try:
            # 首先檢查action中是否有提取的槽位需要更新（來自funnel option selection）
            if hasattr(action, 'extracted_slots') and action.extracted_slots:
                old_slots = state["filled_slots"].copy()
                state["filled_slots"].update(action.extracted_slots)
                self.logger.info(f"推薦前更新槽位: {old_slots} -> {state['filled_slots']}")
            
            self.logger.debug(f"開始生成推薦，當前槽位: {state['filled_slots']}")
            # 生成推薦
            recommendations = self.dialogue_manager.generate_recommendations(state)
            self.logger.info(f"生成了{len(recommendations)}個推薦產品")
            recommendation_message = self.dialogue_manager.format_recommendation_message(recommendations)
        except Exception as e:
            self.logger.error(f"生成推薦時發生錯誤: {e}")
            recommendations = []
            recommendation_message = "抱歉，生成推薦時發生錯誤。請稍後再試。"
        
        # 更新推薦記錄
        state["recommendations"] = [r["id"] for r in recommendations]
        
        # 生成回應
        response_message = {
            "role": "assistant",
            "content": recommendation_message,
            "action_type": "recommendation",
            "recommendations": recommendations
        }
        
        state["chat_history"].append(response_message)
        
        # 更新會話狀態
        self.dialogue_manager.update_session(state["session_id"], {
            "chat_history": state["chat_history"],
            "recommendations": state["recommendations"],
            "current_stage": "engagement"
        })
        
        return {
            "session_id": state["session_id"],
            "response": recommendation_message,
            "action_type": "recommendation",
            "recommendations": recommendations,
            "filled_slots": state["filled_slots"],
            "current_stage": "engagement"
        }
    
    def _handle_interruption(self, state: NotebookDialogueState, action) -> Dict[str, Any]:
        """處理中斷"""
        # 重置會話狀態
        state["filled_slots"] = {}
        state["recommendations"] = []
        state["current_stage"] = "awareness"
        
        # 生成回應
        response_message = {
            "role": "assistant",
            "content": action.message,
            "action_type": "interruption"
        }
        
        state["chat_history"].append(response_message)
        
        # 更新會話狀態
        self.dialogue_manager.update_session(state["session_id"], {
            "chat_history": state["chat_history"],
            "filled_slots": state["filled_slots"],
            "recommendations": state["recommendations"],
            "current_stage": state["current_stage"]
        })
        
        return {
            "session_id": state["session_id"],
            "response": action.message,
            "action_type": "interruption",
            "filled_slots": state["filled_slots"],
            "current_stage": state["current_stage"]
        }
    
    def _handle_unknown_action(self, state: NotebookDialogueState, action) -> Dict[str, Any]:
        """處理未知行動"""
        error_message = "抱歉，我無法理解您的需求。請重新描述您想要的筆電。"
        
        response_message = {
            "role": "assistant",
            "content": error_message,
            "action_type": "error"
        }
        
        state["chat_history"].append(response_message)
        
        return {
            "session_id": state["session_id"],
            "response": error_message,
            "action_type": "error",
            "filled_slots": state["filled_slots"],
            "current_stage": state["current_stage"]
        }

def create_notebook_sales_graph():
    """
    創建筆記型電腦銷售狀態圖
    簡化版本，返回狀態機實例
    """
    dialogue_manager = MGFDDialogueManager()
    return MGFDStateMachine(dialogue_manager)



