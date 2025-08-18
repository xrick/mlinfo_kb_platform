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
        
        # 智能化 Prompt 短語系統 - 增強版轉場詞
        self.prompt_phrases = {
            "opening": "您好！歡迎使用我們的筆記型電腦智慧推薦系統。為了協助您在眾多選擇中，快速找到最適合您的完美電腦，我將會詢問您幾個簡單的問題，整個過程大約需要一分鐘。準備好了嗎？",
            "transitions": {
                "basic": [
                    "了解了！接下來，",
                    "好的。", 
                    "明白了，那麼",
                    "很好！"
                ],
                "performance": [
                    "關於效能配置，",
                    "接下來聊聊規格，",
                    "在硬體方面，"
                ],
                "physical": [
                    "關於外觀和攜帶性，",
                    "在實用性方面，",
                    "考慮到日常使用，"
                ],
                "preference": [
                    "關於您的偏好，",
                    "最後想了解，",
                    "還想確認一下，"
                ],
                "closing": [
                    "我們就快完成了！最後，",
                    "最後一個問題，",
                    "差不多了，請問"
                ]
            },
            "confirmations": [
                "好的，我記下了。",
                "了解您的需求了。",
                "明白，這很重要。",
                "收到，這對推薦很有幫助。"
            ],
            "progress_indicators": [
                "已完成 {current}/{total}",
                "還有 {remaining} 個問題",
                "進度：{percentage}%"
            ],
            "closing": "感謝您的耐心回覆！我為您整理的需求摘要如下："
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
        智能判斷是否應該跳過問題 - 增強版跳過邏輯
        
        Args:
            question_config: 問題配置
            current_slots: 當前已收集的槽位
            
        Returns:
            是否應該跳過
        """
        try:
            enhanced_slot_name = question_config.get("enhanced_slot_name", "")
            
            # 1. 基於用途的智能跳過
            usage = current_slots.get("usage_purpose", "")
            if self._should_skip_by_usage(enhanced_slot_name, usage, current_slots):
                return True
            
            # 2. 基於預算的智能跳過
            budget = current_slots.get("budget_range", "")
            if self._should_skip_by_budget(enhanced_slot_name, budget, current_slots):
                return True
            
            # 3. 基於攜帶性需求的智能跳過
            portability = current_slots.get("portability", "")
            weight_req = current_slots.get("weight_requirement", "")
            if self._should_skip_by_portability(enhanced_slot_name, portability, weight_req):
                return True
            
            # 4. 基於效能需求的智能跳過
            cpu_level = current_slots.get("cpu_level", "")
            gpu_level = current_slots.get("gpu_level", "")
            if self._should_skip_by_performance(enhanced_slot_name, cpu_level, gpu_level):
                return True
            
            # 5. 基於邏輯依賴的智能跳過
            if self._should_skip_by_logical_dependency(enhanced_slot_name, current_slots):
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"判斷跳過邏輯失敗: {e}")
            return False
    
    def _should_skip_by_usage(self, slot_name: str, usage: str, current_slots: Dict[str, Any]) -> bool:
        """基於用途的智能跳過邏輯"""
        if not usage:
            return False
        
        # 文書處理用途：跳過高效能相關問題
        if usage in ["document_processing", "general"]:
            if slot_name in ["gpu_level", "performance_features"]:
                self.logger.info(f"文書處理用途，跳過高效能問題: {slot_name}")
                return True
        
        # 遊戲用途：不跳過任何效能相關問題，但可能跳過攜帶性
        elif usage == "gaming":
            # 遊戲用途通常不太關心攜帶性，但仍然詢問以確認
            pass
        
        # 商務用途：跳過遊戲效能相關問題
        elif usage == "business":
            if slot_name == "gpu_level":
                # 但仍需要確認是否有特殊需求
                if "special_requirement" not in current_slots:
                    return False  # 等待特殊需求確認
        
        # 創作用途：不跳過效能相關問題
        elif usage == "creative":
            pass
        
        return False
    
    def _should_skip_by_budget(self, slot_name: str, budget: str, current_slots: Dict[str, Any]) -> bool:
        """基於預算的智能跳過邏輯"""
        if not budget:
            return False
        
        # 低預算：跳過高端配置相關問題
        if budget in ["budget"]:
            if slot_name in ["gpu_level", "performance_features"] and current_slots.get("usage_purpose") in ["document_processing", "general"]:
                self.logger.info(f"低預算且基本用途，跳過高端配置問題: {slot_name}")
                return True
            
            # 低預算通常不會考慮最新款，但仍詢問以確認用戶偏好
            if slot_name == "release_time":
                return False  # 仍然詢問，但會推薦成熟型號
        
        # 高預算：不跳過任何問題，讓用戶有更多選擇
        elif budget in ["premium"]:
            pass
        
        return False
    
    def _should_skip_by_portability(self, slot_name: str, portability: str, weight_req: str) -> bool:
        """基於攜帶性需求的智能跳過邏輯"""
        # 如果明確表示不攜帶，跳過重量相關問題
        if portability in ["desktop_replacement", "never"] or weight_req in ["heavy"]:
            if slot_name == "weight_requirement" and portability in ["desktop_replacement", "never"]:
                self.logger.info(f"桌面替代用途，跳過重量問題: {slot_name}")
                return True
        
        # 如果已經表示經常攜帶，且已有重量要求，可以推斷攜帶性
        if weight_req in ["ultra_light", "light"] and slot_name == "portability":
            self.logger.info(f"已確認重量要求為輕便，推斷攜帶性需求")
            # 不跳過，而是自動推斷並確認
            return False
        
        return False
    
    def _should_skip_by_performance(self, slot_name: str, cpu_level: str, gpu_level: str) -> bool:
        """基於效能需求的智能跳過邏輯"""
        # 如果用戶對CPU/GPU都選擇了基本等級，可以跳過一些進階問題
        if cpu_level == "basic" and gpu_level == "integrated":
            if slot_name == "performance_features":
                # 基本配置用戶可能不太關心極致的開關機速度
                return False  # 仍詢問，但會推薦平衡選項
        
        # 如果選擇了自動推薦，系統需要更多信息來做決定
        if cpu_level == "auto" or gpu_level == "auto":
            return False  # 不跳過任何問題
        
        return False
    
    def _should_skip_by_logical_dependency(self, slot_name: str, current_slots: Dict[str, Any]) -> bool:
        """基於邏輯依賴的智能跳過"""
        # 如果用戶已經明確表示沒有特殊需求，可以跳過某些細節問題
        special_req = current_slots.get("special_requirement", "")
        if special_req == "none":
            # 用戶沒有特殊需求，但仍需要基本配置信息
            pass
        
        # 如果用戶選擇了"不在意推出時間"，不影響其他問題
        release_time = current_slots.get("release_time", "")
        if release_time == "any":
            # 不跳過任何問題，只是在推薦時不考慮時間因素
            pass
        
        # 邏輯一致性檢查：如果重量要求和攜帶性衝突，需要澄清
        weight_req = current_slots.get("weight_requirement", "")
        portability = current_slots.get("portability", "")
        if weight_req == "heavy" and portability == "frequent":
            # 這種情況需要澄清，不跳過相關問題
            return False
        
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
            step_number: 步驟號碼 (1-11) - 擴展支援完整11個問題
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
                    "transition": self.get_smart_transition(2, "budget_range", current_slots or {})
                }
            elif step_number == 3:
                # 第3步：收集推出時間偏好
                return {
                    "step": 3,
                    "question": "關於推出時間，您對筆電的新舊程度有什麼偏好嗎？",
                    "type": "choice",
                    "slot_name": "release_time",
                    "options": [
                        {"key": "A", "text": "最新款（半年內推出）", "value": "latest"},
                        {"key": "B", "text": "較新款（1年內推出）", "value": "recent"},
                        {"key": "C", "text": "成熟款（1-2年前推出，價格穩定）", "value": "mature"},
                        {"key": "D", "text": "不在意推出時間", "value": "any"}
                    ],
                    "transition": self.get_smart_transition(3, "release_time", current_slots or {})
                }
            elif step_number == 4:
                # 第4步：收集CPU效能需求
                return {
                    "step": 4,
                    "question": "您對處理器效能有什麼要求嗎？",
                    "type": "choice",
                    "slot_name": "cpu_level",
                    "options": [
                        {"key": "A", "text": "基本文書處理即可（i3、Ryzen 3等級）", "value": "basic"},
                        {"key": "B", "text": "中等效能需求（i5、Ryzen 5等級）", "value": "mid"},
                        {"key": "C", "text": "高效能需求（i7、i9、Ryzen 7/9等級）", "value": "high"},
                        {"key": "D", "text": "不確定，請幫我推薦", "value": "auto"}
                    ],
                    "transition": self.get_smart_transition(4, "cpu_level", current_slots or {})
                }
            elif step_number == 5:
                # 第5步：收集GPU效能需求
                return {
                    "step": 5,
                    "question": "您需要獨立顯示卡嗎？",
                    "type": "choice",
                    "slot_name": "gpu_level",
                    "options": [
                        {"key": "A", "text": "不需要，內建顯示卡即可（文書、上網）", "value": "integrated"},
                        {"key": "B", "text": "需要獨立顯卡（遊戲、影片剪輯）", "value": "dedicated"},
                        {"key": "C", "text": "需要專業顯卡（3D設計、工作站等級）", "value": "professional"},
                        {"key": "D", "text": "不確定，請幫我評估", "value": "auto"}
                    ],
                    "transition": self.get_smart_transition(5, "gpu_level", current_slots or {})
                }
            elif step_number == 6:
                # 第6步：收集重量要求
                return {
                    "step": 6,
                    "question": "您對筆電重量有什麼要求嗎？",
                    "type": "choice",
                    "slot_name": "weight_requirement",
                    "options": [
                        {"key": "A", "text": "越輕越好（1kg以下，超輕便）", "value": "ultra_light"},
                        {"key": "B", "text": "輕便即可（1-1.5kg，便於攜帶）", "value": "light"},
                        {"key": "C", "text": "一般重量（1.5-2kg，標準重量）", "value": "standard"},
                        {"key": "D", "text": "重量不重要（效能優先）", "value": "heavy"}
                    ],
                    "transition": self.get_smart_transition(6, "weight_requirement", current_slots or {})
                }
            elif step_number == 7:
                # 第7步：收集攜帶性需求
                return {
                    "step": 7,
                    "question": "您經常需要攜帶筆電外出嗎？",
                    "type": "choice", 
                    "slot_name": "portability",
                    "options": self.slot_mapper.get_prompt_options_for_slot("portability"),
                    "transition": self.get_smart_transition(7, "portability", current_slots or {})
                }
            elif step_number == 8:
                # 第8步：收集開關機速度要求
                return {
                    "step": 8,
                    "question": "您對開關機速度有特別要求嗎？",
                    "type": "choice",
                    "slot_name": "performance_features",
                    "options": [
                        {"key": "A", "text": "很重視（希望10秒內開機）", "value": "fast"},
                        {"key": "B", "text": "有要求（希望30秒內開機）", "value": "moderate"},
                        {"key": "C", "text": "一般即可（1分鐘內可接受）", "value": "normal"},
                        {"key": "D", "text": "不在意開關機速度", "value": "no_care"}
                    ],
                    "transition": self.get_smart_transition(8, "performance_features", current_slots or {})
                }
            elif step_number == 9:
                # 第9步：收集螢幕尺寸
                return {
                    "step": 9,
                    "question": "您希望螢幕尺寸是多大呢？",
                    "type": "choice",
                    "slot_name": "screen_size", 
                    "options": self.slot_mapper.get_prompt_options_for_slot("screen_size"),
                    "transition": self.get_smart_transition(9, "screen_size", current_slots or {})
                }
            elif step_number == 10:
                # 第10步：收集品牌偏好
                return {
                    "step": 10,
                    "question": "您有特別偏好的品牌嗎？如果沒有，可以直接告訴我「沒有偏好」。",
                    "type": "choice_multiple",
                    "slot_name": "brand_preference",
                    "options": self.slot_mapper.get_prompt_options_for_slot("brand_preference"),
                    "transition": self.get_smart_transition(10, "brand_preference", current_slots or {})
                }
            elif step_number == 11:
                # 第11步：收集觸控螢幕等特殊需求
                return {
                    "step": 11,
                    "question": "最後，請問您需要觸控螢幕功能，或是還有其他特別在意的點嗎？",
                    "type": "choice_multiple",
                    "slot_name": "special_requirement",
                    "options": [
                        {"key": "A", "text": "需要觸控螢幕（繪圖、觸控操作）", "value": "touchscreen"},
                        {"key": "B", "text": "開關機和讀取軟體的速度要非常快", "value": "fast_boot"},
                        {"key": "C", "text": "希望是近一年內推出的最新款機種", "value": "latest_model"},
                        {"key": "D", "text": "對CPU或GPU的型號有特定要求", "value": "specific_specs"},
                        {"key": "E", "text": "沒有其他特殊需求", "value": "none"}
                    ],
                    "transition": self.get_smart_transition(11, "special_requirement", current_slots or {})
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"生成Prompt風格問題失敗: {e}")
            return None
    
    def format_question_with_options(self, question_data: Dict[str, Any], current_slots: Dict[str, Any] = None) -> str:
        """
        將問題格式化為包含選項的完整文字 - 增強版包含智能進度和轉場
        
        Args:
            question_data: 問題數據
            current_slots: 當前槽位（用於進度計算）
            
        Returns:
            格式化的問題文字
        """
        if not question_data or "question" not in question_data:
            return ""
        
        try:
            formatted_parts = []
            
            # 添加進度資訊（在特定步驟）
            step = question_data.get("step", 1)
            if current_slots and step > 1:
                progress_text = self.get_progress_info_text(current_slots, step)
                if progress_text:
                    formatted_parts.append(progress_text)
            
            # 添加轉場詞和問題
            transition = question_data.get("transition", "")
            question = question_data["question"]
            formatted_parts.append(transition + question)
            
            # 添加選項
            if "options" in question_data and question_data["options"]:
                options_text = "\n\n選項："
                for option in question_data["options"]:
                    options_text += f"\n{option['key']}) {option['text']}"
                formatted_parts.append(options_text)
            
            # 添加鼓勵性提示（隨機出現）
            if step > 1 and step % 3 == 0:  # 每三題提供一次鼓勵
                import random
                if random.random() < 0.7:  # 70% 機率顯示
                    encouragements = [
                        "\n\n💡 您的回答將幫助我們找到最適合的筆電！",
                        "\n\n✨ 快要完成了，謝謝您的耐心配合！",
                        "\n\n🎯 根據您的需求，我們會推薦最合適的選擇！"
                    ]
                    formatted_parts.append(random.choice(encouragements))
            
            return "".join(formatted_parts)
            
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
            self.logger.info(f"DEBUG - QuestionManager.process_prompt_response:")
            self.logger.info(f"  - step: {step}")
            self.logger.info(f"  - response: '{response}'")
            self.logger.info(f"  - current_slots: {current_slots}")
            
            updated_slots = current_slots.copy()
            step_key = f"step_{step}"

            # 正規化輸入（允許 A-F 與完整選項文字）
            normalized = (response or "").strip()
            normalized_upper = normalized.upper()
            normalized_lower = normalized.lower()
            
            self.logger.info(f"DEBUG - 正規化輸入: '{normalized}' -> upper: '{normalized_upper}'")

            # 允許直接用 value/label（中文全稱）或字母鍵
            # 1) 嘗試字母鍵驗證
            validation_result = self.slot_mapper.validate_prompt_response(step_key, normalized_upper)
            self.logger.info(f"DEBUG - 字母鍵驗證結果: {validation_result}")
            
            if validation_result:
                prompt_responses = {step_key: normalized_upper}
                new_slots = self.slot_mapper.convert_prompt_to_slots(prompt_responses)
                updated_slots.update(new_slots)
                self.logger.info(f"DEBUG - 步驟{step}字母鍵回覆成功: {normalized_upper} -> {new_slots}")
                self.logger.info(f"DEBUG - 最終更新後的槽位: {updated_slots}")
                return updated_slots

            # 2) 嘗試中文全稱/標準值匹配（從選項表反查 key）
            options = []
            if step == 1:
                options = self.slot_mapper.get_prompt_options_for_slot("usage_purpose")
            elif step == 2:
                options = self.slot_mapper.get_prompt_options_for_slot("budget_range")
            elif step == 3:
                # 第3步：推出時間 - 直接提供選項
                options = [
                    {"key": "A", "text": "最新款（半年內推出）", "value": "latest"},
                    {"key": "B", "text": "較新款（1年內推出）", "value": "recent"},
                    {"key": "C", "text": "成熟款（1-2年前推出，價格穩定）", "value": "mature"},
                    {"key": "D", "text": "不在意推出時間", "value": "any"}
                ]
            elif step == 4:
                # 第4步：CPU效能
                options = [
                    {"key": "A", "text": "基本文書處理即可（i3、Ryzen 3等級）", "value": "basic"},
                    {"key": "B", "text": "中等效能需求（i5、Ryzen 5等級）", "value": "mid"},
                    {"key": "C", "text": "高效能需求（i7、i9、Ryzen 7/9等級）", "value": "high"},
                    {"key": "D", "text": "不確定，請幫我推薦", "value": "auto"}
                ]
            elif step == 5:
                # 第5步：GPU效能
                options = [
                    {"key": "A", "text": "不需要，內建顯示卡即可（文書、上網）", "value": "integrated"},
                    {"key": "B", "text": "需要獨立顯卡（遊戲、影片剪輯）", "value": "dedicated"},
                    {"key": "C", "text": "需要專業顯卡（3D設計、工作站等級）", "value": "professional"},
                    {"key": "D", "text": "不確定，請幫我評估", "value": "auto"}
                ]
            elif step == 6:
                # 第6步：重量要求
                options = [
                    {"key": "A", "text": "越輕越好（1kg以下，超輕便）", "value": "ultra_light"},
                    {"key": "B", "text": "輕便即可（1-1.5kg，便於攜帶）", "value": "light"},
                    {"key": "C", "text": "一般重量（1.5-2kg，標準重量）", "value": "standard"},
                    {"key": "D", "text": "重量不重要（效能優先）", "value": "heavy"}
                ]
            elif step == 7:
                options = self.slot_mapper.get_prompt_options_for_slot("portability")
            elif step == 8:
                # 第8步：開關機速度
                options = [
                    {"key": "A", "text": "很重視（希望10秒內開機）", "value": "fast"},
                    {"key": "B", "text": "有要求（希望30秒內開機）", "value": "moderate"},
                    {"key": "C", "text": "一般即可（1分鐘內可接受）", "value": "normal"},
                    {"key": "D", "text": "不在意開關機速度", "value": "no_care"}
                ]
            elif step == 9:
                options = self.slot_mapper.get_prompt_options_for_slot("screen_size")
            elif step == 10:
                options = self.slot_mapper.get_prompt_options_for_slot("brand_preference")
            elif step == 11:
                # 第11步：特殊需求（擴展）
                options = [
                    {"key": "A", "text": "需要觸控螢幕（繪圖、觸控操作）", "value": "touchscreen"},
                    {"key": "B", "text": "開關機和讀取軟體的速度要非常快", "value": "fast_boot"},
                    {"key": "C", "text": "希望是近一年內推出的最新款機種", "value": "latest_model"},
                    {"key": "D", "text": "對CPU或GPU的型號有特定要求", "value": "specific_specs"},
                    {"key": "E", "text": "沒有其他特殊需求", "value": "none"}
                ]

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
                        # 找到對應的prompt步驟 - 更新為11步驟系統
                        step_mapping = {
                            "usage_purpose": 1,
                            "budget_range": 2,
                            "release_time": 3,
                            "cpu_level": 4,
                            "gpu_level": 5,
                            "weight_requirement": 6,
                            "portability": 7,
                            "performance_features": 8,
                            "screen_size": 9,
                            "brand_preference": 10,
                            "special_requirement": 11
                        }
                        
                        if slot_name in step_mapping:
                            return self.get_prompt_style_question(step_mapping[slot_name], current_slots)
            
            # 否則按正常流程
            return self.get_next_question(current_slots)
            
        except Exception as e:
            self.logger.error(f"智能問題選擇失敗: {e}")
            return self.get_next_question(current_slots)
    
    def auto_infer_slots(self, current_slots: Dict[str, Any]) -> Dict[str, Any]:
        """
        基於現有槽位自動推斷其他槽位 - 新增智能推斷功能
        
        Args:
            current_slots: 當前已收集的槽位
            
        Returns:
            包含推斷槽位的更新字典
        """
        try:
            inferred_slots = current_slots.copy()
            
            # 基於用途推斷效能需求
            usage = current_slots.get("usage_purpose", "")
            if usage and "cpu_level" not in inferred_slots:
                cpu_level = self._infer_cpu_level_by_usage(usage)
                if cpu_level:
                    inferred_slots["cpu_level"] = cpu_level
                    self.logger.info(f"基於用途 {usage} 推斷CPU需求: {cpu_level}")
            
            if usage and "gpu_level" not in inferred_slots:
                gpu_level = self._infer_gpu_level_by_usage(usage)
                if gpu_level:
                    inferred_slots["gpu_level"] = gpu_level
                    self.logger.info(f"基於用途 {usage} 推斷GPU需求: {gpu_level}")
            
            # 基於攜帶性推斷重量要求
            portability = current_slots.get("portability", "")
            if portability and "weight_requirement" not in inferred_slots:
                weight_req = self._infer_weight_by_portability(portability)
                if weight_req:
                    inferred_slots["weight_requirement"] = weight_req
                    self.logger.info(f"基於攜帶性 {portability} 推斷重量需求: {weight_req}")
            
            # 基於重量要求推斷攜帶性
            weight_req = current_slots.get("weight_requirement", "")
            if weight_req and "portability" not in inferred_slots:
                portability_inf = self._infer_portability_by_weight(weight_req)
                if portability_inf:
                    inferred_slots["portability"] = portability_inf
                    self.logger.info(f"基於重量需求 {weight_req} 推斷攜帶性: {portability_inf}")
            
            # 基於預算推斷配置傾向
            budget = current_slots.get("budget_range", "")
            if budget:
                # 低預算用戶可能更關心實用性
                if budget == "budget" and "performance_features" not in inferred_slots:
                    inferred_slots["performance_features"] = "normal"
                    self.logger.info(f"基於低預算推斷開關機速度要求: normal")
                
                # 高預算用戶可能關心最新技術
                if budget == "premium" and "release_time" not in inferred_slots:
                    inferred_slots["release_time"] = "recent"
                    self.logger.info(f"基於高預算推斷推出時間偏好: recent")
            
            return inferred_slots
            
        except Exception as e:
            self.logger.error(f"自動推斷槽位失敗: {e}")
            return current_slots
    
    def _infer_cpu_level_by_usage(self, usage: str) -> Optional[str]:
        """基於用途推斷CPU需求"""
        usage_cpu_map = {
            "gaming": "high",
            "creative": "high", 
            "programming": "mid",
            "business": "mid",
            "document_processing": "basic",
            "entertainment": "mid",
            "general": "basic"
        }
        return usage_cpu_map.get(usage)
    
    def _infer_gpu_level_by_usage(self, usage: str) -> Optional[str]:
        """基於用途推斷GPU需求"""
        usage_gpu_map = {
            "gaming": "dedicated",
            "creative": "dedicated",
            "programming": "integrated",
            "business": "integrated",
            "document_processing": "integrated",
            "entertainment": "integrated",
            "general": "integrated"
        }
        return usage_gpu_map.get(usage)
    
    def _infer_weight_by_portability(self, portability: str) -> Optional[str]:
        """基於攜帶性推斷重量要求"""
        portability_weight_map = {
            "frequent": "light",
            "occasional": "standard",
            "desktop_replacement": "heavy"
        }
        return portability_weight_map.get(portability)
    
    def _infer_portability_by_weight(self, weight_req: str) -> Optional[str]:
        """基於重量要求推斷攜帶性"""
        weight_portability_map = {
            "ultra_light": "frequent",
            "light": "frequent", 
            "standard": "occasional",
            "heavy": "desktop_replacement"
        }
        return weight_portability_map.get(weight_req)
    
    def get_smart_transition(self, step: int, slot_name: str, current_slots: Dict[str, Any]) -> str:
        """
        獲取智能轉場詞 - 基於問題類型和上下文
        
        Args:
            step: 當前步驟
            slot_name: 槽位名稱
            current_slots: 當前槽位
            
        Returns:
            適當的轉場詞
        """
        try:
            import random
            
            # 第一題不需要轉場詞
            if step == 1:
                return ""
            
            # 根據問題類型選擇轉場詞類別
            if slot_name in ["cpu_level", "gpu_level", "performance_features"]:
                category = "performance"
            elif slot_name in ["weight_requirement", "portability", "screen_size"]:
                category = "physical"
            elif slot_name in ["brand_preference", "release_time", "special_requirement"]:
                category = "preference"
            elif step >= 10:  # 接近結束
                category = "closing"
            else:
                category = "basic"
            
            # 根據用戶回應選擇語調
            usage = current_slots.get("usage_purpose", "")
            if usage == "gaming":
                # 遊戲用戶可能更關心效能，使用更直接的語調
                if category == "performance":
                    transitions = ["關於遊戲效能，", "在硬體配置上，", "效能方面，"]
                else:
                    transitions = self.prompt_phrases["transitions"][category]
            elif usage == "business":
                # 商務用戶注重效率，使用簡潔的語調
                if category == "physical":
                    transitions = ["考慮到商務需求，", "在便攜性方面，", "關於實用性，"]
                else:
                    transitions = self.prompt_phrases["transitions"][category]
            else:
                transitions = self.prompt_phrases["transitions"][category]
            
            # 隨機選擇避免重複
            return random.choice(transitions)
            
        except Exception as e:
            self.logger.error(f"獲取智能轉場詞失敗: {e}")
            return "接下來，"
    
    def get_progress_info_text(self, current_slots: Dict[str, Any], current_step: int) -> str:
        """
        獲取進度資訊文字
        
        Args:
            current_slots: 當前槽位
            current_step: 當前步驟
            
        Returns:
            進度提示文字
        """
        try:
            progress = self.get_progress_info(current_slots)
            total = progress["total_questions"]
            completed = progress["completed_questions"] 
            percentage = progress["completion_percentage"]
            
            # 只在特定節點顯示進度
            if current_step in [3, 6, 9]:
                import random
                template = random.choice(self.prompt_phrases["progress_indicators"])
                return f"({template.format(current=completed, total=total, remaining=total-completed, percentage=int(percentage))})\n\n"
            
            return ""
            
        except Exception as e:
            self.logger.error(f"獲取進度資訊失敗: {e}")
            return ""
    
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