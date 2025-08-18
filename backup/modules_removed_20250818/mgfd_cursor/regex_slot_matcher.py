#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正則表達式槽位匹配引擎
提供彈性的槽位匹配機制，支援動態槽位學習
"""

import re
import json
import logging
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from difflib import SequenceMatcher
from pathlib import Path
from datetime import datetime


class MatchStrategy(Enum):
    """匹配策略"""
    REGEX = "regex"
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    FUZZY = "fuzzy"
    HYBRID = "hybrid"


class DynamicSlotLearner:
    """動態槽位學習器"""
    
    def __init__(self, config_file_path: str):
        """
        初始化動態槽位學習器
        
        Args:
            config_file_path: 配置文件路徑
        """
        self.config_file_path = Path(config_file_path)
        self.logger = logging.getLogger(__name__)
        self.learning_cache = {}
        self.pending_slots = []
        
        # 確保配置文件存在
        self._ensure_config_file_exists()
        
        self.logger.info(f"動態槽位學習器初始化完成，配置文件: {config_file_path}")
    
    def _ensure_config_file_exists(self):
        """確保配置文件存在"""
        if not self.config_file_path.exists():
            self.logger.warning(f"配置文件不存在，創建新文件: {self.config_file_path}")
            self._create_default_config()
    
    def _create_default_config(self):
        """創建默認配置文件"""
        default_config = {
            "slot_definitions": {},
            "metadata": {
                "version": "1.0",
                "created_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "description": "動態學習的槽位配置",
                "dynamic_learning": True
            },
            "learning_history": [],
            "pending_slots": []
        }
        
        try:
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            self.logger.info("成功創建默認配置文件")
        except Exception as e:
            self.logger.error(f"創建配置文件失敗: {e}")
    
    def load_config(self) -> Dict[str, Any]:
        """載入配置文件"""
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            self.logger.error(f"載入配置文件失敗: {e}")
            return {"slot_definitions": {}, "metadata": {}}
    
    def save_config(self, config: Dict[str, Any]):
        """保存配置文件"""
        try:
            # 更新元數據
            config["metadata"]["last_updated"] = datetime.now().isoformat()
            
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.logger.info("配置文件保存成功")
        except Exception as e:
            self.logger.error(f"保存配置文件失敗: {e}")
    
    def add_new_slot(self, slot_name: str, slot_value: str, user_input: str, 
                    confidence: float = 0.8, learning_source: str = "dynamic_learning") -> bool:
        """
        添加新的槽位值
        
        Args:
            slot_name: 槽位名稱
            slot_value: 槽位值
            user_input: 用戶輸入文本
            confidence: 置信度
            learning_source: 學習來源
            
        Returns:
            是否成功添加
        """
        try:
            self.logger.info(f"嘗試添加新槽位: {slot_name}={slot_value}")
            
            # 載入當前配置
            config = self.load_config()
            
            # 檢查槽位是否已存在
            if slot_name not in config["slot_definitions"]:
                # 創建新的槽位定義
                config["slot_definitions"][slot_name] = self._create_slot_definition(slot_name)
            
            slot_def = config["slot_definitions"][slot_name]
            
            # 檢查值是否已存在
            if "synonyms" not in slot_def:
                slot_def["synonyms"] = {}
            
            if slot_value not in slot_def["synonyms"]:
                # 創建新的值定義
                slot_def["synonyms"][slot_value] = self._create_value_synonyms(slot_value, user_input)
                
                # 更新驗證規則
                if "validation_rules" in slot_def and "allowed_values" in slot_def["validation_rules"]:
                    slot_def["validation_rules"]["allowed_values"].append(slot_value)
                
                # 記錄學習歷史
                learning_record = {
                    "timestamp": datetime.now().isoformat(),
                    "slot_name": slot_name,
                    "slot_value": slot_value,
                    "user_input": user_input,
                    "confidence": confidence,
                    "learning_source": learning_source,
                    "action": "add_new_value"
                }
                
                if "learning_history" not in config:
                    config["learning_history"] = []
                config["learning_history"].append(learning_record)
                
                # 保存配置
                self.save_config(config)
                
                self.logger.info(f"成功添加新槽位值: {slot_name}={slot_value}")
                return True
            else:
                self.logger.info(f"槽位值已存在: {slot_name}={slot_value}")
                return False
                
        except Exception as e:
            self.logger.error(f"添加新槽位失敗: {e}")
            return False
    
    def _create_slot_definition(self, slot_name: str) -> Dict[str, Any]:
        """創建新的槽位定義"""
        return {
            "name": slot_name,
            "type": "enum",
            "required": False,
            "priority": 5,  # 較低優先級
            "description": f"動態學習的槽位: {slot_name}",
            "default_value": None,
            "validation_rules": {
                "allowed_values": [],
                "min_length": 1,
                "max_length": 50
            },
            "collection_prompt": f"請告訴我關於{slot_name}的更多信息？",
            "follow_up_questions": {},
            "matching_strategies": {
                "primary": "hybrid",
                "fallback": "keyword",
                "weights": {
                    "regex": 0.4,
                    "keyword": 0.35,
                    "semantic": 0.25
                }
            },
            "synonyms": {},
            "created_date": datetime.now().isoformat(),
            "learning_source": "dynamic_learning"
        }
    
    def _create_value_synonyms(self, slot_value: str, user_input: str) -> Dict[str, Any]:
        """創建新的值同義詞"""
        # 從用戶輸入中提取關鍵詞
        keywords = self._extract_keywords_from_input(user_input, slot_value)
        
        # 生成正則表達式模式
        regex_patterns = self._generate_regex_patterns(keywords, slot_value)
        
        # 生成語義術語
        semantic_terms = self._generate_semantic_terms(slot_value, keywords)
        
        return {
            "keywords": keywords,
            "regex": regex_patterns,
            "semantic": semantic_terms,
            "fuzzy_match": keywords,  # 使用關鍵詞作為模糊匹配
            "confidence": 0.8,
            "learning_source": "dynamic_learning",
            "created_date": datetime.now().isoformat(),
            "user_input": user_input
        }
    
    def _extract_keywords_from_input(self, user_input: str, slot_value: str) -> List[str]:
        """從用戶輸入中提取關鍵詞"""
        keywords = []
        
        # 添加槽位值本身
        keywords.append(slot_value)
        
        # 提取相關詞彙
        words = user_input.split()
        for word in words:
            # 過濾掉常見的停用詞
            if len(word) > 1 and word not in ["的", "是", "有", "要", "想", "請", "幫", "我", "你", "他", "她", "它"]:
                keywords.append(word)
        
        # 去重並限制數量
        keywords = list(set(keywords))[:10]
        
        return keywords
    
    def _generate_regex_patterns(self, keywords: List[str], slot_value: str) -> List[str]:
        """生成正則表達式模式"""
        patterns = []
        
        # 為每個關鍵詞創建模式
        for keyword in keywords:
            if keyword:
                # 轉義特殊字符
                escaped_keyword = re.escape(keyword)
                patterns.append(escaped_keyword)
        
        # 為槽位值創建模式
        if slot_value:
            escaped_value = re.escape(slot_value)
            patterns.append(escaped_value)
        
        # 添加一些常見的變體模式
        if slot_value:
            patterns.append(f"{re.escape(slot_value)}.*筆電")
            patterns.append(f"筆電.*{re.escape(slot_value)}")
        
        return patterns[:5]  # 限制模式數量
    
    def _generate_semantic_terms(self, slot_value: str, keywords: List[str]) -> List[str]:
        """生成語義術語"""
        semantic_terms = []
        
        # 添加槽位值
        semantic_terms.append(slot_value)
        
        # 添加關鍵詞
        semantic_terms.extend(keywords[:3])
        
        # 添加一些語義相關的術語
        if "遊戲" in slot_value or "gaming" in slot_value.lower():
            semantic_terms.extend(["遊戲體驗", "遊戲效能", "遊戲需求"])
        elif "工作" in slot_value or "business" in slot_value.lower():
            semantic_terms.extend(["工作需求", "商務辦公", "企業使用"])
        elif "學習" in slot_value or "student" in slot_value.lower():
            semantic_terms.extend(["學習需求", "學生使用", "教育用途"])
        
        return list(set(semantic_terms))[:5]
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """獲取學習統計信息"""
        try:
            config = self.load_config()
            
            total_slots = len(config.get("slot_definitions", {}))
            total_values = sum(
                len(slot_def.get("synonyms", {})) 
                for slot_def in config.get("slot_definitions", {}).values()
            )
            learning_history = config.get("learning_history", [])
            
            return {
                "total_slots": total_slots,
                "total_values": total_values,
                "learning_records": len(learning_history),
                "last_learning": learning_history[-1]["timestamp"] if learning_history else None,
                "config_file": str(self.config_file_path)
            }
        except Exception as e:
            self.logger.error(f"獲取學習統計失敗: {e}")
            return {}


class RegexSlotMatcher:
    """正則表達式槽位匹配器"""
    
    def __init__(self, config: Dict[str, Any], config_file_path: str = None):
        """
        初始化匹配器
        
        Args:
            config: 槽位配置
            config_file_path: 配置文件路徑（用於動態學習）
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.compiled_patterns = {}
        self.match_cache = {}
        
        # 初始化動態學習器
        if config_file_path:
            self.dynamic_learner = DynamicSlotLearner(config_file_path)
            self.logger.info("動態學習功能已啟用")
        else:
            self.dynamic_learner = None
            self.logger.info("動態學習功能未啟用")
        
        # 預編譯正則表達式
        self._compile_patterns()
        
        self.logger.info("正則表達式槽位匹配器初始化完成")
    
    def _compile_patterns(self):
        """預編譯所有正則表達式模式"""
        try:
            slot_definitions = self.config.get("slot_definitions", {})
            
            for slot_name, slot_def in slot_definitions.items():
                if "synonyms" not in slot_def:
                    continue
                
                self.compiled_patterns[slot_name] = {}
                synonyms = slot_def["synonyms"]
                
                for value_name, value_synonyms in synonyms.items():
                    if "regex" not in value_synonyms:
                        continue
                    
                    patterns = value_synonyms["regex"]
                    compiled_patterns = []
                    
                    for pattern in patterns:
                        try:
                            # 編譯正則表達式，支援Unicode和忽略大小寫
                            compiled = re.compile(pattern, re.IGNORECASE | re.UNICODE)
                            compiled_patterns.append(compiled)
                        except re.error as e:
                            self.logger.warning(f"正則表達式編譯失敗: {pattern}, 錯誤: {e}")
                            continue
                    
                    if compiled_patterns:
                        self.compiled_patterns[slot_name][value_name] = compiled_patterns
            
            self.logger.info(f"成功編譯 {len(self.compiled_patterns)} 個槽位的正則表達式")
            
        except Exception as e:
            self.logger.error(f"編譯正則表達式失敗: {e}")
    
    def match_slots(self, text: str, target_slots: Optional[List[str]] = None, 
                   enable_learning: bool = True) -> Dict[str, Any]:
        """
        匹配槽位
        
        Args:
            text: 輸入文本
            target_slots: 目標槽位列表，如果為None則匹配所有槽位
            enable_learning: 是否啟用動態學習
            
        Returns:
            匹配結果
        """
        try:
            results = {}
            slot_definitions = self.config.get("slot_definitions", {})
            
            # 確定要匹配的槽位
            slots_to_match = target_slots if target_slots else slot_definitions.keys()
            
            for slot_name in slots_to_match:
                if slot_name not in slot_definitions:
                    continue
                
                slot_result = self._match_single_slot(text, slot_name)
                if slot_result:
                    results[slot_name] = slot_result
            
            # 如果沒有匹配到任何槽位且啟用了學習功能
            if not results and enable_learning and self.dynamic_learner:
                self.logger.info("未匹配到任何槽位，嘗試動態學習")
                learning_result = self._attempt_dynamic_learning(text)
                if learning_result:
                    results.update(learning_result)
            
            return {
                "success": True,
                "matches": results,
                "total_matches": len(results),
                "text": text,
                "learning_attempted": enable_learning and self.dynamic_learner is not None
            }
            
        except Exception as e:
            self.logger.error(f"槽位匹配失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "matches": {}
            }
    
    def _attempt_dynamic_learning(self, text: str) -> Dict[str, Any]:
        """
        嘗試動態學習新的槽位
        
        Args:
            text: 用戶輸入文本
            
        Returns:
            學習結果
        """
        try:
            # 分析文本，嘗試識別可能的槽位
            potential_slots = self._analyze_text_for_potential_slots(text)
            
            learning_results = {}
            
            for slot_name, slot_info in potential_slots.items():
                slot_value = slot_info["value"]
                confidence = slot_info["confidence"]
                
                # 嘗試添加新槽位
                if self.dynamic_learner.add_new_slot(slot_name, slot_value, text, confidence):
                    learning_results[slot_name] = {
                        "value": slot_value,
                        "confidence": confidence,
                        "learning_source": "dynamic_learning",
                        "newly_learned": True
                    }
                    
                    self.logger.info(f"動態學習成功: {slot_name}={slot_value}")
            
            return learning_results
            
        except Exception as e:
            self.logger.error(f"動態學習失敗: {e}")
            return {}
    
    def _analyze_text_for_potential_slots(self, text: str) -> Dict[str, Any]:
        """
        分析文本，識別潛在的槽位
        
        Args:
            text: 用戶輸入文本
            
        Returns:
            潛在槽位信息
        """
        potential_slots = {}
        
        # 簡單的文本分析邏輯
        words = text.split()
        
        # 識別可能的品牌名稱
        brand_keywords = ["華碩", "宏碁", "聯想", "惠普", "戴爾", "蘋果", "asus", "acer", "lenovo", "hp", "dell", "apple"]
        for word in words:
            if word.lower() in [brand.lower() for brand in brand_keywords]:
                potential_slots["brand_preference"] = {
                    "value": word.lower(),
                    "confidence": 0.8
                }
                break
        
        # 識別可能的預算範圍
        budget_patterns = [
            (r"(\d+)[-~](\d+)萬", "budget_range"),
            (r"便宜|平價|經濟", "budget_range"),
            (r"高級|高端|豪華", "budget_range")
        ]
        
        for pattern, slot_name in budget_patterns:
            match = re.search(pattern, text)
            if match:
                if slot_name == "budget_range":
                    if "便宜" in text or "平價" in text:
                        value = "budget"
                    elif "高級" in text or "高端" in text:
                        value = "premium"
                    else:
                        value = "mid_range"
                    
                    potential_slots[slot_name] = {
                        "value": value,
                        "confidence": 0.7
                    }
                break
        
        # 識別可能的使用目的
        usage_patterns = [
            (r"遊戲|gaming|打遊戲", "usage_purpose", "gaming"),
            (r"工作|business|辦公", "usage_purpose", "business"),
            (r"學習|student|上課", "usage_purpose", "student"),
            (r"創意|creative|設計", "usage_purpose", "creative"),
            (r"一般|general|日常", "usage_purpose", "general")
        ]
        
        for pattern, slot_name, value in usage_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                potential_slots[slot_name] = {
                    "value": value,
                    "confidence": 0.8
                }
                break
        
        return potential_slots
    
    def add_new_slot(self, slot_name: str, slot_value: str, user_input: str, 
                    confidence: float = 0.8) -> bool:
        """
        添加新槽位（對外接口）
        
        Args:
            slot_name: 槽位名稱
            slot_value: 槽位值
            user_input: 用戶輸入文本
            confidence: 置信度
            
        Returns:
            是否成功添加
        """
        if not self.dynamic_learner:
            self.logger.warning("動態學習功能未啟用")
            return False
        
        return self.dynamic_learner.add_new_slot(slot_name, slot_value, user_input, confidence)
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """獲取學習統計信息"""
        if not self.dynamic_learner:
            return {"error": "動態學習功能未啟用"}
        
        return self.dynamic_learner.get_learning_statistics()
    
    def _match_single_slot(self, text: str, slot_name: str) -> Optional[Dict[str, Any]]:
        """
        匹配單個槽位
        
        Args:
            text: 輸入文本
            slot_name: 槽位名稱
            
        Returns:
            匹配結果
        """
        try:
            slot_def = self.config["slot_definitions"][slot_name]
            synonyms = slot_def.get("synonyms", {})
            matching_strategies = slot_def.get("matching_strategies", {})
            
            best_match = None
            best_score = 0.0
            match_details = []
            
            # 使用配置的匹配策略
            primary_strategy = matching_strategies.get("primary", "hybrid")
            weights = matching_strategies.get("weights", {
                "regex": 0.4,
                "keyword": 0.35,
                "semantic": 0.25
            })
            
            for value_name, value_synonyms in synonyms.items():
                match_score = 0.0
                strategy_scores = {}
                
                # 正則表達式匹配
                if "regex" in weights and weights["regex"] > 0:
                    regex_score = self._regex_match(text, slot_name, value_name)
                    strategy_scores["regex"] = regex_score
                    match_score += regex_score * weights["regex"]
                
                # 關鍵詞匹配
                if "keyword" in weights and weights["keyword"] > 0:
                    keyword_score = self._keyword_match(text, value_synonyms)
                    strategy_scores["keyword"] = keyword_score
                    match_score += keyword_score * weights["keyword"]
                
                # 語義匹配
                if "semantic" in weights and weights["semantic"] > 0:
                    semantic_score = self._semantic_match(text, value_synonyms)
                    strategy_scores["semantic"] = semantic_score
                    match_score += semantic_score * weights["semantic"]
                
                # 模糊匹配
                fuzzy_score = self._fuzzy_match(text, value_synonyms)
                strategy_scores["fuzzy"] = fuzzy_score
                
                # 記錄匹配詳情
                match_detail = {
                    "value": value_name,
                    "score": match_score,
                    "strategy_scores": strategy_scores,
                    "matched_text": self._extract_matched_text(text, slot_name, value_name)
                }
                match_details.append(match_detail)
                
                # 更新最佳匹配
                if match_score > best_score:
                    best_score = match_score
                    best_match = match_detail
            
            # 檢查是否達到閾值
            confidence_threshold = self.config.get("validation_rules", {}).get("global", {}).get("confidence_threshold", 0.6)
            
            if best_match and best_match["score"] >= confidence_threshold:
                return {
                    "value": best_match["value"],
                    "confidence": best_match["score"],
                    "strategy_scores": best_match["strategy_scores"],
                    "matched_text": best_match["matched_text"],
                    "all_matches": match_details
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"匹配槽位 {slot_name} 失敗: {e}")
            return None
    
    def _regex_match(self, text: str, slot_name: str, value_name: str) -> float:
        """
        正則表達式匹配
        
        Args:
            text: 輸入文本
            slot_name: 槽位名稱
            value_name: 值名稱
            
        Returns:
            匹配分數 (0.0-1.0)
        """
        try:
            if slot_name not in self.compiled_patterns or value_name not in self.compiled_patterns[slot_name]:
                return 0.0
            
            patterns = self.compiled_patterns[slot_name][value_name]
            max_score = 0.0
            
            for pattern in patterns:
                try:
                    matches = pattern.findall(text)
                    if matches:
                        # 計算匹配分數
                        match_length = sum(len(match) for match in matches)
                        text_length = len(text)
                        score = min(1.0, match_length / text_length * 2)  # 加權分數
                        max_score = max(max_score, score)
                        
                except Exception as e:
                    self.logger.debug(f"正則表達式匹配失敗: {e}")
                    continue
            
            return max_score
            
        except Exception as e:
            self.logger.error(f"正則表達式匹配失敗: {e}")
            return 0.0
    
    def _keyword_match(self, text: str, value_synonyms: Dict[str, Any]) -> float:
        """
        關鍵詞匹配
        
        Args:
            text: 輸入文本
            value_synonyms: 值同義詞
            
        Returns:
            匹配分數 (0.0-1.0)
        """
        try:
            keywords = value_synonyms.get("keywords", [])
            if not keywords:
                return 0.0
            
            text_lower = text.lower()
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matched_keywords.append(keyword)
            
            if not matched_keywords:
                return 0.0
            
            # 計算匹配分數
            match_ratio = len(matched_keywords) / len(keywords)
            return min(1.0, match_ratio)
            
        except Exception as e:
            self.logger.error(f"關鍵詞匹配失敗: {e}")
            return 0.0
    
    def _semantic_match(self, text: str, value_synonyms: Dict[str, Any]) -> float:
        """
        語義匹配
        
        Args:
            text: 輸入文本
            value_synonyms: 值同義詞
            
        Returns:
            匹配分數 (0.0-1.0)
        """
        try:
            semantic_terms = value_synonyms.get("semantic", [])
            if not semantic_terms:
                return 0.0
            
            text_lower = text.lower()
            max_similarity = 0.0
            
            for term in semantic_terms:
                # 使用序列匹配器計算相似度
                similarity = SequenceMatcher(None, text_lower, term.lower()).ratio()
                max_similarity = max(max_similarity, similarity)
            
            return max_similarity
            
        except Exception as e:
            self.logger.error(f"語義匹配失敗: {e}")
            return 0.0
    
    def _fuzzy_match(self, text: str, value_synonyms: Dict[str, Any]) -> float:
        """
        模糊匹配
        
        Args:
            text: 輸入文本
            value_synonyms: 值同義詞
            
        Returns:
            匹配分數 (0.0-1.0)
        """
        try:
            fuzzy_terms = value_synonyms.get("fuzzy_match", [])
            if not fuzzy_terms:
                return 0.0
            
            text_lower = text.lower()
            max_similarity = 0.0
            
            for term in fuzzy_terms:
                # 計算模糊相似度
                similarity = SequenceMatcher(None, text_lower, term.lower()).ratio()
                max_similarity = max(max_similarity, similarity)
            
            return max_similarity
            
        except Exception as e:
            self.logger.error(f"模糊匹配失敗: {e}")
            return 0.0
    
    def _extract_matched_text(self, text: str, slot_name: str, value_name: str) -> List[str]:
        """
        提取匹配的文本片段
        
        Args:
            text: 輸入文本
            slot_name: 槽位名稱
            value_name: 值名稱
            
        Returns:
            匹配的文本片段列表
        """
        try:
            matched_texts = []
            
            if slot_name in self.compiled_patterns and value_name in self.compiled_patterns[slot_name]:
                patterns = self.compiled_patterns[slot_name][value_name]
                
                for pattern in patterns:
                    try:
                        matches = pattern.findall(text)
                        if matches:
                            matched_texts.extend(matches)
                    except Exception:
                        continue
            
            return list(set(matched_texts))  # 去重
            
        except Exception as e:
            self.logger.error(f"提取匹配文本失敗: {e}")
            return []
    
    def get_match_statistics(self) -> Dict[str, Any]:
        """
        獲取匹配統計信息
        
        Returns:
            統計信息
        """
        try:
            total_patterns = 0
            total_slots = len(self.compiled_patterns)
            
            for slot_patterns in self.compiled_patterns.values():
                for value_patterns in slot_patterns.values():
                    total_patterns += len(value_patterns)
            
            return {
                "total_slots": total_slots,
                "total_patterns": total_patterns,
                "cache_size": len(self.match_cache),
                "compiled_patterns": {
                    slot: len(patterns) for slot, patterns in self.compiled_patterns.items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"獲取統計信息失敗: {e}")
            return {}
    
    def clear_cache(self):
        """清除匹配緩存"""
        self.match_cache.clear()
        self.logger.info("匹配緩存已清除")
    
    def validate_patterns(self) -> Dict[str, Any]:
        """
        驗證所有正則表達式模式
        
        Returns:
            驗證結果
        """
        try:
            validation_results = {
                "valid_patterns": 0,
                "invalid_patterns": 0,
                "errors": []
            }
            
            slot_definitions = self.config.get("slot_definitions", {})
            
            for slot_name, slot_def in slot_definitions.items():
                if "synonyms" not in slot_def:
                    continue
                
                synonyms = slot_def["synonyms"]
                
                for value_name, value_synonyms in synonyms.items():
                    if "regex" not in value_synonyms:
                        continue
                    
                    patterns = value_synonyms["regex"]
                    
                    for pattern in patterns:
                        try:
                            re.compile(pattern, re.IGNORECASE | re.UNICODE)
                            validation_results["valid_patterns"] += 1
                        except re.error as e:
                            validation_results["invalid_patterns"] += 1
                            validation_results["errors"].append({
                                "slot": slot_name,
                                "value": value_name,
                                "pattern": pattern,
                                "error": str(e)
                            })
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"驗證模式失敗: {e}")
            return {"error": str(e)}


