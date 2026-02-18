"""Configuration routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from api.middleware.auth import verify_api_key
from core.utils.data_store import config_manager

router = APIRouter()


class ConfigUpdate(BaseModel):
    identity: Dict[str, Any] = {}
    heartbeat: Dict[str, Any] = {}
    compaction: Dict[str, Any] = {}
    workspace: Dict[str, Any] = {}


@router.get("/")
async def get_config(user: dict = Depends(verify_api_key)) -> Dict[str, Any]:
    """Get current configuration (API keys masked)."""
    config = await config_manager.load_config()

    # Mask sensitive data
    if "providers" in config:
        for provider in config["providers"]:
            if "api_key" in provider:
                key = provider["api_key"]
                if len(key) > 8:
                    provider["api_key"] = f"{key[:4]}...{key[-4:]}"
                else:
                    provider["api_key"] = "****"

    return config


@router.post("/")
async def update_config(
    update: ConfigUpdate, user: dict = Depends(verify_api_key)
) -> Dict[str, bool]:
    """Update configuration."""
    config = await config_manager.load_config()

    # Update sections
    if update.identity:
        config["identity"] = {**config.get("identity", {}), **update.identity}
    if update.heartbeat:
        config["heartbeat"] = {**config.get("heartbeat", {}), **update.heartbeat}
    if update.compaction:
        config["compaction"] = {**config.get("compaction", {}), **update.compaction}
    if update.workspace:
        config["workspace"] = {**config.get("workspace", {}), **update.workspace}

    success = await config_manager.save_config(config)
    return {"ok": success}
