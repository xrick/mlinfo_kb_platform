import duckdb
from .DatabaseQuery import DatabaseQuery

class DuckDBQuery(DatabaseQuery):
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = duckdb.connect(database=self.db_file, read_only=True)
            print(f"成功連接到 DuckDB: {self.db_file}")
        except Exception as e:
            print(f"連接 DuckDB 失敗: {e}")
            self.connection = None

    def query(self, sql_query: str):
        if not self.connection:
            print("DuckDB 未連接。")
            return None
        try:
            return self.connection.execute(sql_query).fetchall()
        except Exception as e:
            print(f"DuckDB 查詢失敗: {e}")
            return None
        
    def query_with_params(self, sql_query: str, params: list):
        if not self.connection:
            print("DuckDB 未連接。")
            return None
        try:
            return self.connection.execute(sql_query, params).fetchall()
        except Exception as e:
            print(f"DuckDB 參數化查詢失敗: {e}")
            return None

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            print("已斷開 DuckDB 連接。")