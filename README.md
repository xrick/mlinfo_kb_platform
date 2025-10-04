[MODE: EXECUTE]
Of course. Here is a professional README.md for your project.
Sales AI: Multi-turn Guided Funnel Dialogue (MGFD) Platform
This project is an advanced conversational AI platform designed for sales scenarios. It leverages a Retrieval-Augmented Generation (RAG) architecture to provide intelligent, context-aware responses, guiding users through a structured sales funnel. The system is built with a modular kernel architecture, a FastAPI backend, and a vanilla JavaScript frontend.
Features
 * Modular Kernel Architecture: The core logic is orchestrated by the MGFDKernel, which dynamically manages a series of handlers to process user input and generate responses.
 * Stateful Dialogue Management: Utilizes a sophisticated state machine (StateManageHandler) to track conversation context and guide the dialogue flow, ensuring a coherent multi-turn experience.
 * Retrieval-Augmented Generation (RAG): Employs a powerful RAG pipeline to retrieve relevant product information from a knowledge base.
   * Vector Search: Uses Milvus for high-speed semantic search on product data.
   * Structured Data Store: Leverages DuckDB to store and query raw product specifications.
 * Advanced Chunking Strategy: Implements a Parent-Child chunking mechanism to balance retrieval precision with contextual richness for the language model.
 * Streaming API: The backend is built with FastAPI and exposes a streaming chat endpoint (/chat-stream) to provide real-time, "typing" style responses.
 * Dynamic Prompt Engineering: Features a PromptManagementHandler for composing and managing prompts based on the current dialogue state and retrieved context.
Architecture Overview
The MGFD platform operates on a handler-based pipeline orchestrated by a central kernel (MGFDKernel). When a user sends a message, the request is processed through the following stages:
 * API Layer (mgfd_routes.py): A FastAPI router receives the incoming HTTP request.
 * Kernel Orchestration (MGFDKernel): The kernel receives the user input and initiates the processing pipeline.
 * Handler Pipeline:
   * UserInputHandler: Parses and validates the user's message.
   * StateManageHandler: Determines the current state of the conversation and predicts the next state.
   * KnowledgeManageHandler: Queries Milvus and DuckDB to retrieve relevant documents and data based on the user's query and dialogue state.
   * PromptManagementHandler: Constructs a detailed prompt for the LLM using the user query, conversation history, and retrieved knowledge.
   * ResponseGenHandler: Sends the prompt to the configured LLM and streams the generated response back through the pipeline.
 * Streaming Response: The response is streamed back to the user through the FastAPI StreamingResponse mechanism.
Getting Started
Follow these instructions to set up and run the project locally.
Prerequisites
 * Python 3.10+
 * Docker
 * An LLM API key (e.g., OpenAI, Anthropic)
Installation
 * Clone the Repository
   git clone <your-repository-url>
cd mlinfo_kb_platform

 * Install Dependencies
   A convenience script is provided to install all necessary Python packages.
   bash scripts/install.sh

   This will install packages from requirements.txt.
 * Set Up External Services
   This project requires Milvus and Redis. Ensure Docker is running and start these services.
   (Note: You may need a docker-compose.yml file to manage these services, which is not included in the provided file list.)
 * Configure Environment
   Set the required environment variables, such as your LLM API key, in your shell or a .env file. The application configuration is managed in config.py.
Data Ingestion
Before running the main application, you must populate the Milvus and DuckDB knowledge bases using the provided CSV data.
python chunking_data_20250902.py

This script will:
 * Read all CSV files from the data/raw/ directory.
 * Store the raw tabular data in a DuckDB database (semantic_sales_spec.db).
 * Generate semantic parent-child chunks and their vector embeddings.
 * Insert the chunks and embeddings into the product_semantic_chunks collection in Milvus.
Running the Application
Use the provided script to start the FastAPI server.
bash scripts/start_service.sh

The application will be available at http://127.0.0.1:8000.
Usage
 * Navigate to http://127.0.0.1:8000 in your web browser.
 * Use the chat interface to start a conversation. The AI will guide you through a sales-oriented dialogue.
Project Structure
.
├── api/                # FastAPI routers and API models
├── data/               # Raw data (CSV files) for ingestion
├── db/                 # Database files (DuckDB, etc.)
├── libs/               # Core application logic
│   ├── MGFDKernel.py   # Main orchestrator
│   ├── ...Handler/     # Individual handlers for each processing stage
│   └── chunk_utils/    # Utilities for data chunking
├── scripts/            # Helper scripts (install, start, etc.)
├── static/             # Frontend CSS and JavaScript
│   └── js/
│       └── sales_ai.js # Main frontend application logic
├── templates/          # HTML files for the user interface
├── chunking_data_20250902.py # Standalone script for data ingestion
├── main.py             # FastAPI application entry point
└── requirements.txt    # Python package dependencies

