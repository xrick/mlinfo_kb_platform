#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3: Context Assembly & Ranking

This module implements context assembly, product ranking, and intelligent
truncation to fit within token limits.

Author: Claude (SuperClaude)
Date: 2025-10-01
"""

import json
import logging
from typing import Dict, Any, AsyncGenerator, List, Optional

logger = logging.getLogger(__name__)


class Phase3ContextAssembly:
    """
    Phase 3: Context Assembly & Ranking

    This class handles:
    - Merging semantic matches with spec data
    - Ranking products by relevance
    - Intelligent context truncation to fit token limits
    - Token estimation and management

    Features:
    - Multi-criteria product ranking
    - Smart field selection based on query intent
    - Token-aware truncation
    - Context optimization for LLM
    """

    def __init__(self, max_context_tokens: int = 100000):
        """
        Initialize Phase 3 processor

        Args:
            max_context_tokens: Maximum tokens allowed for context (default: 100K)
        """
        self.MAX_CONTEXT_TOKENS = max_context_tokens
        logger.info(f"Phase3ContextAssembly initialized (max tokens: {max_context_tokens})")

    async def process(
        self,
        retrieval_results: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process retrieval results and assemble context

        Args:
            retrieval_results: Results from Phase 2 (merged products)
            analysis: Query analysis from Phase 1

        Yields:
            Progress updates and final phase result
        """
        try:
            yield {
                "type": "progress",
                "phase": 3,
                "message": "Assembling product information...", #"正在整理產品資訊...",
                "progress": 55
            }

            # Get merged products from Phase 2
            merged_products = retrieval_results.get("merged_products", [])

            if not merged_products:
                logger.warning("No merged products to process")
                yield {
                    "type": "phase_result",
                    "phase": 3,
                    "data": {
                        "products": [],
                        "token_count": 0,
                        "truncation_applied": False
                    },
                    "progress": 70
                }
                return

            # Rank products by relevance
            ranked_products = self._rank_products_by_relevance(
                merged_products,
                analysis.get("key_features", []),
                analysis.get("detected_products", [])
            )

            # Context truncation based on token limits
            truncated_context = self._truncate_context(
                ranked_products,
                max_tokens=self.MAX_CONTEXT_TOKENS - 10000,  # Reserve for prompt
                key_features=analysis.get("key_features", [])
            )

            yield {
                "type": "progress",
                "phase": 3,
                "message": "Product information assembly completed", #"整理產品資訊完成",
                "progress": 65
            }

            yield {
                "type": "phase_result",
                "phase": 3,
                "data": truncated_context,
                "progress": 70
            }

        except Exception as e:
            logger.error(f"Phase 3 error: {e}")
            raise

    def _rank_products_by_relevance(
        self,
        products: List[Dict[str, Any]],
        key_features: List[str],
        detected_products: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Rank products by relevance to query

        Ranking criteria:
        1. Exact match with detected products (highest priority)
        2. Semantic similarity score
        3. Completeness of key features
        4. Recency of product

        Args:
            products: List of merged product dictionaries
            key_features: Key features from query analysis
            detected_products: Products explicitly mentioned in query

        Returns:
            Ranked list of products
        """
        for product in products:
            score = 0.0

            # Criterion 1: Exact product match (highest weight)
            modelname = product.get("modelname", "")
            modeltype = product.get("modeltype", "")

            if modelname in detected_products or modeltype in detected_products:
                score += 100.0

            # Criterion 2: Semantic similarity (from Milvus)
            if "similarity_score" in product:
                score += product["similarity_score"] * 50.0

            # Criterion 3: Feature completeness
            feature_map = {
                "CPU": "cpu",
                "GPU": "gpu",
                "記憶體": "memory",
                "儲存": "storage",
                "螢幕": "lcd",
                "電池": "battery"
            }

            feature_count = 0
            for feature in key_features:
                field_name = feature_map.get(feature)
                if field_name and product.get(field_name):
                    feature_count += 1

            feature_completeness = feature_count / len(key_features) if key_features else 0
            score += feature_completeness * 20.0

            # Criterion 4: Recency (if devtime available)
            if product.get("devtime"):
                try:
                    # Assume devtime is a year string like "2023"
                    year = int(str(product["devtime"])[:4])
                    if year >= 2022:
                        score += 10.0
                    elif year >= 2020:
                        score += 5.0
                except (ValueError, TypeError):
                    pass

            # Store relevance score
            product["relevance_score"] = score

        # Sort by relevance score (descending)
        ranked = sorted(products, key=lambda p: p.get("relevance_score", 0), reverse=True)

        logger.info(
            f"Ranked {len(ranked)} products. "
            f"Top 3 scores: {[p.get('relevance_score', 0) for p in ranked[:3]]}"
        )

        return ranked

    def _truncate_context(
        self,
        products: List[Dict[str, Any]],
        max_tokens: int,
        key_features: List[str]
    ) -> Dict[str, Any]:
        """
        Intelligent context truncation to fit token limits

        Strategy:
        1. Keep top-ranked products (relevance priority)
        2. Select essential fields based on key features
        3. Estimate tokens and iteratively truncate
        4. Ensure minimum viable context

        Args:
            products: Ranked product list
            max_tokens: Maximum allowed tokens
            key_features: Key features from query

        Returns:
            Truncated context dictionary
        """
        # Strategy 1: Keep top products by relevance
        initial_limit = min(10, len(products))
        truncated_products = products[:initial_limit]

        # Strategy 2: Essential fields (always include these)
        # Include battery and lcd as default core specs that users frequently ask about
        essential_fields = ['modeltype', 'modelname', 'cpu', 'gpu', 'memory', 'storage', 'battery', 'lcd']

        # Add feature-specific fields
        feature_field_map = {
            "CPU": ["cpu"],
            "GPU": ["gpu"],
            "記憶體": ["memory"],
            "儲存": ["storage"],
            "螢幕": ["lcd"],
            "電池": ["battery"],
            "散熱": ["thermal"],
            "AI": ["ai"]
        }

        for feature in key_features:
            if feature in feature_field_map:
                essential_fields.extend(feature_field_map[feature])

        # Remove duplicates
        essential_fields = list(set(essential_fields))

        # Strategy 3: Extract essential fields from products
        minimized_products = []
        for product in truncated_products:
            minimized = {}
            for field in essential_fields:
                if field in product and product[field]:
                    minimized[field] = product[field]

            # Add semantic content if available (truncated)
            if "semantic_content" in product and product["semantic_content"]:
                content = str(product["semantic_content"])
                minimized["semantic_content"] = content[:200] + "..." if len(content) > 200 else content

            minimized_products.append(minimized)

        # Strategy 4: Estimate tokens
        context_text = json.dumps(minimized_products, ensure_ascii=False)
        estimated_tokens = self._estimate_tokens(context_text)

        # Strategy 5: Further truncate if still over limit
        if estimated_tokens > max_tokens:
            # Reduce number of products
            target_count = max(3, int(len(minimized_products) * max_tokens / estimated_tokens))
            minimized_products = minimized_products[:target_count]

            # Re-estimate
            context_text = json.dumps(minimized_products, ensure_ascii=False)
            estimated_tokens = self._estimate_tokens(context_text)

            logger.warning(
                f"Context truncated to {target_count} products "
                f"({estimated_tokens} tokens)"
            )

        return {
            "products": minimized_products,
            "token_count": estimated_tokens,
            "truncation_applied": len(minimized_products) < len(products),
            "original_count": len(products),
            "kept_count": len(minimized_products)
        }

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text

        This is a rough estimation:
        - English: ~1 token per 4 characters
        - Chinese: ~1 token per 2-3 characters
        - Mixed: Use average of 3 characters per token

        For more accurate estimation, use tiktoken library.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Try to use tiktoken if available
        try:
            import tiktoken
            encoder = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
            return len(encoder.encode(text))
        except (ImportError, Exception):
            # Fallback to character-based estimation
            return len(text) // 3

    def _merge_semantic_and_spec_data(
        self,
        semantic_matches: List[Dict[str, Any]],
        spec_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge semantic matches with structured spec data

        This method is kept for compatibility but is now handled in Phase 2.

        Args:
            semantic_matches: Results from Milvus
            spec_data: Results from DuckDB

        Returns:
            Merged product list
        """
        # Create lookup for spec data
        spec_lookup = {}
        for spec in spec_data:
            key = spec.get("modeltype") or spec.get("modelname")
            if key:
                spec_lookup[key] = spec

        # Merge
        merged = []
        for semantic in semantic_matches:
            product = semantic.copy()

            # Find matching spec
            modeltype = semantic.get("modeltype")
            modelname = semantic.get("modelname")

            matching_spec = None
            if modeltype and modeltype in spec_lookup:
                matching_spec = spec_lookup[modeltype]
            elif modelname and modelname in spec_lookup:
                matching_spec = spec_lookup[modelname]

            # Merge spec data
            if matching_spec:
                product.update(matching_spec)

            merged.append(product)

        # Add spec data that wasn't in semantic matches
        for spec in spec_data:
            key = spec.get("modeltype") or spec.get("modelname")
            if key and not any(
                m.get("modeltype") == key or m.get("modelname") == key
                for m in merged
            ):
                merged.append(spec)

        return merged
