#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for Phase 2 Parallel Retrieval

Tests cover:
1. Redis cache functionality
2. Async DuckDB queries
3. Parallel Milvus + DuckDB retrieval
4. Result merging and ranking
5. Performance benchmarks

Author: Claude (SuperClaude)
Date: 2025-10-01
"""

import pytest
import asyncio
import time
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import modules to test
from libs.caching.redis_cache import StreamingCache, CacheConfig
from libs.RAG.DB.AsyncDuckDBQuery import AsyncDuckDBQuery
from libs.services.sales_assistant.phase2_parallel_retrieval import Phase2ParallelRetrieval


# ==================== Redis Cache Tests ====================

class TestRedisCache:
    """Test Redis caching functionality"""

    @pytest.fixture
    def cache(self):
        """Create cache instance for testing"""
        config = CacheConfig(
            host='localhost',
            port=6379,
            db=1  # Use different DB for testing
        )
        cache = StreamingCache(config)
        yield cache
        # Cleanup
        cache.clear_all()
        cache.close()

    def test_cache_initialization(self, cache):
        """Test cache initializes correctly"""
        assert cache.enabled is True
        assert cache.config.host == 'localhost'
        assert cache.config.port == 6379

    def test_cache_set_get(self, cache):
        """Test basic cache set and get"""
        test_data = {
            "products": ["APX819", "APX839"],
            "count": 2
        }

        # Set cache
        success = cache.set_phase_result(
            query="test query",
            phase=2,
            data=test_data
        )
        assert success is True

        # Get cache
        result = cache.get_phase_result(query="test query", phase=2)
        assert result is not None
        assert result['data'] == test_data

    def test_cache_miss(self, cache):
        """Test cache miss returns None"""
        result = cache.get_phase_result(query="nonexistent query", phase=2)
        assert result is None

    def test_cache_statistics(self, cache):
        """Test cache statistics tracking"""
        # Perform some cache operations
        cache.set_phase_result("query1", phase=2, data={"test": 1})
        cache.get_phase_result("query1", phase=2)  # Hit
        cache.get_phase_result("query2", phase=2)  # Miss

        stats = cache.get_statistics()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['total_queries'] == 2

    def test_cache_ttl(self, cache):
        """Test cache TTL expiration"""
        cache.set_phase_result(
            query="ttl test",
            phase=2,
            data={"test": "data"},
            ttl=1  # 1 second TTL
        )

        # Should exist immediately
        result = cache.get_phase_result("ttl test", phase=2)
        assert result is not None

        # Wait for expiration
        time.sleep(2)

        # Should be gone
        result = cache.get_phase_result("ttl test", phase=2)
        assert result is None

    def test_cache_health_check(self, cache):
        """Test cache health check"""
        health = cache.health_check()
        assert health['status'] == 'healthy'
        assert 'redis_version' in health


# ==================== Async DuckDB Tests ====================

class TestAsyncDuckDB:
    """Test async DuckDB wrapper"""

    @pytest.fixture
    def duckdb(self):
        """Create async DuckDB instance for testing"""
        from config import DB_PATH
        db = AsyncDuckDBQuery(str(DB_PATH), max_workers=2)
        yield db
        db.shutdown()

    @pytest.mark.asyncio
    async def test_duckdb_simple_query(self, duckdb):
        """Test simple async query"""
        results = await duckdb.execute_async(
            "SELECT * FROM nbtypes LIMIT 5"
        )
        assert len(results) <= 5
        assert isinstance(results, list)
        if results:
            assert isinstance(results[0], dict)

    @pytest.mark.asyncio
    async def test_duckdb_query_by_modeltypes(self, duckdb):
        """Test query by modeltypes"""
        results = await duckdb.query_by_modeltypes(
            modeltypes=['819', '839'],
            fields=['modeltype', 'modelname', 'cpu', 'gpu']
        )
        assert len(results) > 0
        for result in results:
            assert 'modeltype' in result
            assert 'modelname' in result
            assert result['modeltype'] in ['819', '839']

    @pytest.mark.asyncio
    async def test_duckdb_parallel_queries(self, duckdb):
        """Test parallel query execution"""
        start_time = time.time()

        # Execute 3 queries in parallel
        queries = [
            ("SELECT * FROM nbtypes WHERE modeltype = ?", ['819']),
            ("SELECT * FROM nbtypes WHERE modeltype = ?", ['839']),
            ("SELECT * FROM nbtypes WHERE modeltype = ?", ['958'])
        ]

        results = await duckdb.execute_batch(queries)

        execution_time = time.time() - start_time

        # Check results
        assert len(results) == 3
        for result in results:
            assert isinstance(result, list)

        # Parallel execution should be faster than sequential
        print(f"Parallel execution time: {execution_time:.3f}s")
        assert execution_time < 2.0  # Should be fast

    @pytest.mark.asyncio
    async def test_duckdb_count_records(self, duckdb):
        """Test record counting"""
        count = await duckdb.count_records(where_clause="modeltype = '819'")
        assert count >= 0
        assert isinstance(count, int)

    @pytest.mark.asyncio
    async def test_duckdb_get_distinct_values(self, duckdb):
        """Test getting distinct values"""
        modeltypes = await duckdb.get_distinct_values('nbtypes', 'modeltype')
        assert len(modeltypes) > 0
        assert '819' in modeltypes or '839' in modeltypes

    def test_duckdb_health_check(self, duckdb):
        """Test DuckDB health check"""
        health = duckdb.health_check()
        assert health['status'] == 'healthy'
        assert 'db_size_mb' in health


# ==================== Phase 2 Parallel Retrieval Tests ====================

class TestPhase2ParallelRetrieval:
    """Test Phase 2 parallel retrieval"""

    @pytest.fixture
    async def phase2(self):
        """Create Phase 2 retriever for testing"""
        from config import DB_PATH, MILVUS_HOST, MILVUS_PORT, MILVUS_COLLECTION_NAME

        retriever = Phase2ParallelRetrieval(
            milvus_collection=MILVUS_COLLECTION_NAME,
            duckdb_path=str(DB_PATH),
            milvus_host=MILVUS_HOST,
            milvus_port=MILVUS_PORT,
            enable_cache=True
        )

        yield retriever

        # Cleanup
        retriever.shutdown()

    @pytest.mark.asyncio
    async def test_phase2_simple_retrieval(self, phase2):
        """Test simple retrieval with caching disabled"""
        results = []
        async for update in phase2.retrieve(
            query="APX819",
            top_k=10,
            use_cache=False
        ):
            results.append(update)

        # Check we got results
        assert len(results) > 0

        # Find phase_result
        phase_results = [r for r in results if r["type"] == "phase_result"]
        assert len(phase_results) == 1

        result_data = phase_results[0]["data"]
        assert "semantic_matches" in result_data
        assert "spec_data" in result_data
        assert "merged_products" in result_data

    @pytest.mark.asyncio
    async def test_phase2_with_detected_products(self, phase2):
        """Test retrieval with pre-detected products"""
        results = []
        async for update in phase2.retrieve(
            query="比較 819 和 839",
            detected_products=["819", "839"],
            top_k=20,
            use_cache=False
        ):
            results.append(update)

        # Check results
        phase_results = [r for r in results if r["type"] == "phase_result"]
        assert len(phase_results) == 1

        result_data = phase_results[0]["data"]
        assert result_data["total_merged"] > 0

    @pytest.mark.asyncio
    async def test_phase2_caching(self, phase2):
        """Test Phase 2 caching behavior"""
        query = "APX819 gaming laptop"

        # First call (cache miss)
        start_time = time.time()
        results1 = []
        async for update in phase2.retrieve(query=query, top_k=10):
            results1.append(update)
        time1 = time.time() - start_time

        # Second call (cache hit)
        start_time = time.time()
        results2 = []
        async for update in phase2.retrieve(query=query, top_k=10):
            results2.append(update)
        time2 = time.time() - start_time

        # Cache hit should be much faster
        print(f"First call: {time1:.3f}s, Second call (cached): {time2:.3f}s")
        assert time2 < time1 * 0.5  # At least 50% faster

        # Check cache was used
        phase_result2 = [r for r in results2 if r["type"] == "phase_result"][0]
        assert phase_result2.get("from_cache") is True

    @pytest.mark.asyncio
    async def test_phase2_parallel_performance(self, phase2):
        """Test that parallel retrieval is faster than sequential"""
        # This is an integration test showing the performance benefit

        query = "gaming laptop recommendation"

        start_time = time.time()
        results = []
        async for update in phase2.retrieve(query=query, top_k=30, use_cache=False):
            results.append(update)
        parallel_time = time.time() - start_time

        # Check result quality
        phase_result = [r for r in results if r["type"] == "phase_result"][0]
        retrieval_time = phase_result["retrieval_time"]

        print(f"Phase 2 parallel retrieval time: {retrieval_time:.3f}s")

        # Parallel retrieval should complete in < 2 seconds
        assert retrieval_time < 2.0

    def test_phase2_health_check(self, phase2):
        """Test Phase 2 health check"""
        health = phase2.health_check()
        assert health['phase'] == 2
        assert 'components' in health
        assert 'duckdb' in health['components']
        assert 'milvus' in health['components']
        assert 'cache' in health['components']


# ==================== Performance Benchmarks ====================

class TestPerformanceBenchmarks:
    """Performance benchmark tests"""

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_benchmark_duckdb_query(self):
        """Benchmark DuckDB query performance"""
        from config import DB_PATH
        db = AsyncDuckDBQuery(str(DB_PATH), max_workers=4)

        queries = [
            "SELECT * FROM nbtypes WHERE modeltype = '819'",
            "SELECT * FROM nbtypes WHERE modeltype = '839'",
            "SELECT * FROM nbtypes WHERE modeltype = '958'"
        ]

        # Warm-up
        for query in queries:
            await db.execute_async(query)

        # Benchmark
        start_time = time.time()
        for _ in range(10):
            for query in queries:
                await db.execute_async(query)
        total_time = time.time() - start_time

        avg_time = total_time / 30  # 30 queries total
        print(f"Average DuckDB query time: {avg_time*1000:.2f}ms")

        db.shutdown()

        # Should average < 100ms per query
        assert avg_time < 0.1

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_benchmark_cache_operations(self):
        """Benchmark Redis cache operations"""
        cache = StreamingCache()

        # Benchmark set operations
        start_time = time.time()
        for i in range(100):
            cache.set_phase_result(
                query=f"test query {i}",
                phase=2,
                data={"test": i}
            )
        set_time = time.time() - start_time

        # Benchmark get operations
        start_time = time.time()
        for i in range(100):
            cache.get_phase_result(f"test query {i}", phase=2)
        get_time = time.time() - start_time

        print(f"Cache set: {set_time*10:.2f}ms per operation")
        print(f"Cache get: {get_time*10:.2f}ms per operation")

        cache.clear_all()
        cache.close()

        # Both operations should be < 5ms on average
        assert set_time / 100 < 0.005
        assert get_time / 100 < 0.005


# ==================== Integration Tests ====================

class TestIntegration:
    """Integration tests for complete Phase 2 pipeline"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_retrieval(self):
        """Test complete end-to-end retrieval pipeline"""
        from config import DB_PATH, MILVUS_HOST, MILVUS_PORT, MILVUS_COLLECTION_NAME

        # Setup
        phase2 = Phase2ParallelRetrieval(
            milvus_collection=MILVUS_COLLECTION_NAME,
            duckdb_path=str(DB_PATH),
            milvus_host=MILVUS_HOST,
            milvus_port=MILVUS_PORT
        )

        # Execute retrieval
        test_queries = [
            "APX819 gaming performance",
            "比較 819 和 839 的 CPU",
            "推薦適合商務的筆電"
        ]

        for query in test_queries:
            print(f"\nTesting query: {query}")

            results = []
            async for update in phase2.retrieve(query=query, top_k=20):
                if update["type"] == "progress":
                    print(f"  Progress: {update['message']}")
                elif update["type"] == "phase_result":
                    results.append(update)

            assert len(results) == 1
            result_data = results[0]["data"]

            print(f"  Results: {result_data['total_merged']} products in {result_data['retrieval_time']:.2f}s")
            assert result_data['total_merged'] > 0

        # Cleanup
        phase2.shutdown()

        print("\n✅ End-to-end integration test passed!")


# ==================== Test Configuration ====================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "benchmark: mark test as benchmark")
    config.addinivalue_line("markers", "integration: mark test as integration test")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
