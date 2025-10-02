#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
槽位映射系統 - 整合Prompt和Chunking搜尋
將prompt選項轉換為chunking搜尋參數
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum

class PromptOptionMapping:
    """Prompt選項到搜尋參數的映射"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 用途映射 (MGFD_collect_slot_value_prompt_v1.txt 第1步)
        self.usage_mapping = {
            "A": "document_processing",     # 日常文書處理與上網
            "B": "entertainment",           # 影音娛樂
            "C": "creative",               # 專業創作
            "D": "gaming",                 # 電競遊戲
            "E": "business",               # 商務辦公
            "F": "programming",            # 程式開發
            "G": "general"                 # 其他
        }
        
        # 預算映射 (第2步)
        self.budget_mapping = {
            "A": "budget",        # 25,000元 以下
            "B": "low_mid",       # 25,001 - 40,000元  
            "C": "mid_range",     # 40,001 - 55,000元
            "D": "high_mid",      # 55,001 - 70,000元
            "E": "premium"        # 70,000元 以上
        }
        
        # 攜帶性映射 (第3步)
        self.portability_mapping = {
            "A": "desktop_replacement",  # 幾乎都在固定地點使用
            "B": "occasional",           # 偶爾攜帶
            "C": "frequent"              # 經常攜帶
        }
        
        # 螢幕尺寸映射 (第4步)  
        self.screen_size_mapping = {
            "A": "13",         # 13吋及以下
            "B": "14",         # 14吋
            "C": "15",         # 15-16吋
            "D": "17"          # 17吋及以上
        }
        
        # 品牌映射 (第5步) - 注意：我們主要推薦公司產品
        self.brand_mapping = {
            "A": "apple",
            "B": "asus", 
            "C": "acer",
            "D": "dell",
            "E": "hp",
            "F": "lenovo",
            "G": "msi",
            "H": "no_preference",  # 沒有特定偏好
            "I": "others"
        }
        
        # 推出時間映射 (第3步)
        self.release_time_mapping = {
            "A": "latest",      # 最新款（半年內推出）
            "B": "recent",      # 較新款（1年內推出）
            "C": "mature",      # 成熟款（1-2年前推出，價格穩定）
            "D": "any"          # 不在意推出時間
        }
        
        # CPU效能映射 (第4步)
        self.cpu_level_mapping = {
            "A": "basic",       # 基本文書處理即可
            "B": "mid",         # 中等效能需求
            "C": "high",        # 高效能需求
            "D": "auto"         # 不確定，請幫我推薦
        }
        
        # GPU效能映射 (第5步)
        self.gpu_level_mapping = {
            "A": "integrated",   # 不需要，內建顯示卡即可
            "B": "dedicated",    # 需要獨立顯卡
            "C": "professional", # 需要專業顯卡
            "D": "auto"          # 不確定，請幫我評估
        }
        
        # 重量要求映射 (第6步)
        self.weight_requirement_mapping = {
            "A": "ultra_light",  # 越輕越好（1kg以下）
            "B": "light",        # 輕便即可（1-1.5kg）
            "C": "standard",     # 一般重量（1.5-2kg）
            "D": "heavy"         # 重量不重要（效能優先）
        }
        
        # 開關機速度映射 (第8步)
        self.performance_features_mapping = {
            "A": "fast",         # 很重視（希望10秒內開機）
            "B": "moderate",     # 有要求（希望30秒內開機）
            "C": "normal",       # 一般即可（1分鐘內可接受）
            "D": "no_care"       # 不在意開關機速度
        }
        
        # 其他需求映射 (第11步) - 擴展選項
        self.special_requirements_mapping = {
            "A": "touchscreen",      # 需要觸控螢幕
            "B": "fast_boot",        # 開關機和讀取軟體的速度要非常快
            "C": "latest_model",     # 近一年內推出的最新款機種
            "D": "specific_specs",   # 對CPU或GPU的型號有特定要求
            "E": "none"              # 沒有其他特殊需求
        }
    
    def convert_prompt_to_slots(self, prompt_responses: Dict[str, str]) -> Dict[str, Any]:
        """
        將prompt回應轉換為搜尋槽位 - 支援擴展的11步驟
        
        Args:
            prompt_responses: 用戶對prompt的回應 {"step_1": "A", "step_2": "C", ...}
            
        Returns:
            搜尋槽位字典
        """
        slots = {}
        
        try:
            # 處理用途
            if "step_1" in prompt_responses:
                usage_choice = prompt_responses["step_1"].upper()
                if usage_choice in self.usage_mapping:
                    slots["usage_purpose"] = self.usage_mapping[usage_choice]
                    self.logger.debug(f"用途映射: {usage_choice} -> {slots['usage_purpose']}")
            
            # 處理預算
            if "step_2" in prompt_responses:
                budget_choice = prompt_responses["step_2"].upper()
                if budget_choice in self.budget_mapping:
                    slots["budget_range"] = self.budget_mapping[budget_choice]
                    self.logger.debug(f"預算映射: {budget_choice} -> {slots['budget_range']}")
            
            # 處理推出時間偏好 - 新增
            if "step_3" in prompt_responses:
                release_choice = prompt_responses["step_3"].upper()
                if release_choice in self.release_time_mapping:
                    slots["release_time"] = self.release_time_mapping[release_choice]
                    self.logger.debug(f"推出時間映射: {release_choice} -> {slots['release_time']}")
            
            # 處理CPU效能需求 - 新增
            if "step_4" in prompt_responses:
                cpu_choice = prompt_responses["step_4"].upper()
                if cpu_choice in self.cpu_level_mapping:
                    slots["cpu_level"] = self.cpu_level_mapping[cpu_choice]
                    self.logger.debug(f"CPU效能映射: {cpu_choice} -> {slots['cpu_level']}")
            
            # 處理GPU效能需求 - 新增
            if "step_5" in prompt_responses:
                gpu_choice = prompt_responses["step_5"].upper()
                if gpu_choice in self.gpu_level_mapping:
                    slots["gpu_level"] = self.gpu_level_mapping[gpu_choice]
                    self.logger.debug(f"GPU效能映射: {gpu_choice} -> {slots['gpu_level']}")
            
            # 處理重量要求 - 新增
            if "step_6" in prompt_responses:
                weight_choice = prompt_responses["step_6"].upper()
                if weight_choice in self.weight_requirement_mapping:
                    slots["weight_requirement"] = self.weight_requirement_mapping[weight_choice]
                    self.logger.debug(f"重量要求映射: {weight_choice} -> {slots['weight_requirement']}")
            
            # 處理攜帶性 - 調整到第7步
            if "step_7" in prompt_responses:
                portability_choice = prompt_responses["step_7"].upper()
                if portability_choice in self.portability_mapping:
                    slots["portability"] = self.portability_mapping[portability_choice]
                    self.logger.debug(f"攜帶性映射: {portability_choice} -> {slots['portability']}")
            
            # 處理開關機速度要求 - 新增
            if "step_8" in prompt_responses:
                perf_choice = prompt_responses["step_8"].upper()
                if perf_choice in self.performance_features_mapping:
                    slots["performance_features"] = self.performance_features_mapping[perf_choice]
                    self.logger.debug(f"開關機速度映射: {perf_choice} -> {slots['performance_features']}")
            
            # 處理螢幕尺寸 - 調整到第9步
            if "step_9" in prompt_responses:
                screen_choice = prompt_responses["step_9"].upper()
                if screen_choice in self.screen_size_mapping:
                    slots["screen_size"] = self.screen_size_mapping[screen_choice]
                    self.logger.debug(f"螢幕尺寸映射: {screen_choice} -> {slots['screen_size']}")
            
            # 處理品牌偏好 - 調整到第10步
            if "step_10" in prompt_responses:
                brand_choice = prompt_responses["step_10"].upper()
                if brand_choice in self.brand_mapping:
                    slots["brand_preference"] = self.brand_mapping[brand_choice]
                    self.logger.debug(f"品牌映射: {brand_choice} -> {slots['brand_preference']}")
            
            # 處理特殊需求 - 調整到第11步，擴展選項
            if "step_11" in prompt_responses:
                special_choice = prompt_responses["step_11"].upper()
                if special_choice in self.special_requirements_mapping:
                    slots["special_requirement"] = self.special_requirements_mapping[special_choice]
                    self.logger.debug(f"特殊需求映射: {special_choice} -> {slots['special_requirement']}")
            
            self.logger.info(f"Prompt轉換為槽位完成: {len(slots)} 個槽位")
            return slots
            
        except Exception as e:
            self.logger.error(f"Prompt轉槽位映射失敗: {e}")
            return {}
    
    def enhance_slots_from_natural_input(self, natural_input: str, existing_slots: Dict[str, Any]) -> Dict[str, Any]:
        """
        從自然語言輸入增強槽位信息
        
        Args:
            natural_input: 用戶的自然語言輸入
            existing_slots: 現有槽位
            
        Returns:
            增強後的槽位
        """
        enhanced_slots = existing_slots.copy()
        natural_lower = natural_input.lower()
        
        try:
            # 用途相關關鍵詞
            if not enhanced_slots.get("usage_purpose"):
                if any(word in natural_lower for word in ["遊戲", "gaming", "電競"]):
                    enhanced_slots["usage_purpose"] = "gaming"
                elif any(word in natural_lower for word in ["文書", "辦公", "office", "工作"]):
                    enhanced_slots["usage_purpose"] = "document_processing"
                elif any(word in natural_lower for word in ["設計", "創作", "修圖", "影片"]):
                    enhanced_slots["usage_purpose"] = "creative"
                elif any(word in natural_lower for word in ["商務", "business", "會議"]):
                    enhanced_slots["usage_purpose"] = "business"
            
            # 便攜性相關關鍵詞
            if not enhanced_slots.get("portability"):
                if any(word in natural_lower for word in ["攜帶", "輕便", "輕薄", "方便帶"]):
                    enhanced_slots["portability"] = "frequent"
                elif any(word in natural_lower for word in ["固定", "桌面", "不移動"]):
                    enhanced_slots["portability"] = "desktop_replacement"
            
            # 重量相關關鍵詞
            if any(word in natural_lower for word in ["輕", "light", "薄", "便攜"]):
                enhanced_slots["weight_requirement"] = "light"
            
            # 預算相關關鍵詞
            if not enhanced_slots.get("budget_range"):
                if any(word in natural_lower for word in ["便宜", "經濟", "預算低", "省錢"]):
                    enhanced_slots["budget_range"] = "budget"
                elif any(word in natural_lower for word in ["高端", "頂級", "專業", "不在乎價錢"]):
                    enhanced_slots["budget_range"] = "premium"
            
            self.logger.debug(f"自然語言增強槽位: {natural_input[:50]}... -> 新增 {len(enhanced_slots) - len(existing_slots)} 個槽位")
            return enhanced_slots
            
        except Exception as e:
            self.logger.error(f"自然語言槽位增強失敗: {e}")
            return existing_slots
    
    def get_prompt_options_for_slot(self, slot_name: str) -> List[Dict[str, str]]:
        """
        獲取特定槽位對應的prompt選項
        
        Args:
            slot_name: 槽位名稱
            
        Returns:
            選項列表
        """
        if slot_name == "usage_purpose":
            return [
                {"key": "A", "text": "日常文書處理與上網", "value": "document_processing"},
                {"key": "B", "text": "影音娛樂", "value": "entertainment"},
                {"key": "C", "text": "專業創作 (例如：修圖、影片剪輯)", "value": "creative"},
                {"key": "D", "text": "電競遊戲", "value": "gaming"},
                {"key": "E", "text": "商務辦公", "value": "business"},
                {"key": "F", "text": "程式開發", "value": "programming"}
            ]
        elif slot_name == "budget_range":
            return [
                {"key": "A", "text": "25,000元 以下", "value": "budget"},
                {"key": "B", "text": "25,001 - 40,000元", "value": "low_mid"},
                {"key": "C", "text": "40,001 - 55,000元", "value": "mid_range"},
                {"key": "D", "text": "55,001 - 70,000元", "value": "high_mid"},
                {"key": "E", "text": "70,000元 以上", "value": "premium"}
            ]
        elif slot_name == "portability":
            return [
                {"key": "A", "text": "幾乎都在固定地點使用", "value": "desktop_replacement"},
                {"key": "B", "text": "偶爾攜帶 (每週數次)", "value": "occasional"},
                {"key": "C", "text": "經常攜帶 (幾乎每天)", "value": "frequent"}
            ]
        elif slot_name == "screen_size":
            return [
                {"key": "A", "text": "13吋及以下 (極致輕薄)", "value": "13"},
                {"key": "B", "text": "14吋 (平衡便攜與視野)", "value": "14"},
                {"key": "C", "text": "15-16吋 (標準尺寸)", "value": "15"},
                {"key": "D", "text": "17吋及以上 (桌機級體驗)", "value": "17"}
            ]
        elif slot_name == "brand_preference":
            return [
                {"key": "A", "text": "Apple", "value": "apple"},
                {"key": "B", "text": "ASUS", "value": "asus"},
                {"key": "C", "text": "Acer", "value": "acer"},
                {"key": "D", "text": "Dell", "value": "dell"},
                {"key": "E", "text": "HP", "value": "hp"},
                {"key": "F", "text": "Lenovo", "value": "lenovo"},
                {"key": "G", "text": "MSI", "value": "msi"},
                {"key": "H", "text": "沒有特定偏好", "value": "no_preference"},
                {"key": "I", "text": "其他", "value": "others"}
            ]
        elif slot_name == "special_requirement":
            return [
                {"key": "A", "text": "開關機和讀取軟體的速度要非常快", "value": "fast_boot"},
                {"key": "B", "text": "希望是近一年內推出的最新款機種", "value": "latest_model"},
                {"key": "C", "text": "對CPU或GPU的型號有特定要求", "value": "specific_specs"},
                {"key": "D", "text": "其他特殊需求 (請說明)", "value": "custom_needs"}
            ]
        else:
            return []
    
    def validate_prompt_response(self, step: str, response: str) -> bool:
        """
        驗證prompt回應是否有效 - 支援擴展的11步驟
        
        Args:
            step: 步驟 (step_1, step_2, ..., step_11)
            response: 用戶回應
            
        Returns:
            是否有效
        """
        mapping_dict = None
        
        if step == "step_1":
            mapping_dict = self.usage_mapping
        elif step == "step_2":
            mapping_dict = self.budget_mapping
        elif step == "step_3":
            mapping_dict = self.release_time_mapping
        elif step == "step_4":
            mapping_dict = self.cpu_level_mapping
        elif step == "step_5":
            mapping_dict = self.gpu_level_mapping
        elif step == "step_6":
            mapping_dict = self.weight_requirement_mapping
        elif step == "step_7":
            mapping_dict = self.portability_mapping
        elif step == "step_8":
            mapping_dict = self.performance_features_mapping
        elif step == "step_9":
            mapping_dict = self.screen_size_mapping
        elif step == "step_10":
            mapping_dict = self.brand_mapping
        elif step == "step_11":
            mapping_dict = self.special_requirements_mapping
        
        if mapping_dict:
            return response.upper() in mapping_dict
        
        return False
    
    def get_slot_priority(self, slots: Dict[str, Any]) -> List[str]:
        """
        根據已有槽位決定下一步詢問的優先順序
        
        Args:
            slots: 已有槽位
            
        Returns:
            優先順序槽位名稱列表
        """
        # 必問槽位
        required_slots = ["usage_purpose", "budget_range"]
        
        # 根據用途決定重要槽位
        usage = slots.get("usage_purpose", "")
        important_slots = []
        
        if usage == "gaming":
            important_slots = ["gpu_level", "cpu_level", "screen_size"]
        elif usage in ["document_processing", "business"]:
            important_slots = ["portability", "weight_requirement", "screen_size"]
        elif usage == "creative":
            important_slots = ["cpu_level", "gpu_level", "screen_size"]
        elif usage == "programming":
            important_slots = ["cpu_level", "screen_size", "portability"]
        else:
            important_slots = ["portability", "screen_size"]
        
        # 組合優先順序
        priority_slots = []
        
        # 先加入必問且未填的槽位
        for slot in required_slots:
            if slot not in slots:
                priority_slots.append(slot)
        
        # 再加入重要且未填的槽位
        for slot in important_slots:
            if slot not in slots and slot not in priority_slots:
                priority_slots.append(slot)
        
        # 最後加入其他未填槽位
        all_possible_slots = ["usage_purpose", "budget_range", "portability", "screen_size", 
                             "brand_preference", "special_requirement", "cpu_level", "gpu_level", 
                             "weight_requirement", "release_time", "performance_features"]
        
        for slot in all_possible_slots:
            if slot not in slots and slot not in priority_slots:
                priority_slots.append(slot)
        
        return priority_slots