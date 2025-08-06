import os
import pandas as pd
import duckdb
from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType
from typing import List, Dict

class DBIngestor:
    def __init__(self):
        self.MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
        self.MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
        self.DUCKDB_FILE = "db/sales_specs.db"  # Adjusted path for lcj_business_ai
        self.COLLECTION_NAME = "sales_notebook_specs"
        self.EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
        self.EMBEDDING_DIM = 384
        self._embedding_model = None
        self.ALL_FIELDS = [
            'modeltype', 'version', 'modelname', 'mainboard', 'devtime', 'pm', 
            'structconfig', 'lcd', 'touchpanel', 'iointerface', 'ledind', 
            'powerbutton', 'keyboard', 'webcamera', 'touchpad', 'fingerprint', 
            'audio', 'battery', 'cpu', 'gpu', 'memory', 'lcdconnector', 'storage', 
            'wifislot', 'thermal', 'tpm', 'rtc', 'wireless', 'lan', 'bluetooth', 
            'softwareconfig', 'ai', 'accessory', 'certifications', 'otherfeatures'
        ]
        self.VECTOR_FIELDS = [
            'modeltype', 'modelname', 'audio', 'battery', 'cpu', 'gpu', 'memory', 
            'storage', 'wifislot', 'thermal', 'wireless', 'lan', 'bluetooth', 'ai', 
            'certifications'
        ]

    @property
    def embedding_model(self):
        """Lazy loading of SentenceTransformer model"""
        if self._embedding_model is None:
            print("載入 SentenceTransformer 模型...")
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer(self.EMBEDDING_MODEL_NAME)
        return self._embedding_model

    def ingest(self, data: List[Dict[str, str]]):
        if not data:
            raise ValueError("Input data cannot be empty")
        
        # Filter out empty records
        valid_data = self._filter_valid_records(data)
        if not valid_data:
            raise ValueError("No valid records found after filtering empty data")
        
        print(f"資料驗證：原始 {len(data)} 筆，有效 {len(valid_data)} 筆，過濾掉 {len(data) - len(valid_data)} 筆空記錄")
        
        # Create DataFrame and ensure all expected columns exist
        df = pd.DataFrame(valid_data)
        
        # Add missing columns with empty strings
        for field in self.ALL_FIELDS:
            if field not in df.columns:
                df[field] = ""
        
        # Select only the expected columns in the correct order
        df = df[self.ALL_FIELDS]
        df = df.astype(str)

        duckdb_count = self._ingest_to_duckdb(df)
        milvus_count = self._ingest_to_milvus(df)

        return duckdb_count, milvus_count

    def _filter_valid_records(self, data: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        過濾掉空記錄，只保留有有效資料的記錄
        
        Args:
            data: 原始資料列表
            
        Returns:
            List[Dict]: 過濾後的有效資料列表
        """
        valid_records = []
        
        for record in data:
            if self._is_valid_record(record):
                valid_records.append(record)
        
        return valid_records
    
    def _is_valid_record(self, record: Dict[str, str]) -> bool:
        """
        檢查記錄是否包含有效資料
        
        Args:
            record: 資料記錄字典
            
        Returns:
            bool: 是否為有效記錄
        """
        if not record:
            return False
        
        # 檢查是否至少有一個非空值
        for key, value in record.items():
            if value and str(value).strip():
                return True
        
        return False

    def _ingest_to_duckdb(self, df: pd.DataFrame) -> int:
        print("--- Ingesting to DuckDB ---")
        try:
            # Check if DuckDB file exists
            db_exists = os.path.exists(self.DUCKDB_FILE)
            if db_exists:
                print(f"Found existing DuckDB file '{self.DUCKDB_FILE}'. Appending data...")
            else:
                print(f"DuckDB file '{self.DUCKDB_FILE}' not found. Creating new database...")
            
            with duckdb.connect(database=self.DUCKDB_FILE, read_only=False) as con:
                # Check if table exists using DuckDB syntax
                table_check = con.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'specs'").fetchone()
                if table_check:
                    print("Found existing 'specs' table. Appending data...")
                else:
                    print("Creating new 'specs' table...")
                
                con.execute(f"CREATE TABLE IF NOT EXISTS specs ({', '.join([f'{col} VARCHAR' for col in self.ALL_FIELDS])})")
                con.execute("INSERT INTO specs SELECT * FROM df")
            
            print(f"Successfully appended {len(df)} rows to DuckDB 'specs' table.")
            return len(df)
        except Exception as e:
            print(f"Error ingesting to DuckDB: {e}")
            raise

    def _ingest_to_milvus(self, df: pd.DataFrame) -> int:
        print("--- Ingesting to Milvus ---")
        try:
            print(f"Connecting to Milvus at {self.MILVUS_HOST}:{self.MILVUS_PORT}...")
            connections.connect("default", host=self.MILVUS_HOST, port=self.MILVUS_PORT)

            if not utility.has_collection(self.COLLECTION_NAME):
                print(f"Collection '{self.COLLECTION_NAME}' not found. Creating new collection...")
                fields = [FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True)]
                for col_name in self.ALL_FIELDS:
                    fields.append(FieldSchema(name=col_name, dtype=DataType.VARCHAR, max_length=2048))
                fields.append(FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.EMBEDDING_DIM))
                schema = CollectionSchema(fields, "Notebook Specifications Knowledge Base")
                collection = Collection(self.COLLECTION_NAME, schema)
                
                print("Creating vector index for embedding field...")
                index_params = {"metric_type": "L2", "index_type": "IVF_FLAT", "params": {"nlist": 128}}
                collection.create_index("embedding", index_params)
                print("New collection created successfully.")
            else:
                print(f"Found existing collection '{self.COLLECTION_NAME}'. Appending data...")
                collection = Collection(self.COLLECTION_NAME)

            # Filter VECTOR_FIELDS to only include columns that exist in the DataFrame
            available_vector_fields = [field for field in self.VECTOR_FIELDS if field in df.columns]
            print(f"Generating embeddings for {len(available_vector_fields)} vector fields...")
            
            texts_to_embed = df[available_vector_fields].apply(
                lambda row: ' '.join([f"{col}: {val}" for col, val in row.items() if val]), 
                axis=1
            ).tolist()
            
            vectors = self.embedding_model.encode(texts_to_embed, show_progress_bar=True)
            
            print("Preparing data for insertion...")
            entities = [df[col].tolist() for col in self.ALL_FIELDS]
            entities.append(vectors.tolist())
            
            collection.insert(entities)
            collection.flush()
            print(f"Successfully appended {len(df)} entities to Milvus collection '{self.COLLECTION_NAME}'.")
            return len(df)
        except Exception as e:
            print(f"Error ingesting to Milvus: {e}")
            raise