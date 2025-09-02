"""
PromptSelector - 提示選擇器
基於對話狀態、用戶意圖和上下文智能選擇最合適的提示模板

選擇策略：
1. 狀態優先策略 - 根據對話狀態選擇提示
2. 意圖匹配策略 - 根據用戶意圖選擇提示
3. 混合策略 - 綜合考慮狀態、意圖、優先級
4. 回退策略 - 在無法匹配時的降級處理
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import re

from .PromptRegistry import PromptRegistry, PromptMetadata

logger = logging.getLogger(__name__)


class SelectionStrategy(Enum):
    """提示選擇策略"""
    STATE_FIRST = "state_first"         # 狀態優先
    INTENT_FIRST = "intent_first"       # 意圖優先
    HYBRID = "hybrid"                   # 混合策略
    PRIORITY_BASED = "priority_based"   # 基於優先級
    ROUND_ROBIN = "round_robin"         # 輪詢策略


@dataclass
class SelectionCriteria:
    """提示選擇條件"""
    state: Optional[str] = None                    # 對話狀態
    intent: Optional[str] = None                   # 用戶意圖
    category: Optional[str] = None                 # 提示分類
    language: str = "zh-TW"                       # 語言偏好
    context_keywords: List[str] = None            # 上下文關鍵詞
    user_profile: Dict[str, Any] = None           # 用戶畫像
    conversation_history: List[str] = None        # 對話歷史
    exclude_prompt_ids: List[str] = None          # 排除的提示ID


@dataclass
class SelectionResult:
    """提示選擇結果"""
    success: bool                           # 是否成功選擇
    selected_prompt_id: Optional[str]       # 選中的提示ID
    prompt_content: Optional[str]           # 提示內容
    metadata: Optional[PromptMetadata]      # 提示元數據
    selection_reason: str                   # 選擇原因
    confidence_score: float                 # 置信度分數 (0-1)
    alternatives: List[str]                 # 備選提示ID列表
    selection_time_ms: float               # 選擇耗時（毫秒）
    strategy_used: SelectionStrategy       # 使用的選擇策略


class PromptSelector:
    """
    提示選擇器
    
    負責根據各種條件智能選擇最合適的提示模板
    """
    
    def __init__(self, prompt_registry: PromptRegistry):
        """
        初始化提示選擇器
        
        Args:
            prompt_registry: 提示註冊中心實例
        """
        self.registry = prompt_registry
        self.default_strategy = SelectionStrategy.HYBRID
        
        # 選擇統計
        self.selection_stats = {
            "total_selections": 0,
            "successful_selections": 0,
            "failed_selections": 0,
            "strategy_usage": {strategy.value: 0 for strategy in SelectionStrategy},
            "state_coverage": {},
            "intent_coverage": {},
            "average_confidence": 0.0,
            "selection_history": []
        }
        
        # 加載配置
        self.state_mapping = self._load_state_mapping()
        self.intent_mapping = self._load_intent_mapping()
        self.fallback_prompts = self._load_fallback_prompts()
        
        logger.info("PromptSelector 初始化完成")
    
    async def select_prompt(
        self, 
        criteria: SelectionCriteria,
        strategy: SelectionStrategy = None
    ) -> SelectionResult:
        """
        選擇最合適的提示
        
        Args:
            criteria: 選擇條件
            strategy: 選擇策略，默認使用混合策略
            
        Returns:
            選擇結果
        """
        start_time = datetime.now()
        
        try:
            # 使用指定策略或默認策略
            strategy = strategy or self.default_strategy
            
            # 根據策略選擇提示
            if strategy == SelectionStrategy.STATE_FIRST:
                result = await self._select_by_state_first(criteria)
            elif strategy == SelectionStrategy.INTENT_FIRST:
                result = await self._select_by_intent_first(criteria)
            elif strategy == SelectionStrategy.HYBRID:
                result = await self._select_by_hybrid(criteria)
            elif strategy == SelectionStrategy.PRIORITY_BASED:
                result = await self._select_by_priority(criteria)
            elif strategy == SelectionStrategy.ROUND_ROBIN:
                result = await self._select_by_round_robin(criteria)
            else:
                result = await self._select_by_hybrid(criteria)
            
            # 設置選擇策略
            result.strategy_used = strategy
            
            # 計算選擇耗時
            end_time = datetime.now()
            result.selection_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # 更新統計
            await self._update_selection_stats(criteria, result, strategy)
            
            return result
            
        except Exception as e:
            logger.error(f"提示選擇失敗: {e}", exc_info=True)
            
            # 返回失敗結果
            end_time = datetime.now()
            return SelectionResult(
                success=False,
                selected_prompt_id=None,
                prompt_content=None,
                metadata=None,
                selection_reason=f"選擇過程發生錯誤: {str(e)}",
                confidence_score=0.0,
                alternatives=[],
                selection_time_ms=(end_time - start_time).total_seconds() * 1000,
                strategy_used=strategy or self.default_strategy
            )
    
    async def _select_by_state_first(self, criteria: SelectionCriteria) -> SelectionResult:
        """
        狀態優先選擇策略
        
        優先根據對話狀態選擇提示，其次考慮意圖
        """
        candidates = []
        
        # 1. 根據狀態查找候選提示
        if criteria.state:
            state_prompts = await self.registry.list_prompts_by_state(criteria.state)
            for prompt_id in state_prompts:
                metadata = await self.registry.get_metadata(prompt_id)
                if metadata and metadata.is_active:
                    score = self._calculate_state_match_score(criteria, metadata)
                    candidates.append((prompt_id, metadata, score, "狀態匹配"))
        
        # 2. 如果沒有找到狀態匹配的提示，嘗試意圖匹配
        if not candidates and criteria.intent:
            intent_prompts = await self.registry.list_prompts_by_intent(criteria.intent)
            for prompt_id in intent_prompts:
                metadata = await self.registry.get_metadata(prompt_id)
                if metadata and metadata.is_active:
                    score = self._calculate_intent_match_score(criteria, metadata)
                    candidates.append((prompt_id, metadata, score, "意圖匹配"))
        
        # 3. 選擇最佳候選
        return await self._select_best_candidate(candidates, criteria)
    
    async def _select_by_intent_first(self, criteria: SelectionCriteria) -> SelectionResult:
        """
        意圖優先選擇策略
        
        優先根據用戶意圖選擇提示，其次考慮狀態
        """
        candidates = []
        
        # 1. 根據意圖查找候選提示
        if criteria.intent:
            intent_prompts = await self.registry.list_prompts_by_intent(criteria.intent)
            for prompt_id in intent_prompts:
                metadata = await self.registry.get_metadata(prompt_id)
                if metadata and metadata.is_active:
                    score = self._calculate_intent_match_score(criteria, metadata)
                    candidates.append((prompt_id, metadata, score, "意圖匹配"))
        
        # 2. 如果沒有找到意圖匹配的提示，嘗試狀態匹配
        if not candidates and criteria.state:
            state_prompts = await self.registry.list_prompts_by_state(criteria.state)
            for prompt_id in state_prompts:
                metadata = await self.registry.get_metadata(prompt_id)
                if metadata and metadata.is_active:
                    score = self._calculate_state_match_score(criteria, metadata)
                    candidates.append((prompt_id, metadata, score, "狀態匹配"))
        
        # 3. 選擇最佳候選
        return await self._select_best_candidate(candidates, criteria)
    
    async def _select_by_hybrid(self, criteria: SelectionCriteria) -> SelectionResult:
        """
        混合選擇策略
        
        綜合考慮狀態、意圖、優先級等多個因素
        """
        candidates = []
        
        # 收集所有可能的候選提示
        all_prompt_ids = set()
        
        # 1. 根據狀態收集候選
        if criteria.state:
            state_prompts = await self.registry.list_prompts_by_state(criteria.state)
            all_prompt_ids.update(state_prompts)
        
        # 2. 根據意圖收集候選
        if criteria.intent:
            intent_prompts = await self.registry.list_prompts_by_intent(criteria.intent)
            all_prompt_ids.update(intent_prompts)
        
        # 3. 根據分類收集候選
        if criteria.category:
            category_prompts = await self.registry.list_prompts_by_category(criteria.category)
            all_prompt_ids.update(category_prompts)
        
        # 4. 計算每個候選的綜合分數
        for prompt_id in all_prompt_ids:
            if criteria.exclude_prompt_ids and prompt_id in criteria.exclude_prompt_ids:
                continue
                
            metadata = await self.registry.get_metadata(prompt_id)
            if metadata and metadata.is_active:
                score = self._calculate_hybrid_score(criteria, metadata)
                reason = self._generate_hybrid_reason(criteria, metadata)
                candidates.append((prompt_id, metadata, score, reason))
        
        # 5. 選擇最佳候選
        return await self._select_best_candidate(candidates, criteria)
    
    async def _select_by_priority(self, criteria: SelectionCriteria) -> SelectionResult:
        """
        基於優先級的選擇策略
        
        優先選擇優先級最高的提示
        """
        candidates = []
        
        # 收集所有符合條件的提示
        for prompt_id, metadata in self.registry.metadata_cache.items():
            if not metadata.is_active:
                continue
                
            if criteria.exclude_prompt_ids and prompt_id in criteria.exclude_prompt_ids:
                continue
            
            # 檢查是否符合基本條件
            if self._meets_basic_criteria(criteria, metadata):
                # 使用優先級作為分數
                score = metadata.priority / 10.0  # 標準化到 0-1
                candidates.append((prompt_id, metadata, score, f"優先級 {metadata.priority}"))
        
        return await self._select_best_candidate(candidates, criteria)
    
    async def _select_by_round_robin(self, criteria: SelectionCriteria) -> SelectionResult:
        """
        輪詢選擇策略
        
        在符合條件的提示中輪詢選擇，避免總是選擇同一個
        """
        candidates = []
        
        # 收集符合條件的提示
        for prompt_id, metadata in self.registry.metadata_cache.items():
            if not metadata.is_active:
                continue
                
            if criteria.exclude_prompt_ids and prompt_id in criteria.exclude_prompt_ids:
                continue
            
            if self._meets_basic_criteria(criteria, metadata):
                # 使用使用次數的倒數作為分數，使用次數少的分數高
                usage_score = 1.0 / max(metadata.usage_count + 1, 1)
                candidates.append((prompt_id, metadata, usage_score, "輪詢選擇"))
        
        return await self._select_best_candidate(candidates, criteria)
    
    async def _select_best_candidate(
        self, 
        candidates: List[Tuple[str, PromptMetadata, float, str]], 
        criteria: SelectionCriteria
    ) -> SelectionResult:
        """
        從候選列表中選擇最佳提示
        
        Args:
            candidates: 候選列表 (prompt_id, metadata, score, reason)
            criteria: 選擇條件
            
        Returns:
            選擇結果
        """
        if not candidates:
            # 沒有候選，使用回退策略
            return await self._fallback_selection(criteria)
        
        # 按分數排序
        candidates.sort(key=lambda x: x[2], reverse=True)
        
        # 選擇最佳候選
        best_prompt_id, best_metadata, best_score, selection_reason = candidates[0]
        
        # 獲取提示內容
        prompt_content = await self.registry.get_prompt(best_prompt_id)
        
        if prompt_content is None:
            return await self._fallback_selection(criteria)
        
        # 準備備選列表
        alternatives = [candidate[0] for candidate in candidates[1:6]]  # 最多5個備選
        
        return SelectionResult(
            success=True,
            selected_prompt_id=best_prompt_id,
            prompt_content=prompt_content,
            metadata=best_metadata,
            selection_reason=selection_reason,
            confidence_score=min(best_score, 1.0),
            alternatives=alternatives,
            selection_time_ms=0.0,  # 會在外層設置
            strategy_used=self.default_strategy  # 會在外層設置
        )
    
    async def _fallback_selection(self, criteria: SelectionCriteria) -> SelectionResult:
        """
        回退選擇策略
        
        當無法找到合適的提示時使用
        """
        # 嘗試使用預設回退提示
        fallback_prompt_id = self._get_fallback_prompt_id(criteria)
        
        if fallback_prompt_id:
            prompt_content = await self.registry.get_prompt(fallback_prompt_id)
            metadata = await self.registry.get_metadata(fallback_prompt_id)
            
            if prompt_content and metadata:
                return SelectionResult(
                    success=True,
                    selected_prompt_id=fallback_prompt_id,
                    prompt_content=prompt_content,
                    metadata=metadata,
                    selection_reason="回退策略 - 使用預設提示",
                    confidence_score=0.3,  # 低置信度
                    alternatives=[],
                    selection_time_ms=0.0,
                    strategy_used=self.default_strategy
                )
        
        # 完全失敗的情況
        return SelectionResult(
            success=False,
            selected_prompt_id=None,
            prompt_content=None,
            metadata=None,
            selection_reason="無法找到合適的提示，且回退策略失敗",
            confidence_score=0.0,
            alternatives=[],
            selection_time_ms=0.0,
            strategy_used=self.default_strategy
        )
    
    def _calculate_state_match_score(self, criteria: SelectionCriteria, metadata: PromptMetadata) -> float:
        """計算狀態匹配分數"""
        base_score = 0.5
        
        # 精確狀態匹配
        if criteria.state and criteria.state in metadata.state_mapping:
            base_score = 0.9
        
        # 語言匹配加分
        if criteria.language == metadata.language:
            base_score += 0.1
        
        # 優先級加分
        priority_bonus = (metadata.priority / 10.0) * 0.1
        base_score += priority_bonus
        
        return min(base_score, 1.0)
    
    def _calculate_intent_match_score(self, criteria: SelectionCriteria, metadata: PromptMetadata) -> float:
        """計算意圖匹配分數"""
        base_score = 0.5
        
        # 精確意圖匹配
        if criteria.intent and criteria.intent in metadata.intent_mapping:
            base_score = 0.9
        
        # 語言匹配加分
        if criteria.language == metadata.language:
            base_score += 0.1
        
        # 優先級加分
        priority_bonus = (metadata.priority / 10.0) * 0.1
        base_score += priority_bonus
        
        return min(base_score, 1.0)
    
    def _calculate_hybrid_score(self, criteria: SelectionCriteria, metadata: PromptMetadata) -> float:
        """計算混合策略分數"""
        total_score = 0.0
        factors = 0
        
        # 狀態匹配分數 (權重: 0.4)
        if criteria.state:
            if criteria.state in metadata.state_mapping:
                total_score += 0.4
            factors += 0.4
        
        # 意圖匹配分數 (權重: 0.3)
        if criteria.intent:
            if criteria.intent in metadata.intent_mapping:
                total_score += 0.3
            factors += 0.3
        
        # 分類匹配分數 (權重: 0.1)
        if criteria.category:
            if criteria.category == metadata.category:
                total_score += 0.1
            factors += 0.1
        
        # 語言匹配分數 (權重: 0.1)
        if criteria.language == metadata.language:
            total_score += 0.1
        factors += 0.1
        
        # 優先級分數 (權重: 0.1)
        priority_score = (metadata.priority / 10.0) * 0.1
        total_score += priority_score
        factors += 0.1
        
        # 上下文關鍵詞匹配
        if criteria.context_keywords:
            keyword_matches = self._count_keyword_matches(criteria.context_keywords, metadata)
            keyword_score = min(keyword_matches * 0.1, 0.2)  # 最多0.2分
            total_score += keyword_score
            factors += 0.2
        
        # 標準化分數
        return total_score / factors if factors > 0 else 0.0
    
    def _meets_basic_criteria(self, criteria: SelectionCriteria, metadata: PromptMetadata) -> bool:
        """檢查是否符合基本條件"""
        # 語言檢查
        if criteria.language and criteria.language != metadata.language:
            return False
        
        # 分類檢查
        if criteria.category and criteria.category != metadata.category:
            return False
        
        # 狀態檢查（如果指定了狀態，至少要有一個匹配）
        if criteria.state and criteria.state not in metadata.state_mapping:
            # 但允許通用提示
            if metadata.state_mapping and 'GENERAL' not in metadata.state_mapping:
                return False
        
        return True
    
    def _count_keyword_matches(self, keywords: List[str], metadata: PromptMetadata) -> int:
        """計算關鍵詞匹配數量"""
        if not keywords:
            return 0
        
        # 搜索範圍：標題、描述、分類
        search_text = f"{metadata.title} {metadata.description} {metadata.category}".lower()
        
        matches = 0
        for keyword in keywords:
            if keyword.lower() in search_text:
                matches += 1
        
        return matches
    
    def _generate_hybrid_reason(self, criteria: SelectionCriteria, metadata: PromptMetadata) -> str:
        """生成混合策略的選擇原因"""
        reasons = []
        
        if criteria.state and criteria.state in metadata.state_mapping:
            reasons.append(f"狀態匹配({criteria.state})")
        
        if criteria.intent and criteria.intent in metadata.intent_mapping:
            reasons.append(f"意圖匹配({criteria.intent})")
        
        if criteria.category and criteria.category == metadata.category:
            reasons.append(f"分類匹配({criteria.category})")
        
        if criteria.language == metadata.language:
            reasons.append("語言匹配")
        
        if metadata.priority >= 8:
            reasons.append("高優先級")
        
        return "混合策略 - " + ", ".join(reasons) if reasons else "混合策略 - 基本匹配"
    
    def _get_fallback_prompt_id(self, criteria: SelectionCriteria) -> Optional[str]:
        """獲取回退提示ID"""
        # 優先使用配置的回退提示
        if criteria.state and criteria.state in self.fallback_prompts:
            return self.fallback_prompts[criteria.state]
        
        # 使用通用回退提示
        return self.fallback_prompts.get('DEFAULT')
    
    def _load_state_mapping(self) -> Dict[str, str]:
        """載入狀態映射配置"""
        # 這裡可以從配置文件載入，現在使用硬編碼
        return {
            "INIT": "mgfd_principal_prompt",
            "FUNNEL_START": "recept_guest_prompt1",
            "FUNNEL_QUESTION": "mgfd_collect_slot_value_prompt_v1",
            "RECOMMENDATION_PREPARATION": "mgfd_principal_prompt",
            "RECOMMENDATION_PRESENTATION": "sales_prompt4",
            "PRODUCT_QA": "sales_prompt4",
            "ELICITATION": "mgfd_collect_slot_value_prompt_v1"
        }
    
    def _load_intent_mapping(self) -> Dict[str, str]:
        """載入意圖映射配置"""
        return {
            "ask_recommendation": "mgfd_principal_prompt",
            "ask_comparison": "sales_prompt4",
            "ask_price": "sales_prompt4",
            "ask_specs": "sales_prompt4",
            "greet": "recept_guest_prompt1",
            "technical_question": "sales_prompt4"
        }
    
    def _load_fallback_prompts(self) -> Dict[str, str]:
        """載入回退提示配置"""
        return {
            "DEFAULT": "mgfd_principal_prompt",
            "INIT": "recept_guest_prompt1",
            "FUNNEL_START": "recept_guest_prompt1",
            "RECOMMENDATION_PRESENTATION": "mgfd_principal_prompt",
            "ERROR": "mgfd_principal_prompt"
        }
    
    async def _update_selection_stats(
        self, 
        criteria: SelectionCriteria, 
        result: SelectionResult,
        strategy: SelectionStrategy
    ):
        """更新選擇統計"""
        self.selection_stats["total_selections"] += 1
        
        if result.success:
            self.selection_stats["successful_selections"] += 1
        else:
            self.selection_stats["failed_selections"] += 1
        
        # 更新策略使用統計
        self.selection_stats["strategy_usage"][strategy.value] += 1
        
        # 更新覆蓋率統計
        if criteria.state:
            if criteria.state not in self.selection_stats["state_coverage"]:
                self.selection_stats["state_coverage"][criteria.state] = 0
            self.selection_stats["state_coverage"][criteria.state] += 1
        
        if criteria.intent:
            if criteria.intent not in self.selection_stats["intent_coverage"]:
                self.selection_stats["intent_coverage"][criteria.intent] = 0
            self.selection_stats["intent_coverage"][criteria.intent] += 1
        
        # 更新平均置信度
        total_confidence = (
            self.selection_stats["average_confidence"] * 
            (self.selection_stats["total_selections"] - 1) + 
            result.confidence_score
        )
        self.selection_stats["average_confidence"] = total_confidence / self.selection_stats["total_selections"]
        
        # 記錄選擇歷史（最多保留100條）
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "state": criteria.state,
            "intent": criteria.intent,
            "selected_prompt_id": result.selected_prompt_id,
            "success": result.success,
            "confidence": result.confidence_score,
            "strategy": strategy.value,
            "selection_time_ms": result.selection_time_ms
        }
        
        self.selection_stats["selection_history"].append(history_entry)
        if len(self.selection_stats["selection_history"]) > 100:
            self.selection_stats["selection_history"] = self.selection_stats["selection_history"][-100:]
    
    def get_selection_stats(self) -> Dict[str, Any]:
        """獲取選擇統計信息"""
        stats = self.selection_stats.copy()
        
        # 計算成功率
        if stats["total_selections"] > 0:
            stats["success_rate"] = stats["successful_selections"] / stats["total_selections"]
        else:
            stats["success_rate"] = 0.0
        
        # 添加時間戳
        stats["timestamp"] = datetime.now().isoformat()
        
        return stats
    
    async def recommend_prompts(
        self, 
        criteria: SelectionCriteria, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        推薦提示列表
        
        Args:
            criteria: 選擇條件
            limit: 推薦數量限制
            
        Returns:
            推薦提示列表，包含ID、元數據和推薦分數
        """
        candidates = []
        
        # 收集所有可能的候選提示
        for prompt_id, metadata in self.registry.metadata_cache.items():
            if not metadata.is_active:
                continue
                
            if criteria.exclude_prompt_ids and prompt_id in criteria.exclude_prompt_ids:
                continue
            
            # 計算推薦分數
            score = self._calculate_hybrid_score(criteria, metadata)
            
            if score > 0.1:  # 過濾低分提示
                candidates.append({
                    "prompt_id": prompt_id,
                    "title": metadata.title,
                    "description": metadata.description,
                    "category": metadata.category,
                    "score": score,
                    "priority": metadata.priority,
                    "usage_count": metadata.usage_count,
                    "state_mapping": metadata.state_mapping,
                    "intent_mapping": metadata.intent_mapping
                })
        
        # 按分數排序並限制數量
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:limit]