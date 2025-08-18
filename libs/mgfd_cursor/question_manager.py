#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD QuestionManager 模組 - 整合Prompt風格
管理問題順序，整合結構化prompt與槽位收集
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from .slot_mapping import PromptOptionMapping

class QuestionManager:
    """問題順序管理器 - 整合Prompt風格與槽位收集"""
    
    def __init__(self, config_path: str = "libs/mgfd_cursor/humandata/default_slots_questions.json"):
        """
        初始化問題管理器
        
        Args:
            config_path: 問題配置文件路徑
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self.questions_config = {}
        self.question_sequence = []
        
        # 初始化槽位映射系統
        self.slot_mapper = PromptOptionMapping()
        
        # 載入問題配置
        self._load_questions_config()
        
        # Prompt風格的問候語和轉場詞
        self.prompt_phrases = {
            "opening": "您好！歡迎使用我們的筆記型電腦智慧推薦系統。為了協助您在眾多選擇中，快速找到最適合您的完美電腦，我將會詢問您幾個簡單的問題，整個過程大約需要一分鐘。準備好了嗎？",
            "transitions": [
                "了解了！接下來，",
                "好的。", 
                "關於",
                "我們就快完成了！最後，"
            ],
            "closing": "感謝您的回覆！我為您整理的需求摘要如下："
        }
    
    def _load_questions_config(self):
        """載入問題配置"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.questions_config = data.get("slot_questions", {})
                    self.question_sequence = self.questions_config.get("question_sequence", [])
                    self.logger.info(f"成功載入 {len(self.question_sequence)} 個問題配置")
            else:
                self.logger.error(f"問題配置文件不存在: {config_file}")
                raise FileNotFoundError(f"配置文件不存在: {config_file}")
        except Exception as e:
            self.logger.error(f"載入問題配置失敗: {e}")
            raise
    
    def get_next_question(self, current_slots: Dict[str, Any], current_question_order: int = 0, use_prompt_style: bool = True) -> Optional[Dict[str, Any]]:
        """
        根據當前狀態獲取下一個問題 - 支援Prompt風格
        
        Args:
            current_slots: 當前已收集的槽位
            current_question_order: 當前問題順序 (0表示從頭開始)
            
        Returns:
            下一個問題的配置，如果沒有更多問題則返回None
        """
        try:
            # 從指定順序開始尋找下一個問題
            for question_config in self.question_sequence:
                order = question_config.get("order", 0)
                
                # 只考慮順序大於當前問題的問題
                if order <= current_question_order:
                    continue
                
                slot_name = question_config.get("enhanced_slot_name", "")
                
                # 檢查是否應該跳過此問題
                if self._should_skip_question(question_config, current_slots):
                    self.logger.info(f"跳過問題 Order {order}: {slot_name}")
                    continue
                
                # 檢查槽位是否已經填充
                if slot_name in current_slots and current_slots[slot_name]:
                    self.logger.info(f"槽位已填充，跳過問題 Order {order}: {slot_name}")
                    continue
                
                # 找到下一個需要詢問的問題
                self.logger.info(f"返回下一個問題 Order {order}: {slot_name}")
                return question_config
            
            # 沒有更多問題需要詢問
            self.logger.info("沒有更多問題需要詢問")
            return None
            
        except Exception as e:
            self.logger.error(f"獲取下一個問題失敗: {e}")
            return None
    
    def _should_skip_question(self, question_config: Dict[str, Any], current_slots: Dict[str, Any]) -> bool:
        """
        判斷是否應該跳過問題
        
        Args:
            question_config: 問題配置
            current_slots: 當前已收集的槽位
            
        Returns:
            是否應該跳過
        """
        try:
            # 獲取跳過條件配置
            skip_conditions = self.questions_config.get("questioning_strategy", {}).get("optional_skip_conditions", {})
            
            # 檢查預算相關跳過邏輯
            if "if_budget_low" in skip_conditions:
                budget = current_slots.get("budget_range", "")
                if budget in ["budget", "經濟實惠型", "便宜", "平價"]:
                    skip_slots = skip_conditions["if_budget_low"]
                    enhanced_slot_name = question_config.get("enhanced_slot_name", "")
                    if enhanced_slot_name in skip_slots:
                        self.logger.info(f"因預算較低跳過問題: {enhanced_slot_name}")
                        return True
            
            # 檢查用途相關跳過邏輯
            if "if_usage_simple" in skip_conditions:
                usage = current_slots.get("usage_purpose", "")
                if usage in ["general", "document_processing", "一般文書處理", "日常上網"]:
                    skip_slots = skip_conditions["if_usage_simple"]
                    enhanced_slot_name = question_config.get("enhanced_slot_name", "")
                    if enhanced_slot_name in skip_slots:
                        self.logger.info(f"因用途簡單跳過問題: {enhanced_slot_name}")
                        return True
            
            # 檢查攜帶性相關跳過邏輯
            if "if_portability_not_important" in skip_conditions:
                portability = current_slots.get("portability", "")
                weight_req = current_slots.get("weight_requirement", "")
                if portability in ["never", "完全不攜帶"] or weight_req in ["heavy", "重量不重要"]:
                    skip_slots = skip_conditions["if_portability_not_important"]
                    enhanced_slot_name = question_config.get("enhanced_slot_name", "")
                    if enhanced_slot_name in skip_slots:
                        self.logger.info(f"因攜帶性不重要跳過問題: {enhanced_slot_name}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"判斷跳過邏輯失敗: {e}")
            return False
    
    def is_collection_complete(self, current_slots: Dict[str, Any]) -> bool:
        """
        判斷槽位收集是否完成（可以進行產品搜索）
        
        Args:
            current_slots: 當前已收集的槽位
            
        Returns:
            是否可以進行產品搜索
        """
        try:
            # 檢查必填槽位
            required_slots = ["usage_purpose", "budget_range"]
            for slot_name in required_slots:
                if slot_name not in current_slots or not current_slots[slot_name]:
                    self.logger.info(f"必填槽位未完成: {slot_name}")
                    return False
            
            # 如果必填槽位已完成，檢查是否還有需要詢問的問題
            next_question = self.get_next_question(current_slots, 0)
            if next_question is None:
                self.logger.info("所有問題都已完成或跳過，可以進行產品搜索")
                return True
            
            # 如果還有重要問題未完成，繼續收集
            return False
            
        except Exception as e:
            self.logger.error(f"判斷收集完成狀態失敗: {e}")
            # 保守起見，如果出錯就認為還未完成
            return False
    
    def get_question_by_order(self, order: int) -> Optional[Dict[str, Any]]:
        """
        根據順序號獲取問題配置
        
        Args:
            order: 問題順序號 (1-11)
            
        Returns:
            問題配置或None
        """
        try:
            for question_config in self.question_sequence:
                if question_config.get("order", 0) == order:
                    return question_config
            return None
        except Exception as e:
            self.logger.error(f"根據順序獲取問題失敗: {e}")
            return None
    
    def get_prompt_style_question(self, step_number: int, current_slots: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        獲取Prompt風格的結構化問題
        
        Args:
            step_number: 步驟號碼 (1-6)
            current_slots: 目前槽位狀態
            
        Returns:
            結構化問題字典
        """
        try:
            if step_number == 1:
                # 第1步：收集用途
                return {
                    "step": 1,
                    "question": "首先，請問您購買這台新電腦，最主要的用途是什麼呢？這將幫助我判斷電腦需要的核心效能。",
                    "type": "choice",
                    "slot_name": "usage_purpose",
                    "options": self.slot_mapper.get_prompt_options_for_slot("usage_purpose"),
                    "transition": ""
                }
            elif step_number == 2:
                # 第2步：收集價格區間
                return {
                    "step": 2, 
                    "question": "了解了！接下來，請問您的預算大概是多少呢？",
                    "type": "choice",
                    "slot_name": "budget_range",
                    "options": self.slot_mapper.get_prompt_options_for_slot("budget_range"),
                    "transition": self.prompt_phrases["transitions"][0]
                }
            elif step_number == 3:
                # 第3步：收集攜帶性
                return {
                    "step": 3,
                    "question": "好的。請問您會多常需要帶著電腦外出使用呢？",
                    "type": "choice", 
                    "slot_name": "portability",
                    "options": self.slot_mapper.get_prompt_options_for_slot("portability"),
                    "transition": self.prompt_phrases["transitions"][1]
                }
            elif step_number == 4:
                # 第4步：收集螢幕尺寸
                return {
                    "step": 4,
                    "question": "關於螢幕大小，您有沒有比較偏好的尺寸呢？",
                    "type": "choice",
                    "slot_name": "screen_size", 
                    "options": self.slot_mapper.get_prompt_options_for_slot("screen_size"),
                    "transition": self.prompt_phrases["transitions"][2]
                }
            elif step_number == 5:
                # 第5步：收集品牌
                return {
                    "step": 5,
                    "question": "您有特別偏好的品牌嗎？如果沒有，可以直接告訴我「沒有偏好」。",
                    "type": "choice_multiple",
                    "slot_name": "brand_preference",
                    "options": self.slot_mapper.get_prompt_options_for_slot("brand_preference"),
                    "transition": ""
                }
            elif step_number == 6:
                # 第6步：收集其他關鍵需求
                return {
                    "step": 6,
                    "question": "我們就快完成了！最後，請問您還有沒有其他特別在意的點？",
                    "type": "choice_multiple",
                    "slot_name": "special_requirement",
                    "options": self.slot_mapper.get_prompt_options_for_slot("special_requirement"),
                    "transition": self.prompt_phrases["transitions"][3]
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"生成Prompt風格問題失敗: {e}")
            return None
    
    def format_question_with_options(self, question_data: Dict[str, Any]) -> str:
        """
        將問題格式化為包含選項的完整文字
        
        Args:
            question_data: 問題數據
            
        Returns:
            格式化的問題文字
        """
        if not question_data or "question" not in question_data:
            return ""
        
        try:
            # 基礎問題文字
            formatted_text = question_data.get("transition", "") + question_data["question"]
            
            # 添加選項
            if "options" in question_data and question_data["options"]:
                formatted_text += "\n\n選項："
                for option in question_data["options"]:
                    formatted_text += f"\n{option['key']}) {option['text']}"
            
            return formatted_text
            
        except Exception as e:
            self.logger.error(f"格式化問題失敗: {e}")
            return question_data.get("question", "")
    
    def process_prompt_response(self, step: int, response: str, current_slots: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理Prompt風格的回應
        
        Args:
            step: 步驟號
            response: 用戶回應
            current_slots: 當前槽位
            
        Returns:
            更新後的槽位
        """
        try:
            updated_slots = current_slots.copy()
            step_key = f"step_{step}"

            # 正規化輸入（允許 A-F 與完整選項文字）
            normalized = (response or "").strip()
            normalized_upper = normalized.upper()
            normalized_lower = normalized.lower()

            # 允許直接用 value/label（中文全稱）或字母鍵
            # 1) 嘗試字母鍵驗證
            if self.slot_mapper.validate_prompt_response(step_key, normalized_upper):
                prompt_responses = {step_key: normalized_upper}
                new_slots = self.slot_mapper.convert_prompt_to_slots(prompt_responses)
                updated_slots.update(new_slots)
                self.logger.info(f"步驟{step}字母鍵回覆: {normalized_upper} -> {new_slots}")
                return updated_slots

            # 2) 嘗試中文全稱/標準值匹配（從選項表反查 key）
            options = []
            if step == 1:
                options = self.slot_mapper.get_prompt_options_for_slot("usage_purpose")
            elif step == 2:
                options = self.slot_mapper.get_prompt_options_for_slot("budget_range")
            elif step == 3:
                options = self.slot_mapper.get_prompt_options_for_slot("portability")
            elif step == 4:
                options = self.slot_mapper.get_prompt_options_for_slot("screen_size")
            elif step == 5:
                options = self.slot_mapper.get_prompt_options_for_slot("brand_preference")
            elif step == 6:
                options = self.slot_mapper.get_prompt_options_for_slot("special_requirement")

            def find_key_by_label_or_value(text: str) -> Optional[str]:
                t = (text or "").strip().lower()
                for opt in options:
                    if opt.get("value", "").lower() == t:
                        return opt.get("key")
                    if opt.get("text", "").lower() == t:
                        return opt.get("key")
                return None

            inferred_key = find_key_by_label_or_value(normalized)
            if inferred_key and self.slot_mapper.validate_prompt_response(step_key, inferred_key):
                prompt_responses = {step_key: inferred_key}
                new_slots = self.slot_mapper.convert_prompt_to_slots(prompt_responses)
                updated_slots.update(new_slots)
                self.logger.info(f"步驟{step}文本回覆匹配: {normalized} -> key={inferred_key} -> {new_slots}")
                return updated_slots

            # 3) 最後嘗試自然語言增強（不推薦，但作為保底）
            enhanced_slots = self.slot_mapper.enhance_slots_from_natural_input(response, current_slots)
            if enhanced_slots != current_slots:
                updated_slots.update(enhanced_slots)
                self.logger.info(f"自然語言處理步驟{step}: {response} -> 新增槽位")
                return updated_slots

            self.logger.warning(f"無法處理步驟{step}的回應: {response}")
            return updated_slots
            
        except Exception as e:
            self.logger.error(f"處理Prompt回應失敗: {e}")
            return current_slots
    
    def generate_summary(self, slots: Dict[str, Any]) -> str:
        """
        生成需求摘要（模仿Prompt風格）
        
        Args:
            slots: 已收集的槽位
            
        Returns:
            摘要文字
        """
        try:
            summary = self.prompt_phrases["closing"] + "\n\n"
            
            # 主要用途
            if "usage_purpose" in slots:
                usage_text = self._get_usage_display_text(slots["usage_purpose"])
                summary += f"主要用途： {usage_text}\n"
            
            # 預算範圍
            if "budget_range" in slots:
                budget_text = self._get_budget_display_text(slots["budget_range"])
                summary += f"預算範圍： {budget_text}\n"
            
            # 攜帶需求
            if "portability" in slots:
                portability_text = self._get_portability_display_text(slots["portability"])
                summary += f"攜帶需求： {portability_text}\n"
            
            # 偏好尺寸
            if "screen_size" in slots:
                screen_text = self._get_screen_display_text(slots["screen_size"])
                summary += f"偏好尺寸： {screen_text}\n"
            
            # 偏好品牌
            if "brand_preference" in slots:
                brand_text = self._get_brand_display_text(slots["brand_preference"])
                summary += f"偏好品牌： {brand_text}\n"
            
            # 其他需求
            if "special_requirement" in slots:
                special_text = self._get_special_display_text(slots["special_requirement"])
                summary += f"其他需求： {special_text}\n"
            
            return summary.strip()
            
        except Exception as e:
            self.logger.error(f"生成摘要失敗: {e}")
            return "需求摘要生成失敗"
    
    def _get_usage_display_text(self, usage_value: str) -> str:
        """獲取用途的顯示文字"""
        mapping = {
            "document_processing": "日常文書處理與上網",
            "entertainment": "影音娛樂",
            "creative": "專業創作 (例如：修圖、影片剪輯)",
            "gaming": "電競遊戲",
            "business": "商務辦公",
            "programming": "程式開發",
            "general": "其他"
        }
        return mapping.get(usage_value, usage_value)
    
    def _get_budget_display_text(self, budget_value: str) -> str:
        """獲取預算的顯示文字"""
        mapping = {
            "budget": "25,000元 以下",
            "low_mid": "25,001 - 40,000元",
            "mid_range": "40,001 - 55,000元", 
            "high_mid": "55,001 - 70,000元",
            "premium": "70,000元 以上"
        }
        return mapping.get(budget_value, budget_value)
    
    def _get_portability_display_text(self, portability_value: str) -> str:
        """獲取攜帶性的顯示文字"""
        mapping = {
            "desktop_replacement": "幾乎都在固定地點使用",
            "occasional": "偶爾攜帶 (每週數次)",
            "frequent": "經常攜帶 (幾乎每天)"
        }
        return mapping.get(portability_value, portability_value)
    
    def _get_screen_display_text(self, screen_value: str) -> str:
        """獲取螢幕尺寸的顯示文字"""
        mapping = {
            "13": "13吋及以下 (極致輕薄)",
            "14": "14吋 (平衡便攜與視野)",
            "15": "15-16吋 (標準尺寸)",
            "17": "17吋及以上 (桌機級體驗)"
        }
        return mapping.get(screen_value, f"{screen_value}吋")
    
    def _get_brand_display_text(self, brand_value: str) -> str:
        """獲取品牌的顯示文字"""
        mapping = {
            "apple": "Apple",
            "asus": "ASUS", 
            "acer": "Acer",
            "dell": "Dell",
            "hp": "HP",
            "lenovo": "Lenovo",
            "msi": "MSI",
            "no_preference": "沒有特定偏好",
            "others": "其他"
        }
        return mapping.get(brand_value, brand_value)
    
    def _get_special_display_text(self, special_value: str) -> str:
        """獲取特殊需求的顯示文字"""
        mapping = {
            "fast_boot": "開關機和讀取軟體的速度要非常快",
            "latest_model": "希望是近一年內推出的最新款機種", 
            "specific_specs": "對CPU或GPU的型號有特定要求",
            "custom_needs": "其他特殊需求"
        }
        return mapping.get(special_value, special_value)
    
    def should_skip_to_search(self, slots: Dict[str, Any]) -> bool:
        """
        判斷是否應該跳過剩餘問題直接搜尋
        
        Args:
            slots: 當前槽位
            
        Returns:
            是否應該跳過
        """
        # 必須有用途和預算
        if "usage_purpose" not in slots or "budget_range" not in slots:
            return False
        
        # 如果已經有足夠信息進行有效搜尋
        slot_count = len(slots)
        if slot_count >= 4:  # 有4個以上槽位就足夠搜尋
            return True
        
        # 如果用戶明確表示不想回答更多問題
        if "skip_remaining" in slots:
            return True
        
        return False
    
    def get_intelligent_next_question(self, current_slots: Dict[str, Any], chunking_results: List[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        基於chunking結果的智能下一問題選擇
        
        Args:
            current_slots: 當前槽位
            chunking_results: chunking搜尋結果（可選）
            
        Returns:
            下一個問題
        """
        try:
            # 如果搜尋結果不理想，詢問更詳細的信息
            if chunking_results is not None and len(chunking_results) < 3:
                # 根據現有槽位決定需要詳細詢問的方面
                missing_priority = self.slot_mapper.get_slot_priority(current_slots)
                
                for slot_name in missing_priority:
                    if slot_name not in current_slots:
                        # 找到對應的prompt步驟
                        step_mapping = {
                            "usage_purpose": 1,
                            "budget_range": 2,
                            "portability": 3,
                            "screen_size": 4,
                            "brand_preference": 5,
                            "special_requirement": 6
                        }
                        
                        if slot_name in step_mapping:
                            return self.get_prompt_style_question(step_mapping[slot_name], current_slots)
            
            # 否則按正常流程
            return self.get_next_question(current_slots)
            
        except Exception as e:
            self.logger.error(f"智能問題選擇失敗: {e}")
            return self.get_next_question(current_slots)
    
    def get_follow_up_question(self, slot_name: str, slot_value: str) -> Optional[str]:
        """
        獲取追問問題
        
        Args:
            slot_name: 槽位名稱
            slot_value: 槽位值
            
        Returns:
            追問問題或None
        """
        try:
            # 尋找對應的問題配置
            for question_config in self.question_sequence:
                if question_config.get("enhanced_slot_name", "") == slot_name:
                    follow_ups = question_config.get("follow_up_questions", {})
                    return follow_ups.get(slot_value)
            return None
        except Exception as e:
            self.logger.error(f"獲取追問問題失敗: {e}")
            return None
    
    def get_progress_info(self, current_slots: Dict[str, Any]) -> Dict[str, Any]:
        """
        獲取問題收集進度信息
        
        Args:
            current_slots: 當前已收集的槽位
            
        Returns:
            進度信息字典
        """
        try:
            total_questions = len(self.question_sequence)
            completed_questions = 0
            skipped_questions = 0
            
            for question_config in self.question_sequence:
                slot_name = question_config.get("enhanced_slot_name", "")
                
                if slot_name in current_slots and current_slots[slot_name]:
                    completed_questions += 1
                elif self._should_skip_question(question_config, current_slots):
                    skipped_questions += 1
            
            remaining_questions = total_questions - completed_questions - skipped_questions
            
            return {
                "total_questions": total_questions,
                "completed_questions": completed_questions,
                "skipped_questions": skipped_questions,
                "remaining_questions": remaining_questions,
                "completion_percentage": round((completed_questions + skipped_questions) / total_questions * 100, 1)
            }
            
        except Exception as e:
            self.logger.error(f"獲取進度信息失敗: {e}")
            return {
                "total_questions": 0,
                "completed_questions": 0,
                "skipped_questions": 0,
                "remaining_questions": 0,
                "completion_percentage": 0
            }