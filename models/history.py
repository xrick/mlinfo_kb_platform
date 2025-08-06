from datetime import datetime
from typing import Dict, Any, Optional
import json
import sqlite3
from pathlib import Path

class HistoryModel:
    """Data history model for tracking processed data"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path(__file__).parent.parent / "db" / "history.db")
        self.init_database()
    
    def init_database(self):
        """Initialize the history database"""
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create history table
        cursor.execute('''
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
        
        conn.commit()
        conn.close()
    
    def add_record(self, filename: str, data_type: str, record_count: int, 
                   error_count: int = 0, status: str = "success", 
                   metadata: Dict[str, Any] = None) -> int:
        """Add a new history record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute('''
            INSERT INTO data_history 
            (filename, data_type, record_count, error_count, status, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (filename, data_type, record_count, error_count, status, metadata_json))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def get_records(self, limit: int = 50) -> list:
        """Get history records"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, filename, data_type, record_count, error_count, 
                   status, timestamp, metadata
            FROM data_history
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        records = cursor.fetchall()
        conn.close()
        
        # Convert to dict format
        history_list = []
        for record in records:
            history_item = {
                "id": record[0],
                "filename": record[1],
                "data_type": record[2],
                "record_count": record[3],
                "error_count": record[4],
                "status": record[5],
                "timestamp": record[6],
                "metadata": json.loads(record[7]) if record[7] else {}
            }
            history_list.append(history_item)
        
        return history_list
    
    def get_record_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific history record by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, filename, data_type, record_count, error_count, 
                   status, timestamp, metadata
            FROM data_history
            WHERE id = ?
        ''', (record_id,))
        
        record = cursor.fetchone()
        conn.close()
        
        if record:
            return {
                "id": record[0],
                "filename": record[1],
                "data_type": record[2],
                "record_count": record[3],
                "error_count": record[4],
                "status": record[5],
                "timestamp": record[6],
                "metadata": json.loads(record[7]) if record[7] else {}
            }
        
        return None
    
    def delete_record(self, record_id: int) -> bool:
        """Delete a history record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM data_history WHERE id = ?', (record_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success
    
    def get_stats(self) -> Dict[str, Any]:
        """Get history statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total records
        cursor.execute('SELECT COUNT(*) FROM data_history')
        total_records = cursor.fetchone()[0]
        
        # Success records
        cursor.execute('SELECT COUNT(*) FROM data_history WHERE status = "success"')
        success_records = cursor.fetchone()[0]
        
        # Total processed
        cursor.execute('SELECT SUM(record_count) FROM data_history')
        total_processed = cursor.fetchone()[0] or 0
        
        # By data type
        cursor.execute('''
            SELECT data_type, COUNT(*), SUM(record_count)
            FROM data_history
            GROUP BY data_type
        ''')
        type_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_records": total_records,
            "success_records": success_records,
            "total_processed": total_processed,
            "type_stats": {
                row[0]: {"count": row[1], "processed": row[2]}
                for row in type_stats
            }
        }
    
    def clear_old_records(self, days: int = 30) -> int:
        """Clear old history records"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM data_history 
            WHERE timestamp < datetime('now', '-{} days')
        '''.format(days))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count