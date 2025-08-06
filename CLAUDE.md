# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **SalesRAG Integration System** - a unified interface combining Sales-AI functionality with data processing capabilities for laptop specifications. The system provides intelligent sales assistance through RAG (Retrieval-Augmented Generation) with chat interface, specification data upload/processing, and data history tracking.

## Architecture

### Core Technology Stack
- **Backend**: FastAPI web framework with Uvicorn ASGI server
- **Frontend**: HTML/CSS/JavaScript with integrated UI components
- **Databases**: 
  - DuckDB for laptop specifications storage
  - SQLite for history tracking
  - Milvus for vector search/similarity matching
- **AI/ML**: LangChain with sentence-transformers for RAG implementation

### Directory Structure
```
├── main.py                     # FastAPI application entry point
├── config.py                   # Central configuration management
├── api/                        # API route handlers
│   ├── sales_routes.py         # Sales-AI chat endpoints
│   ├── specs_routes.py         # Data upload/processing endpoints
│   └── history_routes.py       # Data history management
├── libs/
│   ├── RAG/                    # RAG implementation components
│   │   ├── DB/                 # Database query classes (Milvus, DuckDB)
│   │   ├── LLM/                # LLM initialization and management
│   │   └── Tools/              # Content processing utilities
│   ├── services/               # Business logic services
│   │   └── sales_assistant/    # Sales AI service with prompts
│   └── service_manager.py      # Service orchestration
├── static/                     # Frontend assets (CSS/JS)
├── templates/                  # HTML templates
├── scripts/                    # Deployment and management scripts
└── db/                         # Database files
```

## Development Commands

### Installation and Setup
```bash
# Development mode installation (creates virtual environment)
./scripts/install.sh dev

# Production mode installation
./scripts/install.sh prod

# Manual dependency installation
pip install -r requirements.txt
```

### Running the Application
```bash
# Development mode (foreground, auto-reload)
python main.py
# or
./start.sh

# Production mode (background, multiple workers)
./scripts/start_service.sh prod

# Stop production service
./scripts/stop_service.sh
# or
./stop.sh
```

### Database Management
```bash
# View DuckDB data using CLI tool
python tools/duckdb_viewer_cli.py

# Database files are automatically created in db/ directory
# - db/sales_specs.db (DuckDB for specifications)
# - db/history.db (SQLite for processing history)
```

## Key Components

### RAG System Architecture
The system implements a sophisticated RAG pipeline:
- **Vector Store**: Milvus for semantic search of laptop specifications
- **Database Layer**: DuckDB for structured specification queries
- **LLM Integration**: LangChain-based conversation handling
- **Content Processing**: Automated chunking and embedding generation

### Sales Assistant Service
Located in `libs/services/sales_assistant/`:
- Entity recognition for laptop specifications
- Contextual query processing
- Structured response generation with tables
- Predefined prompts in `prompts/` directory

### API Endpoints
- **Sales Routes** (`/api/sales/`): Chat streaming, service management
- **Specs Routes** (`/api/specs/`): File upload, data processing, templates
- **History Routes** (`/api/history/`): Processing history CRUD operations

## Configuration

### Environment Variables
The system uses `config.py` for centralized configuration:
- Database paths and connection settings
- Milvus vector database configuration
- Application host/port settings (default: 0.0.0.0:8001)
- Service-specific configurations

### Supported File Formats
- Excel files: `.xlsx`, `.xls`
- CSV files: `.csv`
- Automatic data validation and processing

## Development Notes

### Available Model Names and Types
The system supports specific laptop models defined in:
- `AVAILABLE_MODELNAMES`: Pre-configured laptop model identifiers
- `AVAILABLE_MODELTYPES`: Model type categories (819, 839, 958)

### Database Schema
Laptop specifications include fields:
- Basic info: modeltype, version, modelname, mainboard, devtime
- Hardware: cpu, gpu, memory, storage, lcd, audio, battery
- Connectivity: wireless, lan, bluetooth, iointerface
- Features: touchpad, fingerprint, webcamera, ai features
- Certifications and accessories

### Frontend Integration
The UI uses a two-part design:
- Left sidebar: Navigation and data history
- Right content area: Dynamic views for Sales-AI and data management
- Real-time progress tracking for file processing
- Drag-and-drop file upload support

## Testing and Validation

The application includes built-in health checks and validation:
- `/health` endpoint for service status monitoring
- Database connection testing during startup
- Module import validation in installation scripts
- File processing status tracking

## Deployment

### Production Deployment
Use the provided scripts for production deployment:
- Multi-worker Uvicorn configuration
- Background process management with PID files
- Comprehensive logging to `salesrag.log`
- Health check monitoring

### Service Management
- Process monitoring via PID files
- Log rotation and management
- Graceful service shutdown
- Port conflict detection (default port 8001)