"""AI Models routes with full CRUD implementation."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from api.middleware.auth import verify_api_key
from core.utils.data_store import config_manager

router = APIRouter()


class ModelCreate(BaseModel):
    name: str
    provider: str
    model_id: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    max_tokens: int = 4096
    context_window: int = 128000


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    max_tokens: Optional[int] = None
    is_primary: Optional[bool] = None


@router.get("/")
async def list_models(user: dict = Depends(verify_api_key)) -> Dict[str, Any]:
    """List all configured models."""
    config = await config_manager.load_config()
    models = config.get("models", [])

    # Format models for response
    formatted_models = []
    for model in models:
        formatted_models.append(
            {
                "id": f"{model.get('provider')}/{model.get('model_id')}",
                "name": model.get("name", model.get("model_id")),
                "provider": model.get("provider"),
                "model_id": model.get("model_id"),
                "base_url": model.get("base_url", ""),
                "max_tokens": model.get("max_tokens", 4096),
                "context_window": model.get("context_window", 128000),
                "is_primary": model.get("is_primary", False),
                "enabled": model.get("enabled", True),
            }
        )

    return {"models": formatted_models}


@router.post("/")
async def create_model(
    model: ModelCreate, user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Create a new model configuration."""
    config = await config_manager.load_config()

    # Initialize models list if not exists
    if "models" not in config:
        config["models"] = []

    # Check if model already exists
    model_id = f"{model.provider}/{model.model_id}"
    for existing in config["models"]:
        if f"{existing.get('provider')}/{existing.get('model_id')}" == model_id:
            raise HTTPException(status_code=400, detail="Model already exists")

    # Add new model
    new_model = {
        "name": model.name,
        "provider": model.provider,
        "model_id": model.model_id,
        "base_url": model.base_url or "",
        "api_key": model.api_key or "",
        "max_tokens": model.max_tokens,
        "context_window": model.context_window,
        "is_primary": len(config["models"]) == 0,  # First model is primary
        "enabled": True,
    }

    config["models"].append(new_model)

    success = await config_manager.save_config(config)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save model")

    return {
        "id": model_id,
        "ok": True,
        "message": f"Model '{model.name}' created successfully",
    }


@router.get("/{model_id:path}")
async def get_model(
    model_id: str, user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Get specific model details."""
    config = await config_manager.load_config()
    models = config.get("models", [])

    for model in models:
        if f"{model.get('provider')}/{model.get('model_id')}" == model_id:
            return {
                "id": model_id,
                "name": model.get("name"),
                "provider": model.get("provider"),
                "model_id": model.get("model_id"),
                "base_url": model.get("base_url"),
                "max_tokens": model.get("max_tokens"),
                "context_window": model.get("context_window"),
                "is_primary": model.get("is_primary", False),
                "enabled": model.get("enabled", True),
            }

    raise HTTPException(status_code=404, detail="Model not found")


@router.put("/{model_id:path}")
async def update_model(
    model_id: str, update: ModelUpdate, user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Update a model configuration."""
    config = await config_manager.load_config()
    models = config.get("models", [])

    for i, model in enumerate(models):
        if f"{model.get('provider')}/{model.get('model_id')}" == model_id:
            # Update fields
            if update.name is not None:
                model["name"] = update.name
            if update.base_url is not None:
                model["base_url"] = update.base_url
            if update.api_key is not None:
                model["api_key"] = update.api_key
            if update.max_tokens is not None:
                model["max_tokens"] = update.max_tokens

            # Handle primary model change
            if update.is_primary is not None and update.is_primary:
                # Unset all other models as primary
                for m in models:
                    m["is_primary"] = False
                model["is_primary"] = True

            config["models"][i] = model
            success = await config_manager.save_config(config)

            if not success:
                raise HTTPException(status_code=500, detail="Failed to update model")

            return {"ok": True, "message": "Model updated successfully"}

    raise HTTPException(status_code=404, detail="Model not found")


@router.delete("/{model_id:path}")
async def delete_model(
    model_id: str, user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Delete a model configuration."""
    config = await config_manager.load_config()
    models = config.get("models", [])

    for i, model in enumerate(models):
        if f"{model.get('provider')}/{model.get('model_id')}" == model_id:
            # Remove model
            deleted_model = models.pop(i)

            # If deleted model was primary, set another as primary
            if deleted_model.get("is_primary") and models:
                models[0]["is_primary"] = True

            config["models"] = models
            success = await config_manager.save_config(config)

            if not success:
                raise HTTPException(status_code=500, detail="Failed to delete model")

            return {"ok": True, "message": "Model deleted successfully"}

    raise HTTPException(status_code=404, detail="Model not found")


@router.post("/{model_id:path}/activate")
async def activate_model(
    model_id: str, user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Set a model as the primary/active model."""
    config = await config_manager.load_config()
    models = config.get("models", [])

    found = False
    for model in models:
        model_id_str = f"{model.get('provider')}/{model.get('model_id')}"
        if model_id_str == model_id:
            model["is_primary"] = True
            found = True
        else:
            model["is_primary"] = False

    if not found:
        raise HTTPException(status_code=404, detail="Model not found")

    success = await config_manager.save_config(config)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to activate model")

    return {"ok": True, "message": "Model activated successfully"}


@router.post("/{model_id:path}/test")
async def test_model(
    model_id: str, user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Test model connectivity."""
    config = await config_manager.load_config()
    models = config.get("models", [])

    for model in models:
        if f"{model.get('provider')}/{model.get('model_id')}" == model_id:
            # Test connection
            import time

            start_time = time.time()

            try:
                # Import here to avoid startup issues
                import httpx

                base_url = model.get("base_url", "")
                api_key = model.get("api_key", "")

                if not base_url or not api_key:
                    return {
                        "success": False,
                        "provider": model.get("provider"),
                        "model": model.get("model_id"),
                        "error": "Missing base_url or api_key",
                        "latency_ms": 0,
                    }

                # Simple health check
                headers = {"Authorization": f"Bearer {api_key}"}

                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Try to list models or do a simple request
                    response = await client.get(f"{base_url}/models", headers=headers)

                    latency_ms = int((time.time() - start_time) * 1000)

                    if response.status_code == 200:
                        return {
                            "success": True,
                            "provider": model.get("provider"),
                            "model": model.get("model_id"),
                            "latency_ms": latency_ms,
                            "message": "Connection successful",
                        }
                    else:
                        return {
                            "success": False,
                            "provider": model.get("provider"),
                            "model": model.get("model_id"),
                            "error": f"HTTP {response.status_code}: {response.text[:100]}",
                            "latency_ms": latency_ms,
                        }

            except Exception as e:
                latency_ms = int((time.time() - start_time) * 1000)
                return {
                    "success": False,
                    "provider": model.get("provider"),
                    "model": model.get("model_id"),
                    "error": str(e),
                    "latency_ms": latency_ms,
                }

    raise HTTPException(status_code=404, detail="Model not found")
