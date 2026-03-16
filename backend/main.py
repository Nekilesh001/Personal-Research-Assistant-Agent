"""
FastAPI application entry point for the Personal Research Assistant Agent.

Configures CORS, mounts API routes, initializes the database,
and starts the uvicorn ASGI server.
"""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add the backend directory to sys.path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from api.routes import router
from utils.db import init_db
from utils.logger import get_logger, setup_logging

# Re-initialize logging (ensures it's configured before anything else)
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Runs database initialization on startup and cleanup on shutdown.
    """
    logger.info("app_startup", environment=os.getenv("ENVIRONMENT", "development"))

    # Initialize SQLite database
    await init_db()
    logger.info("database_initialized")

    yield

    # Cleanup on shutdown
    logger.info("app_shutdown")


# Create FastAPI app
app = FastAPI(
    title="Personal Research Assistant Agent",
    description=(
        "An AI agent that accepts research queries, fetches academic papers "
        "from arXiv and Semantic Scholar, embeds them into a vector store, "
        "and generates structured research reports using LLMs."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
allowed_origins = [
    frontend_url,
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Mount API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint — redirects to API docs."""
    return {
        "message": "Personal Research Assistant Agent API",
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"

    logger.info("server_starting", host=host, port=port, reload=reload)

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
