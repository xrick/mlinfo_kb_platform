import sqlite3
import duckdb
from pathlib import Path
import logging
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for SalesRAG integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # self.db_path = Path(config.get("db_path", "db/sales_specs.db"))
        logger.info(f"@@@@@@@@@@@@@@@@@ Call Init in database.py @@@@@@@@@@@@@@@@")
        self.db_path = Path(config.get("db_path", "db/all_nbinfo_v2.db"))
        self.history_db_path = Path(config.get("history_db_path", "db/history.db"))
        
        # Ensure database directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_duckdb_connection(self):
        """Get DuckDB connection context manager"""
        conn = None
        try:
            conn = duckdb.connect(str(self.db_path), read_only=True)
            yield conn
        except Exception as e:
            logger.error(f"DuckDB connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_history_connection(self):
        """Get history database connection context manager"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.history_db_path))
            yield conn
        except Exception as e:
            logger.error(f"History database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def test_connections(self) -> Dict[str, bool]:
        """Test database connections"""
        results = {}
        
        # Test DuckDB connection
        try:
            with self.get_duckdb_connection() as conn:
                conn.execute("SELECT 1").fetchone()
                results["duckdb"] = True
        except Exception as e:
            logger.error(f"DuckDB test failed: {e}")
            results["duckdb"] = False
        
        # Test History database connection
        try:
            with self.get_history_connection() as conn:
                conn.execute("SELECT 1").fetchone()
                results["history"] = True
        except Exception as e:
            logger.error(f"History database test failed: {e}")
            results["history"] = False
        
        return results
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get table information"""
        try:
            with self.get_duckdb_connection() as conn:
                # Get column information
                columns = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
                
                # Get row count
                row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                
                return {
                    "table_name": table_name,
                    "columns": columns,
                    "row_count": row_count
                }
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            return None
    
    def execute_query(self, query: str, params: List[Any] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        try:
            with self.get_duckdb_connection() as conn:
                if params:
                    results = conn.execute(query, params).fetchall()
                else:
                    results = conn.execute(query).fetchall()
                
                # Get column names
                columns = [desc[0] for desc in conn.description]
                
                # Convert to dict format
                return [dict(zip(columns, row)) for row in results]
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        try:
            with self.get_duckdb_connection() as conn:
                # Get list of tables
                tables = conn.execute("SHOW TABLES").fetchall()
                stats["tables"] = []
                
                for table in tables:
                    table_name = table[0]
                    try:
                        # Get row count for each table
                        row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                        stats["tables"].append({
                            "name": table_name,
                            "row_count": row_count
                        })
                    except Exception as e:
                        logger.error(f"Failed to get stats for table {table_name}: {e}")
                        stats["tables"].append({
                            "name": table_name,
                            "row_count": 0,
                            "error": str(e)
                        })
        
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            stats["error"] = str(e)
        
        return stats
    
    def backup_database(self, backup_path: str) -> bool:
        """Backup database"""
        try:
            import shutil
            shutil.copy2(str(self.db_path), backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def vacuum_database(self) -> bool:
        """Vacuum database to optimize space"""
        try:
            with self.get_duckdb_connection() as conn:
                conn.execute("VACUUM")
                logger.info("Database vacuumed successfully")
                return True
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")
            return False

class HistoryDatabase:
    """Specialized database manager for history records"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """Initialize history database"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS data_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    record_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    status TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON data_history(timestamp)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_status 
                ON data_history(status)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_data_type 
                ON data_history(data_type)
            ''')
    
    @contextmanager
    def get_connection(self):
        """Get database connection context manager"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            logger.error(f"History database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def add_record(self, filename: str, data_type: str, record_count: int, 
                   error_count: int = 0, status: str = "success", 
                   metadata: str = None) -> int:
        """Add history record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO data_history 
                (filename, data_type, record_count, error_count, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (filename, data_type, record_count, error_count, status, metadata))
            
            return cursor.lastrowid
    
    def get_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get history records"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM data_history
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get history statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Basic stats
            cursor.execute('SELECT COUNT(*) FROM data_history')
            total_records = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM data_history WHERE status = "success"')
            success_records = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(record_count) FROM data_history')
            total_processed = cursor.fetchone()[0] or 0
            
            # By data type
            cursor.execute('''
                SELECT data_type, COUNT(*), SUM(record_count)
                FROM data_history
                GROUP BY data_type
            ''')
            type_stats = cursor.fetchall()
            
            return {
                "total_records": total_records,
                "success_records": success_records,
                "total_processed": total_processed,
                "type_stats": {
                    row[0]: {"count": row[1], "processed": row[2]}
                    for row in type_stats
                }
            }