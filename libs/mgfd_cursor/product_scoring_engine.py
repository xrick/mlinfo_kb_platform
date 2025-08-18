#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD 產品評分引擎 - 多因子評分算法
實現智能的產品推薦評分系統
"""

import logging
import math
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

@dataclass
class ScoringDimension:
    """評分維度配置"""
    name: str
    base_weight: float
    min_score: float = 0.0
    max_score: float = 100.0
    is_critical: bool = False

class UserProfile(Enum):
    """用戶類型枚舉"""
    GAMING = "gaming"
    BUSINESS = "business" 
    CREATIVE = "creative"
    STUDENT = "student"
    GENERAL = "general"

class ProductScoringEngine:
    """
    產品多因子評分引擎
    實現基於用戶需求的智能產品評分與排序
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 評分維度定義
        self.dimensions = {
            "usage_match": ScoringDimension("用途匹配度", 0.25, is_critical=True),
            "performance_match": ScoringDimension("效能需求符合度", 0.20, is_critical=True),
            "budget_fit": ScoringDimension("預算適配度", 0.20, is_critical=True),
            "portability_match": ScoringDimension("攜帶性匹配度", 0.15),
            "brand_preference": ScoringDimension("品牌偏好度", 0.10),
            "special_requirements": ScoringDimension("特殊需求滿足度", 0.10)
        }
        
        # 用途到產品類型的映射
        self.usage_product_mapping = {
            "gaming": ["gaming", "high_performance", "desktop_replacement"],
            "creative": ["creative", "high_performance", "professional"],
            "programming": ["professional", "business", "high_performance"],
            "business": ["business", "professional", "portable"],
            "document_processing": ["business", "general", "portable"],
            "entertainment": ["general", "multimedia", "portable"],
            "general": ["general", "business", "portable"]
        }
        
        # CPU效能等級映射
        self.cpu_performance_levels = {
            "basic": {"score": 30, "suitable_for": ["document_processing", "general", "business"]},
            "mid": {"score": 60, "suitable_for": ["business", "programming", "entertainment"]},
            "high": {"score": 90, "suitable_for": ["gaming", "creative", "programming"]},
            "auto": {"score": 50, "suitable_for": ["general"]}
        }
        
        # GPU效能等級映射
        self.gpu_performance_levels = {
            "integrated": {"score": 30, "suitable_for": ["document_processing", "business", "general"]},
            "dedicated": {"score": 80, "suitable_for": ["gaming", "creative", "entertainment"]},
            "professional": {"score": 95, "suitable_for": ["creative", "programming"]},
            "auto": {"score": 50, "suitable_for": ["general"]}
        }
        
        # 預算等級映射 (新台幣)
        self.budget_ranges = {
            "budget": {"min": 0, "max": 25000, "optimal": 20000},
            "low_mid": {"min": 25001, "max": 40000, "optimal": 32000},
            "mid_range": {"min": 40001, "max": 55000, "optimal": 47000},
            "high_mid": {"min": 55001, "max": 70000, "optimal": 62000},
            "premium": {"min": 70001, "max": 999999, "optimal": 80000}
        }

    def score_product(self, product: Dict[str, Any], user_slots: Dict[str, Any]) -> Dict[str, Any]:
        """
        對單個產品進行多因子評分
        
        Args:
            product: 產品信息
            user_slots: 用戶需求槽位
            
        Returns:
            包含總分和各維度分數的評分結果
        """
        try:
            # 獲取動態權重
            weights = self._calculate_dynamic_weights(user_slots)
            
            # 計算各維度分數
            dimension_scores = {}
            dimension_scores["usage_match"] = self._score_usage_match(product, user_slots)
            dimension_scores["performance_match"] = self._score_performance_match(product, user_slots)
            dimension_scores["budget_fit"] = self._score_budget_fit(product, user_slots)
            dimension_scores["portability_match"] = self._score_portability_match(product, user_slots)
            dimension_scores["brand_preference"] = self._score_brand_preference(product, user_slots)
            dimension_scores["special_requirements"] = self._score_special_requirements(product, user_slots)
            
            # 計算加權總分
            total_score = 0
            weighted_scores = {}
            
            for dimension, score in dimension_scores.items():
                weight = weights.get(dimension, self.dimensions[dimension].base_weight)
                weighted_score = score * weight
                weighted_scores[dimension] = {
                    "raw_score": score,
                    "weight": weight,
                    "weighted_score": weighted_score
                }
                total_score += weighted_score
            
            # 應用獎勵和懲罰
            total_score = self._apply_bonuses_and_penalties(total_score, product, user_slots)
            
            # 限制分數範圍
            total_score = max(0, min(100, total_score))
            
            result = {
                "total_score": round(total_score, 2),
                "dimension_scores": weighted_scores,
                "weights_applied": weights,
                "evaluation_summary": self._generate_evaluation_summary(dimension_scores, user_slots)
            }
            
            self.logger.debug(f"產品 {product.get('modelname', 'Unknown')} 評分: {total_score:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"產品評分計算失敗: {e}")
            return {
                "total_score": 0.0,
                "dimension_scores": {},
                "weights_applied": {},
                "evaluation_summary": "評分計算失敗"
            }

    def _calculate_dynamic_weights(self, user_slots: Dict[str, Any]) -> Dict[str, float]:
        """
        根據用戶特徵動態調整評分權重
        
        Args:
            user_slots: 用戶需求槽位
            
        Returns:
            調整後的權重字典
        """
        weights = {dim: config.base_weight for dim, config in self.dimensions.items()}
        
        try:
            usage = user_slots.get("usage_purpose", "")
            budget = user_slots.get("budget_range", "")
            portability = user_slots.get("portability", "")
            
            # 基於用途調整權重
            if usage == "gaming":
                # 遊戲用戶更重視效能
                weights["performance_match"] = 0.35
                weights["usage_match"] = 0.20
                weights["budget_fit"] = 0.20
                weights["portability_match"] = 0.10
                weights["brand_preference"] = 0.10
                weights["special_requirements"] = 0.05
                
            elif usage in ["creative", "programming"]:
                # 創作和程式開發用戶重視效能和特殊需求
                weights["performance_match"] = 0.30
                weights["usage_match"] = 0.25
                weights["special_requirements"] = 0.15
                weights["budget_fit"] = 0.15
                weights["portability_match"] = 0.10
                weights["brand_preference"] = 0.05
                
            elif usage == "business":
                # 商務用戶重視攜帶性和品質
                weights["usage_match"] = 0.25
                weights["portability_match"] = 0.25
                weights["performance_match"] = 0.15
                weights["budget_fit"] = 0.20
                weights["brand_preference"] = 0.10
                weights["special_requirements"] = 0.05
                
            # 基於預算敏感度調整
            if budget == "budget":
                # 低預算用戶價格敏感
                weights["budget_fit"] = min(0.35, weights["budget_fit"] + 0.10)
                # 相應降低其他權重
                self._normalize_weights(weights)
                
            elif budget == "premium":
                # 高預算用戶更重視品質和特殊需求
                weights["performance_match"] = min(0.35, weights["performance_match"] + 0.05)
                weights["special_requirements"] = min(0.15, weights["special_requirements"] + 0.05)
                weights["budget_fit"] = max(0.10, weights["budget_fit"] - 0.10)
                
            # 基於攜帶需求調整
            if portability == "frequent":
                # 經常攜帶用戶重視便攜性
                weights["portability_match"] = min(0.25, weights["portability_match"] + 0.10)
                self._normalize_weights(weights)
                
            # 確保權重和為1
            self._normalize_weights(weights)
            
            self.logger.debug(f"動態權重調整結果: {weights}")
            return weights
            
        except Exception as e:
            self.logger.error(f"權重計算失敗: {e}")
            return {dim: config.base_weight for dim, config in self.dimensions.items()}

    def _normalize_weights(self, weights: Dict[str, float]) -> None:
        """標準化權重使總和為1"""
        total = sum(weights.values())
        if total > 0:
            for key in weights:
                weights[key] = weights[key] / total

    def _score_usage_match(self, product: Dict[str, Any], user_slots: Dict[str, Any]) -> float:
        """
        評分用途匹配度
        
        Args:
            product: 產品信息
            user_slots: 用戶槽位
            
        Returns:
            用途匹配分數 (0-100)
        """
        try:
            user_usage = user_slots.get("usage_purpose", "")
            if not user_usage:
                return 50.0  # 默認中等分數
            
            product_usage = product.get("primary_usage", "general")
            product_users = product.get("target_users", [])
            
            # 精確匹配
            if product_usage == user_usage:
                return 100.0
            
            # 檢查目標用戶群匹配
            usage_user_mapping = {
                "gaming": ["gamers", "enthusiasts"],
                "creative": ["creators", "designers", "professionals"],
                "programming": ["professionals", "developers"],
                "business": ["professionals", "enterprises"],
                "document_processing": ["students", "general_users", "professionals"],
                "entertainment": ["general_users", "students"],
                "general": ["general_users", "students"]
            }
            
            expected_users = usage_user_mapping.get(user_usage, [])
            match_count = sum(1 for user in expected_users if user in product_users)
            
            if match_count > 0:
                return 70.0 + (match_count / len(expected_users)) * 20.0
            
            # 相容性檢查
            compatibility_matrix = {
                "gaming": {"creative": 60, "programming": 40, "general": 30},
                "creative": {"gaming": 70, "programming": 80, "business": 60},
                "programming": {"creative": 70, "business": 80, "general": 50},
                "business": {"programming": 70, "document_processing": 90, "general": 60},
                "document_processing": {"business": 85, "general": 80, "entertainment": 40},
                "entertainment": {"general": 80, "document_processing": 50, "gaming": 40},
                "general": {"document_processing": 80, "business": 60, "entertainment": 70}
            }
            
            compatibility_score = compatibility_matrix.get(user_usage, {}).get(product_usage, 20)
            return compatibility_score
            
        except Exception as e:
            self.logger.error(f"用途匹配評分失敗: {e}")
            return 50.0

    def _score_performance_match(self, product: Dict[str, Any], user_slots: Dict[str, Any]) -> float:
        """
        評分效能需求符合度
        
        Args:
            product: 產品信息
            user_slots: 用戶槽位
            
        Returns:
            效能匹配分數 (0-100)
        """
        try:
            cpu_score = self._score_cpu_match(product, user_slots)
            gpu_score = self._score_gpu_match(product, user_slots)
            
            # CPU和GPU的權重根據用途調整
            usage = user_slots.get("usage_purpose", "")
            if usage == "gaming":
                # 遊戲更重視GPU
                return cpu_score * 0.4 + gpu_score * 0.6
            elif usage == "creative":
                # 創作需要均衡的CPU和GPU
                return cpu_score * 0.5 + gpu_score * 0.5
            elif usage == "programming":
                # 程式開發更重視CPU
                return cpu_score * 0.7 + gpu_score * 0.3
            else:
                # 一般用途CPU更重要
                return cpu_score * 0.8 + gpu_score * 0.2
                
        except Exception as e:
            self.logger.error(f"效能匹配評分失敗: {e}")
            return 50.0

    def _score_cpu_match(self, product: Dict[str, Any], user_slots: Dict[str, Any]) -> float:
        """評分CPU效能匹配"""
        try:
            user_cpu_level = user_slots.get("cpu_level", "auto")
            usage = user_slots.get("usage_purpose", "")
            
            # 從產品信息推斷CPU等級
            cpu_info = product.get("cpu", "").lower()
            product_cpu_level = self._infer_cpu_level_from_product(cpu_info)
            
            # 獲取用戶需求的CPU等級
            required_level = self._get_required_cpu_level(user_cpu_level, usage)
            
            # 計算匹配分數
            level_mapping = {"basic": 1, "mid": 2, "high": 3}
            required_numeric = level_mapping.get(required_level, 2)
            product_numeric = level_mapping.get(product_cpu_level, 2)
            
            if product_numeric >= required_numeric:
                # 滿足或超出需求
                if product_numeric == required_numeric:
                    return 95.0  # 完美匹配
                elif product_numeric == required_numeric + 1:
                    return 90.0  # 略微超出但很好
                else:
                    return 85.0  # 過度配置，輕微扣分
            else:
                # 不足需求
                gap = required_numeric - product_numeric
                return max(20.0, 70.0 - gap * 25.0)
                
        except Exception as e:
            self.logger.error(f"CPU匹配評分失敗: {e}")
            return 50.0

    def _score_gpu_match(self, product: Dict[str, Any], user_slots: Dict[str, Any]) -> float:
        """評分GPU效能匹配"""
        try:
            user_gpu_level = user_slots.get("gpu_level", "auto")
            usage = user_slots.get("usage_purpose", "")
            
            # 從產品信息推斷GPU等級
            gpu_info = product.get("gpu", "").lower()
            product_gpu_level = self._infer_gpu_level_from_product(gpu_info)
            
            # 獲取用戶需求的GPU等級
            required_level = self._get_required_gpu_level(user_gpu_level, usage)
            
            # 計算匹配分數
            level_mapping = {"integrated": 1, "dedicated": 2, "professional": 3}
            required_numeric = level_mapping.get(required_level, 1)
            product_numeric = level_mapping.get(product_gpu_level, 1)
            
            if product_numeric >= required_numeric:
                if product_numeric == required_numeric:
                    return 95.0
                elif product_numeric == required_numeric + 1:
                    return 90.0
                else:
                    return 85.0
            else:
                gap = required_numeric - product_numeric
                return max(10.0, 60.0 - gap * 30.0)
                
        except Exception as e:
            self.logger.error(f"GPU匹配評分失敗: {e}")
            return 50.0

    def _score_budget_fit(self, product: Dict[str, Any], user_slots: Dict[str, Any]) -> float:
        """
        評分預算適配度
        
        Args:
            product: 產品信息
            user_slots: 用戶槽位
            
        Returns:
            預算適配分數 (0-100)
        """
        try:
            user_budget = user_slots.get("budget_range", "mid_range")
            budget_config = self.budget_ranges.get(user_budget, self.budget_ranges["mid_range"])
            
            # 推斷產品價格（基於等級）
            product_price = self._estimate_product_price(product)
            
            min_budget = budget_config["min"]
            max_budget = budget_config["max"]
            optimal_price = budget_config["optimal"]
            
            if min_budget <= product_price <= max_budget:
                # 在預算範圍內
                distance_from_optimal = abs(product_price - optimal_price) / (max_budget - min_budget)
                return 100.0 - distance_from_optimal * 10.0  # 最高100分，距離最佳價位越遠扣分越多
                
            elif product_price < min_budget:
                # 低於預算下限（可能品質不足）
                under_ratio = (min_budget - product_price) / min_budget
                return max(60.0, 80.0 - under_ratio * 50.0)
                
            else:
                # 超出預算
                over_ratio = (product_price - max_budget) / max_budget
                if over_ratio <= 0.1:  # 超出10%以內
                    return 75.0 - over_ratio * 100.0
                elif over_ratio <= 0.2:  # 超出20%以內
                    return 50.0 - (over_ratio - 0.1) * 200.0
                else:  # 嚴重超出預算
                    return max(0.0, 30.0 - over_ratio * 100.0)
                    
        except Exception as e:
            self.logger.error(f"預算適配評分失敗: {e}")
            return 50.0

    def _score_portability_match(self, product: Dict[str, Any], user_slots: Dict[str, Any]) -> float:
        """
        評分攜帶性匹配度
        
        Args:
            product: 產品信息  
            user_slots: 用戶槽位
            
        Returns:
            攜帶性匹配分數 (0-100)
        """
        try:
            user_portability = user_slots.get("portability", "")
            user_weight_req = user_slots.get("weight_requirement", "")
            
            # 從產品信息推斷重量和尺寸
            product_weight = self._extract_weight_from_product(product)
            screen_size = self._extract_screen_size(product)
            
            # 根據用戶需求計算分數
            if user_portability == "frequent" or user_weight_req in ["ultra_light", "light"]:
                # 經常攜帶，需要輕便
                if product_weight <= 1.2:
                    return 100.0
                elif product_weight <= 1.5:
                    return 85.0
                elif product_weight <= 2.0:
                    return 60.0
                else:
                    return max(20.0, 50.0 - (product_weight - 2.0) * 15.0)
                    
            elif user_portability == "occasional" or user_weight_req == "standard":
                # 偶爾攜帶，標準重量可接受
                if product_weight <= 2.0:
                    return 95.0
                elif product_weight <= 2.5:
                    return 85.0
                elif product_weight <= 3.0:
                    return 70.0
                else:
                    return max(30.0, 60.0 - (product_weight - 3.0) * 10.0)
                    
            elif user_portability == "desktop_replacement" or user_weight_req == "heavy":
                # 桌面替代，重量不重要
                if product_weight >= 2.5 and screen_size >= 15.6:
                    return 100.0  # 大屏重機是優勢
                elif product_weight >= 2.0:
                    return 85.0
                else:
                    return 70.0  # 太輕可能效能不足
                    
            else:
                # 無明確要求，中等評分
                return 75.0
                
        except Exception as e:
            self.logger.error(f"攜帶性匹配評分失敗: {e}")
            return 75.0

    def _score_brand_preference(self, product: Dict[str, Any], user_slots: Dict[str, Any]) -> float:
        """
        評分品牌偏好度
        
        Args:
            product: 產品信息
            user_slots: 用戶槽位
            
        Returns:
            品牌偏好分數 (0-100)
        """
        try:
            user_preference = user_slots.get("brand_preference", "no_preference")
            
            if user_preference == "no_preference":
                return 80.0  # 無偏好時給予中高分
            
            # 從產品型號推斷品牌（基於已有的公司產品邏輯）
            product_brand = self._infer_brand_from_product(product)
            
            if product_brand == user_preference:
                return 100.0  # 完美匹配偏好品牌
            else:
                return 50.0   # 不是偏好品牌但不嚴重影響
                
        except Exception as e:
            self.logger.error(f"品牌偏好評分失敗: {e}")
            return 75.0

    def _score_special_requirements(self, product: Dict[str, Any], user_slots: Dict[str, Any]) -> float:
        """
        評分特殊需求滿足度
        
        Args:
            product: 產品信息
            user_slots: 用戶槽位
            
        Returns:
            特殊需求滿足分數 (0-100)
        """
        try:
            special_req = user_slots.get("special_requirement", "none")
            
            if special_req == "none":
                return 90.0  # 無特殊需求，高分
                
            if special_req == "fast_boot":
                # 檢查是否有SSD
                storage = product.get("storage", "").lower()
                if "ssd" in storage or "nvme" in storage:
                    return 95.0
                else:
                    return 40.0
                    
            elif special_req == "latest_model":
                # 檢查推出時間（這裡簡化處理）
                release_time_pref = user_slots.get("release_time", "any")
                if release_time_pref in ["latest", "recent"]:
                    return 85.0
                else:
                    return 70.0
                    
            elif special_req == "touchscreen":
                # 檢查是否支持觸控（簡化檢查）
                touchpanel = product.get("touchpanel", "").lower()
                if "touch" in touchpanel or touchpanel not in ["no data", ""]:
                    return 90.0
                else:
                    return 30.0
                    
            elif special_req == "specific_specs":
                # 用戶有特定規格要求，需要更詳細匹配
                return 75.0  # 中等分數，需要進一步確認
                
            else:
                return 80.0  # 其他需求給予中高分
                
        except Exception as e:
            self.logger.error(f"特殊需求評分失敗: {e}")
            return 75.0

    # === 輔助方法 ===

    def _apply_bonuses_and_penalties(self, base_score: float, product: Dict[str, Any], user_slots: Dict[str, Any]) -> float:
        """應用獎勵和懲罰調整"""
        adjusted_score = base_score
        
        try:
            # 熱門度獎勵
            popularity = product.get("popularity_score", 5.0)
            if popularity >= 8.0:
                adjusted_score += 2.0  # 高熱門度產品獎勵
            elif popularity <= 3.0:
                adjusted_score -= 2.0  # 低熱門度產品懲罰
            
            # 性價比獎勵
            price_tier = product.get("price_tier", "standard")
            usage = user_slots.get("usage_purpose", "")
            
            if price_tier == "budget" and usage in ["document_processing", "general"]:
                adjusted_score += 3.0  # 經濟型產品用於基本需求獎勵
            elif price_tier == "premium" and usage in ["gaming", "creative"]:
                adjusted_score += 2.0  # 高端產品用於專業需求獎勵
            
            return adjusted_score
            
        except Exception as e:
            self.logger.error(f"獎懲調整失敗: {e}")
            return base_score

    def _generate_evaluation_summary(self, dimension_scores: Dict[str, float], user_slots: Dict[str, Any]) -> str:
        """生成評價摘要"""
        try:
            summary_parts = []
            
            # 找出最高分和最低分的維度
            max_dim = max(dimension_scores.items(), key=lambda x: x[1])
            min_dim = min(dimension_scores.items(), key=lambda x: x[1])
            
            dim_names = {
                "usage_match": "用途匹配",
                "performance_match": "效能匹配", 
                "budget_fit": "預算適配",
                "portability_match": "攜帶便利",
                "brand_preference": "品牌偏好",
                "special_requirements": "特殊需求"
            }
            
            if max_dim[1] >= 80:
                summary_parts.append(f"✅ {dim_names.get(max_dim[0], max_dim[0])}表現優秀")
            
            if min_dim[1] <= 50:
                summary_parts.append(f"⚠️ {dim_names.get(min_dim[0], min_dim[0])}需要關注")
            
            return "；".join(summary_parts) if summary_parts else "整體表現平衡"
            
        except Exception as e:
            self.logger.error(f"評價摘要生成失敗: {e}")
            return "評價分析中"

    # === 產品信息推斷方法 ===
    
    def _infer_cpu_level_from_product(self, cpu_info: str) -> str:
        """從CPU信息推斷效能等級"""
        if any(term in cpu_info for term in ["i7", "i9", "ryzen 7", "ryzen 9"]):
            return "high"
        elif any(term in cpu_info for term in ["i5", "ryzen 5"]):
            return "mid"
        else:
            return "basic"

    def _infer_gpu_level_from_product(self, gpu_info: str) -> str:
        """從GPU信息推斷效能等級"""
        if any(term in gpu_info for term in ["rtx", "gtx", "radeon rx"]):
            return "dedicated"
        elif any(term in gpu_info for term in ["professional", "quadro", "workstation"]):
            return "professional"
        else:
            return "integrated"

    def _get_required_cpu_level(self, user_level: str, usage: str) -> str:
        """獲取用戶所需的CPU等級"""
        if user_level != "auto":
            return user_level
        
        # 根據用途推斷需求
        usage_cpu_map = {
            "gaming": "high",
            "creative": "high",
            "programming": "mid",
            "business": "mid", 
            "document_processing": "basic",
            "entertainment": "mid",
            "general": "basic"
        }
        return usage_cpu_map.get(usage, "mid")

    def _get_required_gpu_level(self, user_level: str, usage: str) -> str:
        """獲取用戶所需的GPU等級"""
        if user_level != "auto":
            return user_level
        
        usage_gpu_map = {
            "gaming": "dedicated",
            "creative": "dedicated",
            "programming": "integrated",
            "business": "integrated",
            "document_processing": "integrated", 
            "entertainment": "integrated",
            "general": "integrated"
        }
        return usage_gpu_map.get(usage, "integrated")

    def _estimate_product_price(self, product: Dict[str, Any]) -> float:
        """估算產品價格"""
        try:
            price_tier = product.get("price_tier", "standard")
            tier_prices = {
                "budget": 22000,
                "mid_range": 45000, 
                "premium": 75000,
                "standard": 35000
            }
            return tier_prices.get(price_tier, 35000)
        except Exception:
            return 35000

    def _extract_weight_from_product(self, product: Dict[str, Any]) -> float:
        """從產品信息提取重量"""
        try:
            struct_info = product.get("structconfig", "")
            if "kg" in struct_info.lower():
                # 簡化提取邏輯
                if "1.8" in struct_info:
                    return 1.8
                elif "2.1" in struct_info:
                    return 2.1
                elif "2.6" in struct_info:
                    return 2.6
                elif "1.6" in struct_info:
                    return 1.6
            return 2.0  # 默認重量
        except Exception:
            return 2.0

    def _extract_screen_size(self, product: Dict[str, Any]) -> float:
        """從產品信息提取螢幕尺寸"""
        try:
            lcd_info = product.get("lcd", "")
            if "16.0" in lcd_info:
                return 16.0
            elif "15.6" in lcd_info:
                return 15.6
            elif "14" in lcd_info:
                return 14.0
            return 15.6  # 默認尺寸
        except Exception:
            return 15.6

    def _infer_brand_from_product(self, product: Dict[str, Any]) -> str:
        """從產品信息推斷品牌"""
        # 由於這些是公司內部產品，統一處理
        return "company"  # 公司品牌

    def batch_score_products(self, products: List[Dict[str, Any]], user_slots: Dict[str, Any]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        批量評分產品列表
        
        Args:
            products: 產品列表
            user_slots: 用戶需求槽位
            
        Returns:
            按分數排序的 (產品, 評分結果) 元組列表
        """
        try:
            scored_products = []
            
            for product in products:
                score_result = self.score_product(product, user_slots)
                scored_products.append((product, score_result))
            
            # 按總分排序
            scored_products.sort(key=lambda x: x[1]["total_score"], reverse=True)
            
            self.logger.info(f"完成 {len(products)} 個產品的批量評分")
            return scored_products
            
        except Exception as e:
            self.logger.error(f"批量評分失敗: {e}")
            return []