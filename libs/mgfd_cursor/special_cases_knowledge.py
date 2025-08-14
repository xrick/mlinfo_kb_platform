#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD 特殊案例知識庫模組
實現基於相似度匹配的特殊案例處理，防止循環和處理困難槽位檢測
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class SpecialCasesKnowledgeBase:
    """特殊案例知識庫類別"""
    
    def __init__(self, knowledge_file_path: str = "libs/mgfd_cursor/humandata/special_cases_knowledge.json"):
        """
        初始化特殊案例知識庫
        
        Args:
            knowledge_file_path: 知識庫JSON檔案路径
        """
        self.knowledge_file_path = Path(knowledge_file_path)
        self.knowledge_data = {}
        self.embedding_model = None
        self.cached_embeddings = {}
        self.loop_detection_history = {}
        self.logger = logging.getLogger(__name__)
        
        # 載入知識庫
        self._load_knowledge_base()
        
        # 初始化嵌入模型
        self._initialize_embedding_model()
    
    def _load_knowledge_base(self):
        """載入知識庫數據"""
        try:
            if self.knowledge_file_path.exists():
                with open(self.knowledge_file_path, 'r', encoding='utf-8') as f:
                    self.knowledge_data = json.load(f)
                self.logger.info(f"成功載入知識庫: {len(self.knowledge_data.get('categories', {}))} 個類別")
            else:
                self.logger.warning(f"知識庫文件不存在: {self.knowledge_file_path}")
                self.knowledge_data = {"categories": {}, "similarity_matching": {}, "loop_prevention": {}}
        except Exception as e:
            self.logger.error(f"載入知識庫失敗: {e}")
            self.knowledge_data = {"categories": {}, "similarity_matching": {}, "loop_prevention": {}}
    
    def _initialize_embedding_model(self):
        """初始化文本嵌入模型"""
        try:
            model_name = self.knowledge_data.get("similarity_matching", {}).get(
                "embedding_model", 
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            self.embedding_model = SentenceTransformer(model_name)
            self.logger.info(f"成功初始化嵌入模型: {model_name}")
        except Exception as e:
            self.logger.error(f"初始化嵌入模型失敗: {e}")
            self.embedding_model = None
    
    def find_matching_case(self, query: str, session_id: str = None) -> Optional[Dict[str, Any]]:
        """
        尋找匹配的特殊案例
        
        Args:
            query: 用戶查詢文本
            session_id: 會話ID（用於循環檢測）
            
        Returns:
            匹配的案例資訊，如果沒有匹配則返回None
        """
        try:
            # 檢查是否處於循環狀態
            if session_id and self._is_in_loop(session_id, query):
                return self._get_loop_breaking_case(query)
            
            best_match = None
            best_similarity = 0.0
            primary_threshold = self.knowledge_data.get("similarity_matching", {}).get("primary_threshold", 0.75)
            
            # 遍歷所有類別尋找匹配
            categories = self.knowledge_data.get("categories", {})
            for category_name, category_data in categories.items():
                cases = category_data.get("cases", [])
                
                for case in cases:
                    similarity = self._calculate_case_similarity(query, case)
                    
                    if similarity > best_similarity and similarity >= primary_threshold:
                        best_similarity = similarity
                        best_match = {
                            **case,
                            "matched_category": category_name,
                            "similarity_score": similarity
                        }
            
            # 如果找到匹配，記錄使用統計
            if best_match:
                self._record_case_usage(best_match)
                if session_id:
                    self._update_loop_detection_history(session_id, query, best_match)
            
            return best_match
            
        except Exception as e:
            self.logger.error(f"尋找匹配案例失敗: {e}")
            return None
    
    def _calculate_case_similarity(self, query: str, case: Dict[str, Any]) -> float:
        """
        計算查詢與案例的相似度
        
        Args:
            query: 用戶查詢
            case: 案例數據
            
        Returns:
            相似度分數 (0-1)
        """
        if not self.embedding_model:
            return self._fallback_similarity_calculation(query, case)
        
        try:
            # 準備比較文本列表
            comparison_texts = [case.get("customer_query", "")]
            comparison_texts.extend(case.get("query_variants", []))
            
            # 計算嵌入向量
            query_embedding = self._get_or_compute_embedding(query)
            case_embeddings = [self._get_or_compute_embedding(text) for text in comparison_texts if text]
            
            if not case_embeddings:
                return 0.0
            
            # 計算相似度
            similarities = []
            for case_embedding in case_embeddings:
                similarity = cosine_similarity([query_embedding], [case_embedding])[0][0]
                # 轉換 np.float32 到 Python native float 以避免序列化問題
                similarities.append(float(similarity))
            
            # 根據權重計算最終相似度
            weights = self.knowledge_data.get("similarity_matching", {}).get("similarity_weights", {
                "main_query": 0.7, "variants": 0.3
            })
            
            main_similarity = similarities[0] if similarities else 0.0
            variant_similarities = similarities[1:] if len(similarities) > 1 else []
            
            final_similarity = (
                main_similarity * weights.get("main_query", 0.7) +
                (max(variant_similarities) if variant_similarities else 0.0) * weights.get("variants", 0.3)
            )
            
            # 確保返回 Python native float 類型
            return float(final_similarity)
            
        except Exception as e:
            self.logger.error(f"計算相似度失敗: {e}")
            return self._fallback_similarity_calculation(query, case)
    
    def _get_or_compute_embedding(self, text: str) -> np.ndarray:
        """獲取或計算文本嵌入向量"""
        if text in self.cached_embeddings:
            return self.cached_embeddings[text]
        
        embedding = self.embedding_model.encode(text)
        self.cached_embeddings[text] = embedding
        return embedding
    
    def _fallback_similarity_calculation(self, query: str, case: Dict[str, Any]) -> float:
        """備用相似度計算（基於關鍵字匹配）"""
        try:
            query_lower = query.lower()
            comparison_texts = [case.get("customer_query", "")]
            comparison_texts.extend(case.get("query_variants", []))
            
            max_similarity = 0.0
            for text in comparison_texts:
                if not text:
                    continue
                
                text_lower = text.lower()
                # 簡單字符匹配
                common_chars = sum(1 for c in query_lower if c in text_lower)
                similarity = common_chars / max(len(query_lower), len(text_lower))
                max_similarity = max(max_similarity, similarity)
            
            return max_similarity
            
        except Exception as e:
            self.logger.error(f"備用相似度計算失敗: {e}")
            return 0.0
    
    def _is_in_loop(self, session_id: str, query: str) -> bool:
        """檢測是否處於循環狀態"""
        try:
            if session_id not in self.loop_detection_history:
                return False
            
            history = self.loop_detection_history[session_id]
            loop_config = self.knowledge_data.get("loop_prevention", {})
            
            max_repeats = loop_config.get("max_same_question_repeats", 2)
            detection_window = loop_config.get("loop_detection_window", 10)
            
            # 檢查最近的查詢歷史
            recent_queries = history[-detection_window:] if len(history) >= detection_window else history
            
            # 計算相似查詢的數量
            similar_count = 0
            for historical_query in recent_queries:
                if self._queries_are_similar(query, historical_query.get("query", "")):
                    similar_count += 1
            
            return similar_count >= max_repeats
            
        except Exception as e:
            self.logger.error(f"循環檢測失敗: {e}")
            return False
    
    def _queries_are_similar(self, query1: str, query2: str, threshold: float = 0.8) -> bool:
        """判斷兩個查詢是否相似"""
        if not query1 or not query2:
            return False
        
        if self.embedding_model:
            try:
                emb1 = self._get_or_compute_embedding(query1)
                emb2 = self._get_or_compute_embedding(query2)
                similarity = float(cosine_similarity([emb1], [emb2])[0][0])
                return similarity >= threshold
            except:
                pass
        
        # 備用方法：簡單字符匹配
        return query1.lower() == query2.lower()
    
    def _get_loop_breaking_case(self, query: str) -> Dict[str, Any]:
        """獲取打破循環的特殊案例"""
        return {
            "case_id": "LOOP_BREAKER",
            "priority": "high",
            "customer_query": query,
            "detected_intent": {
                "primary_slot": "loop_detected",
                "confidence": 0.95,
                "reasoning": "檢測到循環模式，啟動循環打破機制"
            },
            "recommended_response": {
                "response_type": "loop_breaking_consultation",
                "message": "我注意到我們可能在重複相同的問題。讓我換個方式來幫助您：",
                "funnel_question": {
                    "question_id": "loop_breaking_direct",
                    "question_text": "為了更直接地幫助您，請告訴我您的具體需求：",
                    "options": [
                        {
                            "option_id": "direct_consultation",
                            "label": "🎯 直接推薦",
                            "description": "根據目前資訊直接為您推薦產品",
                            "route": "direct_recommendation"
                        },
                        {
                            "option_id": "restart_consultation",
                            "label": "🔄 重新開始",
                            "description": "重新開始更詳細的諮詢過程",
                            "route": "restart_flow"
                        },
                        {
                            "option_id": "human_assistance",
                            "label": "👤 人工協助",
                            "description": "轉接專業人員為您服務",
                            "route": "human_handoff"
                        }
                    ]
                }
            },
            "matched_category": "loop_prevention",
            "similarity_score": 1.0,
            "loop_breaking": True
        }
    
    def _update_loop_detection_history(self, session_id: str, query: str, matched_case: Dict[str, Any]):
        """更新循環檢測歷史"""
        if session_id not in self.loop_detection_history:
            self.loop_detection_history[session_id] = []
        
        history_entry = {
            "query": query,
            "matched_case_id": matched_case.get("case_id", ""),
            "timestamp": datetime.now().isoformat(),
            "similarity_score": matched_case.get("similarity_score", 0.0)
        }
        
        self.loop_detection_history[session_id].append(history_entry)
        
        # 保持歷史記錄在合理範圍內
        max_history = 50
        if len(self.loop_detection_history[session_id]) > max_history:
            self.loop_detection_history[session_id] = self.loop_detection_history[session_id][-max_history:]
    
    def _record_case_usage(self, case: Dict[str, Any]):
        """記錄案例使用統計"""
        try:
            case_id = case.get("case_id", "")
            if not case_id:
                return
            
            # 更新知識庫中的使用統計
            categories = self.knowledge_data.get("categories", {})
            for category_name, category_data in categories.items():
                cases = category_data.get("cases", [])
                for i, stored_case in enumerate(cases):
                    if stored_case.get("case_id") == case_id:
                        stored_case["usage_count"] = stored_case.get("usage_count", 0) + 1
                        stored_case["last_used"] = datetime.now().isoformat()
                        break
            
            # 保存更新後的知識庫
            self._save_knowledge_base()
            
        except Exception as e:
            self.logger.error(f"記錄案例使用統計失敗: {e}")
    
    def get_case_response(self, matched_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        獲取匹配案例的推薦回應
        
        Args:
            matched_case: 匹配的案例
            
        Returns:
            格式化的回應數據
        """
        try:
            recommended_response = matched_case.get("recommended_response", {})
            
            # 基本回應結構
            response = {
                "type": "special_case_response",
                "case_id": matched_case.get("case_id", ""),
                "matched_category": matched_case.get("matched_category", ""),
                "similarity_score": matched_case.get("similarity_score", 0.0),
                "message": recommended_response.get("message", ""),
                "response_type": recommended_response.get("response_type", ""),
                "confidence": matched_case.get("detected_intent", {}).get("confidence", 0.8),
                "timestamp": datetime.now().isoformat()
            }
            
            # 添加漏斗問題（如果存在）
            if "funnel_question" in recommended_response:
                response["funnel_question"] = recommended_response["funnel_question"]
            
            # 添加推薦的槽位值（如果存在）
            detected_intent = matched_case.get("detected_intent", {})
            if "inferred_slots" in detected_intent:
                response["inferred_slots"] = detected_intent["inferred_slots"]
            
            # 添加特殊處理標記
            if matched_case.get("loop_breaking", False):
                response["loop_breaking"] = True
            
            # 添加後續問題（如果存在）
            if "follow_up_questions" in recommended_response:
                response["follow_up_questions"] = recommended_response["follow_up_questions"]
            
            return response
            
        except Exception as e:
            self.logger.error(f"獲取案例回應失敗: {e}")
            return {
                "type": "error",
                "message": "處理特殊案例時發生錯誤",
                "confidence": 0.0
            }
    
    def add_new_case(self, category: str, case_data: Dict[str, Any]) -> bool:
        """
        添加新的特殊案例
        
        Args:
            category: 案例類別
            case_data: 案例數據
            
        Returns:
            是否成功添加
        """
        try:
            categories = self.knowledge_data.get("categories", {})
            
            if category not in categories:
                categories[category] = {
                    "description": f"{category} 案例",
                    "total_cases": 0,
                    "cases": []
                }
            
            # 生成案例ID
            existing_cases = len(categories[category]["cases"])
            case_data["case_id"] = f"{category.upper()}_{existing_cases + 1:03d}"
            case_data["created_date"] = datetime.now().isoformat()
            case_data["usage_count"] = 0
            case_data["last_used"] = None
            
            # 添加案例
            categories[category]["cases"].append(case_data)
            categories[category]["total_cases"] = len(categories[category]["cases"])
            
            # 保存知識庫
            self._save_knowledge_base()
            
            self.logger.info(f"成功添加新案例: {case_data['case_id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加新案例失敗: {e}")
            return False
    
    def _save_knowledge_base(self):
        """保存知識庫到文件"""
        try:
            # 更新統計信息
            self._update_statistics()
            
            with open(self.knowledge_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存知識庫失敗: {e}")
    
    def _update_statistics(self):
        """更新知識庫統計信息"""
        try:
            categories = self.knowledge_data.get("categories", {})
            total_cases = sum(len(cat.get("cases", [])) for cat in categories.values())
            
            # 計算總體成功率
            all_success_rates = []
            total_matches = 0
            
            for category_data in categories.values():
                for case in category_data.get("cases", []):
                    success_rate = case.get("success_rate", 0.0)
                    usage_count = case.get("usage_count", 0)
                    if usage_count > 0:
                        all_success_rates.append(success_rate)
                        total_matches += usage_count
            
            avg_success_rate = np.mean(all_success_rates) if all_success_rates else 0.0
            
            # 更新統計信息
            stats = self.knowledge_data.get("usage_statistics", {})
            stats.update({
                "total_cases": total_cases,
                "total_successful_matches": total_matches,
                "average_success_rate": round(avg_success_rate, 3),
                "last_statistics_update": datetime.now().isoformat()
            })
            
            self.knowledge_data["usage_statistics"] = stats
            
        except Exception as e:
            self.logger.error(f"更新統計信息失敗: {e}")
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """獲取知識庫統計信息"""
        return self.knowledge_data.get("usage_statistics", {})
    
    def clear_loop_history(self, session_id: str = None):
        """清除循環檢測歷史"""
        if session_id:
            self.loop_detection_history.pop(session_id, None)
        else:
            self.loop_detection_history.clear()
        
        self.logger.info(f"清除循環歷史: {'所有會話' if not session_id else session_id}")