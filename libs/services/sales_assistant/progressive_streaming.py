#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Progressive Streaming System - Main Orchestrator

This module orchestrates the 5-phase progressive streaming system for
ChatGPT-style markdown rendering with optimized performance.

Phases:
1. Query Understanding & Entity Extraction
2. Multi-source Data Retrieval (Parallel)
3. Context Assembly & Ranking
4. Response Generation (Progressive Markdown)
5. Post-processing & Formatting

Author: Claude (SuperClaude)
Date: 2025-10-01
"""

import json
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime

# Import all phase processors
from .phase1_query_understanding import Phase1QueryUnderstanding
from .phase2_parallel_retrieval import Phase2ParallelRetrieval
from .phase3_context_assembly import Phase3ContextAssembly
from .phase4_response_generation import Phase4ResponseGeneration
from .phase5_postprocessing import Phase5Postprocessing

logger = logging.getLogger(__name__)


class ProgressiveStreamingService:
    """
    Main orchestrator for 5-phase progressive streaming

    This service coordinates all phases and provides a unified interface
    for progressive streaming with the following features:

    - Phase-by-phase progress updates
    - Token-by-token markdown streaming
    - Parallel data retrieval
    - Intelligent caching
    - Error recovery with partial results

    Example:
        >>> service = ProgressiveStreamingService(llm, config)
        >>> async for update in service.chat_stream_progressive(query):
        ...     print(update)
    """

    def __init__(
        self,
        llm: Any,
        milvus_query: Any,
        duckdb_query: Any,
        available_modelnames: list,
        available_modeltypes: list,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize progressive streaming service

        Args:
            llm: LangChain LLM instance
            milvus_query: Milvus query instance
            duckdb_query: DuckDB query instance
            available_modelnames: List of available model names
            available_modeltypes: List of available model types
            config: Optional configuration dictionary
        """
        self.llm = llm
        self.milvus_query = milvus_query
        self.duckdb_query = duckdb_query
        self.available_modelnames = available_modelnames
        self.available_modeltypes = available_modeltypes
        self.config = config or {}

        # Initialize cache (optional)
        self.cache = self._initialize_cache()

        # Initialize all phase processors
        self.phase1 = Phase1QueryUnderstanding(llm=llm, cache=self.cache)

        self.phase2 = Phase2ParallelRetrieval(
            milvus_collection=self.config.get("milvus_collection", "sales_notebook_specs"),
            duckdb_path=self.config.get("duckdb_path"),
            milvus_host=self.config.get("milvus_host", "localhost"),
            milvus_port=self.config.get("milvus_port", 19530)
        )

        self.phase3 = Phase3ContextAssembly(
            max_context_tokens=self.config.get("max_context_tokens", 100000)
        )

        self.phase4 = Phase4ResponseGeneration(llm=llm, cache=self.cache)

        self.phase5 = Phase5Postprocessing(
            model_name=self.config.get("model_name", "gpt-oss:20b")
        )

        logger.info("ProgressiveStreamingService initialized with all phases")

    def _initialize_cache(self) -> Optional[Any]:
        """Initialize cache instance (Redis)"""
        try:
            from ...caching import get_cache_instance
            cache = get_cache_instance()
            logger.info("Cache initialized successfully")
            return cache
        except Exception as e:
            logger.warning(f"Cache initialization failed: {e}. Running without cache.")
            return None

    async def chat_stream_progressive(
        self,
        query: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Main progressive streaming function

        This method orchestrates all 5 phases and yields SSE-formatted
        updates for real-time UI rendering.

        Args:
            query: User query string
            **kwargs: Additional parameters

        Yields:
            SSE-formatted strings with progress and content

        Message Types:
            - "progress": Phase progress updates
            - "phase_result": Phase completion results
            - "markdown_token": Markdown tokens (Phase 4)
            - "complete": Final completion
            - "error": Error messages

        Example:
            >>> async for update in service.chat_stream_progressive("比較 APX819 和 APX839"):
            ...     print(update)  # data: {...}\n\n
        """
        start_time = datetime.now()
        phase_timings = {}

        try:
            logger.info(f"[Progressive] Starting for query: {query[:50]}...")

            # Phase 1: Query Understanding
            phase1_start = datetime.now()
            analysis = None

            async for update in self.phase1.process(
                query=query,
                available_modelnames=self.available_modelnames,
                available_modeltypes=self.available_modeltypes
            ):
                yield self._format_sse(update)

                if update["type"] == "phase_result":
                    analysis = update["data"]

            phase_timings[1] = (datetime.now() - phase1_start).total_seconds()
            logger.info(f"Phase 1 completed in {phase_timings[1]:.2f}s")

            if not analysis:
                raise Exception("Phase 1 failed to produce analysis")

            # Phase 2: Data Retrieval (Parallel)
            phase2_start = datetime.now()
            retrieval_results = None

            detected_products = []
            if analysis.get("detected_products"):
                detected_products.extend(analysis["detected_products"])
            if analysis.get("detected_modeltypes"):
                detected_products.extend(analysis["detected_modeltypes"])

            async for update in self.phase2.retrieve(
                query=query,
                detected_products=detected_products if detected_products else None,
                top_k=30
            ):
                yield self._format_sse(update)

                if update["type"] == "phase_result":
                    retrieval_results = update["data"]

            phase_timings[2] = (datetime.now() - phase2_start).total_seconds()
            logger.info(f"Phase 2 completed in {phase_timings[2]:.2f}s")

            if not retrieval_results or not retrieval_results.get("merged_products"):
                raise Exception("Phase 2 failed to retrieve products")

            # Phase 3: Context Assembly
            phase3_start = datetime.now()
            context = None

            async for update in self.phase3.process(
                retrieval_results=retrieval_results,
                analysis=analysis
            ):
                yield self._format_sse(update)

                if update["type"] == "phase_result":
                    context = update["data"]

            phase_timings[3] = (datetime.now() - phase3_start).total_seconds()
            logger.info(f"Phase 3 completed in {phase_timings[3]:.2f}s")

            if not context:
                raise Exception("Phase 3 failed to assemble context")

            # Phase 4: Response Generation (Progressive Markdown)
            phase4_start = datetime.now()
            generated_response = ""

            async for update in self.phase4.process(
                query=query,
                analysis=analysis,
                context=context
            ):
                yield self._format_sse(update)

                # Accumulate response text
                if update.get("type") == "markdown_token":
                    generated_response += update.get("token", "")

            phase_timings[4] = (datetime.now() - phase4_start).total_seconds()
            logger.info(f"Phase 4 completed in {phase_timings[4]:.2f}s")

            # Phase 5: Post-processing
            phase5_start = datetime.now()

            async for update in self.phase5.process(
                generated_response=generated_response,
                context=context,
                analysis=analysis,
                query=query
            ):
                yield self._format_sse(update)

            phase_timings[5] = (datetime.now() - phase5_start).total_seconds()
            logger.info(f"Phase 5 completed in {phase_timings[5]:.2f}s")

            # Log overall timing
            total_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"[Progressive] Complete in {total_time:.2f}s. "
                f"Phase times: {phase_timings}"
            )

        except Exception as e:
            logger.error(f"Error in progressive streaming: {e}", exc_info=True)

            # Send error message
            error_response = {
                "type": "error",
                "message": f"處理過程中發生錯誤: {str(e)}",
                "partial_results": True,
                "phase_timings": phase_timings
            }
            yield self._format_sse(error_response)

    def _format_sse(self, data: Dict[str, Any]) -> str:
        """
        Format data as Server-Sent Event

        Args:
            data: Data dictionary

        Returns:
            SSE-formatted string
        """
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# Factory function for easy integration

def create_progressive_streaming_service(
    sales_service: Any,
    config: Optional[Dict[str, Any]] = None
) -> ProgressiveStreamingService:
    """
    Factory function to create ProgressiveStreamingService

    This is a convenience function that creates a service instance
    using an existing SalesAssistantService.

    Args:
        sales_service: Existing SalesAssistantService instance
        config: Optional configuration overrides

    Returns:
        ProgressiveStreamingService instance

    Example:
        >>> from libs.services.sales_assistant.service import SalesAssistantService
        >>> sales_service = SalesAssistantService()
        >>> progressive_service = create_progressive_streaming_service(sales_service)
        >>> async for update in progressive_service.chat_stream_progressive(query):
        ...     print(update)
    """
    # Extract configuration from sales_service and config
    from config import DB_PATH, MILVUS_HOST, MILVUS_PORT, MILVUS_COLLECTION_NAME

    service_config = {
        "milvus_collection": MILVUS_COLLECTION_NAME,
        "duckdb_path": str(DB_PATH),
        "milvus_host": MILVUS_HOST,
        "milvus_port": MILVUS_PORT,
        "max_context_tokens": 100000,
        "model_name": "gpt-oss:20b"
    }

    # Merge with user config
    if config:
        service_config.update(config)

    # Get available models from sales_service
    from . import service as sales_service_module
    available_modelnames = sales_service_module.AVAILABLE_MODELNAMES
    available_modeltypes = sales_service_module.AVAILABLE_MODELTYPES

    # Create service
    progressive_service = ProgressiveStreamingService(
        llm=sales_service.llm,
        milvus_query=sales_service.milvus_query,
        duckdb_query=sales_service.duckdb_query,
        available_modelnames=available_modelnames,
        available_modeltypes=available_modeltypes,
        config=service_config
    )

    return progressive_service
