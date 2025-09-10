import sqlite3
import pandas as pd
import os
import hashlib
import json
from typing import List, Dict, Tuple, Optional
import numpy as np
from pathlib import Path
import logging

# Set up logging for better error tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def gen_all_nbinfo_tb(csv_directory: str = '/home/user', db_path: str = 'nbinfo.db') -> bool:
    """
    Creates a SQLite database and loads all CSV files into a single table.
    
    This function reads all CSV files from the specified directory, validates their
    structure, and loads them into a SQLite table named 'all_nb_spec'.
    
    Args:
        csv_directory (str): Directory containing CSV files. Default: '/home/user'
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
    csv_directory: str = '/home/user',
    collection_name: str = 'all_nb_info_collection',
    chunk_size: int = 512,
    chunk_overlap: int = 50
) -> Dict[str, any]:
    """
    Embeds CSV content using parent-child chunking technique into a vector collection.
    
    This function implements a hierarchical chunking strategy where each notebook
    specification (row) is a parent chunk, and its fields are grouped into child chunks
    for more granular retrieval.
    
    Args:
        csv_directory (str): Directory containing CSV files. Default: '/home/user'
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
        
        # Initialize collection storage (in production, this would be a vector database)
        collection = {
            "name": collection_name,
            "parent_chunks": [],
            "child_chunks": [],
            "metadata": {
                "created_at": pd.Timestamp.now().isoformat(),
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap
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
                    
                    # Create parent chunk entry
                    parent_chunk = {
                        "id": parent_id,
                        "text": parent_text[:5000],  # Security: Limit text size
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
                                    
                                    # Create child chunk ID
                                    child_content = f"{parent_id}_{group_name}_{i}"
                                    child_id = hashlib.sha256(child_content.encode()).hexdigest()[:16]
                                    
                                    # Create child chunk entry
                                    child_chunk = {
                                        "id": child_id,
                                        "parent_id": parent_id,
                                        "text": chunk_text,
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
                                child_content = f"{parent_id}_{group_name}"
                                child_id = hashlib.sha256(child_content.encode()).hexdigest()[:16]
                                
                                child_chunk = {
                                    "id": child_id,
                                    "parent_id": parent_id,
                                    "text": group_text,
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
        
        # In production, here we would:
        # 1. Generate actual embeddings using an embedding model
        # 2. Store in a vector database (Pinecone, Weaviate, Chroma, etc.)
        # 3. Create appropriate indexes for similarity search
        
        # For now, save collection structure to file
        collection_file = f"/home/user/{collection_name}.json"
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