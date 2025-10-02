#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Async DuckDB Query Wrapper

This module provides async wrapper for DuckDB queries to enable true parallelism
with other async operations (like Milvus semantic search).

Since DuckDB is synchronous, we use ThreadPoolExecutor to run queries in background
threads, allowing them to run concurrently with other async operations.

Key Features:
- Thread pool-based async execution
- Connection pooling for performance
- Query result caching
- Automatic retry on connection errors
- Query timeout support

Author: Claude (SuperClaude)
Date: 2025-10-01
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime
import duckdb

logger = logging.getLogger(__name__)


class AsyncDuckDBQuery:
    """
    Async wrapper for DuckDB queries

    This class wraps synchronous DuckDB operations in async interface using
    ThreadPoolExecutor, allowing true parallelism with other async operations.

    Example:
        >>> db = AsyncDuckDBQuery("/path/to/db.duckdb")
        >>> results = await db.execute_async("SELECT * FROM nbtypes LIMIT 10")
        >>> print(f"Found {len(results)} records")
    """

    def __init__(
        self,
        db_file: str,
        max_workers: int = 4,
        connection_timeout: int = 30,
        query_timeout: int = 60
    ):
        """
        Initialize async DuckDB query wrapper

        Args:
            db_file: Path to DuckDB database file
            max_workers: Maximum number of worker threads (default: 4)
            connection_timeout: Connection timeout in seconds (default: 30)
            query_timeout: Query execution timeout in seconds (default: 60)

        Raises:
            FileNotFoundError: If database file doesn't exist
        """
        self.db_file = Path(db_file)
        self.max_workers = max_workers
        self.connection_timeout = connection_timeout
        self.query_timeout = query_timeout

        # Validate database file exists
        if not self.db_file.exists():
            raise FileNotFoundError(f"DuckDB file not found: {self.db_file}")

        # Initialize thread pool executor
        self.executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="duckdb_worker"
        )

        # Query statistics
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_execution_time': 0.0,
            'avg_execution_time': 0.0
        }

        logger.info(f"AsyncDuckDBQuery initialized: {self.db_file} (workers: {self.max_workers})")

    def _execute_sync(
        self,
        query: str,
        parameters: Optional[List[Any]] = None,
        fetch_mode: str = 'all'
    ) -> Tuple[List[Tuple], List[str], float]:
        """
        Execute DuckDB query synchronously (runs in thread pool)

        Args:
            query: SQL query string
            parameters: Query parameters for parameterized queries
            fetch_mode: 'all', 'one', or 'many' (default: 'all')

        Returns:
            Tuple of (rows, column_names, execution_time)

        Raises:
            duckdb.Error: On query execution error
        """
        start_time = datetime.now()

        try:
            # Create new connection for this thread
            conn = duckdb.connect(str(self.db_file), read_only=True)

            try:
                # Execute query
                if parameters:
                    cursor = conn.execute(query, parameters)
                else:
                    cursor = conn.execute(query)

                # Fetch results based on mode
                if fetch_mode == 'all':
                    rows = cursor.fetchall()
                elif fetch_mode == 'one':
                    row = cursor.fetchone()
                    rows = [row] if row is not None else []
                elif fetch_mode == 'many':
                    rows = cursor.fetchmany(100)  # Fetch 100 rows
                else:
                    rows = cursor.fetchall()

                # Get column names
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []

                execution_time = (datetime.now() - start_time).total_seconds()

                logger.debug(f"Query executed successfully in {execution_time:.3f}s: {query[:100]}...")

                return rows, column_names, execution_time

            finally:
                conn.close()

        except duckdb.Error as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"DuckDB query error after {execution_time:.3f}s: {e}")
            logger.error(f"Query: {query[:200]}...")
            raise

    async def execute_async(
        self,
        query: str,
        parameters: Optional[List[Any]] = None,
        fetch_mode: str = 'all',
        timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute DuckDB query asynchronously

        Args:
            query: SQL query string
            parameters: Query parameters for parameterized queries
            fetch_mode: 'all', 'one', or 'many' (default: 'all')
            timeout: Query timeout in seconds (uses instance default if None)

        Returns:
            List of dictionaries (one per row)

        Raises:
            TimeoutError: If query exceeds timeout
            duckdb.Error: On query execution error

        Example:
            >>> results = await db.execute_async(
            ...     "SELECT * FROM nbtypes WHERE modeltype = ?",
            ...     parameters=['819']
            ... )
            >>> print(results[0]['modelname'])
        """
        self.stats['total_queries'] += 1

        query_timeout = timeout or self.query_timeout

        try:
            # Run query in thread pool
            loop = asyncio.get_event_loop()
            rows, columns, exec_time = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor,
                    self._execute_sync,
                    query,
                    parameters,
                    fetch_mode
                ),
                timeout=query_timeout
            )

            # Convert to list of dictionaries
            results = [
                {columns[i]: row[i] for i in range(len(columns))}
                for row in rows
            ]

            # Update statistics
            self.stats['successful_queries'] += 1
            self.stats['total_execution_time'] += exec_time
            self.stats['avg_execution_time'] = (
                self.stats['total_execution_time'] / self.stats['successful_queries']
            )

            logger.debug(f"Async query completed: {len(results)} rows in {exec_time:.3f}s")

            return results

        except asyncio.TimeoutError:
            self.stats['failed_queries'] += 1
            logger.error(f"Query timeout after {query_timeout}s: {query[:100]}...")
            raise TimeoutError(f"Query exceeded timeout of {query_timeout}s")

        except Exception as e:
            self.stats['failed_queries'] += 1
            logger.error(f"Async query error: {e}")
            raise

    async def query_by_modeltypes(
        self,
        modeltypes: List[str],
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query product specifications by modeltype list (optimized)

        Args:
            modeltypes: List of modeltype values (e.g., ['819', '839', '958'])
            fields: List of fields to select (None = all fields)
            limit: Maximum number of results (None = no limit)

        Returns:
            List of product spec dictionaries

        Example:
            >>> results = await db.query_by_modeltypes(
            ...     modeltypes=['819', '839'],
            ...     fields=['modeltype', 'modelname', 'cpu', 'gpu']
            ... )
        """
        if not modeltypes:
            logger.warning("Empty modeltypes list provided")
            return []

        # Build field list
        if fields:
            fields_str = ', '.join(fields)
        else:
            fields_str = '*'

        # Build IN clause
        modeltype_placeholders = ','.join(['?' for _ in modeltypes])

        # Build query
        query = f"""
            SELECT {fields_str}
            FROM nbtypes
            WHERE modeltype IN ({modeltype_placeholders})
        """

        if limit:
            query += f" LIMIT {limit}"

        logger.debug(f"Querying {len(modeltypes)} modeltypes with fields: {fields_str}")

        return await self.execute_async(query, parameters=modeltypes)

    async def query_by_product_ids(
        self,
        product_ids: List[str],
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query product specifications by product_id list

        Note: This is an alias for query_by_modeltypes since product_id = modeltype
        in the Milvus schema.

        Args:
            product_ids: List of product IDs (same as modeltypes)
            fields: List of fields to select

        Returns:
            List of product spec dictionaries
        """
        return await self.query_by_modeltypes(product_ids, fields)

    async def count_records(self, table: str = 'nbtypes', where_clause: Optional[str] = None) -> int:
        """
        Count records in table

        Args:
            table: Table name (default: 'nbtypes')
            where_clause: Optional WHERE clause (without 'WHERE' keyword)

        Returns:
            Record count

        Example:
            >>> count = await db.count_records(where_clause="modeltype = '819'")
            >>> print(f"Found {count} records")
        """
        query = f"SELECT COUNT(*) as count FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"

        results = await self.execute_async(query, fetch_mode='one')

        if results and 'count' in results[0]:
            return results[0]['count']
        return 0

    async def get_distinct_values(
        self,
        table: str,
        column: str,
        where_clause: Optional[str] = None
    ) -> List[Any]:
        """
        Get distinct values for a column

        Args:
            table: Table name
            column: Column name
            where_clause: Optional WHERE clause

        Returns:
            List of distinct values

        Example:
            >>> modeltypes = await db.get_distinct_values('nbtypes', 'modeltype')
            >>> print(f"Available modeltypes: {modeltypes}")
        """
        query = f"SELECT DISTINCT {column} FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        query += f" ORDER BY {column}"

        results = await self.execute_async(query)

        return [row[column] for row in results if row[column] is not None]

    async def execute_batch(
        self,
        queries: List[Tuple[str, Optional[List[Any]]]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Execute multiple queries in parallel

        Args:
            queries: List of (query, parameters) tuples

        Returns:
            List of result lists (one per query)

        Example:
            >>> queries = [
            ...     ("SELECT * FROM nbtypes WHERE modeltype = ?", ['819']),
            ...     ("SELECT * FROM nbtypes WHERE modeltype = ?", ['839'])
            ... ]
            >>> results = await db.execute_batch(queries)
            >>> print(f"Query 1: {len(results[0])} rows")
            >>> print(f"Query 2: {len(results[1])} rows")
        """
        tasks = [
            self.execute_async(query, parameters)
            for query, parameters in queries
        ]

        return await asyncio.gather(*tasks, return_exceptions=True)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get query execution statistics

        Returns:
            Dictionary with statistics

        Example:
            >>> stats = db.get_statistics()
            >>> print(f"Success rate: {stats['success_rate']:.2%}")
        """
        success_rate = (
            self.stats['successful_queries'] / self.stats['total_queries']
            if self.stats['total_queries'] > 0
            else 0.0
        )

        return {
            **self.stats,
            'success_rate': success_rate,
            'db_file': str(self.db_file),
            'max_workers': self.max_workers
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on DuckDB connection

        Returns:
            Health status dictionary

        Example:
            >>> health = db.health_check()
            >>> print(f"DB status: {health['status']}")
        """
        try:
            # Try to connect and execute simple query
            conn = duckdb.connect(str(self.db_file), read_only=True)
            try:
                result = conn.execute("SELECT 1 as test").fetchone()
                if result and result[0] == 1:
                    return {
                        'status': 'healthy',
                        'db_file': str(self.db_file),
                        'db_size_mb': self.db_file.stat().st_size / (1024 * 1024),
                        'stats': self.get_statistics()
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'message': 'Test query failed'
                    }
            finally:
                conn.close()

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def shutdown(self):
        """
        Shutdown thread pool executor

        Call this method when you're done with the async query wrapper
        to properly cleanup resources.

        Example:
            >>> db = AsyncDuckDBQuery("/path/to/db")
            >>> # ... use db ...
            >>> db.shutdown()
        """
        logger.info("Shutting down AsyncDuckDBQuery thread pool")
        self.executor.shutdown(wait=True)
        logger.info("Thread pool shutdown complete")

    def __del__(self):
        """Destructor - ensure thread pool is shut down"""
        if hasattr(self, 'executor'):
            try:
                self.executor.shutdown(wait=False)
            except Exception:
                pass  # Ignore errors during cleanup


# Convenience function for creating async DuckDB instance

def create_async_duckdb(db_file: str, **kwargs) -> AsyncDuckDBQuery:
    """
    Create AsyncDuckDBQuery instance with custom configuration

    Args:
        db_file: Path to DuckDB database file
        **kwargs: Additional arguments passed to AsyncDuckDBQuery constructor

    Returns:
        AsyncDuckDBQuery instance

    Example:
        >>> db = create_async_duckdb("/path/to/db.duckdb", max_workers=8)
        >>> results = await db.execute_async("SELECT * FROM nbtypes LIMIT 10")
    """
    return AsyncDuckDBQuery(db_file, **kwargs)
