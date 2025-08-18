#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD 相似度計算引擎
使用 sentence-transformers 進行語義相似度計算
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers 不可用，將使用備用方案")

class MGFDSimilarityEngine:
    """MGFD 相似度計算引擎"""
    
    def __init__(self, 
                 model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                 cache_size: int = 1000,
                 enable_cache: bool = True):
        """
        初始化相似度引擎
        
        Args:
            model_name: sentence-transformers 模型名稱
            cache_size: 緩存大小
            enable_cache: 是否啟用緩存
        """
        self.model_name = model_name
        self.cache_size = cache_size
        self.enable_cache = enable_cache
        self.logger = logging.getLogger(__name__)
        
        # 性能監控
        self.metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "average_response_time": 0.0,
            "error_count": 0,
            "model_load_time": 0.0
        }
        
        # 緩存
        self.cache = {}
        
        # 閾值配置
        self.thresholds = {
            "special_case_match": 0.75,
            "slot_synonym_match": 0.8,
            "loop_detection": 0.9,
            "general_similarity": 0.7
        }
        
        # 初始化模型
        self._initialize_model()
    
    def _initialize_model(self):
        """初始化 sentence-transformers 模型"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            self.logger.error("sentence-transformers 不可用")
            self.model = None
            return
        
        try:
            start_time = time.time()
            self.model = SentenceTransformer(self.model_name)
            self.metrics["model_load_time"] = time.time() - start_time
            
            self.logger.info(f"成功載入 sentence-transformers 模型: {self.model_name}")
            self.logger.info(f"模型載入時間: {self.metrics['model_load_time']:.2f}秒")
            
        except Exception as e:
            self.logger.error(f"載入 sentence-transformers 模型失敗: {e}")
            self.model = None
    
    def calculate_similarity(self, query: str, candidates: List[str]) -> List[float]:
        """
        計算查詢與候選項的相似度
        
        Args:
            query: 查詢文本
            candidates: 候選項列表
            
        Returns:
            相似度分數列表
        """
        if not self.model:
            self.logger.warning("模型未初始化，返回默認相似度")
            return [0.0] * len(candidates)
        
        start_time = time.time()
        
        try:
            # 檢查緩存
            cache_key = self._generate_cache_key(query, candidates)
            if self.enable_cache and cache_key in self.cache:
                self.metrics["cache_hits"] += 1
                self.logger.debug("使用緩存的相似度結果")
                return self.cache[cache_key]
            
            # 編碼查詢和候選項
            texts = [query] + candidates
            embeddings = self.model.encode(texts)
            
            # 計算餘弦相似度
            query_embedding = embeddings[0:1]
            candidate_embeddings = embeddings[1:]
            similarities = cosine_similarity(query_embedding, candidate_embeddings)[0]
            
            # 轉換為Python列表
            result = similarities.tolist()
            
            # 緩存結果
            if self.enable_cache:
                self._cache_result(cache_key, result)
            
            # 更新性能指標
            response_time = time.time() - start_time
            self._update_metrics(response_time)
            
            self.logger.debug(f"相似度計算完成，查詢: {query[:30]}..., 候選項數量: {len(candidates)}")
            return result
            
        except Exception as e:
            self.metrics["error_count"] += 1
            self.logger.error(f"相似度計算失敗: {e}")
            return [0.0] * len(candidates)
    
    def match_special_case(self, user_query: str, cases: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        匹配特殊案例
        
        Args:
            user_query: 用戶查詢
            cases: 特殊案例列表
            
        Returns:
            匹配的案例，如果沒有匹配則返回None
        """
        if not cases:
            return None
        
        # 提取案例查詢文本
        case_queries = []
        for case in cases:
            # 包含主查詢和變體查詢
            queries = [case.get("customer_query", "")]
            queries.extend(case.get("query_variants", []))
            case_queries.extend(queries)
        
        # 計算相似度
        similarities = self.calculate_similarity(user_query, case_queries)
        
        # 找到最佳匹配
        best_match_idx = np.argmax(similarities)
        best_similarity = similarities[best_match_idx]
        
        if best_similarity >= self.thresholds["special_case_match"]:
            # 找到對應的案例
            case_idx = best_match_idx // len(cases)
            if case_idx < len(cases):
                matched_case = cases[case_idx].copy()
                matched_case["similarity_score"] = float(best_similarity)
                self.logger.info(f"找到特殊案例匹配: {matched_case.get('case_id', 'unknown')}, 相似度: {best_similarity:.3f}")
                return matched_case
        
        return None
    
    def match_slot_synonyms(self, user_input: str, synonyms: List[str]) -> Optional[str]:
        """
        匹配槽位同義詞
        
        Args:
            user_input: 用戶輸入
            synonyms: 同義詞列表
            
        Returns:
            匹配的同義詞，如果沒有匹配則返回None
        """
        if not synonyms:
            return None
        
        similarities = self.calculate_similarity(user_input, synonyms)
        best_match_idx = np.argmax(similarities)
        best_similarity = similarities[best_match_idx]
        
        if best_similarity >= self.thresholds["slot_synonym_match"]:
            matched_synonym = synonyms[best_match_idx]
            self.logger.debug(f"找到同義詞匹配: {matched_synonym}, 相似度: {best_similarity:.3f}")
            return matched_synonym
        
        return None
    
    def detect_loop(self, current_query: str, history: List[str], window_size: int = 3) -> bool:
        """
        檢測循環
        
        Args:
            current_query: 當前查詢
            history: 歷史查詢列表
            window_size: 檢測窗口大小
            
        Returns:
            是否檢測到循環
        """
        if len(history) < 2:
            return False
        
        # 與最近N個查詢比較
        recent_queries = history[-window_size:]
        similarities = self.calculate_similarity(current_query, recent_queries)
        
        # 檢查是否有高相似度查詢
        high_similarity_count = sum(1 for sim in similarities if sim > self.thresholds["loop_detection"])
        
        if high_similarity_count >= 2:  # 至少2個高相似度查詢
            self.logger.warning(f"檢測到循環，當前查詢: {current_query[:30]}...")
            return True
        
        return False
    
    def find_most_similar(self, query: str, candidates: List[str], threshold: float = None) -> Optional[Tuple[str, float]]:
        """
        找到最相似的候選項
        
        Args:
            query: 查詢文本
            candidates: 候選項列表
            threshold: 相似度閾值
            
        Returns:
            (最相似候選項, 相似度分數) 的元組，如果沒有達到閾值則返回None
        """
        if not candidates:
            return None
        
        if threshold is None:
            threshold = self.thresholds["general_similarity"]
        
        similarities = self.calculate_similarity(query, candidates)
        best_match_idx = np.argmax(similarities)
        best_similarity = similarities[best_match_idx]
        
        if best_similarity >= threshold:
            return (candidates[best_match_idx], best_similarity)
        
        return None
    
    def _generate_cache_key(self, query: str, candidates: List[str]) -> str:
        """生成緩存鍵"""
        content = f"{query}:{','.join(sorted(candidates))}"
        return str(hash(content))
    
    def _cache_result(self, cache_key: str, result: List[float]):
        """緩存結果"""
        if len(self.cache) >= self.cache_size:
            # 簡單的LRU緩存：移除最舊的項目
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[cache_key] = result
    
    def _update_metrics(self, response_time: float):
        """更新性能指標"""
        self.metrics["total_queries"] += 1
        
        # 更新平均響應時間
        current_avg = self.metrics["average_response_time"]
        total_queries = self.metrics["total_queries"]
        self.metrics["average_response_time"] = (
            (current_avg * (total_queries - 1) + response_time) / total_queries
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        cache_hit_rate = (
            self.metrics["cache_hits"] / self.metrics["total_queries"] 
            if self.metrics["total_queries"] > 0 else 0.0
        )
        
        return {
            **self.metrics,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self.cache),
            "model_loaded": self.model is not None
        }
    
    def clear_cache(self):
        """清理緩存"""
        self.cache.clear()
        self.logger.info("相似度引擎緩存已清理")
    
    def update_thresholds(self, new_thresholds: Dict[str, float]):
        """更新閾值配置"""
        self.thresholds.update(new_thresholds)
        self.logger.info(f"更新相似度閾值: {new_thresholds}")
    
    def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        return {
            "model_loaded": self.model is not None,
            "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE,
            "cache_enabled": self.enable_cache,
            "metrics": self.get_metrics()
        }

