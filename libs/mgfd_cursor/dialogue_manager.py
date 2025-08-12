#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD 對話管理器 (Router)
實現Think階段的決策邏輯和對話流程管理
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

class DialogueManager:
    """對話管理器 - 路由節點"""
    
    def __init__(self, llm_manager, slot_schema: Dict[str, Any]):
        """
        初始化對話管理器
        
        Args:
            llm_manager: LLM管理器
            slot_schema: 槽位架構定義
        """
        self.llm_manager = llm_manager
        self.slot_schema = slot_schema
        self.logger = logging.getLogger(__name__)
        
        # 必要槽位定義
        self.required_slots = ["usage_purpose", "budget_range"]
        
        # 中斷意圖關鍵詞
        self.interruption_keywords = [
            "重新開始", "換個話題", "不要了", "算了", "停止",
            "重新", "reset", "stop", "cancel", "重新來"
        ]
    
    def route_next_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Think階段：分析狀態並決定下一步行動
        
        Args:
            state: 當前對話狀態
            
        Returns:
            結構化指令
        """
        try:
            # 檢查是否為中斷意圖
            if self._is_interruption(state):
                return {
                    "action": "HANDLE_INTERRUPTION",
                    "target_slot": None,
                    "reasoning": "檢測到中斷意圖",
                    "confidence": 0.9
                }
            
            # 使用LLM進行Think階段決策
            instruction = "分析當前對話狀態，決定下一步行動"
            context = {
                "chat_history": state.get("chat_history", []),
                "filled_slots": state.get("filled_slots", {}),
                "current_stage": state.get("current_stage", "awareness")
            }
            
            # 調用LLM進行決策
            decision = self.llm_manager.think_phase(instruction, context)
            
            # 驗證決策的合理性
            validated_decision = self._validate_decision(decision, state)
            
            self.logger.info(f"路由決策: {validated_decision}")
            return {
                "success": True,
                "command": validated_decision
            }
            
        except Exception as e:
            self.logger.error(f"路由決策失敗: {e}")
            fallback_decision = self._get_fallback_decision(state)
            return {
                "success": True,
                "command": fallback_decision
            }
    
    def check_required_slots(self, state: Dict[str, Any]) -> List[str]:
        """
        檢查缺失的必要槽位
        
        Args:
            state: 對話狀態
            
        Returns:
            缺失的必要槽位列表
        """
        filled_slots = state.get("filled_slots", {})
        missing_slots = []
        
        for slot_name in self.required_slots:
            if slot_name not in filled_slots or not filled_slots[slot_name]:
                missing_slots.append(slot_name)
        
        return missing_slots
    
    def _is_interruption(self, state: Dict[str, Any]) -> bool:
        """
        檢查是否為中斷意圖
        
        Args:
            state: 對話狀態
            
        Returns:
            是否為中斷意圖
        """
        chat_history = state.get("chat_history", [])
        if not chat_history:
            return False
        
        # 檢查最後一條用戶消息
        last_user_message = None
        for msg in reversed(chat_history):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break
        
        if not last_user_message:
            return False
        
        # 檢查是否包含中斷關鍵詞
        user_input_lower = last_user_message.lower()
        return any(keyword in user_input_lower for keyword in self.interruption_keywords)
    
    def _validate_decision(self, decision: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證決策的合理性
        
        Args:
            decision: LLM生成的決策
            state: 對話狀態
            
        Returns:
            驗證後的決策
        """
        action = decision.get("action", "")
        target_slot = decision.get("target_slot", "")
        
        # 檢查缺失的必要槽位
        missing_slots = self.check_required_slots(state)
        
        # 如果還有必要槽位缺失，優先收集信息
        if missing_slots and action != "RECOMMEND_PRODUCTS":
            return {
                "action": "ELICIT_SLOT",
                "target_slot": missing_slots[0],
                "reasoning": f"必要槽位 {missing_slots[0]} 缺失",
                "confidence": 0.95
            }
        
        # 如果所有必要槽位都已填寫，可以進行推薦
        if not missing_slots and action == "ELICIT_SLOT":
            return {
                "action": "RECOMMEND_PRODUCTS",
                "target_slot": None,
                "reasoning": "所有必要槽位已填寫，可以進行推薦",
                "confidence": 0.9
            }
        
        # 驗證目標槽位的有效性
        if action == "ELICIT_SLOT" and target_slot:
            if target_slot not in self.slot_schema:
                # 如果目標槽位無效，選擇第一個缺失的必要槽位
                if missing_slots:
                    return {
                        "action": "ELICIT_SLOT",
                        "target_slot": missing_slots[0],
                        "reasoning": f"目標槽位 {target_slot} 無效，改為詢問 {missing_slots[0]}",
                        "confidence": 0.8
                    }
                else:
                    return {
                        "action": "RECOMMEND_PRODUCTS",
                        "target_slot": None,
                        "reasoning": "目標槽位無效且無缺失槽位，進行推薦",
                        "confidence": 0.8
                    }
        
        return decision
    
    def _get_fallback_decision(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        獲取回退決策
        
        Args:
            state: 對話狀態
            
        Returns:
            回退決策
        """
        missing_slots = self.check_required_slots(state)
        
        if missing_slots:
            return {
                "action": "ELICIT_SLOT",
                "target_slot": missing_slots[0],
                "reasoning": "回退策略：詢問缺失的必要槽位",
                "confidence": 0.5
            }
        else:
            return {
                "action": "RECOMMEND_PRODUCTS",
                "target_slot": None,
                "reasoning": "回退策略：進行產品推薦",
                "confidence": 0.5
            }
    
    def get_dialogue_stage(self, state: Dict[str, Any]) -> str:
        """
        獲取當前對話階段
        
        Args:
            state: 對話狀態
            
        Returns:
            對話階段
        """
        filled_slots = state.get("filled_slots", {})
        chat_history = state.get("chat_history", [])
        
        # 根據已填寫的槽位數量判斷階段
        filled_count = len([slot for slot in self.required_slots if slot in filled_slots])
        total_required = len(self.required_slots)
        
        if filled_count == 0:
            return "awareness"
        elif filled_count < total_required:
            return "interest"
        elif filled_count == total_required:
            return "evaluation"
        else:
            return "engagement"
    
    def should_escalate_to_human(self, state: Dict[str, Any]) -> bool:
        """
        判斷是否需要升級給人工客服
        
        Args:
            state: 對話狀態
            
        Returns:
            是否需要升級
        """
        chat_history = state.get("chat_history", [])
        
        # 檢查對話長度
        if len(chat_history) > 20:
            return True
        
        # 檢查是否有多次錯誤
        error_count = 0
        for msg in chat_history:
            if msg.get("role") == "assistant" and "抱歉" in msg.get("content", ""):
                error_count += 1
        
        if error_count >= 3:
            return True
        
        return False



