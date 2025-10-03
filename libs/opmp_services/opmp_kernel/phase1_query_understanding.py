#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1: Query Understanding & Entity Extraction

This module implements the first phase of the progressive streaming system,
which analyzes user queries and extracts structured intent and entities.

Author: Claude (SuperClaude)
Date: 2025-10-01
"""

import json
import logging
import re
from typing import Dict, Any, AsyncGenerator, List, Optional

logger = logging.getLogger(__name__)


# Prompt template for Phase 1
QUERY_UNDERSTANDING_PROMPT = """你是一個專業的產品查詢分析助手。請分析以下用戶查詢並提取關鍵信息。

用戶查詢：{user_query}

可用產品型號（部分）：{available_modelnames}
可用機型類別：{available_modeltypes}

請以 JSON 格式回答，包含以下欄位：
{{
  "intent": "compare|recommend|spec_query|general_inquiry",
  "detected_products": ["產品1", "產品2"],
  "detected_modeltypes": ["819", "839"],
  "key_features": ["CPU", "GPU", "記憶體"],
  "user_focus": "效能|價格|攜帶性|電池續航力",
  "complexity": "simple|medium|complex"
}}

只回覆 JSON，不要其他說明。
"""


class Phase1QueryUnderstanding:
    """
    Phase 1: Query Understanding & Entity Extraction

    This class analyzes user queries to extract:
    - Intent (compare, recommend, spec_query, general_inquiry)
    - Detected products and model types
    - Key features the user is interested in
    - User focus (performance, price, portability, battery)
    - Query complexity (simple, medium, complex)

    Features:
    - LLM-based entity extraction
    - Regex-based fast path for simple queries
    - Caching for frequent queries
    - Progressive streaming of results
    """

    def __init__(self, llm: Any, cache: Optional[Any] = None):
        """
        Initialize Phase 1 processor

        Args:
            llm: LangChain LLM instance
            cache: Optional cache instance (Redis)
        """
        self.llm = llm
        self.cache = cache

        # Regex patterns for fast path
        self.product_pattern = re.compile(r'\b(APX|AHP|AG|ARB|AMD|AB|AKK)\s*(\d{3,4})\b', re.IGNORECASE)
        self.modeltype_pattern = re.compile(r'\b(819|839|928|958|960|AC01)\b')

        logger.info("Phase1QueryUnderstanding initialized")

    async def process(
        self,
        query: str,
        available_modelnames: List[str],
        available_modeltypes: List[str]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process query and extract understanding

        Args:
            query: User query string
            available_modelnames: List of available product model names
            available_modeltypes: List of available model types

        Yields:
            Progress updates and final phase result
        """
        try:
            # Progress update
            yield {
                "type": "progress",
                "phase": 1,
                "message": "🔍 正在分析您的查詢...",
                "progress": 10
            }

            # Check cache first
            if self.cache:
                cached = await self._get_cached_analysis(query)
                if cached:
                    logger.info(f"Phase 1 cache hit for query: {query[:30]}")
                    yield {
                        "type": "progress",
                        "phase": 1,
                        "message": "✓ 查詢分析完成（從緩存）",
                        "progress": 20
                    }
                    yield {
                        "type": "phase_result",
                        "phase": 1,
                        "data": cached,
                        "progress": 20,
                        "from_cache": True
                    }
                    return

            # Try fast path first (regex-based extraction)
            fast_result = self._fast_path_extraction(query, available_modelnames, available_modeltypes)
            if fast_result and fast_result.get("confidence") == "high":
                logger.info(f"Phase 1 fast path success for query: {query[:30]}")
                yield {
                    "type": "progress",
                    "phase": 1,
                    "message": "✓ 查詢分析完成（快速路徑）",
                    "progress": 20
                }

                # Cache result
                if self.cache:
                    await self._cache_analysis(query, fast_result)

                yield {
                    "type": "phase_result",
                    "phase": 1,
                    "data": fast_result,
                    "progress": 20
                }
                return

            # LLM-based extraction (slower but more accurate)
            logger.info(f"Phase 1 using LLM for query: {query[:30]}")
            llm_result = await self._llm_extraction(query, available_modelnames, available_modeltypes)

            yield {
                "type": "progress",
                "phase": 1,
                "message": "✓ 查詢分析完成",
                "progress": 20
            }

            # Cache result
            if self.cache:
                await self._cache_analysis(query, llm_result)

            yield {
                "type": "phase_result",
                "phase": 1,
                "data": llm_result,
                "progress": 20
            }

        except Exception as e:
            logger.error(f"Phase 1 error: {e}")
            # Return fallback result
            fallback_result = self._fallback_extraction(query)
            yield {
                "type": "phase_result",
                "phase": 1,
                "data": fallback_result,
                "progress": 20,
                "error": str(e)
            }

    def _fast_path_extraction(
        self,
        query: str,
        available_modelnames: List[str],
        available_modeltypes: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Fast path extraction using regex patterns

        This is used for simple queries with clear product mentions.

        Args:
            query: User query
            available_modelnames: Available model names
            available_modeltypes: Available model types

        Returns:
            Extraction result or None if fast path not applicable
        """
        # Extract products using regex
        product_matches = self.product_pattern.findall(query)
        detected_products = [f"{prefix}{num}" for prefix, num in product_matches]

        # Extract model types
        modeltype_matches = self.modeltype_pattern.findall(query)
        detected_modeltypes = list(set(modeltype_matches))

        # Check if fast path is applicable
        if not detected_products and not detected_modeltypes:
            return None

        # Determine intent from keywords
        intent = "spec_query"  # default
        if any(kw in query for kw in ["比較", "比对", "差異", "對比", "vs"]):
            intent = "compare"
        elif any(kw in query for kw in ["推薦", "推荐", "建議", "適合", "選擇"]):
            intent = "recommend"

        # Determine key features from query
        key_features = []
        feature_keywords = {
            "CPU": ["cpu", "處理器", "核心"],
            "GPU": ["gpu", "顯卡", "顯示卡", "圖形"],
            "記憶體": ["記憶體", "内存", "ram", "memory"],
            "儲存": ["儲存", "存储", "硬碟", "ssd", "storage"],
            "螢幕": ["螢幕", "屏幕", "顯示", "lcd"],
            "電池": ["電池", "电池", "續航", "续航", "續航力", "续航力", "battery", "充電", "充电"]
        }

        for feature, keywords in feature_keywords.items():
            if any(kw in query.lower() for kw in keywords):
                key_features.append(feature)

        # Determine user focus
        user_focus = "全面評估"
        if any(kw in query for kw in ["效能", "性能", "快速", "強大"]):
            user_focus = "效能"
        elif any(kw in query for kw in ["價格", "便宜", "划算"]):
            user_focus = "價格"
        elif any(kw in query for kw in ["輕薄", "便攜", "攜帶"]):
            user_focus = "攜帶性"
        elif any(kw in query for kw in ["電池", "續航"]):
            user_focus = "電池續航力"

        # Determine complexity
        complexity = "simple"
        if len(detected_products) >= 3 or len(key_features) >= 4:
            complexity = "complex"
        elif len(detected_products) == 2 or len(key_features) >= 2:
            complexity = "medium"

        result = {
            "intent": intent,
            "detected_products": detected_products,
            "detected_modeltypes": detected_modeltypes,
            "key_features": key_features if key_features else ["CPU", "GPU", "記憶體"],
            "user_focus": user_focus,
            "complexity": complexity,
            "confidence": "high" if detected_products else "medium"
        }

        return result

    async def _llm_extraction(
        self,
        query: str,
        available_modelnames: List[str],
        available_modeltypes: List[str]
    ) -> Dict[str, Any]:
        """
        LLM-based extraction for complex queries

        Args:
            query: User query
            available_modelnames: Available model names
            available_modeltypes: Available model types

        Returns:
            Extraction result
        """
        # Prepare prompt
        prompt = QUERY_UNDERSTANDING_PROMPT.format(
            user_query=query,
            available_modelnames=", ".join(available_modelnames[:20]),  # Limit for token efficiency
            available_modeltypes=", ".join(available_modeltypes)
        )

        # Call LLM
        try:
            import asyncio
            response = await asyncio.to_thread(self.llm.invoke, prompt)

            # Parse response
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)

            # Extract JSON from response
            analysis = self._parse_json_response(response_text)

            if analysis:
                return analysis
            else:
                logger.warning("Failed to parse LLM response, using fallback")
                return self._fallback_extraction(query)

        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
            return self._fallback_extraction(query)

    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response

        Args:
            response_text: LLM response text

        Returns:
            Parsed JSON or None if parsing fails
        """
        try:
            # Try direct JSON parsing
            analysis = json.loads(response_text)
            return analysis
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    analysis = json.loads(json_match.group(1))
                    return analysis
                except json.JSONDecodeError:
                    pass

            # Try to find JSON object in text
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text)
            if json_match:
                try:
                    analysis = json.loads(json_match.group(0))
                    return analysis
                except json.JSONDecodeError:
                    pass

        return None

    def _fallback_extraction(self, query: str) -> Dict[str, Any]:
        """
        Fallback extraction when all methods fail

        Args:
            query: User query

        Returns:
            Basic extraction result
        """
        return {
            "intent": "general_inquiry",
            "detected_products": [],
            "detected_modeltypes": [],
            "key_features": ["CPU", "GPU", "記憶體"],
            "user_focus": "全面評估",
            "complexity": "medium",
            "confidence": "low"
        }

    async def _get_cached_analysis(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis from Redis"""
        if not self.cache:
            return None

        try:
            import hashlib
            query_hash = hashlib.md5(query.encode()).hexdigest()
            cache_key = f"phase1:{query_hash}"

            cached = await self.cache.get_async(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")

        return None

    async def _cache_analysis(self, query: str, analysis: Dict[str, Any]) -> None:
        """Cache analysis to Redis"""
        if not self.cache:
            return

        try:
            import hashlib
            query_hash = hashlib.md5(query.encode()).hexdigest()
            cache_key = f"phase1:{query_hash}"

            await self.cache.set_async(
                cache_key,
                json.dumps(analysis, ensure_ascii=False),
                ttl=300  # 5 minutes
            )
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
