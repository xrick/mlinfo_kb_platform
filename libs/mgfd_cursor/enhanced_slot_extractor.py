#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD 增強型槽位提取器
實現LLM驅動的智能槽位分類系統
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

class EnhancedSlotExtractor:
    """增強型槽位提取器 - 支援智能分類未知槽位"""
    
    def __init__(self, llm_manager, slot_schema, confidence_threshold: float = 0.7):
        """
        初始化增強型槽位提取器
        
        Args:
            llm_manager: LLM管理器
            slot_schema: 槽位架構定義
            confidence_threshold: 置信度閾值
        """
        self.llm_manager = llm_manager
        self.slot_schema = slot_schema
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(__name__)
        
        # 槽位特徵定義
        self.slot_features = {
            "usage_purpose": {
                "description": "使用目的/用途",
                "keywords": ["做什麼", "用途", "目的", "需求", "工作", "遊戲", "學習", "創作", "辦公"],
                "examples": ["遊戲→gaming", "工作→business", "學習→student"]
            },
            "budget_range": {
                "description": "預算範圍/價格",
                "keywords": ["價格", "預算", "錢", "費用", "多少", "萬元", "便宜", "貴", "經濟"],
                "examples": ["便宜→budget", "中等價位→mid_range", "高級→premium"]
            },
            "performance_priority": {
                "description": "性能優先級/重視的硬體",
                "keywords": ["性能", "速度", "處理器", "顯卡", "記憶體", "CPU", "GPU", "RAM", "電池"],
                "examples": ["快速→cpu", "遊戲顯卡→gpu", "電池續航→battery"]
            },
            "portability_need": {
                "description": "便攜性需求/使用場景",
                "keywords": ["攜帶", "重量", "便攜", "移動", "外出", "輕薄", "大小"],
                "examples": ["輕薄→ultra_portable", "經常帶→balanced"]
            },
            "brand_preference": {
                "description": "品牌偏好",
                "keywords": ["品牌", "牌子", "廠商", "華碩", "宏碁", "聯想", "惠普", "戴爾", "蘋果"],
                "examples": ["華碩→asus", "蘋果→apple"]
            }
        }
    
    def extract_slots_with_classification(self, user_input: str, current_slots: Dict[str, Any]) -> Dict[str, Any]:
        """
        增強版槽位提取，包含未知槽位分類
        
        Args:
            user_input: 用戶輸入
            current_slots: 當前已填充的槽位
            
        Returns:
            提取的槽位信息
        """
        self.logger.info(f"增強型槽位提取，輸入: {user_input[:50]}...")
        
        # 1. 嘗試傳統關鍵詞匹配
        extracted_slots = self._traditional_slot_extraction(user_input, current_slots)
        
        # 2. 如果沒有提取到任何槽位，使用LLM分類
        if not extracted_slots:
            self.logger.info("傳統提取未找到槽位，使用LLM智能分類")
            classified_result = self._classify_unknown_input(user_input)
            
            if classified_result["confidence"] >= self.confidence_threshold:
                slot_name = classified_result["classified_slot"]
                slot_value = classified_result["extracted_value"]
                
                # 將分類結果轉換為標準槽位格式
                if slot_name != "unknown" and slot_value:
                    extracted_slots[slot_name] = self._normalize_slot_value(slot_name, slot_value)
                    self.logger.info(f"LLM分類成功: {slot_name} = {slot_value} (置信度: {classified_result['confidence']})")
            else:
                self.logger.warning(f"LLM分類置信度不足: {classified_result['confidence']}")
        
        # 3. 記錄分類結果以供學習改進
        self._log_classification_result(user_input, extracted_slots)
        
        return extracted_slots
    
    def _traditional_slot_extraction(self, user_input: str, current_slots: Dict[str, Any]) -> Dict[str, Any]:
        """
        傳統關鍵詞匹配槽位提取
        """
        extracted_slots = {}
        user_input_lower = user_input.lower()
        
        # 提取使用目的
        if "usage_purpose" not in current_slots:
            if any(word in user_input_lower for word in ["遊戲", "gaming", "打遊戲"]):
                extracted_slots["usage_purpose"] = "gaming"
            elif any(word in user_input_lower for word in ["工作", "business", "辦公", "商務", "文書"]):
                extracted_slots["usage_purpose"] = "business"
            elif any(word in user_input_lower for word in ["學習", "student", "上課", "作業"]):
                extracted_slots["usage_purpose"] = "student"
            elif any(word in user_input_lower for word in ["創意", "creative", "設計", "剪輯"]):
                extracted_slots["usage_purpose"] = "creative"
            elif any(word in user_input_lower for word in ["一般", "general", "日常", "上網"]):
                extracted_slots["usage_purpose"] = "general"
        
        # 提取預算範圍
        if "budget_range" not in current_slots:
            if any(word in user_input_lower for word in ["便宜", "budget", "經濟", "平價", "不要太高"]):
                extracted_slots["budget_range"] = "budget"
            elif any(word in user_input_lower for word in ["中等", "mid_range", "中端"]):
                extracted_slots["budget_range"] = "mid_range"
            elif any(word in user_input_lower for word in ["高級", "premium", "高端"]):
                extracted_slots["budget_range"] = "premium"
            elif any(word in user_input_lower for word in ["豪華", "luxury", "頂級"]):
                extracted_slots["budget_range"] = "luxury"
        
        # 提取性能優先級
        if "performance_priority" not in current_slots:
            performance_keywords = []
            if any(word in user_input_lower for word in ["快速", "cpu", "處理器", "運算"]):
                performance_keywords.append("cpu")
            if any(word in user_input_lower for word in ["顯卡", "gpu", "圖形", "遊戲性能"]):
                performance_keywords.append("gpu")
            if any(word in user_input_lower for word in ["記憶體", "ram", "容量"]):
                performance_keywords.append("ram")
            if any(word in user_input_lower for word in ["儲存", "硬碟", "ssd", "storage"]):
                performance_keywords.append("storage")
            if any(word in user_input_lower for word in ["電池", "續航", "battery"]):
                performance_keywords.append("battery")
            
            if performance_keywords:
                extracted_slots["performance_priority"] = performance_keywords
        
        # 提取便攜性需求
        if "portability_need" not in current_slots:
            if any(word in user_input_lower for word in ["輕薄", "ultra", "便攜", "小"]):
                extracted_slots["portability_need"] = "ultra_portable"
            elif any(word in user_input_lower for word in ["攜帶", "帶著", "移動", "咖啡廳"]):
                extracted_slots["portability_need"] = "balanced"
            elif any(word in user_input_lower for word in ["桌機", "desktop", "大螢幕", "性能優先"]):
                extracted_slots["portability_need"] = "desktop_replacement"
        
        # 提取品牌偏好
        if "brand_preference" not in current_slots:
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
    
    def _classify_unknown_input(self, user_input: str) -> Dict[str, Any]:
        """
        使用LLM分類未知輸入
        """
        prompt = self._generate_slot_classification_prompt(user_input)
        
        try:
            response = self.llm_manager.classify_slot(prompt)
            classification_result = json.loads(response)
            return classification_result
        except Exception as e:
            self.logger.error(f"LLM槽位分類失敗: {e}")
            return {
                "classified_slot": "unknown",
                "confidence": 0.0,
                "extracted_value": None,
                "reasoning": f"LLM分類失敗: {str(e)}",
                "alternative_slots": []
            }
    
    def _generate_slot_classification_prompt(self, user_input: str) -> str:
        """
        生成槽位分類提示詞
        """
        slot_descriptions = []
        for slot_name, features in self.slot_features.items():
            slot_descriptions.append(f"""
{slot_name} ({features['description']}):
- 關鍵特徵: {', '.join(features['keywords'])}
- 範例: {', '.join(features['examples'])}""")
        
        prompt = f"""
你是一位專業的語義分析專家，專門分析筆記型電腦購買意圖中的槽位信息。

用戶輸入: "{user_input}"

已知槽位類型定義:
{chr(10).join(slot_descriptions)}

請分析用戶輸入，判斷它最可能屬於哪個槽位類型，並提供：

回應格式 (必須是有效的JSON):
{{
  "classified_slot": "槽位名稱",
  "confidence": 0.85,
  "extracted_value": "提取的值",
  "reasoning": "分類理由",
  "alternative_slots": ["備選槽位1", "備選槽位2"]
}}

如果無法分類為任何已知槽位，請返回:
{{
  "classified_slot": "unknown",
  "confidence": 0.0,
  "extracted_value": null,
  "reasoning": "無法映射到已知槽位類型",
  "alternative_slots": []
}}

重要：只返回JSON，不要包含其他文字。
"""
        return prompt
    
    def _normalize_slot_value(self, slot_name: str, slot_value: str) -> Any:
        """
        標準化槽位值
        """
        if slot_name == "performance_priority":
            # 性能優先級可能是列表
            if isinstance(slot_value, str):
                return [slot_value]
            return slot_value
        
        return slot_value
    
    def _log_classification_result(self, user_input: str, extracted_slots: Dict[str, Any]):
        """
        記錄分類結果以供學習改進
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "extracted_slots": extracted_slots,
            "extraction_method": "enhanced" if extracted_slots else "failed"
        }
        
        self.logger.info(f"槽位提取結果: {log_entry}")