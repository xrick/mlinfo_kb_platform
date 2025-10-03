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
│   ├── mgfd_routes.py          # MGFD核心系統 API endpoints
│   ├── specs_routes.py         # Data upload/processing endpoints
│   ├── history_routes.py       # Data history management
│   └── milvus_routes.py        # Milvus vector database viewer
├── libs/
│   ├── MGFDKernel.py           # 核心系統 Kernel (統一入口)
│   ├── RAG/                    # RAG implementation components
│   │   ├── DB/                 # Database query classes (Milvus, DuckDB)
│   │   ├── LLM/                # LLM initialization and management
│   │   └── Tools/              # Content processing utilities
│   ├── opmp_services/          # OPMP Business logic services
│   │   ├── milvus_service.py   # Milvus database management service
│   │   └── opmp_kernel/        # OPMP Kernel with progressive streaming
│   │       ├── progressive_streaming.py  # 5-phase streaming orchestrator
│   │       ├── phase1_query_understanding.py
│   │       ├── phase2_parallel_retrieval.py
│   │       ├── phase3_context_assembly.py
│   │       ├── phase4_response_generation.py
│   │       ├── phase5_postprocessing.py
│   │       └── model_constants.py
│   ├── caching/                # Redis cache for streaming optimization
│   ├── UserInputHandler/       # 用戶輸入處理與槽位抽取
│   ├── KnowledgeManageHandler/ # 知識庫管理 (Milvus + 多源檢索)
│   ├── PromptManagementHandler/# Prompt 模板管理
│   ├── ResponseGenHandler/     # 響應生成策略
│   └── StateManageHandler/     # 狀態管理與流程控制
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

### System Architecture Evolution

**Current Architecture (v2.0.0)**: Kernel-Based Unified System
- **Execution Path**: `main.py` → `mgfd_routes.py` → `MGFDKernel.py`
- **MGFDKernel**: Centralized kernel orchestrating all system components
- **Progressive Streaming**: 5-phase ChatGPT-style markdown rendering system
- **Modular Handlers**: Specialized handlers for input, knowledge, prompts, responses, and state

**Deprecated Architecture (v1.x)**: Service-Based Distributed System
- Removed `ServiceManager` auto-discovery pattern
- Removed `sales_routes.py` and old service-based endpoints
- All functionality migrated to MGFDKernel-based architecture

### MGFDKernel - Core System
Located in `libs/MGFDKernel.py`, this is the unified entry point providing:
- **LLM Management**: OllamaLLM initialization and configuration
- **User Input Handler**: Slot extraction and intent recognition
- **Knowledge Manager**: Multi-source retrieval (Milvus + DuckDB)
- **Prompt Manager**: Template-based prompt generation
- **Response Generator**: Strategy-based response generation
- **State Manager**: DSM (Dynamic State Machine) for workflow control
- **Progressive Streaming**: Integration of 5-phase streaming service

### Progressive Streaming System
Located in `libs/services/sales_assistant/progressive_streaming.py`:

**5-Phase Pipeline**:
1. **Query Understanding**: Entity extraction, intent analysis (Phase 1)
2. **Parallel Retrieval**: Multi-source data retrieval from Milvus/DuckDB (Phase 2)
3. **Context Assembly**: Ranking and token-aware context building (Phase 3)
4. **Response Generation**: Token-by-token markdown streaming (Phase 4)
5. **Post-processing**: Final formatting and quality checks (Phase 5)

**Features**:
- Real-time SSE (Server-Sent Events) streaming
- Redis caching for Phase 1 & 4 optimization
- Intelligent parallel data retrieval
- ChatGPT-style progressive rendering

### RAG System Architecture
The system implements a sophisticated RAG pipeline:
- **Vector Store**: Milvus for semantic search of laptop specifications
- **Database Layer**: DuckDB for structured specification queries
- **LLM Integration**: LangChain-based conversation handling
- **Content Processing**: Automated chunking and embedding generation
- **Caching Layer**: Redis-based cache for query analysis and responses

### API Endpoints
- **MGFD Routes** (`/api/mgfd/`): Chat streaming, system status, progressive streaming
- **Specs Routes** (`/api/specs/`): File upload, data processing, templates
- **History Routes** (`/api/history/`): Processing history CRUD operations
- **Milvus Routes** (`/api/milvus/`): Vector database viewer and management

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

### Architecture Migration (v1.x → v2.0.0)

**Removed Components** (backed up in `backup/deprecated_service_manager/`):
- `libs/service_manager.py`: Old auto-discovery service orchestration
- `libs/services/base_service.py`: Base class for service pattern
- `api/sales_routes.py`: Deprecated sales API routes
- `api/mgfdsys_routes_deprecated.py`: Old MGFD system routes

**Key Technical Changes**:
1. **Circular Import Resolution**: Created `model_constants.py` to break import cycles
2. **Async Cache Integration**: Added `get_async()` and `set_async()` to `StreamingCache`
3. **Native OllamaLLM Streaming**: Removed LangChain callbacks, using native `astream()`
4. **Path Resolution**: Changed to relative paths using `Path(__file__).parent`

### Available Model Names and Types
The system supports specific laptop models defined in `libs/services/sales_assistant/model_constants.py`:
- `AVAILABLE_MODELNAMES`: Pre-configured laptop model identifiers (from DuckDB)
- `AVAILABLE_MODELTYPES`: Model type categories (819, 839, 958, etc.)
- Functions: `get_available_modelnames()`, `get_available_modeltypes()`, `refresh_model_lists()`

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