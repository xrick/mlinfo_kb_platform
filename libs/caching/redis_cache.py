#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis-based caching for progressive streaming

This module provides Redis caching infrastructure for the 5-phase streaming pipeline.
It implements intelligent cache key generation, TTL management, and fallback strategies.

Key Features:
- Query-based cache key generation with MD5 hashing
- Phase-specific TTL configuration
- Automatic JSON serialization/deserialization
- Connection pooling and error recovery
- Cache statistics tracking

Author: Claude (SuperClaude)
Date: 2025-10-01
"""

import json
import hashlib
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta

try:
    import redis
    from redis.connection import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    ConnectionPool = None

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Redis cache configuration"""

    host: str = 'localhost'
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    max_connections: int = 50
    decode_responses: bool = True

    # TTL settings (in seconds)
    phase1_ttl: int = 300      # Query understanding: 5 minutes
    phase2_semantic_ttl: int = 300   # Semantic search: 5 minutes
    phase2_spec_ttl: int = 1800      # Spec query: 30 minutes
    phase3_ttl: int = 300      # Context assembly: 5 minutes
    phase4_ttl: int = 1800     # Response generation: 30 minutes

    # Cache key prefixes
    key_prefix: str = 'mlinfo_kb'
    version: str = 'v1'


class CacheStatistics:
    """Track cache performance statistics"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.total_queries = 0
        self.last_reset = datetime.now()

    def record_hit(self):
        """Record cache hit"""
        self.hits += 1
        self.total_queries += 1

    def record_miss(self):
        """Record cache miss"""
        self.misses += 1
        self.total_queries += 1

    def record_error(self):
        """Record cache error"""
        self.errors += 1

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if self.total_queries == 0:
            return 0.0
        return self.hits / self.total_queries

    def get_summary(self) -> Dict[str, Any]:
        """Get statistics summary"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'errors': self.errors,
            'total_queries': self.total_queries,
            'hit_rate': f"{self.hit_rate:.2%}",
            'uptime': str(datetime.now() - self.last_reset)
        }

    def reset(self):
        """Reset statistics"""
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.total_queries = 0
        self.last_reset = datetime.now()


