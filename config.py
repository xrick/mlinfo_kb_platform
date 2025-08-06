import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Database configuration
DB_PATH = BASE_DIR / "db" / "sales_specs.db"
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
MILVUS_COLLECTION_NAME = "sales_notebook_specs"

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