#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD 混合檢索器系統
實現語義搜索 + 槽位過濾 + 相關性評分的綜合檢索策略
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .chunking import ProductChunkingEngine, ChunkingContext, ChunkingStrategyType
from .knowledge_base import NotebookKnowledgeBase


class HybridProductRetriever:
    """混合產品檢索器 - 實現RAG檢索策略"""
    
    def __init__(self, chunking_engine: Optional[ProductChunkingEngine] = None):
        """
        初始化混合檢索器
        
        Args:
            chunking_engine: 分塊引擎，如果不提供會自動創建
        """
        self.logger = logging.getLogger(__name__)
        
        # 初始化組件 - 使用Strategy模式
        if chunking_engine:
            self.chunking_context = ChunkingContext(chunking_engine)
        else:
            # 默認使用parent_child策略
            default_engine = ProductChunkingEngine()
            self.chunking_context = ChunkingContext(default_engine)
        
        self.chunking_engine = self.chunking_context.get_strategy()
        self.knowledge_base = NotebookKnowledgeBase()
        
        # 分塊存儲
        self.parent_chunks = {}  # {chunk_id: parent_chunk}
        self.child_chunks = []   # [child_chunk, ...]
        self.chunk_index = {}    # {product_id: [chunk_ids]}
        
        # 檢索配置
        self.retrieval_config = {
            "top_k_semantic": 20,
            "top_k_final": 5,
            "similarity_threshold": 0.6,
            "chunk_weights": {
                "performance": 0.3,
                "design": 0.25,
                "connectivity": 0.2,
                "business": 0.25
            },
            "ranking_weights": {
                "semantic_similarity": 0.4,
                "slot_match": 0.35,
                "popularity": 0.15,
                "completeness": 0.1
            }
        }
        
        # 檢索統計
        self.stats = {
            "total_retrievals": 0,
            "avg_retrieval_time": 0.0,
            "cache_hits": 0,
            "last_retrieval": None
        }
        
        # 簡單LRU緩存
        self.query_cache = {}
        self.cache_max_size = 100
        
        # 載入和處理所有產品
        self._initialize_chunks()
    
    def _initialize_chunks(self):
        """初始化產品分塊"""
        try:
            self.logger.info("開始初始化產品分塊...")
            
            # 載入所有產品
            products = self.knowledge_base.load_products()
            if not products:
                self.logger.warning("沒有載入到任何產品，檢索功能將受限")
                return
            
            # 批量創建分塊
            all_parents, all_children = self.chunking_engine.batch_create_chunks(products)
            
            # 建立索引
            self._build_chunk_index(all_parents, all_children)
            
            self.logger.info(f"分塊初始化完成: {len(self.parent_chunks)} 個父分塊, {len(self.child_chunks)} 個子分塊")
            
        except Exception as e:
            self.logger.error(f"初始化分塊失敗: {e}")
            raise
    
    def _build_chunk_index(self, parent_chunks: List[Dict], child_chunks: List[Dict]):
        """建立分塊索引"""
        # 存儲父分塊
        for parent in parent_chunks:
            self.parent_chunks[parent['chunk_id']] = parent
        
        # 存儲子分塊
        self.child_chunks = child_chunks
        
        # 建立產品ID到分塊的映射
        for parent in parent_chunks:
            product_id = parent['product_id']
            if product_id not in self.chunk_index:
                self.chunk_index[product_id] = {'parent': [], 'children': []}
            self.chunk_index[product_id]['parent'].append(parent['chunk_id'])
        
        for child in child_chunks:
            product_id = child['product_id']
            if product_id not in self.chunk_index:
                self.chunk_index[product_id] = {'parent': [], 'children': []}
            self.chunk_index[product_id]['children'].append(child['chunk_id'])
    
    def retrieve(self, query: str, user_slots: Optional[Dict[str, Any]] = None, 
                top_k: int = 5, strategy: str = "default") -> List[Dict[str, Any]]:
        """
        主要檢索方法
        
        Args:
            query: 查詢字符串
            user_slots: 用戶槽位信息
            top_k: 返回結果數量
            strategy: 檢索策略 ("default", "popularity_focused", "performance_focused")
            
        Returns:
            檢索結果列表
        """
        try:
            start_time = datetime.now()
            
            # 檢查緩存
            cache_key = self._generate_cache_key(query, user_slots or {}, top_k, strategy)
            if cache_key in self.query_cache:
                self.stats["cache_hits"] += 1
                self.logger.debug(f"緩存命中: {cache_key}")
                return self.query_cache[cache_key]
            
            # 執行檢索
            results = self._execute_retrieval(query, user_slots or {}, top_k, strategy)
            
            # 更新統計
            end_time = datetime.now()
            retrieval_time = (end_time - start_time).total_seconds()
            self._update_stats(retrieval_time)
            
            # 緩存結果
            self._cache_result(cache_key, results)
            
            self.logger.info(f"檢索完成: 查詢='{query}', 結果數={len(results)}, 用時={retrieval_time:.3f}s")
            
            return results
            
        except Exception as e:
            self.logger.error(f"檢索失敗: {e}")
            return []
    
    def _execute_retrieval(self, query: str, user_slots: Dict[str, Any], 
                          top_k: int, strategy: str) -> List[Dict[str, Any]]:
        """執行檢索邏輯"""
        
        # 步驟1: 語義檢索 (從child chunks開始)
        semantic_matches = self._semantic_retrieval(query, self.retrieval_config["top_k_semantic"])
        
        # 步驟2: 槽位過濾
        filtered_matches = self._slot_based_filtering(semantic_matches, user_slots)
        
        # 步驟3: 聚合到父分塊
        aggregated_products = self._aggregate_by_parent(filtered_matches)
        
        # 步驟4: 綜合排序
        final_ranking = self._comprehensive_ranking(aggregated_products, query, user_slots, strategy)
        
        # 步驟5: 格式化結果
        formatted_results = self._format_retrieval_results(final_ranking[:top_k])
        
        return formatted_results
    
    def _semantic_retrieval(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """語義檢索 - 從child chunks中搜索"""
        try:
            # 生成查詢嵌入
            query_embedding = self.chunking_engine.generate_embedding(query)
            
            similarities = []
            
            for chunk in self.child_chunks:
                try:
                    # 計算餘弦相似度
                    chunk_embedding = chunk.get('embedding')
                    if chunk_embedding is not None:
                        similarity = float(cosine_similarity(
                            query_embedding.reshape(1, -1),
                            chunk_embedding.reshape(1, -1)
                        )[0][0])
                        
                        similarities.append({
                            "chunk": chunk,
                            "parent_id": chunk.get("parent_id"),
                            "chunk_type": chunk["chunk_type"],
                            "similarity": similarity,
                            "focus": chunk["metadata"].get("focus", "unknown")
                        })
                    
                except Exception as e:
                    self.logger.debug(f"計算相似度失敗: {e}")
                    continue
            
            # 按相似度排序
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # 過濾低相似度結果
            threshold = self.retrieval_config["similarity_threshold"]
            filtered_similarities = [s for s in similarities if s['similarity'] >= threshold]
            
            return filtered_similarities[:top_k]
            
        except Exception as e:
            self.logger.error(f"語義檢索失敗: {e}")
            return []
    
    def _slot_based_filtering(self, semantic_matches: List[Dict], user_slots: Dict[str, Any]) -> List[Dict]:
        """基於用戶槽位進行過濾"""
        if not user_slots:
            return semantic_matches
        
        filtered = []
        
        for match in semantic_matches:
            try:
                # 獲取對應的父分塊元數據
                parent_id = match.get("parent_id")
                if not parent_id or parent_id not in self.parent_chunks:
                    continue
                
                parent_metadata = self.parent_chunks[parent_id]["metadata"]
                
                # 進行槽位匹配
                if self._match_user_slots(parent_metadata, user_slots):
                    filtered.append(match)
                    
            except Exception as e:
                self.logger.debug(f"槽位過濾錯誤: {e}")
                continue
        
        return filtered
    
    def _match_user_slots(self, parent_metadata: Dict[str, Any], user_slots: Dict[str, Any]) -> bool:
        """匹配用戶槽位"""
        
        # 預算範圍匹配
        if "budget_range" in user_slots:
            if not self._match_budget(parent_metadata.get("price_tier"), user_slots["budget_range"]):
                return False
        
        # 使用目的匹配
        if "usage_purpose" in user_slots:
            if not self._match_usage(parent_metadata.get("primary_usage"), user_slots["usage_purpose"]):
                return False
        
        # 品牌偏好匹配
        if "brand_preference" in user_slots:
            if not self._match_brand(parent_metadata.get("modelname", ""), user_slots["brand_preference"]):
                return False
        
        # 效能需求匹配
        if "performance_priority" in user_slots:
            if not self._match_performance_need(parent_metadata, user_slots["performance_priority"]):
                return False
        
        return True
    
    def _match_budget(self, price_tier: str, budget_range: str) -> bool:
        """匹配預算範圍"""
        budget_mapping = {
            "budget": ["budget"],
            "mid_range": ["budget", "mid_range"],
            "premium": ["mid_range", "premium"],
            "luxury": ["premium", "luxury"]
        }
        
        user_budget = budget_range.lower()
        if user_budget in budget_mapping:
            return price_tier in budget_mapping[user_budget]
        
        return True  # 如果無法匹配則允許通過
    
    def _match_usage(self, primary_usage: str, usage_purpose: str) -> bool:
        """匹配使用目的"""
        usage_mapping = {
            "gaming": ["gaming", "general"],
            "business": ["business", "general"],
            "creative": ["creative", "business", "general"],
            "general": ["general", "business", "creative"]
        }
        
        user_usage = usage_purpose.lower()
        if user_usage in usage_mapping:
            return primary_usage in usage_mapping[user_usage]
        
        return True
    
    def _match_brand(self, modelname: str, brand_preference: str) -> bool:
        """匹配品牌偏好"""
        # 這裡可以根據實際的品牌識別邏輯進行匹配
        # 由於目前的產品都是公司內部產品，暫時返回True
        return True
    
    def _match_performance_need(self, parent_metadata: Dict[str, Any], performance_priority: List[str]) -> bool:
        """匹配效能需求"""
        # 基於效能優先級進行匹配
        popularity_score = parent_metadata.get("popularity_score", 5.0)
        
        if "high_performance" in performance_priority:
            return popularity_score >= 7.0
        elif "gaming" in performance_priority:
            return popularity_score >= 6.0
        
        return True
    
    def _aggregate_by_parent(self, filtered_matches: List[Dict]) -> List[Dict[str, Any]]:
        """聚合到父分塊級別"""
        product_aggregation = {}
        
        for match in filtered_matches:
            parent_id = match.get("parent_id")
            if not parent_id or parent_id not in self.parent_chunks:
                continue
            
            if parent_id not in product_aggregation:
                parent_chunk = self.parent_chunks[parent_id]
                product_aggregation[parent_id] = {
                    "parent_chunk": parent_chunk,
                    "parent_metadata": parent_chunk["metadata"],
                    "matching_children": [],
                    "max_similarity": 0.0,
                    "avg_similarity": 0.0,
                    "chunk_type_scores": {}
                }
            
            # 添加匹配的子分塊
            agg = product_aggregation[parent_id]
            agg["matching_children"].append(match)
            
            # 更新最大相似度
            similarity = match["similarity"]
            if similarity > agg["max_similarity"]:
                agg["max_similarity"] = similarity
            
            # 記錄各類型分塊的最高分
            chunk_focus = match.get("focus", "unknown")
            if chunk_focus not in agg["chunk_type_scores"]:
                agg["chunk_type_scores"][chunk_focus] = 0.0
            if similarity > agg["chunk_type_scores"][chunk_focus]:
                agg["chunk_type_scores"][chunk_focus] = similarity
        
        # 計算平均相似度
        for agg in product_aggregation.values():
            if agg["matching_children"]:
                similarities = [m["similarity"] for m in agg["matching_children"]]
                agg["avg_similarity"] = sum(similarities) / len(similarities)
        
        return list(product_aggregation.values())
    
    def _comprehensive_ranking(self, products: List[Dict], query: str, user_slots: Dict[str, Any], 
                             strategy: str) -> List[Dict[str, Any]]:
        """綜合排序"""
        
        # 根據策略調整權重
        weights = self._get_strategy_weights(strategy)
        
        for product in products:
            # 語義相似度分數 (40%)
            semantic_score = product["max_similarity"]
            
            # 槽位匹配分數 (35%)
            slot_match_score = self._calculate_slot_match_score(product, user_slots)
            
            # 熱門度分數 (15%)
            popularity_score = product["parent_metadata"].get("popularity_score", 5.0) / 10.0
            
            # 完整性分數 (10%)
            completeness_score = self._assess_data_completeness(product)
            
            # 計算最終分數
            product["final_score"] = (
                semantic_score * weights["semantic_similarity"] +
                slot_match_score * weights["slot_match"] +
                popularity_score * weights["popularity"] +
                completeness_score * weights["completeness"]
            )
            
            # 添加調試信息
            product["score_breakdown"] = {
                "semantic": semantic_score,
                "slot_match": slot_match_score,
                "popularity": popularity_score,
                "completeness": completeness_score
            }
        
        # 按最終分數排序
        products.sort(key=lambda x: x["final_score"], reverse=True)
        
        return products
    
    def _get_strategy_weights(self, strategy: str) -> Dict[str, float]:
        """根據策略獲取權重"""
        base_weights = self.retrieval_config["ranking_weights"]
        
        if strategy == "popularity_focused":
            return {
                "semantic_similarity": 0.25,
                "slot_match": 0.25,
                "popularity": 0.40,
                "completeness": 0.10
            }
        elif strategy == "performance_focused":
            return {
                "semantic_similarity": 0.50,
                "slot_match": 0.40,
                "popularity": 0.05,
                "completeness": 0.05
            }
        else:
            return base_weights
    
    def _calculate_slot_match_score(self, product: Dict, user_slots: Dict[str, Any]) -> float:
        """計算槽位匹配分數"""
        if not user_slots:
            return 0.8  # 無槽位信息時給予中等分數
        
        metadata = product["parent_metadata"]
        match_count = 0
        total_slots = len(user_slots)
        
        # 檢查各種槽位匹配
        if "budget_range" in user_slots:
            if self._match_budget(metadata.get("price_tier"), user_slots["budget_range"]):
                match_count += 1
        
        if "usage_purpose" in user_slots:
            if self._match_usage(metadata.get("primary_usage"), user_slots["usage_purpose"]):
                match_count += 1
        
        if "brand_preference" in user_slots:
            if self._match_brand(metadata.get("modelname", ""), user_slots["brand_preference"]):
                match_count += 1
        
        # 計算匹配比例
        match_ratio = match_count / total_slots if total_slots > 0 else 0.8
        
        return min(match_ratio, 1.0)
    
    def _assess_data_completeness(self, product: Dict) -> float:
        """評估數據完整性"""
        metadata = product["parent_metadata"]
        
        # 檢查必要字段的完整性
        required_fields = ["modeltype", "modelname", "price_tier", "primary_usage"]
        complete_fields = sum(1 for field in required_fields if metadata.get(field))
        
        completeness = complete_fields / len(required_fields)
        
        # 加分項目
        bonus_fields = ["key_features", "target_users", "popularity_score"]
        bonus_points = sum(0.1 for field in bonus_fields if metadata.get(field))
        
        return min(completeness + bonus_points, 1.0)
    
    def _format_retrieval_results(self, ranked_products: List[Dict]) -> List[Dict[str, Any]]:
        """格式化檢索結果"""
        results = []
        
        for product in ranked_products:
            parent_chunk = product["parent_chunk"]
            metadata = product["parent_metadata"]
            
            # 提取原始產品數據
            raw_product = parent_chunk.get("raw_product", {})
            
            # 構建結果項
            result = {
                "id": metadata.get("modeltype", "unknown"),
                "modelname": metadata.get("modelname", "Unknown Model"),
                "modeltype": metadata.get("modeltype", "unknown"),
                "price_tier": metadata.get("price_tier", "standard"),
                "primary_usage": metadata.get("primary_usage", "general"),
                "popularity_score": metadata.get("popularity_score", 5.0),
                "key_features": metadata.get("key_features", []),
                "target_users": metadata.get("target_users", []),
                
                # 檢索相關信息
                "retrieval_score": product["final_score"],
                "max_similarity": product["max_similarity"],
                "matching_chunk_types": list(product["chunk_type_scores"].keys()),
                "score_breakdown": product.get("score_breakdown", {}),
                
                # 原始產品數據
                "raw_product": raw_product
            }
            
            results.append(result)
        
        return results
    
    # === 特殊檢索方法 ===
    
    def retrieve_popular_products(self, criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """檢索熱門產品"""
        try:
            # 基於父分塊的熱門度排序
            popular_parents = sorted(
                self.parent_chunks.values(),
                key=lambda x: x['metadata'].get('popularity_score', 0),
                reverse=True
            )
            
            # 應用條件過濾
            if criteria:
                filtered_parents = []
                for parent in popular_parents:
                    if self._match_user_slots(parent['metadata'], criteria):
                        filtered_parents.append(parent)
                popular_parents = filtered_parents
            
            # 格式化結果
            results = []
            for parent in popular_parents[:5]:  # 取前5個
                raw_product = parent.get("raw_product", {})
                metadata = parent["metadata"]
                
                result = {
                    "id": metadata.get("modeltype", "unknown"),
                    "modelname": metadata.get("modelname", "Unknown Model"),
                    "modeltype": metadata.get("modeltype", "unknown"),
                    "price_tier": metadata.get("price_tier", "standard"),
                    "primary_usage": metadata.get("primary_usage", "general"),
                    "popularity_score": metadata.get("popularity_score", 5.0),
                    "key_features": metadata.get("key_features", []),
                    "target_users": metadata.get("target_users", []),
                    "raw_product": raw_product
                }
                results.append(result)
            
            self.logger.info(f"檢索到 {len(results)} 個熱門產品")
            return results
            
        except Exception as e:
            self.logger.error(f"檢索熱門產品失敗: {e}")
            return []
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """純語義搜索"""
        return self.retrieve(query, user_slots={}, top_k=top_k, strategy="performance_focused")
    
    # === 緩存和統計方法 ===
    
    def _generate_cache_key(self, query: str, user_slots: Dict[str, Any], 
                           top_k: int, strategy: str) -> str:
        """生成緩存鍵"""
        import hashlib
        key_data = {
            "query": query,
            "slots": sorted(user_slots.items()) if user_slots else [],
            "top_k": top_k,
            "strategy": strategy
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _cache_result(self, cache_key: str, result: List[Dict]):
        """緩存結果"""
        if len(self.query_cache) >= self.cache_max_size:
            # 簡單的LRU：刪除最舊的項目
            oldest_key = next(iter(self.query_cache))
            del self.query_cache[oldest_key]
        
        self.query_cache[cache_key] = result
    
    def _update_stats(self, retrieval_time: float):
        """更新統計信息"""
        self.stats["total_retrievals"] += 1
        
        # 更新平均檢索時間
        total_time = self.stats["avg_retrieval_time"] * (self.stats["total_retrievals"] - 1) + retrieval_time
        self.stats["avg_retrieval_time"] = total_time / self.stats["total_retrievals"]
        
        self.stats["last_retrieval"] = datetime.now().isoformat()
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """獲取檢索統計"""
        stats = self.stats.copy()
        stats.update({
            "total_products": len(self.parent_chunks),
            "total_chunks": len(self.child_chunks),
            "cache_size": len(self.query_cache),
            "chunk_types": list(set(chunk["chunk_type"] for chunk in self.child_chunks))
        })
        return stats
    
    def clear_cache(self):
        """清空緩存"""
        self.query_cache.clear()
        self.logger.info("檢索緩存已清空")
    
    def reload_products(self):
        """重新載入產品數據"""
        try:
            self.logger.info("重新載入產品數據...")
            
            # 清空現有數據
            self.parent_chunks.clear()
            self.child_chunks.clear()
            self.chunk_index.clear()
            self.clear_cache()
            
            # 重新初始化
            self._initialize_chunks()
            
            self.logger.info("產品數據重新載入完成")
            
        except Exception as e:
            self.logger.error(f"重新載入產品數據失敗: {e}")
            raise