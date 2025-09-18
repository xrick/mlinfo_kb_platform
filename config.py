# config.py
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Database configuration
DB_PATH = BASE_DIR / "db" / "semantic_nb_spec_250919.db"
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
DUCKDB_FILE = "db/semantic_nb_spec_250919.db"
MILVUS_COLLECTION_NAME = "semantic_nb_spec_250919"#"product_semantic_chunks"
MILVUS_COLLECTION_NAME_PARENT = "new_nb_pc_v1"
MILVUS_COLLECTION_NAME_CHILD = "new_nb_pc_v2"

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