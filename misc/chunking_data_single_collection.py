# chunking_data_20250902.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processes raw CSV data, creates semantic chunks, and stores data in Milvus and DuckDB.
"""

import os
import logging
import pandas as pd
import duckdb
from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection
from libs.chunk_utils.chunking.semantic_chunking.semantic_chunking_engine import SemanticChunkingEngine

# --- Configuration ---
SOURCE_DIR = "data/raw/EM_New TTL_241104_AllModelsParsed"
DUCKDB_FILE = "db/all_nbinfo_v2.db"
MILVUS_COLLECTION_NAME = "semantic_nb_spec_250919"#"product_semantic_chunks"
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
EMBEDDING_DIM = 384  # Based on the paraphrase-multilingual-MiniLM-L12-v2 model

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_to_milvus():
    """Establishes connection to Milvus."""
    try:
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
        logging.info("Successfully connected to Milvus.")
    except Exception as e:
        logging.error(f"Failed to connect to Milvus: {e}")
        raise

def setup_milvus_collection():
    """Drops the collection if it exists, then creates a new one."""
    if utility.has_collection(MILVUS_COLLECTION_NAME):
        logging.warning(f"Collection '{MILVUS_COLLECTION_NAME}' exists. Dropping it.")
        utility.drop_collection(MILVUS_COLLECTION_NAME)

    fields = [
        FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, is_primary=True, max_length=256),
        FieldSchema(name="product_id", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="chunk_type", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="semantic_group", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)
    ]
    schema = CollectionSchema(fields, "Product semantic chunks for sales RAG.")
    collection = Collection(MILVUS_COLLECTION_NAME, schema)
    
    # Create an index for the embedding field
    index_params = {
        "metric_type": "L2",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024}
    }
    collection.create_index("embedding", index_params)
    logging.info(f"Collection '{MILVUS_COLLECTION_NAME}' created and indexed.")
    return collection

def process_files():
    """Main function to process all CSV files."""
    connect_to_milvus()
    milvus_collection = setup_milvus_collection()
    
    # Initialize DuckDB connection
    # con = duckdb.connect(database=DUCKDB_FILE, read_only=False)
    
    # Initialize the chunking engine
    chunker = SemanticChunkingEngine()

    files_to_process = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.csv')]
    logging.info(f"Found {len(files_to_process)} CSV files to process.")

    for filename in files_to_process:
        file_path = os.path.join(SOURCE_DIR, filename)
        table_name = f"spec_{os.path.splitext(filename)[0]}" # Use filename as table name

        try:
            logging.info(f"--- Processing file: {filename} ---")
            # Ensure modeltype is read as string to prevent Milvus type errors
            df = pd.read_csv(file_path, dtype={'modeltype': str})
            
            # # 1. Store raw data in DuckDB
            # con.register('df_temp', df)
            # con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df_temp")
            # logging.info(f"Stored raw data in DuckDB table: {table_name}")

            # 2. Generate and store chunks in Milvus
            products = df.to_dict('records')
            parent_chunks, child_chunks = chunker.batch_create_chunks(products)
            
            all_chunks = parent_chunks + child_chunks
            if not all_chunks:
                logging.warning(f"No chunks created for {filename}.")
                continue

            entities = []
            for chunk in all_chunks:
                entities.append({
                    "chunk_id": chunk["chunk_id"],
                    "product_id": chunk["product_id"],
                    "chunk_type": chunk["chunk_type"],
                    "semantic_group": chunk.get("semantic_group", ""),
                    "content": chunk["content"],
                    "embedding": chunk["embedding"]
                })
            
            milvus_collection.insert(entities)
            logging.info(f"Inserted {len(entities)} chunks into Milvus for {filename}.")

        except Exception as e:
            logging.error(f"Failed to process file {filename}: {e}")

    # Clean up
    # con.close()
    milvus_collection.load() # Load collection into memory for searching
    milvus_collection.flush()
    connections.disconnect("default")
    logging.info("--- All files processed. ---")

if __name__ == "__main__":
    process_files()
