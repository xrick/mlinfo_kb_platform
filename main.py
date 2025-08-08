import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

# Add project root to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import configuration
from config import STATIC_DIR, TEMPLATES_DIR, APP_HOST, APP_PORT

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Initialize FastAPI application
app = FastAPI(title="SalesRAG Integration System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Import API routes (will be created later)
try:
    from api import sales_routes, specs_routes, history_routes, import_data_routes
    app.include_router(sales_routes.router, prefix="/api/sales", tags=["sales"])
    app.include_router(specs_routes.router, prefix="/api/specs", tags=["specs"])
    app.include_router(history_routes.router, prefix="/api/history", tags=["history"])
    app.include_router(import_data_routes.router, prefix="/api", tags=["import"])
except ImportError as e:
    logging.warning(f"Some API routes not yet available: {e}")

# Import MGFD routes
try:
    from api import mgfd_routes
    app.include_router(mgfd_routes.router, prefix="/api/mgfd_cursor", tags=["mgfd"])
except ImportError as e:
    logging.warning(f"MGFD routes not available: {e}")

@app.get("/", response_class=HTMLResponse)
async def main_interface(request: Request):
    """Main integrated interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/mgfd_cursor", response_class=HTMLResponse)
async def mgfd_interface(request: Request):
    """MGFD interface"""
    return templates.TemplateResponse("mgfd_interface.html", {"request": request})




@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "SalesRAG Integration"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)