class StreamingCache:
    """
    Redis-based cache manager for progressive streaming pipeline

    This class provides caching functionality for each phase of the streaming pipeline,
    with intelligent key generation, TTL management, and fallback strategies.

    Example:
        >>> cache = StreamingCache()
        >>> cache.set_phase_result(query="APX819 規格", phase=1, data={"intent": "spec_query"})
        >>> result = cache.get_phase_result(query="APX819 規格", phase=1)
        >>> print(result)
        {'intent': 'spec_query'}
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialize Redis cache manager

        Args:
            config: Cache configuration. If None, uses default configuration.

        Raises:
            ImportError: If redis package is not installed
            redis.ConnectionError: If cannot connect to Redis server
        """
        if not REDIS_AVAILABLE:
            logger.error("Redis package not installed. Caching will be disabled.")
            self.enabled = False
            return

        self.config = config or CacheConfig()
        self.enabled = True
        self.stats = CacheStatistics()

        # Initialize connection pool
        try:
            self._init_connection_pool()
            self._test_connection()
            logger.info(f"Redis cache initialized: {self.config.host}:{self.config.port}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            self.enabled = False

    def _init_connection_pool(self):
        """Initialize Redis connection pool"""
        pool_kwargs = {
            'host': self.config.host,
            'port': self.config.port,
            'db': self.config.db,
            'socket_timeout': self.config.socket_timeout,
            'socket_connect_timeout': self.config.socket_connect_timeout,
            'max_connections': self.config.max_connections,
            'decode_responses': self.config.decode_responses
        }

        if self.config.password:
            pool_kwargs['password'] = self.config.password

        self.pool = ConnectionPool(**pool_kwargs)
        self.client = redis.Redis(connection_pool=self.pool)

    def _test_connection(self):
        """Test Redis connection"""
        try:
            self.client.ping()
            logger.info("Redis connection test successful")
        except redis.ConnectionError as e:
            logger.error(f"Redis connection test failed: {e}")
            raise

    def _generate_cache_key(
        self,
        query: str,
        phase: int,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate cache key for query and phase

        Args:
            query: User query string
            phase: Phase number (1-5)
            additional_params: Additional parameters to include in key

        Returns:
            Cache key string in format: {prefix}:{version}:phase{phase}:{hash}

        Example:
            >>> key = cache._generate_cache_key("APX819", phase=2)
            >>> print(key)
            'mlinfo_kb:v1:phase2:a3f5c8b2...'
        """
        # Normalize query
        query_normalized = query.strip().lower()

        # Create hash input
        hash_input = f"{query_normalized}|phase{phase}"

        # Add additional parameters if provided
        if additional_params:
            params_str = json.dumps(additional_params, sort_keys=True, ensure_ascii=False)
            hash_input += f"|{params_str}"

        # Generate MD5 hash
        query_hash = hashlib.md5(hash_input.encode('utf-8')).hexdigest()

        # Build cache key
        cache_key = f"{self.config.key_prefix}:{self.config.version}:phase{phase}:{query_hash}"

        return cache_key

    def _get_ttl_for_phase(self, phase: int) -> int:
        """
        Get TTL (Time To Live) for specific phase

        Args:
            phase: Phase number (1-5)

        Returns:
            TTL in seconds
        """
        ttl_mapping = {
            1: self.config.phase1_ttl,
            2: self.config.phase2_semantic_ttl,
            3: self.config.phase3_ttl,
            4: self.config.phase4_ttl,
            5: self.config.phase1_ttl  # Phase 5 uses same as Phase 1
        }
        return ttl_mapping.get(phase, 300)  # Default: 5 minutes

    def get_phase_result(
        self,
        query: str,
        phase: int,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached result for query and phase

        Args:
            query: User query string
            phase: Phase number (1-5)
            additional_params: Additional parameters used in cache key

        Returns:
            Cached result dictionary, or None if not found

        Example:
            >>> result = cache.get_phase_result("APX819", phase=2)
            >>> if result:
            ...     print(f"Cache hit! Found {len(result['products'])} products")
        """
        if not self.enabled:
            return None

        try:
            cache_key = self._generate_cache_key(query, phase, additional_params)
            cached_data = self.client.get(cache_key)

            if cached_data:
                self.stats.record_hit()
                result = json.loads(cached_data)
                logger.debug(f"Cache HIT for phase {phase}: {cache_key[:50]}...")
                return result
            else:
                self.stats.record_miss()
                logger.debug(f"Cache MISS for phase {phase}: {cache_key[:50]}...")
                return None

        except redis.RedisError as e:
            logger.error(f"Redis error in get_phase_result: {e}")
            self.stats.record_error()
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in get_phase_result: {e}")
            self.stats.record_error()
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_phase_result: {e}")
            self.stats.record_error()
            return None

    def set_phase_result(
        self,
        query: str,
        phase: int,
        data: Dict[str, Any],
        additional_params: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache result for query and phase

        Args:
            query: User query string
            phase: Phase number (1-5)
            data: Data to cache (must be JSON-serializable)
            additional_params: Additional parameters used in cache key
            ttl: Custom TTL in seconds. If None, uses phase-specific default.

        Returns:
            True if cached successfully, False otherwise

        Example:
            >>> success = cache.set_phase_result(
            ...     query="APX819",
            ...     phase=2,
            ...     data={"products": [...], "count": 1}
            ... )
            >>> print(f"Cache set: {success}")
        """
        if not self.enabled:
            return False

        try:
            cache_key = self._generate_cache_key(query, phase, additional_params)

            # Use custom TTL or phase-specific default
            cache_ttl = ttl if ttl is not None else self._get_ttl_for_phase(phase)

            # Add metadata
            cache_data = {
                'data': data,
                'metadata': {
                    'query': query,
                    'phase': phase,
                    'cached_at': datetime.now().isoformat(),
                    'ttl': cache_ttl
                }
            }

            # Serialize and cache
            serialized = json.dumps(cache_data, ensure_ascii=False)
            self.client.setex(cache_key, cache_ttl, serialized)

            logger.debug(f"Cache SET for phase {phase}: {cache_key[:50]}... (TTL: {cache_ttl}s)")
            return True

        except redis.RedisError as e:
            logger.error(f"Redis error in set_phase_result: {e}")
            self.stats.record_error()
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Serialization error in set_phase_result: {e}")
            self.stats.record_error()
            return False
        except Exception as e:
            logger.error(f"Unexpected error in set_phase_result: {e}")
            self.stats.record_error()
            return False

    def invalidate_phase(self, query: str, phase: int) -> bool:
        """
        Invalidate cached result for specific query and phase

        Args:
            query: User query string
            phase: Phase number (1-5)

        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            cache_key = self._generate_cache_key(query, phase)
            deleted = self.client.delete(cache_key)
            logger.debug(f"Cache invalidated for phase {phase}: {cache_key[:50]}...")
            return deleted > 0
        except redis.RedisError as e:
            logger.error(f"Redis error in invalidate_phase: {e}")
            return False

    def invalidate_query(self, query: str) -> int:
        """
        Invalidate all cached results for a specific query (all phases)

        Args:
            query: User query string

        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0

        try:
            deleted_count = 0
            for phase in range(1, 6):
                cache_key = self._generate_cache_key(query, phase)
                deleted = self.client.delete(cache_key)
                deleted_count += deleted

            logger.info(f"Invalidated {deleted_count} cache entries for query: {query[:50]}...")
            return deleted_count
        except redis.RedisError as e:
            logger.error(f"Redis error in invalidate_query: {e}")
            return 0

    def clear_all(self) -> bool:
        """
        Clear all cache entries for this application

        Warning: This will delete all keys matching the key_prefix pattern.

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            pattern = f"{self.config.key_prefix}:{self.config.version}:*"
            keys = self.client.keys(pattern)

            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Cleared {deleted} cache entries")
                return True
            else:
                logger.info("No cache entries to clear")
                return True

        except redis.RedisError as e:
            logger.error(f"Redis error in clear_all: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache performance statistics

        Returns:
            Dictionary with cache statistics

        Example:
            >>> stats = cache.get_statistics()
            >>> print(f"Cache hit rate: {stats['hit_rate']}")
        """
        stats = self.stats.get_summary()
        stats['enabled'] = self.enabled
        stats['redis_info'] = self._get_redis_info() if self.enabled else None
        return stats

    def _get_redis_info(self) -> Dict[str, Any]:
        """Get Redis server information"""
        try:
            info = self.client.info('stats')
            return {
                'total_connections_received': info.get('total_connections_received', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0)
            }
        except Exception as e:
            logger.error(f"Error getting Redis info: {e}")
            return {}

    def health_check(self) -> Dict[str, Any]:
        """
        Perform cache health check

        Returns:
            Dictionary with health status

        Example:
            >>> health = cache.health_check()
            >>> print(f"Cache status: {health['status']}")
        """
        if not self.enabled:
            return {
                'status': 'disabled',
                'message': 'Redis cache is disabled'
            }

        try:
            # Test connection
            self.client.ping()

            # Get memory info
            info = self.client.info('memory')

            return {
                'status': 'healthy',
                'redis_version': self.client.info('server').get('redis_version', 'unknown'),
                'used_memory_human': info.get('used_memory_human', 'unknown'),
                'connected_clients': self.client.info('clients').get('connected_clients', 0),
                'stats': self.stats.get_summary()
            }

        except redis.ConnectionError:
            return {
                'status': 'unhealthy',
                'message': 'Cannot connect to Redis server'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def close(self):
        """Close Redis connection pool"""
        if self.enabled and hasattr(self, 'pool'):
            try:
                self.pool.disconnect()
                logger.info("Redis connection pool closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection pool: {e}")


# Convenience functions for quick cache operations

def get_default_cache() -> StreamingCache:
    """
    Get default cache instance with standard configuration

    Returns:
        StreamingCache instance

    Example:
        >>> cache = get_default_cache()
        >>> cache.set_phase_result("test query", phase=1, data={"result": "test"})
    """
    return StreamingCache()


# Module-level cache instance (singleton pattern)
_default_cache_instance: Optional[StreamingCache] = None


def get_cache_instance() -> StreamingCache:
    """
    Get or create singleton cache instance

    Returns:
        StreamingCache singleton instance

    Example:
        >>> cache = get_cache_instance()
        >>> health = cache.health_check()
    """
    global _default_cache_instance
    if _default_cache_instance is None:
        _default_cache_instance = StreamingCache()
    return _default_cache_instance
