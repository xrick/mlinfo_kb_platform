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
from .config_loader import MGFDConfigLoader

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
        # 載入人類可配置資料
        self.config_loader = MGFDConfigLoader()
        self.slot_synonyms = self._load_slot_synonyms()
        
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
    
    def route_action(self, state: NotebookDialogueState, user_input: str) -> DialogueAction:
        """
        Think步驟：分析狀態並決定下一步行動
        
        Args:
            state: 當前對話狀態
            user_input: 用戶輸入
            
        Returns:
            對話行動
        """
        # 檢查是否為中斷意圖
        if self._is_interruption(user_input):
            return DialogueAction(
                action_type=ActionType.HANDLE_INTERRUPTION,
                message="我理解您想要改變話題。讓我重新開始幫助您找到合適的筆電。"
            )
        
        # 檢查缺失的必要槽位
        missing_required_slots = self._get_missing_required_slots(state)
        
        if missing_required_slots:
            # 還有必要槽位未填寫，繼續收集信息
            next_slot = missing_required_slots[0]
            return DialogueAction(
                action_type=ActionType.ELICIT_INFORMATION,
                target_slot=next_slot,
                message=self._generate_elicitation_question(next_slot, state)
            )
        else:
            # 所有必要槽位已填寫，可以進行推薦
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
    
    def _get_missing_required_slots(self, state: NotebookDialogueState) -> List[str]:
        """獲取缺失的必要槽位"""
        missing_slots = []
        
        for slot_name, slot_config in self.slot_schema.items():
            if slot_config.required and slot_name not in state["filled_slots"]:
                missing_slots.append(slot_name)
        
        return missing_slots
    
    def _generate_elicitation_question(self, slot_name: str, state: NotebookDialogueState) -> str:
        """生成詢問問題"""
        slot_config = self.slot_schema[slot_name]
        templates_cfg = self.config_loader.get_response_templates().get("response_templates", {})
        slot_tpls = templates_cfg.get("slot_elicitation", {}).get(slot_name, {})

        # 1) 取模板或回退 example_question
        base_templates = slot_tpls.get("templates") or [slot_config.example_question]

        # 2) 上下文前綴
        prefixes: List[str] = []
        ctx = slot_tpls.get("context_adaptations", {})
        if "brand_preference" in state["filled_slots"] and ctx.get("has_brand_preference"):
            prefixes.append(ctx["has_brand_preference"].format(brand=state["filled_slots"]["brand_preference"]))
        if "budget_range" in state["filled_slots"] and ctx.get("has_budget"):
            prefixes.append(ctx["has_budget"])
        if "usage_purpose" in state["filled_slots"] and ctx.get("has_usage_purpose"):
            purpose_map = {
                "gaming": "遊戲",
                "business": "商務",
                "student": "學習",
                "creative": "創作",
                "general": "一般"
            }
            purpose_val = purpose_map.get(state["filled_slots"]["usage_purpose"], state["filled_slots"]["usage_purpose"]) 
            prefixes.append(ctx["has_usage_purpose"].format(usage_purpose=purpose_val))

        # 3) 合成問題
        question = ("".join(prefixes) + (base_templates[0] if base_templates else slot_config.example_question)).strip()
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

        # 使用可配置同義詞映射來提取槽位
        def match_by_synonyms(slot_name: str) -> Optional[str]:
            mapping = self.slot_synonyms.get(slot_name, {})
            for normalized_value, synonyms in mapping.items():
                for term in synonyms:
                    if term.lower() in user_input_lower:
                        return normalized_value
            return None

        if "usage_purpose" not in state["filled_slots"]:
            value = match_by_synonyms("usage_purpose")
            if value:
                extracted_slots["usage_purpose"] = value

        if "budget_range" not in state["filled_slots"]:
            value = match_by_synonyms("budget_range")
            if value:
                extracted_slots["budget_range"] = value

        if "brand_preference" not in state["filled_slots"]:
            value = match_by_synonyms("brand_preference")
            if value:
                extracted_slots["brand_preference"] = value

        return extracted_slots

    def _load_slot_synonyms(self) -> Dict[str, Dict[str, List[str]]]:
        """從配置載入槽位同義詞，提供合理的預設以避免硬依賴檔案"""
        data = self.config_loader.get_slot_synonyms() or {}
        # 預設基本詞庫，避免冷啟動失敗
        default_mapping: Dict[str, Dict[str, List[str]]] = {
            "usage_purpose": {
                "gaming": ["遊戲", "打遊戲", "電競", "gaming"],
                "business": ["工作", "商務", "辦公", "business", "職場", "上班"],
                "student": ["學生", "學習", "上課", "作業", "student"],
                "creative": ["創作", "設計", "剪輯", "creative"],
                "general": ["一般", "日常", "上網", "general"]
            },
            "budget_range": {
                "budget": ["便宜", "平價", "入門", "budget"],
                "mid_range": ["中等", "中端", "mid"],
                "premium": ["高端", "高級", "premium"],
                "luxury": ["旗艦", "頂級", "豪華", "luxury"]
            },
            "brand_preference": {
                "asus": ["asus", "華碩"],
                "acer": ["acer", "宏碁"],
                "lenovo": ["lenovo", "聯想"],
                "hp": ["hp", "惠普"],
                "dell": ["dell", "戴爾"],
                "apple": ["apple", "蘋果", "mac", "macbook"]
            }
        }

        # 混合外部配置與預設
        for slot, mapping in default_mapping.items():
            if slot not in data:
                data[slot] = mapping
                continue
            # 合併：若外部已定義，補齊預設缺失鍵，並去重
            for val, synonyms in mapping.items():
                merged = list({*(data[slot].get(val, [])), *synonyms})
                data[slot][val] = merged
        return data
    
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
