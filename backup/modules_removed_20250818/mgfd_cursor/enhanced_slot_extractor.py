#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD 增強型槽位提取器
實現LLM驅動的智能槽位分類系統，整合特殊案例知識庫
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from .special_cases_knowledge import SpecialCasesKnowledgeBase
from .similarity_engine import MGFDSimilarityEngine

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
        
        # 初始化特殊案例知識庫
        try:
            self.knowledge_base = SpecialCasesKnowledgeBase()
            self.logger.info("成功初始化特殊案例知識庫")
        except Exception as e:
            self.logger.warning(f"初始化特殊案例知識庫失敗: {e}")
            self.knowledge_base = None
        
        # 初始化相似度引擎
        try:
            self.similarity_engine = MGFDSimilarityEngine()
            self.logger.info("成功初始化相似度引擎")
        except Exception as e:
            self.logger.warning(f"初始化相似度引擎失敗: {e}")
            self.similarity_engine = None
        
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
    
    def extract_slots_with_classification(self, user_input: str, current_slots: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
        """
        增強版槽位提取，包含特殊案例知識庫和未知槽位分類
        
        Args:
            user_input: 用戶輸入
            current_slots: 當前已填充的槽位
            session_id: 會話ID（用於循環檢測）
            
        Returns:
            提取的槽位信息和特殊案例處理結果
        """
        self.logger.info(f"增強型槽位提取，輸入: {user_input[:50]}...")
        
        # 0. 首先檢查是否為funnel question選項回應
        if self._is_funnel_option_response(user_input):
            self.logger.info("檢測到funnel question選項回應，跳過特殊案例檢查")
            extracted_slots = self._extract_option_selection(user_input)
            return {
                "extracted_slots": extracted_slots,
                "extraction_method": "funnel_option_selection"
            }
        
        # 1. 檢查特殊案例知識庫
        special_case_result = self._check_special_cases(user_input, session_id)
        if special_case_result:
            self.logger.info(f"找到特殊案例匹配: {special_case_result['case_id']}")
            return {
                "extracted_slots": special_case_result.get("inferred_slots", {}),
                "special_case": special_case_result,
                "extraction_method": "special_case_knowledge"
            }
        
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
        
        return {
            "extracted_slots": extracted_slots,
            "extraction_method": "enhanced_extraction"
        }
    
    def _check_special_cases(self, user_input: str, session_id: str = None) -> Optional[Dict[str, Any]]:
        """
        檢查特殊案例知識庫匹配
        
        Args:
            user_input: 用戶輸入
            session_id: 會話ID
            
        Returns:
            特殊案例匹配結果，如果沒有匹配則返回None
        """
        if not self.knowledge_base:
            return None
        
        try:
            matched_case = self.knowledge_base.find_matching_case(user_input, session_id)
            if matched_case:
                return self.knowledge_base.get_case_response(matched_case)
            return None
        except Exception as e:
            self.logger.error(f"檢查特殊案例失敗: {e}")
            return None
    
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
    
    def add_special_case_from_interaction(self, user_input: str, successful_slots: Dict[str, Any], 
                                        category: str = "difficult_slot_detection") -> bool:
        """
        從成功的交互中添加新的特殊案例到知識庫
        
        Args:
            user_input: 用戶輸入
            successful_slots: 成功提取的槽位
            category: 案例類別
            
        Returns:
            是否成功添加
        """
        if not self.knowledge_base:
            return False
        
        try:
            # 構建新的案例數據
            case_data = {
                "priority": "medium",
                "customer_query": user_input,
                "query_variants": [],  # 可以之後由系統學習生成
                "detected_intent": {
                    "inferred_slots": successful_slots,
                    "confidence": 0.8,
                    "reasoning": "從用戶交互中學習得出"
                },
                "recommended_response": {
                    "response_type": "learned_case",
                    "message": "基於您的需求，我為您推薦：",
                    "skip_generic_usage_question": len(successful_slots) > 1
                },
                "success_rate": 0.8,
                "tags": ["learned_case", "user_generated"]
            }
            
            success = self.knowledge_base.add_new_case(category, case_data)
            if success:
                self.logger.info(f"成功添加新特殊案例: {user_input[:30]}...")
            
            return success
            
        except Exception as e:
            self.logger.error(f"添加特殊案例失敗: {e}")
            return False
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """獲取知識庫統計信息"""
        if self.knowledge_base:
            return self.knowledge_base.get_knowledge_base_stats()
        return {}
    
    def clear_session_loop_history(self, session_id: str):
        """清除特定會話的循環歷史"""
        if self.knowledge_base:
            self.knowledge_base.clear_loop_history(session_id)
    
    def _is_funnel_option_response(self, user_input: str) -> bool:
        """檢查輸入是否為funnel question選項回應"""
        try:
            user_input_lower = user_input.lower().strip()
            self.logger.debug(f"檢查funnel選項回應: '{user_input_lower}'")
            
            # 檢查是否為"選擇選項: xxx"格式
            option_patterns = [
                r"選擇選項[:：]\s*(\w+)",
                r"option[:：]\s*(\w+)",
                r"我選擇\s*(\w+)",
                r"選\s*(\w+)",
            ]
            
            for pattern in option_patterns:
                match = re.search(pattern, user_input_lower)
                if match:
                    self.logger.info(f"匹配到funnel選項模式 '{pattern}': {match.group(1)}")
                    return True
            
            # 檢查是否直接是選項值
            known_options = [
                "gaming", "business", "student", "creative", "general",
                "budget", "mid_range", "premium", "luxury",
                "ultra_portable", "balanced", "desktop_replacement"
            ]
            
            if user_input_lower in known_options:
                self.logger.info(f"檢測到直接選項值: '{user_input_lower}'")
                return True
            
            self.logger.debug(f"未檢測到funnel選項回應: '{user_input_lower}'")
            return False
            
        except Exception as e:
            self.logger.error(f"檢查funnel選項回應時發生錯誤: {e}")
            return False
    
    def _extract_option_selection(self, user_input: str) -> Dict[str, Any]:
        """從選項回應中提取槽位信息"""
        try:
            extracted_slots = {}
            user_input_lower = user_input.lower().strip()
            self.logger.debug(f"開始提取選項選擇: '{user_input_lower}'")
            
            # 提取選項值
            option_value = None
            
            # 從"選擇選項: xxx"格式中提取
            option_patterns = [
                r"選擇選項[:：]\s*(\w+)",
                r"option[:：]\s*(\w+)",
                r"我選擇\s*(\w+)",
                r"選\s*(\w+)",
            ]
            
            for pattern in option_patterns:
                match = re.search(pattern, user_input_lower)
                if match:
                    option_value = match.group(1)
                    self.logger.debug(f"使用模式 '{pattern}' 提取到選項值: '{option_value}'")
                    break
            
            # 如果沒有匹配到模式，檢查是否直接是選項值
            if not option_value:
                known_options = [
                    "gaming", "business", "student", "creative", "general",
                    "budget", "mid_range", "premium", "luxury", 
                    "ultra_portable", "balanced", "desktop_replacement"
                ]
                if user_input_lower in known_options:
                    option_value = user_input_lower
                    self.logger.debug(f"直接匹配到選項值: '{option_value}'")
            
            # 根據選項值確定槽位
            if option_value:
                # 使用目的選項
                if option_value in ["gaming", "business", "student", "creative", "general"]:
                    extracted_slots["usage_purpose"] = option_value
                    self.logger.info(f"提取usage_purpose槽位: {option_value}")
                
                # 預算範圍選項
                elif option_value in ["budget", "mid_range", "premium", "luxury"]:
                    extracted_slots["budget_range"] = option_value
                    self.logger.info(f"提取budget_range槽位: {option_value}")
                
                # 便攜性需求選項
                elif option_value in ["ultra_portable", "balanced", "desktop_replacement"]:
                    extracted_slots["portability_need"] = option_value
                    self.logger.info(f"提取portability_need槽位: {option_value}")
                else:
                    self.logger.warning(f"無法分類選項值到任何槽位: '{option_value}'")
            else:
                self.logger.warning(f"無法從輸入中提取選項值: '{user_input_lower}'")
            
            self.logger.info(f"從選項回應中提取的槽位: {extracted_slots}")
            return extracted_slots
            
        except Exception as e:
            self.logger.error(f"提取選項選擇時發生錯誤: {e}")
            return {}