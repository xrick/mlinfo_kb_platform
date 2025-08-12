#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD UserInputHandler 模組
實現LLM驅動的用戶輸入處理和槽位提取
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

class UserInputHandler:
    """用戶輸入處理模組"""
    
    def __init__(self, llm_manager, slot_schema: Dict[str, Any]):
        """
        初始化用戶輸入處理器
        
        Args:
            llm_manager: LLM管理器
            slot_schema: 槽位架構定義
        """
        self.llm_manager = llm_manager
        self.slot_schema = slot_schema
        self.logger = logging.getLogger(__name__)
    
    def extract_slots_from_text(self, text: str, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用LLM從文本中提取槽位信息
        
        Args:
            text: 用戶輸入文本
            current_state: 當前對話狀態
            
        Returns:
            提取的槽位信息
        """
        try:
            # 構建槽位提取提示詞
            prompt = self._build_slot_extraction_prompt(text, current_state)
            
            # 調用LLM進行槽位提取
            response = self.llm_manager.extract_slots_with_llm(text, self.slot_schema)
            
            # 解析LLM回應
            extracted_slots = self._parse_slot_extraction_response(response)
            
            self.logger.info(f"槽位提取結果: {extracted_slots}")
            return extracted_slots
            
        except Exception as e:
            self.logger.error(f"槽位提取失敗: {e}")
            return {}
    
    def process_user_input(self, raw_text: str, session_id: str, state_manager) -> Dict[str, Any]:
        """
        處理用戶輸入的完整流程
        
        Args:
            raw_text: 原始用戶輸入
            session_id: 會話ID
            state_manager: 狀態管理器
            
        Returns:
            處理結果
        """
        try:
            # 1. 載入當前狀態
            current_state = state_manager.load_session_state(session_id)
            if not current_state:
                current_state = self._create_initial_state(session_id)
            
            # 2. 提取槽位信息
            extracted_slots = self.extract_slots_from_text(raw_text, current_state)
            
            # 3. 更新對話狀態
            updated_state = self._update_dialogue_state(current_state, raw_text, extracted_slots)
            
            # 4. 保存更新後的狀態
            state_manager.save_session_state(session_id, updated_state)
            
            return {
                "session_id": session_id,
                "extracted_slots": extracted_slots,
                "state": updated_state,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"用戶輸入處理失敗: {e}")
            return {
                "session_id": session_id,
                "extracted_slots": {},
                "error": str(e),
                "success": False
            }
    
    def _build_slot_extraction_prompt(self, text: str, current_state: Dict[str, Any]) -> str:
        """構建槽位提取提示詞"""
        filled_slots = current_state.get("filled_slots", {})
        
        prompt = f"""
你是一個專業的筆電銷售助手，需要從用戶輸入中提取結構化信息。

用戶輸入：{text}

已填寫的槽位：{json.dumps(filled_slots, ensure_ascii=False)}

請提取以下信息：
- 使用目的 (usage_purpose): gaming, business, student, creative, general
- 預算範圍 (budget_range): budget, mid_range, premium, luxury
- 性能需求 (performance_features): fast, portable, powerful, quiet, battery
- 品牌偏好 (brand_preference): asus, acer, lenovo, hp, dell, apple
- 便攜性需求 (portability_need): ultra_portable, balanced, desktop_replacement

輸出格式：JSON
{{
  "extracted_slots": {{
    "usage_purpose": "business",
    "budget_range": "mid_range",
    "performance_features": ["fast", "portable"],
    "brand_preference": "asus",
    "portability_need": "balanced"
  }},
  "confidence": 0.9,
  "reasoning": "提取理由"
}}

只輸出JSON格式，不要其他文字。
"""
        return prompt
    
    def _parse_slot_extraction_response(self, response: str) -> Dict[str, Any]:
        """解析LLM的槽位提取回應"""
        try:
            # 嘗試解析JSON回應
            if isinstance(response, str):
                # 提取JSON部分
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = response[start_idx:end_idx]
                    parsed = json.loads(json_str)
                    return parsed.get("extracted_slots", {})
            
            return {}
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失敗: {e}")
            return {}
    
    def _create_initial_state(self, session_id: str) -> Dict[str, Any]:
        """創建初始對話狀態"""
        return {
            "session_id": session_id,
            "chat_history": [],
            "filled_slots": {},
            "recommendations": [],
            "user_preferences": {},
            "current_stage": "awareness",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    
    def _update_dialogue_state(self, current_state: Dict[str, Any], 
                              user_input: str, extracted_slots: Dict[str, Any]) -> Dict[str, Any]:
        """更新對話狀態"""
        updated_state = current_state.copy()
        
        # 添加用戶消息到歷史記錄
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        }
        updated_state["chat_history"].append(user_message)
        
        # 更新已填寫的槽位
        if extracted_slots:
            current_filled_slots = updated_state.get("filled_slots", {})
            current_filled_slots.update(extracted_slots)
            updated_state["filled_slots"] = current_filled_slots
        
        # 更新時間戳
        updated_state["last_updated"] = datetime.now().isoformat()
        
        return updated_state
