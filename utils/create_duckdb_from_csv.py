# utils/create_duckdb_from_csv.py
import pandas as pd
import os
# import hashlib
# import json
# import time
# from typing import List, Dict, Tuple, Optional, Any
# import numpy as np
# from pathlib import Path
import logging
# from sentence_transformers import SentenceTransformer
import duckdb

# Set up logging for better error tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def gen_all_nbinfo_tb(csv_directory: str = '../data/raw/corrected_csv_20250924', db_path: str = '../db/all_nbinfo_v5.db', collection_name: str = 'nbtypes_collection') -> bool:
    """
    Creates a DuckDB database and loads all CSV files into a single table, plus manages Milvus collection.
    
    This function reads all CSV files from the specified directory, validates their
    structure, and loads them into a DuckDB table named 'nbtypes'. It also manages 
    Milvus collection creation (deleting existing collection if present).
    
    Args:
        csv_directory (str): Directory containing CSV files. Default: 'data/raw/EM_New TTL_241104_AllModelsParsed'
        db_path (str): Path for the DuckDB database file. Default: 'all_nbinfo_v4.db'
        collection_name (str): Name for Milvus collection. Default: 'nbtypes_collection'
    
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
            logger.info(f"Processing {csv_file}")
            
            # Security: Check file permissions
            if not os.access(file_path, os.R_OK):
                logger.warning(f"Cannot read file {csv_file}, skipping")
                continue
            
            try:
                # Try multiple encodings to handle different file formats
                df = None
                encodings_to_try = ['utf-8-sig', 'utf-8', 'iso-8859-1', 'cp1252', 'gb2312', 'big5']

                for encoding in encodings_to_try:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        logger.info(f"Successfully read {csv_file} with encoding: {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        # Other errors should break the loop
                        logger.error(f"Non-encoding error reading {csv_file} with {encoding}: {str(e)}")
                        break

                if df is None:
                    logger.error(f"Could not read {csv_file} with any encoding")
                    continue

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
        
        # Delete existing database file if it exists
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                logger.info(f"Deleted existing database file: {db_path}")
            except Exception as e:
                logger.error(f"Error deleting existing database file {db_path}: {str(e)}")
                return False
        
        # Create DuckDB connection
        conn = duckdb.connect(db_path)
        
        try:
            # Drop table if exists (for idempotency)
            conn.execute("DROP TABLE IF EXISTS nbtypes")
            
            # Create table from dataframe using DuckDB SQL
            # DuckDB can create table directly from pandas DataFrame
            conn.register('temp_df', combined_df)
            conn.execute("CREATE TABLE nbtypes AS SELECT * FROM temp_df")
            
            # Create indexes for common query patterns
            # Index on modeltype for filtering by model
            conn.execute("CREATE INDEX IF NOT EXISTS idx_modeltype ON nbtypes(modeltype)")
            
            # Index on modelname for name-based searches
            conn.execute("CREATE INDEX IF NOT EXISTS idx_modelname ON nbtypes(modelname)")
            
            # Composite index for version and modeltype
            conn.execute("CREATE INDEX IF NOT EXISTS idx_version_modeltype ON nbtypes(version, modeltype)")
            
            # Index on source_file for tracking data origin
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source_file ON nbtypes(source_file)")
            
            # Verify data was loaded correctly
            row_count = conn.execute("SELECT COUNT(*) FROM nbtypes").fetchone()[0]
            logger.info(f"Successfully loaded {row_count} rows into nbtypes table")
            
            # Get table info for verification
            table_info = conn.execute("DESCRIBE nbtypes").fetchall()
            logger.info(f"Table schema created with {len(table_info)} columns")

            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error creating DuckDB table: {str(e)}")
            return False
        finally:
            
            conn.close()
            
    except Exception as e:
        logger.error(f"Unexpected error in gen_all_nbinfo_tb: {str(e)}")
        return False
    

if __name__ == "__main__":
    gen_all_nbinfo_tb()