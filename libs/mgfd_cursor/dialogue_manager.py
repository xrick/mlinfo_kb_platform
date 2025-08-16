#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD 對話管理器
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from .models import (
    NotebookDialogueState, DialogueStage, ActionType, 
    DialogueAction, NOTEBOOK_SLOT_SCHEMA
)
from .knowledge_base import NotebookKnowledgeBase

class MGFDDialogueManager:
    """MGFD對話管理器"""
    
    def __init__(self, notebook_kb_path: Optional[str] = None):
        """
        初始化對話管理器
        
        Args:
            notebook_kb_path: 筆記型電腦知識庫路徑
        """
        self.notebook_kb = NotebookKnowledgeBase(notebook_kb_path)
        self.slot_schema = NOTEBOOK_SLOT_SCHEMA
        self.logger = logging.getLogger(__name__)
        
        # 活躍的對話會話
        self.active_sessions: Dict[str, NotebookDialogueState] = {}
        
    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        創建新的對話會話
        
        Args:
            user_id: 用戶ID
            
        Returns:
            會話ID
        """
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        initial_state = NotebookDialogueState(
            chat_history=[],
            filled_slots={},
            recommendations=[],
            user_preferences={},
            current_stage=DialogueStage.AWARENESS.value,
            session_id=session_id,
            created_at=now,
            last_updated=now
        )
        
        self.active_sessions[session_id] = initial_state
        self.logger.info(f"創建新會話: {session_id}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[NotebookDialogueState]:
        """獲取會話狀態"""
        return self.active_sessions.get(session_id)
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新會話狀態
        
        Args:
            session_id: 會話ID
            updates: 更新內容
            
        Returns:
            是否更新成功
        """
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        session.update(updates)
        session["last_updated"] = datetime.now()
        
        return True
    
    def route_action(self, state: NotebookDialogueState, user_input: str, enhanced_slot_extractor=None) -> DialogueAction:
        """
        Think步驟：分析狀態並決定下一步行動
        
        Args:
            state: 當前對話狀態
            user_input: 用戶輸入
            enhanced_slot_extractor: 增強型槽位提取器（包含特殊案例知識庫）
            
        Returns:
            對話行動
        """
        # 0. 首先檢查特殊案例知識庫（如果可用）
        if enhanced_slot_extractor:
            try:
                self.logger.debug(f"使用enhanced_slot_extractor處理輸入: '{user_input[:50]}...'")
                extraction_result = enhanced_slot_extractor.extract_slots_with_classification(
                    user_input, state.get("filled_slots", {}), state.get("session_id")
                )
                
                extraction_method = extraction_result.get("extraction_method", "unknown")
                self.logger.info(f"提取方法: {extraction_method}")
                
                # 如果是funnel option selection，直接處理槽位提取並繼續對話流程
                if extraction_method == "funnel_option_selection":
                    extracted_slots = extraction_result.get("extracted_slots", {})
                    self.logger.info(f"檢測到funnel選項選擇，提取槽位: {extracted_slots}")
                    
                    if extracted_slots:
                        # 更新狀態中的槽位
                        old_slots = state["filled_slots"].copy()
                        state["filled_slots"].update(extracted_slots)
                        self.logger.info(f"槽位更新: {old_slots} -> {state['filled_slots']}")
                    
                    # 檢查是否還有缺失的必要槽位
                    missing_required_slots = self._get_missing_required_slots(state)
                    self.logger.debug(f"缺失的必要槽位: {missing_required_slots}")
                    
                    if missing_required_slots:
                        # 還有必要槽位未填寫，繼續收集信息
                        next_slot = missing_required_slots[0]
                        self.logger.info(f"需要繼續收集槽位: {next_slot}")
                        return DialogueAction(
                            action_type=ActionType.ELICIT_INFORMATION,
                            target_slot=next_slot,
                            message=self._generate_elicitation_question(next_slot, state),
                            extracted_slots=extracted_slots
                        )
                    else:
                        # 所有必要槽位已填寫，可以進行推薦
                        self.logger.info("所有必要槽位已填寫，進行產品推薦")
                        return DialogueAction(
                            action_type=ActionType.RECOMMEND_PRODUCTS,
                            message="根據您的選擇，我為您推薦以下筆電：",
                            extracted_slots=extracted_slots
                        )
                # 如果找到特殊案例匹配
                elif extraction_method == "special_case_knowledge":
                    special_case = extraction_result.get("special_case", {})
                    self.logger.info(f"檢測到特殊案例: {special_case.get('case_id', 'unknown')}")
                    return DialogueAction(
                        action_type="special_case_response",
                        special_case=special_case,
                        message=special_case.get("message", "")
                    )
            except Exception as e:
                self.logger.error(f"enhanced_slot_extractor處理失敗: {e}")
                # 繼續使用原本的流程
        
        # 1. 檢查是否為中斷意圖
        if self._is_interruption(user_input):
            return DialogueAction(
                action_type=ActionType.HANDLE_INTERRUPTION,
                message="我理解您想要改變話題。讓我重新開始幫助您找到合適的筆電。"
            )
        
        # 檢查是否為熱門產品請求
        if self._is_popular_request(user_input):
            self.logger.info("檢測到熱門產品請求")
            return DialogueAction(
                action_type=ActionType.RECOMMEND_POPULAR_PRODUCTS,
                message="我了解您想要了解熱門筆電！讓我為您推薦目前最受歡迎的選擇。"
            )
        
        # 檢查缺失的必要槽位
        missing_required_slots = self._get_missing_required_slots(state)
        current_slots = state.get("filled_slots", {})
        
        # 增強的決策日誌
        self.logger.info(f"對話決策分析:")
        self.logger.info(f"  - 當前已填槽位: {current_slots}")
        self.logger.info(f"  - 缺失的必要槽位: {missing_required_slots}")
        self.logger.info(f"  - 用戶輸入: '{user_input[:50]}{'...' if len(user_input) > 50 else ''}'")
        
        if missing_required_slots:
            # 還有必要槽位未填寫，繼續收集信息
            next_slot = missing_required_slots[0]
            self.logger.info(f"決策結果: 需要收集槽位 '{next_slot}' (剩餘 {len(missing_required_slots)} 個必要槽位)")
            return DialogueAction(
                action_type=ActionType.ELICIT_INFORMATION,
                target_slot=next_slot,
                message=self._generate_elicitation_question(next_slot, state)
            )
        else:
            # 所有必要槽位已填寫，可以進行推薦
            self.logger.info("決策結果: 所有必要槽位已填寫，進行產品推薦")
            return DialogueAction(
                action_type=ActionType.RECOMMEND_PRODUCTS,
                message="根據您的需求，我為您推薦以下筆電："
            )
    
    def _is_interruption(self, user_input: str) -> bool:
        """檢查是否為中斷意圖"""
        interruption_keywords = [
            "重新開始", "換個話題", "不要了", "算了", "停止",
            "重新", "reset", "stop", "cancel", "重新來"
        ]
        
        user_input_lower = user_input.lower()
        return any(keyword in user_input_lower for keyword in interruption_keywords)
    
    def _is_popular_request(self, user_input: str) -> bool:
        """檢查是否為熱門產品請求"""
        popular_keywords = [
            "多人選擇", "熱門", "受歡迎", "銷量好", "比較多人", 
            "最受歡迎", "大家都在買", "熱銷", "人氣", "推薦度高"
        ]
        
        user_input_lower = user_input.lower()
        return any(keyword in user_input_lower for keyword in popular_keywords)
    
    def _get_missing_required_slots(self, state: NotebookDialogueState) -> List[str]:
        """獲取缺失的必要槽位"""
        missing_slots = []
        filled_slots = state.get("filled_slots", {})
        
        self.logger.debug(f"檢查必要槽位 - 當前已填槽位: {filled_slots}")
        
        for slot_name, slot_config in self.slot_schema.items():
            if slot_config.required:
                slot_value = filled_slots.get(slot_name)
                if slot_value is None or slot_value == "":
                    missing_slots.append(slot_name)
                    self.logger.debug(f"缺失必要槽位: {slot_name}")
                else:
                    self.logger.debug(f"已填必要槽位: {slot_name} = '{slot_value}'")
            else:
                self.logger.debug(f"可選槽位: {slot_name} (當前值: {filled_slots.get(slot_name, 'None')})")
        
        self.logger.info(f"槽位檢查結果 - 缺失的必要槽位: {missing_slots}")
        return missing_slots
    
    def _generate_elicitation_question(self, slot_name: str, state: NotebookDialogueState) -> str:
        """生成詢問問題"""
        slot_config = self.slot_schema[slot_name]
        
        # 基礎問題
        question = slot_config.example_question
        
        # 根據已填寫的槽位調整問題
        if "usage_purpose" in state["filled_slots"]:
            purpose = state["filled_slots"]["usage_purpose"]
            if slot_name == "budget_range":
                if purpose == "gaming":
                    question = "考慮到您需要遊戲性能，您的預算大概在哪個範圍？"
                elif purpose == "business":
                    question = "考慮到商務需求，您的預算大概在哪個範圍？"
        
        return question
    
    def extract_slots_from_input(self, user_input: str, state: NotebookDialogueState) -> Dict[str, Any]:
        """
        從用戶輸入中提取槽位信息
        
        Args:
            user_input: 用戶輸入
            state: 當前對話狀態
            
        Returns:
            提取的槽位信息
        """
        extracted_slots = {}
        user_input_lower = user_input.lower()
        
        # 提取使用目的
        if "usage_purpose" not in state["filled_slots"]:
            if any(word in user_input_lower for word in ["遊戲", "gaming", "打遊戲"]):
                extracted_slots["usage_purpose"] = "gaming"
            elif any(word in user_input_lower for word in ["工作", "business", "辦公", "商務"]):
                extracted_slots["usage_purpose"] = "business"
            elif any(word in user_input_lower for word in ["學習", "student", "上課", "作業"]):
                extracted_slots["usage_purpose"] = "student"
            elif any(word in user_input_lower for word in ["創意", "creative", "設計", "剪輯"]):
                extracted_slots["usage_purpose"] = "creative"
            elif any(word in user_input_lower for word in ["一般", "general", "日常", "上網"]):
                extracted_slots["usage_purpose"] = "general"
        
        # 提取預算範圍
        if "budget_range" not in state["filled_slots"]:
            if any(word in user_input_lower for word in ["便宜", "budget", "經濟", "平價"]):
                extracted_slots["budget_range"] = "budget"
            elif any(word in user_input_lower for word in ["中等", "mid_range", "中端"]):
                extracted_slots["budget_range"] = "mid_range"
            elif any(word in user_input_lower for word in ["高級", "premium", "高端"]):
                extracted_slots["budget_range"] = "premium"
            elif any(word in user_input_lower for word in ["豪華", "luxury", "頂級"]):
                extracted_slots["budget_range"] = "luxury"
        
        # 提取品牌偏好
        if "brand_preference" not in state["filled_slots"]:
            if "asus" in user_input_lower or "華碩" in user_input_lower:
                extracted_slots["brand_preference"] = "asus"
            elif "acer" in user_input_lower or "宏碁" in user_input_lower:
                extracted_slots["brand_preference"] = "acer"
            elif "lenovo" in user_input_lower or "聯想" in user_input_lower:
                extracted_slots["brand_preference"] = "lenovo"
            elif "hp" in user_input_lower or "惠普" in user_input_lower:
                extracted_slots["brand_preference"] = "hp"
            elif "dell" in user_input_lower or "戴爾" in user_input_lower:
                extracted_slots["brand_preference"] = "dell"
            elif "apple" in user_input_lower or "蘋果" in user_input_lower or "mac" in user_input_lower:
                extracted_slots["brand_preference"] = "apple"
        
        return extracted_slots
    
    def generate_recommendations(self, state: NotebookDialogueState) -> List[Dict[str, Any]]:
        """
        生成產品推薦
        
        Args:
            state: 對話狀態
            
        Returns:
            推薦產品列表
        """
        preferences = state["filled_slots"]
        filtered_products = self.notebook_kb.filter_products(preferences)
        
        # 如果過濾後沒有產品，放寬條件
        if not filtered_products:
            # 移除品牌偏好重新過濾
            if "brand_preference" in preferences:
                temp_preferences = preferences.copy()
                del temp_preferences["brand_preference"]
                filtered_products = self.notebook_kb.filter_products(temp_preferences)
        
        # 如果還是沒有，返回所有產品
        if not filtered_products:
            filtered_products = self.notebook_kb.products
        
        # 限制推薦數量
        return filtered_products[:3]
    
    def format_recommendation_message(self, products: List[Dict[str, Any]]) -> str:
        """格式化推薦消息"""
        if not products:
            return "抱歉，目前沒有找到完全符合您需求的產品。請嘗試調整您的偏好。"
        
        message = "根據您的需求，我為您推薦以下筆電：\n\n"
        
        for i, product in enumerate(products, 1):
            message += f"{i}. **{product['name']}**\n"
            message += f"   - 品牌：{product['brand'].upper()}\n"

          
            message += f"   - 處理器：{product['cpu']}\n"
            message += f"   - 顯示卡：{product['gpu']}\n"
            message += f"   - 記憶體：{product['ram']}\n"
            message += f"   - 重量：{product['weight']}\n"
            message += f"   - 描述：{product['description']}\n\n"
        
        message += "您對哪一款比較感興趣？我可以為您提供更詳細的信息。"
        
        return message
    
    def cleanup_expired_sessions(self, hours: int = 24):
        """清理過期的會話"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            time_diff = now - session["created_at"]
            if time_diff.total_seconds() > hours * 3600:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            self.logger.info(f"清理過期會話: {session_id}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """獲取會話統計信息"""
        return {
            "active_sessions": len(self.active_sessions),
            "total_products": len(self.notebook_kb.products),
            "slot_schema_count": len(self.slot_schema)
        }

# 向後相容性：提供 DialogueManager 別名
DialogueManager = MGFDDialogueManager
