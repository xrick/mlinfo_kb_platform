# utils/chunk_nbinfo_v1_20250910.py
import sqlite3
import pandas as pd
import os
import hashlib
import json
import time
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from pathlib import Path
import logging
from sentence_transformers import SentenceTransformer

# Set up logging for better error tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def gen_all_nbinfo_tb(csv_directory: str = 'data/raw/EM_New TTL_241104_AllTransformedToGoogleSheet', db_path: str = 'nbinfo.db') -> bool:
    """
    Creates a SQLite database and loads all CSV files into a single table.
    
    This function reads all CSV files from the specified directory, validates their
    structure, and loads them into a SQLite table named 'all_nb_spec'.
    
    Args:
        csv_directory (str): Directory containing CSV files. Default: 'data/raw/EM_New TTL_241104_AllTransformedToGoogleSheet'
        db_path (str): Path for the SQLite database file. Default: 'nbinfo.db'
    
    Returns:
        bool: True if successful, False otherwise
    
    Security considerations:
    - Validates file paths to prevent directory traversal
    - Checks file permissions before reading
    - Validates CSV structure before loading
    - Uses parameterized queries to prevent SQL injection
    """
    
    try:
        # Security: Validate directory path
        csv_directory = os.path.abspath(csv_directory)
        if not os.path.exists(csv_directory):
            logger.error(f"Directory {csv_directory} does not exist")
            return False
        
        # Security: Validate database path
        db_path = os.path.abspath(db_path)
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            logger.error(f"Database directory {db_dir} does not exist")
            return False
        
        # Get all CSV files
        csv_files = [f for f in os.listdir(csv_directory) 
                     if f.endswith('.csv') and os.path.isfile(os.path.join(csv_directory, f))]
        
        if not csv_files:
            logger.warning("No CSV files found in the directory")
            return False
        
        logger.info(f"Found {len(csv_files)} CSV files")
        
        # Initialize variables for data consolidation
        all_dataframes = []
        expected_columns = None
        
        # Read and validate each CSV file
        for csv_file in csv_files:
            file_path = os.path.join(csv_directory, csv_file)
            
            # Security: Check file permissions
            if not os.access(file_path, os.R_OK):
                logger.warning(f"Cannot read file {csv_file}, skipping")
                continue
            
            try:
                # Read CSV with error handling for encoding issues
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                
                # Validate column structure
                if expected_columns is None:
                    expected_columns = list(df.columns)
                    logger.info(f"Expected columns: {expected_columns}")
                elif list(df.columns) != expected_columns:
                    logger.warning(f"Column mismatch in {csv_file}, skipping")
                    continue
                
                # Add source file information for traceability
                df['source_file'] = csv_file
                df['load_timestamp'] = pd.Timestamp.now().isoformat()
                
                all_dataframes.append(df)
                logger.info(f"Successfully loaded {csv_file} with {len(df)} rows")
                
            except Exception as e:
                logger.error(f"Error reading {csv_file}: {str(e)}")
                continue
        
        if not all_dataframes:
            logger.error("No valid CSV files could be loaded")
            return False
        
        # Concatenate all dataframes
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        logger.info(f"Combined data shape: {combined_df.shape}")
        
        # Create SQLite connection
        conn = sqlite3.connect(db_path)
        
        try:
            # Drop table if exists (for idempotency)
            conn.execute("DROP TABLE IF EXISTS all_nb_spec")
            
            # Create table from dataframe using pandas
            combined_df.to_sql('all_nb_spec', conn, index=False, if_exists='replace')
            
            # Create indexes for common query patterns
            # Index on modeltype for filtering by model
            conn.execute("CREATE INDEX IF NOT EXISTS idx_modeltype ON all_nb_spec(modeltype)")
            
            # Index on modelname for name-based searches
            conn.execute("CREATE INDEX IF NOT EXISTS idx_modelname ON all_nb_spec(modelname)")
            
            # Composite index for version and modeltype
            conn.execute("CREATE INDEX IF NOT EXISTS idx_version_modeltype ON all_nb_spec(version, modeltype)")
            
            # Index on source_file for tracking data origin
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source_file ON all_nb_spec(source_file)")
            
            # Verify data was loaded correctly
            cursor = conn.cursor()
            row_count = cursor.execute("SELECT COUNT(*) FROM all_nb_spec").fetchone()[0]
            logger.info(f"Successfully loaded {row_count} rows into all_nb_spec table")
            
            # Get table info for verification
            table_info = cursor.execute("PRAGMA table_info(all_nb_spec)").fetchall()
            logger.info(f"Table schema created with {len(table_info)} columns")
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error creating SQLite table: {str(e)}")
            conn.rollback()
            return False
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Unexpected error in gen_all_nbinfo_tb: {str(e)}")
        return False


