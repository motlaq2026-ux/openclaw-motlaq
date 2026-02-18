"""OpenClaw API Routes - Main Router."""

from fastapi import APIRouter

# Import route modules
from . import config, models, channels, agents, mcp, system, skills, logs, chat

# Create main router
router = APIRouter(prefix="/api")

# Include all sub-routers
router.include_router(config.router, prefix="/config", tags=["Configuration"])
router.include_router(models.router, prefix="/models", tags=["AI Models"])
router.include_router(channels.router, prefix="/channels", tags=["Channels"])
router.include_router(agents.router, prefix="/agents", tags=["Agents"])
router.include_router(mcp.router, prefix="/mcp", tags=["MCP Servers"])
router.include_router(system.router, prefix="/system", tags=["System"])
router.include_router(skills.router, prefix="/skills", tags=["Skills"])
router.include_router(logs.router, prefix="/logs", tags=["Logs"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "2.1.0"}
