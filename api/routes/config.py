"""Configuration routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from api.middleware.auth import verify_api_key
from core.utils.data_store import config_manager

router = APIRouter()


class ConfigUpdate(BaseModel):
    identity: Dict[str, Any] = {}
    heartbeat: Dict[str, Any] = {}
    compaction: Dict[str, Any] = {}
    workspace: Dict[str, Any] = {}


# Official provider presets
OFFICIAL_PROVIDERS = [
    {
        "id": "openai",
        "name": "OpenAI",
        "icon": "🤖",
        "default_base_url": "https://api.openai.com/v1",
        "api_type": "openai",
        "suggested_models": [
            {
                "id": "gpt-4o",
                "name": "GPT-4o",
                "context_window": 128000,
                "max_tokens": 4096,
            },
            {
                "id": "gpt-4o-mini",
                "name": "GPT-4o Mini",
                "context_window": 128000,
                "max_tokens": 4096,
            },
        ],
        "requires_api_key": True,
    },
    {
        "id": "anthropic",
        "name": "Anthropic",
        "icon": "🧠",
        "default_base_url": "https://api.anthropic.com/v1",
        "api_type": "anthropic",
        "suggested_models": [
            {
                "id": "claude-3-5-sonnet-20241022",
                "name": "Claude 3.5 Sonnet",
                "context_window": 200000,
                "max_tokens": 8192,
            },
            {
                "id": "claude-3-opus-20240229",
                "name": "Claude 3 Opus",
                "context_window": 200000,
                "max_tokens": 4096,
            },
        ],
        "requires_api_key": True,
    },
    {
        "id": "groq",
        "name": "Groq",
        "icon": "⚡",
        "default_base_url": "https://api.groq.com/openai/v1",
        "api_type": "openai",
        "suggested_models": [
            {
                "id": "llama-3.3-70b-versatile",
                "name": "Llama 3.3 70B",
                "context_window": 128000,
                "max_tokens": 8192,
            },
            {
                "id": "mixtral-8x7b-32768",
                "name": "Mixtral 8x7B",
                "context_window": 32768,
                "max_tokens": 4096,
            },
        ],
        "requires_api_key": True,
    },
    {
        "id": "gemini",
        "name": "Google Gemini",
        "icon": "♊",
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "api_type": "openai",
        "suggested_models": [
            {
                "id": "gemini-1.5-flash",
                "name": "Gemini 1.5 Flash",
                "context_window": 1000000,
                "max_tokens": 8192,
            },
            {
                "id": "gemini-1.5-pro",
                "name": "Gemini 1.5 Pro",
                "context_window": 2000000,
                "max_tokens": 8192,
            },
        ],
        "requires_api_key": True,
    },
]


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


@router.get("/providers/official")
async def get_official_providers(
    user: dict = Depends(verify_api_key),
) -> List[Dict[str, Any]]:
    """Get official provider presets."""
    return OFFICIAL_PROVIDERS


@router.get("/providers/ai-config")
async def get_ai_config(user: dict = Depends(verify_api_key)) -> Dict[str, Any]:
    """Get AI configuration overview."""
    config = await config_manager.load_config()

    providers = config.get("providers", [])
    models = config.get("models", [])

    # Build configured providers list
    configured_providers = []
    for provider in providers:
        provider_data = {
            "name": provider.get("name", "unknown"),
            "base_url": provider.get("base_url", ""),
            "has_api_key": bool(provider.get("api_key")),
            "api_key_masked": f"{provider.get('api_key', '')[:4]}..."
            if provider.get("api_key")
            else None,
            "models": [],
        }

        # Add models for this provider
        for model in models:
            if model.get("provider") == provider.get("name"):
                provider_data["models"].append(
                    {
                        "full_id": f"{provider.get('name')}/{model.get('model_id')}",
                        "id": model.get("model_id"),
                        "name": model.get("name"),
                        "is_primary": model.get("is_primary", False),
                        "context_window": model.get("context_window"),
                        "max_tokens": model.get("max_tokens"),
                    }
                )

        configured_providers.append(provider_data)

    # Get primary model
    primary_model = None
    for model in models:
        if model.get("is_primary"):
            primary_model = f"{model.get('provider')}/{model.get('model_id')}"
            break

    return {
        "primary_model": primary_model,
        "configured_providers": configured_providers,
        "available_models": [
            f"{m.get('provider')}/{m.get('model_id')}" for m in models
        ],
    }
