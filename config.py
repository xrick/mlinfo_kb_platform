# config.py
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Database configuration
DB_PATH = BASE_DIR / "db" / "all_nbinfo_v5.db"
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
DUCKDB_FILE = "db/all_nbinfo_v5.db"
MILVUS_COLLECTION_NAME = "semantic_nb_250926_utf8_collection"#"product_semantic_chunks"

MILVUS_COLLECTION_NAME_PARENT = "parent_chunks_20250926"
MILVUS_COLLECTION_NAME_CHILD = "child_chunks_20250926"

# Application settings
APP_HOST = "0.0.0.0"
APP_PORT = 8001

# Static files and templates
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# History database
HISTORY_DB_PATH = BASE_DIR / "db" / "history.db"

# Services configuration
SERVICES_CONFIG = {
    "sales_assistant": {
        "enabled": True,
        "db_path": str(DB_PATH),
        "milvus_host": MILVUS_HOST,
        "milvus_port": MILVUS_PORT,
        "collection_name": MILVUS_COLLECTION_NAME
    }
}