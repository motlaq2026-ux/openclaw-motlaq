"""OpenClaw Fortress - Secure API Server."""

import os
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

# Import security middleware
from api.middleware.auth import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    CORSMiddlewareSecure,
)

# Import new routes
from api.routes import router as api_router

# Import core systems
from core.utils.data_store import config_manager

# Configuration
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
START_TIME = datetime.utcnow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    print("🚀 OpenClaw Fortress starting...")
    print(f"⏰ Started at: {START_TIME.isoformat()}")
    print("🔐 Security middleware enabled")
    print("⚡ API routes loaded")

    yield

    # Shutdown
    print("🛑 Shutting down OpenClaw Fortress...")


# Create FastAPI app with security
app = FastAPI(
    title="OpenClaw Fortress",
    version="2.1.0",
    docs_url=None,  # Disable docs in production
    redoc_url=None,
    lifespan=lifespan,
)

# Add security middleware (order matters!)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=120)
app.add_middleware(CORSMiddlewareSecure)

# Mount static files
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler - don't expose internals."""
    print(f"❌ Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Serve the frontend."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "OpenClaw Fortress API", "version": "2.1.0"}


@app.get("/api")
async def api_info():
    """API information."""
    return {
        "name": "OpenClaw Fortress",
        "version": "2.1.0",
        "secure": True,
        "endpoints": [
            "/api/health",
            "/api/config",
            "/api/models",
            "/api/channels",
            "/api/agents",
            "/api/mcp",
            "/api/system",
            "/api/skills",
            "/api/logs",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)
