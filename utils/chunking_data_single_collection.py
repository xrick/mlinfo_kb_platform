# utils/chunking_data_single_collection.py
# chunking_data_20250902.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loads data from DuckDB, creates semantic chunks, and stores chunks in Milvus collection.
"""

import logging
import duckdb
import sys
import time

from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection
from pymilvus.exceptions import MilvusException
sys.path.append("../")
from libs.chunk_utils.chunking.semantic_chunking.semantic_chunking_engine import SemanticChunkingEngine
import config
# --- Configuration ---
DUCKDB_FILE = config.DB_PATH#"../db/all_nbinfo_v5.db"
MILVUS_COLLECTION_NAME = config.MILVUS_COLLECTION_NAME#"semantic_nb_250926_utf8_collection"#"product_semantic_chunks"
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
EMBEDDING_DIM = 384  # Based on the paraphrase-multilingual-MiniLM-L12-v2 model

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Utility Functions ---
def retry_with_backoff(func, max_retries=3, base_delay=1.0, max_delay=8.0):
    """Execute function with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            return func()
        except MilvusException as e:
            if attempt == max_retries - 1:
                raise e

            delay = min(base_delay * (2 ** attempt), max_delay)
            logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
            time.sleep(delay)

def refresh_milvus_connection():
    """Refresh Milvus connection to clear stale cache."""
    try:
        if connections.has_connection("default"):
            connections.disconnect("default")
            logging.info("Disconnected from Milvus to clear cache.")

        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
        logging.info("Refreshed Milvus connection.")
        return True
    except Exception as e:
        logging.error(f"Failed to refresh Milvus connection: {e}")
        return False

def wait_for_collection_drop(collection_name, max_wait=10.0):
    """Wait for collection to be completely dropped."""
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if not utility.has_collection(collection_name):
            logging.info(f"Collection '{collection_name}' successfully dropped.")
            return True
        time.sleep(0.5)

    logging.warning(f"Collection '{collection_name}' may still exist after {max_wait}s wait.")
    return False

def connect_to_milvus():
    """Establishes robust connection to Milvus with verification."""
    def _connect():
        # Clear any existing connection first
        if connections.has_connection("default"):
            connections.disconnect("default")

        # Establish new connection
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)

        # Verify connection by listing collections
        collections = utility.list_collections()
        logging.info(f"Successfully connected to Milvus. Available collections: {collections}")
        return True

    try:
        return retry_with_backoff(_connect, max_retries=3)
    except Exception as e:
        logging.error(f"Failed to establish Milvus connection after retries: {e}")
        raise

def setup_milvus_collection():
    """Drops the collection if it exists, then creates a new one with robust error handling."""
    def _drop_collection():
        if utility.has_collection(MILVUS_COLLECTION_NAME):
            logging.warning(f"Collection '{MILVUS_COLLECTION_NAME}' exists. Dropping it.")
            utility.drop_collection(MILVUS_COLLECTION_NAME)
            wait_for_collection_drop(MILVUS_COLLECTION_NAME)
        return True

    def _create_collection():
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

    try:
        # Step 1: Drop existing collection with retry
        retry_with_backoff(_drop_collection, max_retries=2)

        # Step 2: Create new collection with retry and connection refresh on failure
        try:
            return retry_with_backoff(_create_collection, max_retries=2)
        except MilvusException as e:
            if "node not match" in str(e) or "InvalidateCollectionMetaCache" in str(e):
                logging.warning("Node mismatch detected. Refreshing connection and retrying...")
                refresh_milvus_connection()
                return retry_with_backoff(_create_collection, max_retries=3)
            else:
                raise e

    except Exception as e:
        logging.error(f"Failed to setup Milvus collection: {e}")
        raise

def process_files():
    """Main function to process all data from DuckDB and create Milvus collection."""
    connect_to_milvus()
    milvus_collection = setup_milvus_collection()

    # Initialize the chunking engine
    chunker = SemanticChunkingEngine()

    try:
        logging.info("--- Loading data from DuckDB ---")

        # Connect to DuckDB and query all data
        con = duckdb.connect(database=DUCKDB_FILE, read_only=True)
        df = con.execute("SELECT * FROM nbtypes").df()
        con.close()

        logging.info(f"Loaded {len(df)} rows from DuckDB table 'nbtypes'.")

        # Ensure modeltype is string to prevent Milvus type errors
        df['modeltype'] = df['modeltype'].astype(str)

        # Generate and store chunks in Milvus
        products = df.to_dict('records')
        parent_chunks, child_chunks = chunker.batch_create_chunks(products)

        all_chunks = parent_chunks + child_chunks
        if not all_chunks:
            logging.warning("No chunks created from the data.")
            return

        logging.info(f"Generated {len(all_chunks)} chunks from {len(df)} products.")

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
        logging.info(f"Inserted {len(entities)} chunks into Milvus collection '{MILVUS_COLLECTION_NAME}'.")

    except Exception as e:
        logging.error(f"Failed to process data from DuckDB: {e}")
        raise

    # Clean up
    milvus_collection.load() # Load collection into memory for searching
    milvus_collection.flush()
    connections.disconnect("default")
    logging.info("--- Data processing completed successfully. ---")

if __name__ == "__main__":
    process_files()