# 使用示例
if __name__ == "__main__":
    # 測試配置
    test_config = {
        "slot_definitions": {
            "usage_purpose": {
                "synonyms": {
                    "gaming": {
                        "keywords": ["遊戲", "打遊戲"],
                        "regex": ["遊戲|gaming|電競"],
                        "semantic": ["遊戲體驗"],
                        "fuzzy_match": ["game", "play"]
                    }
                }
            }
        }
    }
    
    # 創建匹配器（啟用動態學習）
    config_file_path = "libs/mgfd_cursor/humandata/default_slots_enhanced.json"
    matcher = RegexSlotMatcher(test_config, config_file_path)
    
    # 測試基本匹配
    result = matcher.match_slots("我想要一台遊戲筆電")
    print(f"基本匹配結果: {result}")
    
    # 測試動態學習
    print("\n=== 測試動態學習 ===")
    
    # 測試未知槽位
    unknown_result = matcher.match_slots("我想要一台華碩筆電", enable_learning=True)
    print(f"未知槽位匹配結果: {unknown_result}")
    
    # 手動添加新槽位
    print("\n=== 手動添加新槽位 ===")
    success = matcher.add_new_slot(
        "special_requirement", 
        "觸控螢幕", 
        "我需要有觸控螢幕的筆電", 
        0.9
    )
    print(f"手動添加結果: {success}")
    
    # 測試新添加的槽位
    new_slot_result = matcher.match_slots("我需要有觸控螢幕的筆電")
    print(f"新槽位匹配結果: {new_slot_result}")
    
    # 獲取學習統計信息
    learning_stats = matcher.get_learning_statistics()
    print(f"\n學習統計信息: {learning_stats}")
    
    # 獲取匹配統計信息
    stats = matcher.get_match_statistics()
    print(f"匹配統計信息: {stats}")
    
    # 驗證模式
    validation = matcher.validate_patterns()
    print(f"模式驗證結果: {validation}")
