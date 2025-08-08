#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD 狀態機實現
簡化版本，不依賴LangGraph
"""

import logging
from typing import Dict, Any, Optional
from .models import NotebookDialogueState, ActionType
from .dialogue_manager import MGFDDialogueManager

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
        # 獲取會話狀態
        state = self.dialogue_manager.get_session(session_id)
        if not state:
            return {
                "error": "會話不存在",
                "session_id": session_id
            }
        
        # 添加用戶消息到歷史記錄
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": self.dialogue_manager.active_sessions[session_id]["last_updated"]
        }
        state["chat_history"].append(user_message)
        
        # Think步驟：決定下一步行動
        action = self.dialogue_manager.route_action(state, user_input)
        
        # Act步驟：執行行動
        if action.action_type == ActionType.ELICIT_INFORMATION:
            return self._handle_elicitation(state, action)
        elif action.action_type == ActionType.RECOMMEND_PRODUCTS:
            return self._handle_recommendation(state, action)
        elif action.action_type == ActionType.HANDLE_INTERRUPTION:
            return self._handle_interruption(state, action)
        else:
            return self._handle_unknown_action(state, action)
    
    def _handle_elicitation(self, state: NotebookDialogueState, action) -> Dict[str, Any]:
        """處理信息收集"""
        # 從用戶輸入中提取槽位信息
        extracted_slots = self.dialogue_manager.extract_slots_from_input(
            state["chat_history"][-1]["content"], 
            state
        )
        
        # 更新已填寫的槽位
        if extracted_slots:
            state["filled_slots"].update(extracted_slots)
        
        # 生成回應
        response_message = {
            "role": "assistant",
            "content": action.message,
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
            "response": action.message,
            "action_type": "elicitation",
            "target_slot": action.target_slot,
            "extracted_slots": extracted_slots,
            "filled_slots": state["filled_slots"],
            "current_stage": state["current_stage"]
        }
    
    def _handle_recommendation(self, state: NotebookDialogueState, action) -> Dict[str, Any]:
        """處理產品推薦"""
        # 生成推薦
        recommendations = self.dialogue_manager.generate_recommendations(state)
        recommendation_message = self.dialogue_manager.format_recommendation_message(recommendations)
        
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