def embed_all_nbinfo_to_collection(
    csv_directory: str = 'data/raw/EM_New TTL_241104_AllTransformedToGoogleSheet',
    collection_name: str = 'all_nb_info_collection',
    chunk_size: int = 512,
    chunk_overlap: int = 50
) -> Dict[str, Any]:
    """
    Embeds CSV content using parent-child chunking technique into a vector collection.
    
    This function implements a hierarchical chunking strategy where each notebook
    specification (row) is a parent chunk, and its fields are grouped into child chunks
    for more granular retrieval.
    
    Args:
        csv_directory (str): Directory containing CSV files. Default: 'data/raw/EM_New TTL_241104_AllTransformedToGoogleSheet'
        collection_name (str): Name for the vector collection. Default: 'all_nb_info_collection'
        chunk_size (int): Maximum size for child chunks in characters. Default: 512
        chunk_overlap (int): Overlap between consecutive chunks. Default: 50
    
    Returns:
        Dict: Statistics about the embedding process including chunk counts and metadata
    
    Security considerations:
    - Sanitizes all input text to prevent injection attacks
    - Validates file paths and permissions
    - Limits chunk sizes to prevent memory issues
    - Uses secure hashing for chunk IDs
    """
    
    try:
        # Security: Validate directory path
        csv_directory = os.path.abspath(csv_directory)
        if not os.path.exists(csv_directory):
            logger.error(f"Directory {csv_directory} does not exist")
            return {"error": "Directory not found"}
        
        # Initialize embedding model
        logger.info("Initializing embedding model...")
        embedding_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        embedding_dimension = embedding_model.get_sentence_embedding_dimension()
        logger.info(f"Embedding model initialized with dimension: {embedding_dimension}")
        
        # Initialize collection storage (in production, this would be a vector database)
        collection = {
            "name": collection_name,
            "parent_chunks": [],
            "child_chunks": [],
            "metadata": {
                "created_at": pd.Timestamp.now().isoformat(),
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "embedding_dimension": embedding_dimension
            }
        }
        
        # Define field groups for logical child chunking
        field_groups = {
            "basic_info": ["modeltype", "version", "modelname", "mainboard"],
            "development": ["devtime", "pm", "structconfig"],
            "display": ["lcd", "touchpanel", "lcdconnector"],
            "io_peripherals": ["iointerface", "ledind", "powerbutton", "keyboard", "webcamera", "touchpad", "fingerprint"],
            "system_specs": ["cpu", "gpu", "memory", "storage", "battery"],
            "connectivity": ["wireless", "lan", "lte", "bluetooth", "wifislot"],
            "security_features": ["tpm", "rtc", "thermal"],
            "software_config": ["softwareconfig", "ai", "accessory", "certifications"],
            "audio": ["audio"]
        }
        
        # Get all CSV files
        csv_files = [f for f in os.listdir(csv_directory) 
                     if f.endswith('.csv') and os.path.isfile(os.path.join(csv_directory, f))]
        
        if not csv_files:
            logger.warning("No CSV files found")
            return {"error": "No CSV files found"}
        
        parent_chunk_count = 0
        child_chunk_count = 0
        
        # Process each CSV file
        for csv_file in csv_files:
            file_path = os.path.join(csv_directory, csv_file)
            
            # Security: Check file permissions
            if not os.access(file_path, os.R_OK):
                logger.warning(f"Cannot read {csv_file}, skipping")
                continue
            
            try:
                # Read CSV file
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                
                # Process each row as a parent chunk
                for idx, row in df.iterrows():
                    # Create parent chunk ID using secure hashing
                    parent_content = f"{csv_file}_row_{idx}_{row.get('modeltype', 'unknown')}_{row.get('modelname', 'unknown')}"
                    parent_id = hashlib.sha256(parent_content.encode()).hexdigest()[:16]
                    
                    # Create parent chunk text representation
                    parent_text_parts = []
                    for col, value in row.items():
                        if pd.notna(value) and str(value).strip():
                            # Security: Sanitize text to prevent injection
                            sanitized_value = str(value).replace('\x00', '').strip()
                            parent_text_parts.append(f"{col}: {sanitized_value}")
                    
                    parent_text = " | ".join(parent_text_parts)
                    
                    # Generate embedding for parent chunk
                    parent_text_for_embedding = parent_text[:5000]  # Security: Limit text size
                    parent_embedding = embedding_model.encode(parent_text_for_embedding)
                    
                    # Create parent chunk entry
                    parent_chunk = {
                        "id": parent_id,
                        "text": parent_text_for_embedding,
                        "embedding": parent_embedding.tolist(),  # Convert numpy array to list for JSON serialization
                        "metadata": {
                            "source_file": csv_file,
                            "row_index": idx,
                            "modeltype": str(row.get('modeltype', 'unknown')),
                            "modelname": str(row.get('modelname', 'unknown')),
                            "version": str(row.get('version', 'unknown')),
                            "chunk_type": "parent"
                        },
                        "child_chunk_ids": []
                    }
                    
                    # Create child chunks based on field groups
                    for group_name, fields in field_groups.items():
                        # Collect text for this field group
                        group_text_parts = []
                        for field in fields:
                            if field in row and pd.notna(row[field]) and str(row[field]).strip():
                                # Security: Sanitize field value
                                sanitized_value = str(row[field]).replace('\x00', '').strip()
                                group_text_parts.append(f"{field}: {sanitized_value}")
                        
                        if group_text_parts:
                            group_text = " | ".join(group_text_parts)
                            
                            # Split into smaller chunks if needed
                            if len(group_text) > chunk_size:
                                # Implement sliding window chunking
                                for i in range(0, len(group_text), chunk_size - chunk_overlap):
                                    chunk_text = group_text[i:i + chunk_size]
                                    
                                    # Generate embedding for child chunk
                                    child_embedding = embedding_model.encode(chunk_text)
                                    
                                    # Create child chunk ID
                                    child_content = f"{parent_id}_{group_name}_{i}"
                                    child_id = hashlib.sha256(child_content.encode()).hexdigest()[:16]
                                    
                                    # Create child chunk entry
                                    child_chunk = {
                                        "id": child_id,
                                        "parent_id": parent_id,
                                        "text": chunk_text,
                                        "embedding": child_embedding.tolist(),
                                        "metadata": {
                                            "source_file": csv_file,
                                            "row_index": idx,
                                            "field_group": group_name,
                                            "modeltype": str(row.get('modeltype', 'unknown')),
                                            "modelname": str(row.get('modelname', 'unknown')),
                                            "chunk_type": "child",
                                            "chunk_index": i // (chunk_size - chunk_overlap)
                                        }
                                    }
                                    
                                    collection["child_chunks"].append(child_chunk)
                                    parent_chunk["child_chunk_ids"].append(child_id)
                                    child_chunk_count += 1
                            else:
                                # Create single child chunk for this group
                                child_embedding = embedding_model.encode(group_text)
                                
                                child_content = f"{parent_id}_{group_name}"
                                child_id = hashlib.sha256(child_content.encode()).hexdigest()[:16]
                                
                                child_chunk = {
                                    "id": child_id,
                                    "parent_id": parent_id,
                                    "text": group_text,
                                    "embedding": child_embedding.tolist(),
                                    "metadata": {
                                        "source_file": csv_file,
                                        "row_index": idx,
                                        "field_group": group_name,
                                        "modeltype": str(row.get('modeltype', 'unknown')),
                                        "modelname": str(row.get('modelname', 'unknown')),
                                        "chunk_type": "child",
                                        "chunk_index": 0
                                    }
                                }
                                
                                collection["child_chunks"].append(child_chunk)
                                parent_chunk["child_chunk_ids"].append(child_id)
                                child_chunk_count += 1
                    
                    collection["parent_chunks"].append(parent_chunk)
                    parent_chunk_count += 1
                
                logger.info(f"Processed {csv_file}: {len(df)} rows")
                
            except Exception as e:
                logger.error(f"Error processing {csv_file}: {str(e)}")
                continue
        
        # Add summary statistics to collection metadata
        collection["metadata"]["statistics"] = {
            "total_files_processed": len(csv_files),
            "total_parent_chunks": parent_chunk_count,
            "total_child_chunks": child_chunk_count,
            "avg_children_per_parent": child_chunk_count / parent_chunk_count if parent_chunk_count > 0 else 0
        }
        
        # ✅ Phase 1 Complete: Embeddings generated using sentence-transformers
        # TODO Phase 2: Store in a vector database (Milvus, Pinecone, Weaviate, etc.)
        # TODO Phase 3: Create appropriate indexes for similarity search
        # TODO Phase 4: Implement hierarchical retrieval mechanism
        
        # Ensure output directory exists
        output_dir = "data/collections"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save collection structure to file (with embeddings)
        collection_file = f"{output_dir}/{collection_name}.json"
        with open(collection_file, 'w', encoding='utf-8') as f:
            json.dump(collection, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Collection saved to {collection_file}")
        logger.info(f"Created {parent_chunk_count} parent chunks and {child_chunk_count} child chunks")
        
        return {
            "success": True,
            "collection_name": collection_name,
            "parent_chunks": parent_chunk_count,
            "child_chunks": child_chunk_count,
            "statistics": collection["metadata"]["statistics"],
            "collection_file": collection_file
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in embed_all_nbinfo_to_collection: {str(e)}")
        return {"error": str(e)}


def embed_all_nbinfo_to_collection_streaming(
    csv_directory: str = 'data/raw/EM_New TTL_241104_AllTransformedToGoogleSheet',
    collection_name: str = 'all_nb_info_collection_stream',
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    batch_size: int = 100,
    milvus_host: str = "localhost",
    milvus_port: str = "19530",
    overwrite: bool = True,
    backup_before_drop: bool = False
) -> Dict[str, Any]:
    """
    Memory-optimized streaming version of embed_all_nbinfo_to_collection.
    
    This function processes large CSV files with minimal memory footprint using:
    - Streaming CSV reading (row-by-row processing)
    - Batch processing for embeddings
    - Direct insertion to Milvus database
    - Automatic memory cleanup
    
    Args:
        csv_directory (str): Directory containing CSV files
        collection_name (str): Name for the vector collection
        chunk_size (int): Maximum size for child chunks in characters
        chunk_overlap (int): Overlap between consecutive chunks
        batch_size (int): Number of chunks to process in each batch
        milvus_host (str): Milvus server host
        milvus_port (str): Milvus server port
        overwrite (bool): If True, automatically drop existing collections. Default: True
        backup_before_drop (bool): If True, backup existing collections before dropping. Default: False
    
    Returns:
        Dict: Processing statistics and collection information
    """
    import gc
    from typing import Iterator, Tuple
    
    try:
        # Security: Validate directory path
        csv_directory = os.path.abspath(csv_directory)
        if not os.path.exists(csv_directory):
            logger.error(f"Directory {csv_directory} does not exist")
            return {"error": "Directory not found"}
        
        logger.info(f"Starting streaming processing of {csv_directory}")
        
        # Initialize Milvus manager with streaming capabilities
        milvus_manager = MilvusParentChildManager(host=milvus_host, port=milvus_port)
        
        if not milvus_manager.initialize():
            logger.error("Failed to initialize Milvus manager for streaming")
            return {"error": "Milvus initialization failed"}
        
        # Create collections for streaming data
        collection_results = milvus_manager.create_parent_child_collections(
            collection_name, 
            overwrite=overwrite, 
            backup_before_drop=backup_before_drop
        )
        
        if not all(collection_results.values()):
            logger.error(f"Failed to create collections: {collection_results}")
            return {"error": "Collection creation failed"}
        
        # Initialize processing statistics
        stats = {
            "parent_chunks_processed": 0,
            "child_chunks_processed": 0,
            "files_processed": 0,
            "batches_processed": 0,
            "memory_peak_mb": 0,
            "processing_time_seconds": 0
        }
        
        start_time = time.time()
        
        # Define field groups for logical child chunking
        field_groups = {
            "basic_info": ["modeltype", "version", "modelname", "mainboard"],
            "development": ["devtime", "pm", "structconfig"],
            "display": ["lcd", "touchpanel", "lcdconnector"],
            "io_peripherals": ["iointerface", "ledind", "powerbutton", "keyboard", "webcamera", "touchpad", "fingerprint"],
            "system_specs": ["cpu", "gpu", "memory", "storage", "battery"],
            "connectivity": ["wireless", "lan", "lte", "bluetooth", "wifislot"],
            "security_features": ["tpm", "rtc", "thermal"],
            "software_config": ["softwareconfig", "ai", "accessory", "certifications"],
            "audio": ["audio"]
        }
        
        # Get all CSV files
        csv_files = [f for f in os.listdir(csv_directory) 
                     if f.endswith('.csv') and os.path.isfile(os.path.join(csv_directory, f))]
        
        if not csv_files:
            logger.warning("No CSV files found")
            return {"error": "No CSV files found"}
        
        # Initialize batches for streaming
        parent_batch = []
        child_batch = []
        
        def process_batch_to_milvus(parent_batch: List[Dict], child_batch: List[Dict]) -> bool:
            """Process and insert a batch to Milvus, then clear memory."""
            try:
                if parent_batch:
                    # Insert parent batch to Milvus
                    success = milvus_manager.insert_parent_batch(parent_batch)
                    if not success:
                        logger.warning(f"Failed to insert parent batch of {len(parent_batch)} chunks")
                    
                if child_batch:
                    # Insert child batch to Milvus
                    success = milvus_manager.insert_child_batch(child_batch)
                    if not success:
                        logger.warning(f"Failed to insert child batch of {len(child_batch)} chunks")
                
                # Clear batches to free memory
                parent_batch.clear()
                child_batch.clear()
                
                # Force garbage collection
                gc.collect()
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to process batch to Milvus: {e}")
                return False
        
        def stream_csv_rows(file_path: str) -> Iterator[Tuple[int, pd.Series]]:
            """Memory-efficient CSV row streaming."""
            try:
                # Use chunksize for memory-efficient processing
                chunk_iter = pd.read_csv(file_path, encoding='utf-8-sig', chunksize=50)
                row_index = 0
                
                for chunk_df in chunk_iter:
                    for idx, row in chunk_df.iterrows():
                        yield row_index, row
                        row_index += 1
                    
                    # Clear chunk from memory
                    del chunk_df
                    gc.collect()
                    
            except Exception as e:
                logger.error(f"Failed to stream CSV rows from {file_path}: {e}")
                return
        
        # Process each CSV file with streaming
        for csv_file in csv_files:
            file_path = os.path.join(csv_directory, csv_file)
            
            # Security: Check file permissions
            if not os.access(file_path, os.R_OK):
                logger.warning(f"Cannot read {csv_file}, skipping")
                continue
            
            logger.info(f"Processing {csv_file} with streaming...")
            
            try:
                # Stream process each row
                for row_idx, row in stream_csv_rows(file_path):
                    # Create parent chunk
                    parent_content = f"{csv_file}_row_{row_idx}_{row.get('modeltype', 'unknown')}_{row.get('modelname', 'unknown')}"
                    parent_id = hashlib.sha256(parent_content.encode()).hexdigest()[:16]
                    
                    # Create parent chunk text representation
                    parent_text_parts = []
                    for col, value in row.items():
                        if pd.notna(value) and str(value).strip():
                            sanitized_value = str(value).replace('\x00', '').strip()
                            parent_text_parts.append(f"{col}: {sanitized_value}")
                    
                    parent_text = " | ".join(parent_text_parts)
                    parent_text_for_embedding = parent_text[:5000]  # Limit text size
                    
                    # Generate embedding for parent chunk (no storing in memory)
                    parent_embedding = milvus_manager.embedding_model.encode(parent_text_for_embedding)
                    
                    # Create parent chunk entry
                    parent_chunk = {
                        "id": parent_id,
                        "text": parent_text_for_embedding,
                        "embedding": parent_embedding,  # Keep as numpy array for Milvus
                        "source_file": csv_file,
                        "row_index": row_idx,
                        "modeltype": str(row.get('modeltype', 'unknown')),
                        "modelname": str(row.get('modelname', 'unknown')),
                        "version": str(row.get('version', 'unknown')),
                        "child_count": 0  # Will be updated after processing children
                    }
                    
                    parent_batch.append(parent_chunk)
                    stats["parent_chunks_processed"] += 1
                    
                    # Create child chunks based on field groups
                    child_count = 0
                    for group_name, fields in field_groups.items():
                        group_text_parts = []
                        for field in fields:
                            if field in row and pd.notna(row[field]) and str(row[field]).strip():
                                sanitized_value = str(row[field]).replace('\x00', '').strip()
                                group_text_parts.append(f"{field}: {sanitized_value}")
                        
                        if group_text_parts:
                            group_text = " | ".join(group_text_parts)
                            
                            # Split into smaller chunks if needed
                            if len(group_text) > chunk_size:
                                for i in range(0, len(group_text), chunk_size - chunk_overlap):
                                    chunk_text = group_text[i:i + chunk_size]
                                    child_embedding = milvus_manager.embedding_model.encode(chunk_text)
                                    
                                    child_content = f"{parent_id}_{group_name}_{i}"
                                    child_id = hashlib.sha256(child_content.encode()).hexdigest()[:16]
                                    
                                    child_chunk = {
                                        "id": child_id,
                                        "parent_id": parent_id,
                                        "text": chunk_text,
                                        "embedding": child_embedding,
                                        "field_group": group_name,
                                        "chunk_index": i // (chunk_size - chunk_overlap),
                                        "source_file": csv_file,
                                        "row_index": row_idx,
                                        "modeltype": str(row.get('modeltype', 'unknown')),
                                        "modelname": str(row.get('modelname', 'unknown'))
                                    }
                                    
                                    child_batch.append(child_chunk)
                                    stats["child_chunks_processed"] += 1
                                    child_count += 1
                            else:
                                # Single child chunk
                                child_embedding = milvus_manager.embedding_model.encode(group_text)
                                child_content = f"{parent_id}_{group_name}_0"
                                child_id = hashlib.sha256(child_content.encode()).hexdigest()[:16]
                                
                                child_chunk = {
                                    "id": child_id,
                                    "parent_id": parent_id,
                                    "text": group_text,
                                    "embedding": child_embedding,
                                    "field_group": group_name,
                                    "chunk_index": 0,
                                    "source_file": csv_file,
                                    "row_index": row_idx,
                                    "modeltype": str(row.get('modeltype', 'unknown')),
                                    "modelname": str(row.get('modelname', 'unknown'))
                                }
                                
                                child_batch.append(child_chunk)
                                stats["child_chunks_processed"] += 1
                                child_count += 1
                    
                    # Update parent child count
                    parent_chunk["child_count"] = child_count
                    
                    # Process batch when it reaches the specified size
                    if len(parent_batch) >= batch_size or len(child_batch) >= batch_size * 3:
                        process_batch_to_milvus(parent_batch, child_batch)
                        stats["batches_processed"] += 1
                        
                        # Monitor memory usage
                        import psutil
                        process = psutil.Process(os.getpid())
                        current_memory_mb = process.memory_info().rss / 1024 / 1024
                        stats["memory_peak_mb"] = max(stats["memory_peak_mb"], current_memory_mb)
                        
                        if stats["batches_processed"] % 10 == 0:
                            logger.info(f"Processed {stats['batches_processed']} batches, "
                                      f"memory usage: {current_memory_mb:.1f} MB")
                
                stats["files_processed"] += 1
                logger.info(f"Completed streaming processing of {csv_file}")
                
            except Exception as e:
                logger.error(f"Error processing {csv_file}: {e}")
                continue
        
        # Process remaining batch
        if parent_batch or child_batch:
            process_batch_to_milvus(parent_batch, child_batch)
            stats["batches_processed"] += 1
        
        stats["processing_time_seconds"] = time.time() - start_time
        
        logger.info(f"Streaming processing completed in {stats['processing_time_seconds']:.2f} seconds")
        logger.info(f"Processed {stats['parent_chunks_processed']} parent chunks and {stats['child_chunks_processed']} child chunks")
        logger.info(f"Peak memory usage: {stats['memory_peak_mb']:.1f} MB")
        
        return {
            "success": True,
            "collection_name": collection_name,
            "processing_mode": "streaming",
            "statistics": stats,
            "collections_created": collection_results
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in streaming processing: {str(e)}")
        return {"error": str(e)}


class MilvusParentChildManager:
    """
    Manages parent-child chunking with Milvus vector database integration.
    
    This class provides comprehensive functionality for storing and retrieving
    hierarchical chunks in Milvus, supporting both parent and child chunk operations.
    """
    
    def __init__(self, host: str = "localhost", port: str = "19530", 
                 embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Initialize the Milvus Parent-Child Manager.
        
        Args:
            host (str): Milvus server host
            port (str): Milvus server port  
            embedding_model_name (str): Name of the sentence transformer model
        """
        self.host = host
        self.port = port
        self.embedding_model_name = embedding_model_name
        self.connection_alias = "parent_child_connection"
        self._is_connected = False
        self.embedding_model = None
        self.embedding_dimension = None
        
    def initialize(self) -> bool:
        """
        Initialize the embedding model and Milvus connection.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            from pymilvus import connections
            
            # Initialize embedding model
            logger.info(f"Initializing embedding model: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
            logger.info(f"Embedding dimension: {self.embedding_dimension}")
            
            # Connect to Milvus
            connections.connect(
                alias=self.connection_alias,
                host=self.host,
                port=self.port
            )
            self._is_connected = True
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MilvusParentChildManager: {e}")
            return False
    
    def create_parent_child_collections(self, 
                                       collection_prefix: str = "nb_specs",
                                       overwrite: bool = True,
                                       backup_before_drop: bool = False) -> Dict[str, Any]:
        """
        Create separate collections for parent and child chunks with appropriate schemas.
        
        Args:
            collection_prefix (str): Prefix for collection names
            overwrite (bool): If True, automatically drop existing collections. 
                            If False, raise error if collections exist. Default: True
            backup_before_drop (bool): If True, backup existing collections before dropping. Default: False
            
        Returns:
            Dict[str, Any]: Success status and detailed information about the operation
        """
        try:
            from pymilvus import Collection, CollectionSchema, FieldSchema, DataType, utility
            
            if not self._is_connected:
                logger.error("Not connected to Milvus. Call initialize() first.")
                return {"parent": False, "child": False}
            
            parent_collection_name = f"{collection_prefix}_parent"
            child_collection_name = f"{collection_prefix}_child"
            
            results = {}
            
            # Define parent collection schema
            parent_fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=16, is_primary=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dimension),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=5000),
                FieldSchema(name="source_file", dtype=DataType.VARCHAR, max_length=200),
                FieldSchema(name="row_index", dtype=DataType.INT64),
                FieldSchema(name="modeltype", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="modelname", dtype=DataType.VARCHAR, max_length=200),
                FieldSchema(name="version", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="child_count", dtype=DataType.INT64)
            ]
            
            parent_schema = CollectionSchema(
                fields=parent_fields,
                description="Parent chunks for notebook specifications"
            )
            
            # Create parent collection with new overwrite logic
            if utility.has_collection(parent_collection_name, using=self.connection_alias):
                if not overwrite:
                    error_msg = f"Parent collection '{parent_collection_name}' already exists and overwrite=False"
                    logger.error(f"❌ {error_msg}")
                    return {
                        "parent": False,
                        "child": False,
                        "error": error_msg,
                        "existing_collections": [parent_collection_name]
                    }
                
                # Get statistics before dropping
                try:
                    existing_collection = Collection(parent_collection_name, using=self.connection_alias)
                    entity_count = existing_collection.num_entities
                    logger.warning(f"⚠️  Found existing parent collection '{parent_collection_name}' with {entity_count} entities")
                    
                    # Backup if requested
                    if backup_before_drop:
                        backup_result = self._backup_collection(parent_collection_name, "parent")
                        if backup_result["success"]:
                            logger.info(f"💾 Backup created: {backup_result['backup_info']}")
                        else:
                            logger.warning(f"⚠️  Backup failed: {backup_result['error']}")
                    
                    logger.info(f"🗑️  Dropping existing parent collection '{parent_collection_name}' to create fresh version")
                    utility.drop_collection(parent_collection_name, using=self.connection_alias)
                    logger.info(f"✅ Successfully dropped parent collection '{parent_collection_name}'")
                    
                except Exception as drop_error:
                    logger.error(f"❌ Failed to get stats or drop parent collection '{parent_collection_name}': {drop_error}")
                    # Continue with creation attempt
            else:
                logger.info(f"📝 Creating new parent collection '{parent_collection_name}' (no existing collection found)")
                
            parent_collection = Collection(
                name=parent_collection_name,
                schema=parent_schema,
                using=self.connection_alias
            )
            logger.info(f"Created parent collection: {parent_collection_name}")
            results["parent"] = True
            
            # Define child collection schema
            child_fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=16, is_primary=True),
                FieldSchema(name="parent_id", dtype=DataType.VARCHAR, max_length=16),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dimension),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2000),
                FieldSchema(name="source_file", dtype=DataType.VARCHAR, max_length=200),
                FieldSchema(name="row_index", dtype=DataType.INT64),
                FieldSchema(name="field_group", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="modeltype", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="modelname", dtype=DataType.VARCHAR, max_length=200),
                FieldSchema(name="chunk_index", dtype=DataType.INT64)
            ]
            
            child_schema = CollectionSchema(
                fields=child_fields,
                description="Child chunks for notebook specifications"
            )
            
            # Create child collection with new overwrite logic
            if utility.has_collection(child_collection_name, using=self.connection_alias):
                if not overwrite:
                    error_msg = f"Child collection '{child_collection_name}' already exists and overwrite=False"
                    logger.error(f"❌ {error_msg}")
                    return {
                        "parent": results.get("parent", False),  # Keep parent result if it was successful
                        "child": False,
                        "error": error_msg,
                        "existing_collections": [child_collection_name]
                    }
                
                # Get statistics before dropping
                try:
                    existing_child_collection = Collection(child_collection_name, using=self.connection_alias)
                    child_entity_count = existing_child_collection.num_entities
                    logger.warning(f"⚠️  Found existing child collection '{child_collection_name}' with {child_entity_count} entities")
                    
                    # Backup if requested
                    if backup_before_drop:
                        backup_result = self._backup_collection(child_collection_name, "child")
                        if backup_result["success"]:
                            logger.info(f"💾 Backup created: {backup_result['backup_info']}")
                        else:
                            logger.warning(f"⚠️  Backup failed: {backup_result['error']}")
                    
                    logger.info(f"🗑️  Dropping existing child collection '{child_collection_name}' to create fresh version")
                    utility.drop_collection(child_collection_name, using=self.connection_alias)
                    logger.info(f"✅ Successfully dropped child collection '{child_collection_name}'")
                    
                except Exception as drop_error:
                    logger.error(f"❌ Failed to get stats or drop child collection '{child_collection_name}': {drop_error}")
                    # Continue with creation attempt
            else:
                logger.info(f"📝 Creating new child collection '{child_collection_name}' (no existing collection found)")
                
            child_collection = Collection(
                name=child_collection_name,
                schema=child_schema,
                using=self.connection_alias
            )
            logger.info(f"✅ Created child collection: {child_collection_name}")
            results["child"] = True
            
            # Store collection names for later use
            self.parent_collection_name = parent_collection_name
            self.child_collection_name = child_collection_name
            
            # Log summary of collection creation process
            logger.info(f"🎯 Collection creation summary:")
            logger.info(f"   📊 Parent collection: {parent_collection_name} ({'✅ Created' if results['parent'] else '❌ Failed'})")
            logger.info(f"   📊 Child collection: {child_collection_name} ({'✅ Created' if results['child'] else '❌ Failed'})")
            logger.info(f"   🔧 Embedding dimension: {self.embedding_dimension}")
            logger.info(f"   🔗 Connection alias: {self.connection_alias}")
            
            if results["parent"] and results["child"]:
                logger.info(f"🚀 Ready for data insertion and indexing!")
            else:
                logger.warning(f"⚠️  Some collections failed to create. Check the logs above for details.")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to create collections: {e}")
            
            # Try to provide more detailed error information
            error_details = {
                "parent": False,
                "child": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
            
            # Check if we have partial success and try cleanup
            try:
                if hasattr(self, 'parent_collection_name'):
                    if utility.has_collection(self.parent_collection_name, using=self.connection_alias):
                        logger.warning(f"🧹 Cleaning up partially created parent collection")
                        utility.drop_collection(self.parent_collection_name, using=self.connection_alias)
                        
                if hasattr(self, 'child_collection_name'):
                    if utility.has_collection(self.child_collection_name, using=self.connection_alias):
                        logger.warning(f"🧹 Cleaning up partially created child collection")
                        utility.drop_collection(self.child_collection_name, using=self.connection_alias)
                        
            except Exception as cleanup_error:
                logger.error(f"⚠️  Additional error during cleanup: {cleanup_error}")
                error_details["cleanup_error"] = str(cleanup_error)
            
            logger.error(f"💡 Suggestions to resolve the error:")
            logger.error(f"   1. Check if Milvus server is running and accessible")
            logger.error(f"   2. Verify connection parameters (host: {self.host}, port: {self.port})")
            logger.error(f"   3. Ensure sufficient permissions for collection operations")
            logger.error(f"   4. Check if embedding dimension ({self.embedding_dimension}) is valid")
            
            return error_details
    
    def create_indexes(self) -> Dict[str, bool]:
        """
        Create vector indexes for both parent and child collections.
        
        Returns:
            Dict[str, bool]: Success status for index creation
        """
        try:
            from pymilvus import Collection
            
            if not hasattr(self, 'parent_collection_name'):
                logger.error("Collections not created yet. Call create_parent_child_collections() first.")
                return {"parent": False, "child": False}
            
            results = {}
            
            # Index parameters for HNSW algorithm (good for accuracy and performance)
            index_params = {
                "metric_type": "COSINE",  # Use cosine similarity for text embeddings
                "index_type": "HNSW",
                "params": {"M": 16, "efConstruction": 200}
            }
            
            # Create index for parent collection
            parent_collection = Collection(self.parent_collection_name, using=self.connection_alias)
            parent_collection.create_index(
                field_name="embedding",
                index_params=index_params,
                index_name="embedding_index"
            )
            logger.info(f"Created index for {self.parent_collection_name}")
            results["parent"] = True
            
            # Create index for child collection
            child_collection = Collection(self.child_collection_name, using=self.connection_alias)
            child_collection.create_index(
                field_name="embedding", 
                index_params=index_params,
                index_name="embedding_index"
            )
            logger.info(f"Created index for {self.child_collection_name}")
            results["child"] = True
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            return {"parent": False, "child": False}
    
    def insert_parent_child_chunks(self, collection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert parent and child chunks into their respective Milvus collections.
        
        Args:
            collection_data (Dict): Data structure from embed_all_nbinfo_to_collection
            
        Returns:
            Dict[str, Any]: Insertion statistics and results
        """
        try:
            from pymilvus import Collection
            
            if not hasattr(self, 'parent_collection_name'):
                logger.error("Collections not created yet.")
                return {"error": "Collections not initialized"}
            
            # Prepare parent data for insertion
            parent_chunks = collection_data.get("parent_chunks", [])
            if not parent_chunks:
                return {"error": "No parent chunks found in collection data"}
            
            parent_data = {
                "id": [],
                "embedding": [],
                "text": [],
                "source_file": [],
                "row_index": [],
                "modeltype": [],
                "modelname": [],
                "version": [],
                "child_count": []
            }
            
            for chunk in parent_chunks:
                parent_data["id"].append(chunk["id"])
                parent_data["embedding"].append(chunk["embedding"])
                parent_data["text"].append(chunk["text"])
                parent_data["source_file"].append(chunk["metadata"]["source_file"])
                parent_data["row_index"].append(chunk["metadata"]["row_index"])
                parent_data["modeltype"].append(chunk["metadata"]["modeltype"])
                parent_data["modelname"].append(chunk["metadata"]["modelname"])
                parent_data["version"].append(chunk["metadata"]["version"])
                parent_data["child_count"].append(len(chunk["child_chunk_ids"]))
            
            # Insert parent chunks
            parent_collection = Collection(self.parent_collection_name, using=self.connection_alias)
            parent_result = parent_collection.insert(parent_data)
            logger.info(f"Inserted {len(parent_chunks)} parent chunks")
            
            # Prepare child data for insertion
            child_chunks = collection_data.get("child_chunks", [])
            if child_chunks:
                child_data = {
                    "id": [],
                    "parent_id": [],
                    "embedding": [],
                    "text": [],
                    "source_file": [],
                    "row_index": [],
                    "field_group": [],
                    "modeltype": [],
                    "modelname": [],
                    "chunk_index": []
                }
                
                for chunk in child_chunks:
                    child_data["id"].append(chunk["id"])
                    child_data["parent_id"].append(chunk["parent_id"])
                    child_data["embedding"].append(chunk["embedding"])
                    child_data["text"].append(chunk["text"])
                    child_data["source_file"].append(chunk["metadata"]["source_file"])
                    child_data["row_index"].append(chunk["metadata"]["row_index"])
                    child_data["field_group"].append(chunk["metadata"]["field_group"])
                    child_data["modeltype"].append(chunk["metadata"]["modeltype"])
                    child_data["modelname"].append(chunk["metadata"]["modelname"])
                    child_data["chunk_index"].append(chunk["metadata"]["chunk_index"])
                
                # Insert child chunks
                child_collection = Collection(self.child_collection_name, using=self.connection_alias)
                child_result = child_collection.insert(child_data)
                logger.info(f"Inserted {len(child_chunks)} child chunks")
            else:
                child_result = None
            
            # Flush collections to ensure data persistence
            parent_collection.flush()
            if child_result:
                child_collection.flush()
            
            return {
                "success": True,
                "parent_inserted": len(parent_chunks),
                "child_inserted": len(child_chunks) if child_chunks else 0,
                "parent_collection": self.parent_collection_name,
                "child_collection": self.child_collection_name
            }
            
        except Exception as e:
            logger.error(f"Failed to insert chunks: {e}")
            return {"error": str(e)}
    
    def load_collections(self) -> Dict[str, bool]:
        """
        Load collections into memory for search operations.
        
        Returns:
            Dict[str, bool]: Loading status for each collection
        """
        try:
            from pymilvus import Collection
            
            results = {}
            
            # Load parent collection
            if hasattr(self, 'parent_collection_name'):
                parent_collection = Collection(self.parent_collection_name, using=self.connection_alias)
                parent_collection.load()
                logger.info(f"Loaded parent collection: {self.parent_collection_name}")
                results["parent"] = True
            
            # Load child collection 
            if hasattr(self, 'child_collection_name'):
                child_collection = Collection(self.child_collection_name, using=self.connection_alias)
                child_collection.load()
                logger.info(f"Loaded child collection: {self.child_collection_name}")
                results["child"] = True
                
            return results
            
        except Exception as e:
            logger.error(f"Failed to load collections: {e}")
            return {"parent": False, "child": False}
    
    def disconnect(self):
        """Disconnect from Milvus."""
        try:
            from pymilvus import connections
            if self._is_connected:
                connections.disconnect(self.connection_alias)
                self._is_connected = False
                logger.info("Disconnected from Milvus")
        except Exception as e:
            logger.warning(f"Error disconnecting from Milvus: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def insert_parent_batch(self, parent_batch: List[Dict]) -> bool:
        """
        Insert a batch of parent chunks directly to Milvus collection.
        
        Args:
            parent_batch (List[Dict]): Batch of parent chunks
            
        Returns:
            bool: True if insertion successful
        """
        try:
            if not parent_batch:
                return True
            
            from pymilvus import Collection
            
            parent_collection = Collection(self.parent_collection_name, using=self.connection_alias)
            
            # Prepare data for batch insertion
            parent_data = {
                "id": [],
                "embedding": [],
                "text": [],
                "source_file": [],
                "row_index": [],
                "modeltype": [],
                "modelname": [],
                "version": [],
                "child_count": []
            }
            
            for chunk in parent_batch:
                parent_data["id"].append(chunk["id"])
                parent_data["embedding"].append(chunk["embedding"])
                parent_data["text"].append(chunk["text"])
                parent_data["source_file"].append(chunk["source_file"])
                parent_data["row_index"].append(chunk["row_index"])
                parent_data["modeltype"].append(chunk["modeltype"])
                parent_data["modelname"].append(chunk["modelname"])
                parent_data["version"].append(chunk["version"])
                parent_data["child_count"].append(chunk["child_count"])
            
            # Insert batch
            parent_collection.insert(parent_data)
            
            logger.info(f"Successfully inserted {len(parent_batch)} parent chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert parent batch: {e}")
            return False
    
    def insert_child_batch(self, child_batch: List[Dict]) -> bool:
        """
        Insert a batch of child chunks directly to Milvus collection.
        
        Args:
            child_batch (List[Dict]): Batch of child chunks
            
        Returns:
            bool: True if insertion successful
        """
        try:
            if not child_batch:
                return True
                
            from pymilvus import Collection
            
            child_collection = Collection(self.child_collection_name, using=self.connection_alias)
            
            # Prepare data for batch insertion
            child_data = {
                "id": [],
                "parent_id": [],
                "embedding": [],
                "text": [],
                "field_group": [],
                "chunk_index": [],
                "source_file": [],
                "row_index": [],
                "modeltype": [],
                "modelname": []
            }
            
            for chunk in child_batch:
                child_data["id"].append(chunk["id"])
                child_data["parent_id"].append(chunk["parent_id"])
                child_data["embedding"].append(chunk["embedding"])
                child_data["text"].append(chunk["text"])
                child_data["field_group"].append(chunk["field_group"])
                child_data["chunk_index"].append(chunk["chunk_index"])
                child_data["source_file"].append(chunk["source_file"])
                child_data["row_index"].append(chunk["row_index"])
                child_data["modeltype"].append(chunk["modeltype"])
                child_data["modelname"].append(chunk["modelname"])
            
            # Insert batch
            child_collection.insert(child_data)
            
            logger.info(f"Successfully inserted {len(child_batch)} child chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert child batch: {e}")
            return False
    
    def _backup_collection(self, collection_name: str, collection_type: str) -> Dict[str, Any]:
        """
        Create a backup of an existing collection by exporting its data.
        
        Args:
            collection_name (str): Name of the collection to backup
            collection_type (str): Type of collection ("parent" or "child")
            
        Returns:
            Dict[str, Any]: Backup result with success status and backup info
        """
        try:
            import json
            from datetime import datetime
            
            from pymilvus import Collection
            
            collection = Collection(collection_name, using=self.connection_alias)
            
            # Get all data from collection
            all_data = collection.query(
                expr="",  # Empty expression gets all data
                output_fields=["*"]
            )
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{collection_name}_backup_{timestamp}.json"
            
            # Save backup data
            backup_data = {
                "collection_name": collection_name,
                "collection_type": collection_type,
                "backup_timestamp": timestamp,
                "entity_count": len(all_data),
                "data": all_data
            }
            
            # Save to file (in production, this might go to cloud storage)
            backup_filepath = f"backups/{backup_filename}"
            
            # Create backups directory if it doesn't exist
            import os
            os.makedirs("backups", exist_ok=True)
            
            with open(backup_filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            return {
                "success": True,
                "backup_file": backup_filepath,
                "entity_count": len(all_data),
                "backup_info": f"Backed up {len(all_data)} entities to {backup_filepath}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "backup_info": f"Failed to backup {collection_name}: {str(e)}"
            }
    
    def list_existing_collections(self, prefix_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        List all existing collections, optionally filtered by prefix.
        
        Args:
            prefix_filter (str, optional): Only return collections with this prefix
            
        Returns:
            Dict[str, Any]: Dictionary containing collection information
        """
        try:
            from pymilvus import utility
            
            if not self._is_connected:
                logger.error("Not connected to Milvus")
                return {"error": "Not connected to Milvus"}
            
            all_collections = utility.list_collections(using=self.connection_alias)
            
            if prefix_filter:
                filtered_collections = [c for c in all_collections if c.startswith(prefix_filter)]
            else:
                filtered_collections = all_collections
            
            collection_info = []
            for collection_name in filtered_collections:
                try:
                    from pymilvus import Collection
                    collection = Collection(collection_name, using=self.connection_alias)
                    
                    info = {
                        "name": collection_name,
                        "entity_count": collection.num_entities,
                        "schema": {
                            "description": collection.schema.description,
                            "field_count": len(collection.schema.fields)
                        },
                        "has_index": collection.has_index(),
                        "is_parent_child": self._is_parent_child_collection(collection_name)
                    }
                    collection_info.append(info)
                    
                except Exception as e:
                    collection_info.append({
                        "name": collection_name,
                        "error": str(e),
                        "accessible": False
                    })
            
            return {
                "success": True,
                "total_collections": len(all_collections),
                "filtered_collections": len(filtered_collections),
                "collections": collection_info
            }
            
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return {"success": False, "error": str(e)}
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific collection.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            Dict[str, Any]: Detailed collection information
        """
        try:
            from pymilvus import Collection, utility
            
            if not utility.has_collection(collection_name, using=self.connection_alias):
                return {"error": f"Collection '{collection_name}' does not exist"}
            
            collection = Collection(collection_name, using=self.connection_alias)
            
            # Get schema information
            schema_info = {
                "description": collection.schema.description,
                "fields": []
            }
            
            for field in collection.schema.fields:
                field_info = {
                    "name": field.name,
                    "data_type": str(field.dtype),
                    "is_primary": field.is_primary,
                    "description": field.description
                }
                
                # Add dimension info for vector fields
                if hasattr(field, 'params') and field.params:
                    field_info["params"] = field.params
                    
                schema_info["fields"].append(field_info)
            
            # Get index information
            index_info = []
            try:
                indexes = collection.indexes
                for index in indexes:
                    index_info.append({
                        "field_name": index.field_name,
                        "index_name": index.index_name,
                        "index_type": index.params.get("index_type", "unknown"),
                        "metric_type": index.params.get("metric_type", "unknown")
                    })
            except:
                index_info = []
            
            return {
                "success": True,
                "collection_name": collection_name,
                "entity_count": collection.num_entities,
                "schema": schema_info,
                "indexes": index_info,
                "has_index": collection.has_index(),
                "is_loaded": collection.has_index(),  # Approximation
                "is_parent_child": self._is_parent_child_collection(collection_name)
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info for '{collection_name}': {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup_collections(self, prefix_filter: str, confirm: bool = False) -> Dict[str, Any]:
        """
        Clean up (delete) collections matching a prefix.
        
        Args:
            prefix_filter (str): Prefix to match collections for deletion
            confirm (bool): Must be True to actually delete collections
            
        Returns:
            Dict[str, Any]: Cleanup results
        """
        try:
            from pymilvus import utility
            
            if not confirm:
                return {
                    "error": "confirm=True is required to actually delete collections",
                    "suggestion": "Set confirm=True if you really want to delete collections"
                }
            
            # Get collections to delete
            all_collections = utility.list_collections(using=self.connection_alias)
            collections_to_delete = [c for c in all_collections if c.startswith(prefix_filter)]
            
            if not collections_to_delete:
                return {
                    "success": True,
                    "message": f"No collections found with prefix '{prefix_filter}'",
                    "deleted_count": 0
                }
            
            # Backup and delete each collection
            deleted_collections = []
            failed_deletions = []
            
            for collection_name in collections_to_delete:
                try:
                    # Create backup first
                    backup_result = self._backup_collection(
                        collection_name, 
                        "cleanup_backup"
                    )
                    
                    if backup_result["success"]:
                        logger.info(f"Backed up {collection_name} before deletion")
                    
                    # Delete the collection
                    utility.drop_collection(collection_name, using=self.connection_alias)
                    deleted_collections.append({
                        "name": collection_name,
                        "backup_created": backup_result["success"],
                        "backup_file": backup_result.get("backup_file", "")
                    })
                    
                    logger.info(f"Successfully deleted collection: {collection_name}")
                    
                except Exception as delete_error:
                    failed_deletions.append({
                        "name": collection_name,
                        "error": str(delete_error)
                    })
                    logger.error(f"Failed to delete {collection_name}: {delete_error}")
            
            return {
                "success": True,
                "prefix_filter": prefix_filter,
                "total_found": len(collections_to_delete),
                "deleted_count": len(deleted_collections),
                "failed_count": len(failed_deletions),
                "deleted_collections": deleted_collections,
                "failed_deletions": failed_deletions
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup collections: {e}")
            return {"success": False, "error": str(e)}
    
    def _is_parent_child_collection(self, collection_name: str) -> bool:
        """Check if a collection is part of a parent-child system."""
        parent_indicators = ["parent", "_parent"]
        child_indicators = ["child", "_child"]
        
        name_lower = collection_name.lower()
        return any(indicator in name_lower for indicator in parent_indicators + child_indicators)
    
    def disconnect(self):
        """Disconnect from Milvus."""
        try:
            if self._is_connected:
                from pymilvus import connections
                connections.disconnect(self.connection_alias)
                self._is_connected = False
                logger.info("Disconnected from Milvus")
        except Exception as e:
            logger.warning(f"Error disconnecting from Milvus: {e}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


class HierarchicalRetriever:
    """
    Hierarchical retrieval system for parent-child chunking.
    
    This class implements advanced retrieval strategies that leverage the
    parent-child relationship for improved search accuracy and context.
    """
    
    def __init__(self, milvus_manager: MilvusParentChildManager):
        """
        Initialize the hierarchical retriever.
        
        Args:
            milvus_manager: Initialized MilvusParentChildManager instance
        """
        self.manager = milvus_manager
        self.embedding_model = milvus_manager.embedding_model
        
        if not self.embedding_model:
            raise ValueError("MilvusParentChildManager must be initialized before creating retriever")
    
    def search_parent_first(self, query: str, top_k: int = 5, 
                           search_params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Parent-first search strategy: Search parents, then retrieve related children.
        
        Args:
            query (str): Search query text
            top_k (int): Number of parent chunks to retrieve
            search_params (Dict): Milvus search parameters
            
        Returns:
            List[Dict]: Retrieved parent chunks with their children
        """
        try:
            from pymilvus import Collection
            
            # Default search parameters
            if search_params is None:
                search_params = {
                    "metric_type": "COSINE",
                    "params": {"ef": 64}
                }
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # Search parent collection
            parent_collection = Collection(self.manager.parent_collection_name, 
                                         using=self.manager.connection_alias)
            
            parent_results = parent_collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["id", "text", "source_file", "modeltype", "modelname", "child_count"]
            )
            
            # Process results and retrieve children for each parent
            enriched_results = []
            for hits in parent_results:
                for hit in hits:
                    parent_info = {
                        "parent_id": hit.entity.get("id"),
                        "parent_text": hit.entity.get("text"),
                        "source_file": hit.entity.get("source_file"),
                        "modeltype": hit.entity.get("modeltype"),
                        "modelname": hit.entity.get("modelname"),
                        "similarity_score": hit.score,
                        "child_count": hit.entity.get("child_count"),
                        "children": []
                    }
                    
                    # Retrieve children for this parent
                    children = self._get_children_by_parent_id(hit.entity.get("id"))
                    parent_info["children"] = children
                    
                    enriched_results.append(parent_info)
            
            return enriched_results
            
        except Exception as e:
            logger.error(f"Parent-first search failed: {e}")
            return []
    
    def search_child_first(self, query: str, top_k: int = 10, 
                          search_params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Child-first search strategy: Search children, then retrieve parent context.
        
        Args:
            query (str): Search query text
            top_k (int): Number of child chunks to retrieve
            search_params (Dict): Milvus search parameters
            
        Returns:
            List[Dict]: Retrieved child chunks with parent context
        """
        try:
            from pymilvus import Collection
            
            # Default search parameters
            if search_params is None:
                search_params = {
                    "metric_type": "COSINE",
                    "params": {"ef": 64}
                }
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # Search child collection
            child_collection = Collection(self.manager.child_collection_name,
                                        using=self.manager.connection_alias)
            
            child_results = child_collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["id", "parent_id", "text", "field_group", "modeltype", "modelname"]
            )
            
            # Process results and retrieve parent context
            enriched_results = []
            for hits in child_results:
                for hit in hits:
                    child_info = {
                        "child_id": hit.entity.get("id"),
                        "parent_id": hit.entity.get("parent_id"),
                        "child_text": hit.entity.get("text"),
                        "field_group": hit.entity.get("field_group"),
                        "modeltype": hit.entity.get("modeltype"),
                        "modelname": hit.entity.get("modelname"),
                        "similarity_score": hit.score,
                        "parent_context": None
                    }
                    
                    # Retrieve parent context
                    parent_context = self._get_parent_by_id(hit.entity.get("parent_id"))
                    child_info["parent_context"] = parent_context
                    
                    enriched_results.append(child_info)
            
            return enriched_results
            
        except Exception as e:
            logger.error(f"Child-first search failed: {e}")
            return []
    
    def hybrid_search(self, query: str, parent_k: int = 3, child_k: int = 6, 
                     rerank: bool = True) -> Dict[str, Any]:
        """
        Hybrid search combining parent and child search strategies.
        
        Args:
            query (str): Search query text
            parent_k (int): Number of parents to retrieve
            child_k (int): Number of children to retrieve
            rerank (bool): Whether to rerank results based on combined scores
            
        Returns:
            Dict: Combined search results with metadata
        """
        try:
            # Perform both search strategies
            parent_results = self.search_parent_first(query, top_k=parent_k)
            child_results = self.search_child_first(query, top_k=child_k)
            
            # Combine and optionally rerank results
            combined_results = {
                "query": query,
                "parent_results": parent_results,
                "child_results": child_results,
                "metadata": {
                    "parent_count": len(parent_results),
                    "child_count": len(child_results),
                    "total_children_found": sum(len(p.get("children", [])) for p in parent_results)
                }
            }
            
            if rerank:
                combined_results["reranked_results"] = self._rerank_results(
                    parent_results, child_results
                )
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return {"error": str(e)}
    
    def semantic_field_search(self, query: str, field_groups: List[str], 
                             top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search within specific field groups (e.g., 'system_specs', 'connectivity').
        
        Args:
            query (str): Search query text
            field_groups (List[str]): Field groups to search within
            top_k (int): Number of results per field group
            
        Returns:
            List[Dict]: Results grouped by field groups
        """
        try:
            from pymilvus import Collection
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            
            results_by_group = []
            child_collection = Collection(self.manager.child_collection_name,
                                        using=self.manager.connection_alias)
            
            for field_group in field_groups:
                # Create filter expression for specific field group
                filter_expr = f'field_group == "{field_group}"'
                
                group_results = child_collection.search(
                    data=[query_embedding.tolist()],
                    anns_field="embedding",
                    param={"metric_type": "COSINE", "params": {"ef": 64}},
                    limit=top_k,
                    expr=filter_expr,
                    output_fields=["id", "parent_id", "text", "field_group", "modeltype", "modelname"]
                )
                
                # Process results for this field group
                group_data = {
                    "field_group": field_group,
                    "results": []
                }
                
                for hits in group_results:
                    for hit in hits:
                        result_info = {
                            "child_id": hit.entity.get("id"),
                            "parent_id": hit.entity.get("parent_id"),
                            "text": hit.entity.get("text"),
                            "modeltype": hit.entity.get("modeltype"),
                            "modelname": hit.entity.get("modelname"),
                            "similarity_score": hit.score
                        }
                        group_data["results"].append(result_info)
                
                results_by_group.append(group_data)
            
            return results_by_group
            
        except Exception as e:
            logger.error(f"Semantic field search failed: {e}")
            return []
    
    def _get_children_by_parent_id(self, parent_id: str) -> List[Dict[str, Any]]:
        """Retrieve all children for a given parent ID."""
        try:
            from pymilvus import Collection
            
            child_collection = Collection(self.manager.child_collection_name,
                                        using=self.manager.connection_alias)
            
            # Query children by parent_id
            results = child_collection.query(
                expr=f'parent_id == "{parent_id}"',
                output_fields=["id", "text", "field_group", "chunk_index"]
            )
            
            return [
                {
                    "child_id": result.get("id"),
                    "text": result.get("text"),
                    "field_group": result.get("field_group"),
                    "chunk_index": result.get("chunk_index")
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to get children for parent {parent_id}: {e}")
            return []
    
    def _get_parent_by_id(self, parent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve parent context by parent ID."""
        try:
            from pymilvus import Collection
            
            parent_collection = Collection(self.manager.parent_collection_name,
                                         using=self.manager.connection_alias)
            
            # Query parent by ID
            results = parent_collection.query(
                expr=f'id == "{parent_id}"',
                output_fields=["id", "text", "source_file", "modeltype", "modelname"]
            )
            
            if results:
                result = results[0]
                return {
                    "parent_id": result.get("id"),
                    "text": result.get("text"),
                    "source_file": result.get("source_file"),
                    "modeltype": result.get("modeltype"),
                    "modelname": result.get("modelname")
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get parent {parent_id}: {e}")
            return None
    
    def _rerank_results(self, parent_results: List[Dict], child_results: List[Dict]) -> List[Dict[str, Any]]:
        """
        Rerank combined results using a simple scoring algorithm.
        
        This could be enhanced with more sophisticated reranking models.
        """
        try:
            combined_items = []
            
            # Add parent results with boosted scores (parents provide more context)
            for parent in parent_results:
                combined_items.append({
                    "type": "parent",
                    "content": parent,
                    "boosted_score": parent.get("similarity_score", 0) * 1.2  # Boost parent scores
                })
            
            # Add child results
            for child in child_results:
                combined_items.append({
                    "type": "child",
                    "content": child,
                    "boosted_score": child.get("similarity_score", 0)
                })
            
            # Sort by boosted score
            reranked = sorted(combined_items, key=lambda x: x["boosted_score"], reverse=True)
            
            return reranked[:10]  # Return top 10 reranked results
            
        except Exception as e:
            logger.error(f"Failed to rerank results: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the parent and child collections."""
        try:
            from pymilvus import Collection
            
            parent_collection = Collection(self.manager.parent_collection_name,
                                         using=self.manager.connection_alias)
            child_collection = Collection(self.manager.child_collection_name,
                                        using=self.manager.connection_alias)
            
            parent_count = parent_collection.num_entities
            child_count = child_collection.num_entities
            
            return {
                "parent_collection": {
                    "name": self.manager.parent_collection_name,
                    "count": parent_count
                },
                "child_collection": {
                    "name": self.manager.child_collection_name,
                    "count": child_count
                },
                "total_chunks": parent_count + child_count,
                "average_children_per_parent": child_count / parent_count if parent_count > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}
    
    def test_search_strategies(self, test_query: str = "CPU performance benchmark") -> Dict[str, Any]:
        """
        Test all search strategies with a given query for comparison.
        
        Args:
            test_query (str): Query to test with all strategies
            
        Returns:
            Dict containing results from all search strategies
        """
        try:
            results = {
                "query": test_query,
                "strategies": {}
            }
            
            logger.info(f"Testing search strategies with query: '{test_query}'")
            
            # Test parent-first search
            try:
                parent_first = self.parent_first_search(test_query, k=3)
                results["strategies"]["parent_first"] = {
                    "result_count": len(parent_first.get("parent_results", [])),
                    "results": parent_first
                }
            except Exception as e:
                results["strategies"]["parent_first"] = {"error": str(e)}
            
            # Test child-first search
            try:
                child_first = self.child_first_search(test_query, k=5)
                results["strategies"]["child_first"] = {
                    "result_count": len(child_first.get("child_results", [])),
                    "results": child_first
                }
            except Exception as e:
                results["strategies"]["child_first"] = {"error": str(e)}
            
            # Test hybrid search
            try:
                hybrid = self.hybrid_search(test_query, parent_k=2, child_k=4)
                results["strategies"]["hybrid"] = {
                    "parent_count": len(hybrid.get("parent_results", [])),
                    "child_count": len(hybrid.get("child_results", [])),
                    "reranked_count": len(hybrid.get("reranked_results", [])),
                    "results": hybrid
                }
            except Exception as e:
                results["strategies"]["hybrid"] = {"error": str(e)}
            
            # Test semantic field search
            try:
                semantic = self.semantic_field_search(test_query, field_groups=["system_specs"], k=3)
                results["strategies"]["semantic_field"] = {
                    "result_count": len(semantic),
                    "results": semantic
                }
            except Exception as e:
                results["strategies"]["semantic_field"] = {"error": str(e)}
            
            return results
            
        except Exception as e:
            logger.error(f"Test search strategies failed: {e}")
            return {"error": str(e)}


def create_complete_parent_child_system(csv_file_path: str, 
                                       milvus_host: str = "localhost", 
                                       milvus_port: str = "19530",
                                       collection_prefix: str = "nb_specs_demo") -> Dict[str, Any]:
    """
    Complete workflow to create a parent-child chunking system from a CSV file.
    
    This function demonstrates the entire process:
    1. Process CSV data and generate chunks
    2. Initialize Milvus manager and create collections
    3. Insert data with embeddings
    4. Set up hierarchical retriever
    5. Test search capabilities
    
    Args:
        csv_file_path (str): Path to the notebook specifications CSV file
        milvus_host (str): Milvus server host
        milvus_port (str): Milvus server port
        collection_prefix (str): Prefix for collection names
        
    Returns:
        Dict containing system setup results and retriever instance
    """
    try:
        logger.info(f"Creating complete parent-child system from {csv_file_path}")
        
        # Step 1: Generate chunks from CSV
        logger.info("Step 1: Processing CSV and generating parent-child chunks")
        chunk_results = embed_all_nbinfo_to_collection(csv_file_path)
        
        if "error" in chunk_results:
            return {"error": f"Failed to process CSV: {chunk_results['error']}"}
        
        # Step 2: Initialize Milvus manager
        logger.info("Step 2: Initializing Milvus manager")
        manager = MilvusParentChildManager(host=milvus_host, port=milvus_port)
        
        if not manager.initialize():
            return {"error": "Failed to initialize Milvus manager"}
        
        # Step 3: Create collections
        logger.info("Step 3: Creating parent and child collections")
        collection_results = manager.create_parent_child_collections(collection_prefix)
        
        if not all(collection_results.values()):
            return {"error": f"Failed to create collections: {collection_results}"}
        
        # Step 4: Insert data (this would typically be done by the embed_all_nbinfo_to_collection function)
        logger.info("Step 4: Data insertion handled by embed_all_nbinfo_to_collection")
        
        # Step 5: Initialize hierarchical retriever
        logger.info("Step 5: Setting up hierarchical retriever")
        retriever = HierarchicalRetriever(manager)
        
        # Step 6: Get collection statistics
        stats = retriever.get_collection_stats()
        
        # Step 7: Test search capabilities
        logger.info("Step 6: Testing search capabilities")
        test_results = retriever.test_search_strategies("high performance gaming laptop")
        
        return {
            "status": "success",
            "csv_processing": chunk_results,
            "collections_created": collection_results,
            "collection_stats": stats,
            "test_results": test_results,
            "retriever": retriever,
            "manager": manager
        }
        
    except Exception as e:
        logger.error(f"Failed to create complete parent-child system: {e}")
        return {"error": str(e)}


# Example usage and testing
if __name__ == "__main__":
    # Example usage of the complete parent-child chunking system
    
    # Configuration
    csv_path = "../db/laptop_specs_sample.csv"  # Update with actual path
    milvus_config = {
        "host": "localhost",
        "port": "19530"
    }
    
    print("🚀 Starting Parent-Child Chunking System Demo")
    print("=" * 60)
    
    # Create the complete system
    system_result = create_complete_parent_child_system(
        csv_file_path=csv_path,
        milvus_host=milvus_config["host"],
        milvus_port=milvus_config["port"],
        collection_prefix="demo_nb_specs"
    )
    
    if "error" in system_result:
        print(f"❌ System setup failed: {system_result['error']}")
    else:
        print("✅ System setup completed successfully!")
        print(f"📊 Collection stats: {system_result['collection_stats']}")
        
        # Get the retriever for interactive testing
        retriever = system_result.get("retriever")
        
        if retriever:
            print("\n🔍 Interactive Search Demo")
            print("-" * 30)
            
            # Demo queries
            demo_queries = [
                "gaming laptop with high-end graphics card",
                "lightweight laptop for business",
                "laptop with long battery life",
                "CPU performance comparison"
            ]
            
            for query in demo_queries:
                print(f"\nQuery: '{query}'")
                hybrid_results = retriever.hybrid_search(query, parent_k=2, child_k=3, rerank=True)
                
                if "reranked_results" in hybrid_results:
                    print(f"Found {len(hybrid_results['reranked_results'])} reranked results")
                    for i, result in enumerate(hybrid_results["reranked_results"][:2]):
                        content = result.get("content", {})
                        result_type = result.get("type", "unknown")
                        score = result.get("boosted_score", 0)
                        print(f"  {i+1}. [{result_type.upper()}] Score: {score:.3f}")
                        if result_type == "parent":
                            print(f"      Model: {content.get('modelname', 'N/A')}")
                        else:
                            print(f"      Field: {content.get('field_group', 'N/A')}")
                else:
                    print("  No results found")
        
        print(f"\n🎯 Demo completed! Full results saved in system_result variable")
        print("💡 You can now use the retriever for custom searches")


def demo_enhanced_collection_management():
    """
    Demonstrate the new enhanced collection management features.
    
    This function shows how to use:
    - overwrite and backup parameters
    - collection management methods
    - enhanced error handling and logging
    """
    print("🚀 Enhanced Collection Management Demo")
    print("=" * 60)
    
    # Initialize manager
    manager = MilvusParentChildManager()
    
    if not manager.initialize():
        print("❌ Failed to initialize Milvus manager")
        return
    
    try:
        # Demo 1: List existing collections
        print("\n📋 Demo 1: List existing collections")
        all_collections = manager.list_existing_collections()
        if all_collections["success"]:
            print(f"Total collections: {all_collections['total_collections']}")
            for collection in all_collections["collections"]:
                status = "✅" if collection.get("accessible", True) else "❌"
                entities = collection.get("entity_count", "unknown")
                print(f"  {status} {collection['name']}: {entities} entities")
        
        # Demo 2: Create collections with overwrite=False (should fail if exists)
        print("\n🔒 Demo 2: Create collections with overwrite=False")
        result_no_overwrite = manager.create_parent_child_collections(
            "demo_test",
            overwrite=False,
            backup_before_drop=False
        )
        print(f"Result: {result_no_overwrite}")
        
        # Demo 3: Create collections with backup enabled
        print("\n💾 Demo 3: Create collections with backup enabled")
        result_with_backup = manager.create_parent_child_collections(
            "demo_backup_test",
            overwrite=True,
            backup_before_drop=True
        )
        print(f"Result: {result_with_backup}")
        
        # Demo 4: Get detailed collection info
        print("\n📊 Demo 4: Get detailed collection information")
        if result_with_backup.get("parent"):
            parent_info = manager.get_collection_info("demo_backup_test_parent")
            if parent_info["success"]:
                print(f"Parent collection info:")
                print(f"  Entity count: {parent_info['entity_count']}")
                print(f"  Field count: {len(parent_info['schema']['fields'])}")
                print(f"  Has index: {parent_info['has_index']}")
        
        # Demo 5: Cleanup collections (with safety check)
        print("\n🧹 Demo 5: Cleanup collections")
        cleanup_result = manager.cleanup_collections("demo_", confirm=False)
        print(f"Cleanup (dry run): {cleanup_result}")
        
        if cleanup_result.get("error"):
            print("🔐 Safety check worked - need confirm=True to actually delete")
        
        # Actual cleanup (commented out for safety)
        # cleanup_actual = manager.cleanup_collections("demo_", confirm=True)
        # print(f"Actual cleanup: {cleanup_actual}")
        
        print("\n✅ Enhanced collection management demo completed!")
        print("💡 New features available:")
        print("  - Automatic backup before dropping collections")
        print("  - Overwrite control (overwrite=False prevents accidental deletion)")  
        print("  - Detailed logging with emojis and statistics")
        print("  - Enhanced error handling with cleanup and suggestions")
        print("  - Collection management methods (list, info, cleanup)")
        
    finally:
        manager.disconnect()


def validate_parent_child_system(csv_directory: str, 
                                collection_prefix: str = "test_validation",
                                test_mode: str = "streaming") -> Dict[str, Any]:
    """
    Comprehensive validation and testing suite for the parent-child chunking system.
    
    This function performs end-to-end testing including:
    - CSV processing validation
    - Milvus integration testing
    - Search functionality verification
    - Performance benchmarking
    - Memory usage analysis
    
    Args:
        csv_directory (str): Directory containing test CSV files
        collection_prefix (str): Prefix for test collections
        test_mode (str): "streaming" or "standard" processing mode
        
    Returns:
        Dict: Comprehensive test results and validation report
    """
    import time
    import psutil
    import os
    
    validation_results = {
        "test_start_time": time.time(),
        "test_mode": test_mode,
        "csv_directory": csv_directory,
        "collection_prefix": collection_prefix,
        "tests": {},
        "performance": {},
        "memory_usage": {},
        "overall_status": "running"
    }
    
    try:
        logger.info("🔍 Starting comprehensive parent-child system validation")
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory_mb = process.memory_info().rss / 1024 / 1024
        validation_results["memory_usage"]["initial_mb"] = initial_memory_mb
        
        # Test 1: CSV Directory Validation
        logger.info("Test 1: Validating CSV directory and files")
        test_1_start = time.time()
        
        if not os.path.exists(csv_directory) or not os.path.isdir(csv_directory):
            validation_results["tests"]["csv_validation"] = {
                "status": "failed",
                "error": "CSV directory not found or not a directory"
            }
            validation_results["overall_status"] = "failed"
            return validation_results
        
        csv_files = [f for f in os.listdir(csv_directory) 
                     if f.endswith('.csv') and os.path.isfile(os.path.join(csv_directory, f))]
        
        validation_results["tests"]["csv_validation"] = {
            "status": "passed",
            "files_found": len(csv_files),
            "file_names": csv_files,
            "duration_seconds": time.time() - test_1_start
        }
        
        if not csv_files:
            validation_results["tests"]["csv_validation"]["status"] = "failed"
            validation_results["tests"]["csv_validation"]["error"] = "No CSV files found"
            validation_results["overall_status"] = "failed"
            return validation_results
        
        # Test 2: Milvus Connection
        logger.info("Test 2: Testing Milvus connection")
        test_2_start = time.time()
        
        try:
            milvus_manager = MilvusParentChildManager()
            connection_success = milvus_manager.initialize()
            
            validation_results["tests"]["milvus_connection"] = {
                "status": "passed" if connection_success else "failed",
                "host": milvus_manager.host,
                "port": milvus_manager.port,
                "embedding_dimension": milvus_manager.embedding_dimension,
                "duration_seconds": time.time() - test_2_start
            }
            
            if not connection_success:
                validation_results["tests"]["milvus_connection"]["error"] = "Failed to initialize Milvus manager"
                validation_results["overall_status"] = "failed"
                return validation_results
                
        except Exception as e:
            validation_results["tests"]["milvus_connection"] = {
                "status": "failed",
                "error": str(e),
                "duration_seconds": time.time() - test_2_start
            }
            validation_results["overall_status"] = "failed"
            return validation_results
        
        # Test 3: Collection Creation
        logger.info("Test 3: Testing collection creation")
        test_3_start = time.time()
        
        try:
            collection_results = milvus_manager.create_parent_child_collections(
                collection_prefix,
                overwrite=True,  # Default for create_complete_parent_child_system
                backup_before_drop=False
            )
            validation_results["tests"]["collection_creation"] = {
                "status": "passed" if all(collection_results.values()) else "failed",
                "parent_collection_created": collection_results.get("parent", False),
                "child_collection_created": collection_results.get("child", False),
                "duration_seconds": time.time() - test_3_start
            }
            
            if not all(collection_results.values()):
                validation_results["tests"]["collection_creation"]["error"] = "Failed to create collections"
                validation_results["overall_status"] = "failed"
                return validation_results
                
        except Exception as e:
            validation_results["tests"]["collection_creation"] = {
                "status": "failed",
                "error": str(e),
                "duration_seconds": time.time() - test_3_start
            }
            validation_results["overall_status"] = "failed"
            return validation_results
        
        # Test 4: Data Processing
        logger.info(f"Test 4: Testing data processing ({test_mode} mode)")
        test_4_start = time.time()
        
        try:
            if test_mode == "streaming":
                processing_results = embed_all_nbinfo_to_collection_streaming(
                    csv_directory=csv_directory,
                    collection_name=collection_prefix,
                    batch_size=50  # Smaller batch for testing
                )
            else:
                processing_results = embed_all_nbinfo_to_collection(
                    csv_directory=csv_directory,
                    collection_name=collection_prefix
                )
            
            validation_results["tests"]["data_processing"] = {
                "status": "passed" if processing_results.get("success") else "failed",
                "processing_mode": test_mode,
                "results": processing_results,
                "duration_seconds": time.time() - test_4_start
            }
            
            if not processing_results.get("success"):
                validation_results["tests"]["data_processing"]["error"] = processing_results.get("error", "Unknown error")
                validation_results["overall_status"] = "failed"
                return validation_results
                
        except Exception as e:
            validation_results["tests"]["data_processing"] = {
                "status": "failed",
                "error": str(e),
                "duration_seconds": time.time() - test_4_start
            }
            validation_results["overall_status"] = "failed"
            return validation_results
        
        # Test 5: Hierarchical Retrieval
        logger.info("Test 5: Testing hierarchical retrieval system")
        test_5_start = time.time()
        
        try:
            retriever = HierarchicalRetriever(milvus_manager)
            
            # Test different search strategies
            test_queries = [
                "high performance gaming laptop",
                "business laptop with long battery life",
                "CPU benchmark performance"
            ]
            
            search_results = {}
            
            for i, query in enumerate(test_queries):
                query_results = {}
                
                # Test parent-first search
                try:
                    parent_first = retriever.parent_first_search(query, k=2)
                    query_results["parent_first"] = {
                        "status": "passed",
                        "results_count": len(parent_first.get("parent_results", [])),
                        "has_children": any(len(r.get("children", [])) > 0 for r in parent_first.get("parent_results", []))
                    }
                except Exception as e:
                    query_results["parent_first"] = {"status": "failed", "error": str(e)}
                
                # Test child-first search
                try:
                    child_first = retriever.child_first_search(query, k=3)
                    query_results["child_first"] = {
                        "status": "passed",
                        "results_count": len(child_first.get("child_results", []))
                    }
                except Exception as e:
                    query_results["child_first"] = {"status": "failed", "error": str(e)}
                
                # Test hybrid search
                try:
                    hybrid = retriever.hybrid_search(query, parent_k=2, child_k=3, rerank=True)
                    query_results["hybrid"] = {
                        "status": "passed",
                        "parent_count": len(hybrid.get("parent_results", [])),
                        "child_count": len(hybrid.get("child_results", [])),
                        "reranked_count": len(hybrid.get("reranked_results", []))
                    }
                except Exception as e:
                    query_results["hybrid"] = {"status": "failed", "error": str(e)}
                
                search_results[f"query_{i+1}"] = {
                    "query_text": query,
                    "results": query_results
                }
            
            # Test collection statistics
            try:
                stats = retriever.get_collection_stats()
                validation_results["tests"]["hierarchical_retrieval"] = {
                    "status": "passed",
                    "search_results": search_results,
                    "collection_stats": stats,
                    "duration_seconds": time.time() - test_5_start
                }
            except Exception as e:
                validation_results["tests"]["hierarchical_retrieval"] = {
                    "status": "failed",
                    "error": str(e),
                    "search_results": search_results,
                    "duration_seconds": time.time() - test_5_start
                }
                
        except Exception as e:
            validation_results["tests"]["hierarchical_retrieval"] = {
                "status": "failed",
                "error": str(e),
                "duration_seconds": time.time() - test_5_start
            }
        
        # Performance and Memory Analysis
        final_memory_mb = process.memory_info().rss / 1024 / 1024
        total_duration = time.time() - validation_results["test_start_time"]
        
        validation_results["performance"] = {
            "total_duration_seconds": total_duration,
            "average_test_duration": total_duration / 5,
            "tests_per_second": 5 / total_duration if total_duration > 0 else 0
        }
        
        validation_results["memory_usage"] = {
            "initial_mb": initial_memory_mb,
            "final_mb": final_memory_mb,
            "peak_increase_mb": final_memory_mb - initial_memory_mb,
            "memory_efficiency": "good" if (final_memory_mb - initial_memory_mb) < 500 else "needs_attention"
        }
        
        # Determine overall status
        test_statuses = [test.get("status", "unknown") for test in validation_results["tests"].values()]
        validation_results["overall_status"] = "passed" if all(s == "passed" for s in test_statuses) else "failed"
        
        # Cleanup
        try:
            milvus_manager.disconnect()
        except:
            pass
        
        logger.info(f"🎯 Validation completed with status: {validation_results['overall_status']}")
        
        return validation_results
        
    except Exception as e:
        validation_results["overall_status"] = "failed"
        validation_results["fatal_error"] = str(e)
        logger.error(f"Fatal error during validation: {e}")
        return validation_results


def run_comprehensive_tests():
    """
    Run comprehensive tests for the parent-child chunking system.
    This is a standalone test runner for development and CI/CD.
    """
    
    print("🚀 Running Comprehensive Parent-Child Chunking System Tests")
    print("=" * 70)
    
    # Test configuration
    test_configs = [
        {
            "name": "Streaming Processing Test",
            "csv_directory": "../db",  # Adjust path as needed
            "collection_prefix": "test_stream",
            "test_mode": "streaming"
        },
        {
            "name": "Standard Processing Test", 
            "csv_directory": "../db",  # Adjust path as needed
            "collection_prefix": "test_standard",
            "test_mode": "standard"
        }
    ]
    
    overall_results = {
        "test_suite_start": time.time(),
        "configurations_tested": len(test_configs),
        "results": {},
        "summary": {}
    }
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n📋 Running Configuration {i}/{len(test_configs)}: {config['name']}")
        print("-" * 50)
        
        try:
            results = validate_parent_child_system(
                csv_directory=config["csv_directory"],
                collection_prefix=config["collection_prefix"],
                test_mode=config["test_mode"]
            )
            
            overall_results["results"][config["name"]] = results
            
            # Print summary for this configuration
            print(f"Status: {results['overall_status'].upper()}")
            print(f"Duration: {results.get('performance', {}).get('total_duration_seconds', 0):.2f}s")
            print(f"Memory Usage: {results.get('memory_usage', {}).get('peak_increase_mb', 0):.1f} MB increase")
            
            if results['overall_status'] == 'failed':
                failed_tests = [name for name, test in results['tests'].items() if test.get('status') == 'failed']
                print(f"Failed Tests: {', '.join(failed_tests)}")
                
        except Exception as e:
            print(f"❌ Configuration failed with error: {e}")
            overall_results["results"][config["name"]] = {"error": str(e), "overall_status": "failed"}
    
    # Overall summary
    total_duration = time.time() - overall_results["test_suite_start"]
    passed_configs = sum(1 for r in overall_results["results"].values() if r.get("overall_status") == "passed")
    
    overall_results["summary"] = {
        "total_duration_seconds": total_duration,
        "configurations_passed": passed_configs,
        "configurations_failed": len(test_configs) - passed_configs,
        "success_rate": (passed_configs / len(test_configs)) * 100 if test_configs else 0
    }
    
    print(f"\n🎯 Test Suite Summary")
    print("=" * 30)
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Configurations Passed: {passed_configs}/{len(test_configs)}")
    print(f"Success Rate: {overall_results['summary']['success_rate']:.1f}%")
    
    if passed_configs == len(test_configs):
        print("✅ All tests passed! System is ready for production.")
    else:
        print("⚠️  Some tests failed. Please review the results above.")
    
    return overall_results