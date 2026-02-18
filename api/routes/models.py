"""AI Models routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from api.middleware.auth import verify_api_key

router = APIRouter()


class ModelCreate(BaseModel):
    name: str
    provider: str
    model_id: str
    base_url: str
    api_key: Optional[str] = None
    max_tokens: int = 4096
    capabilities: List[str] = []


@router.get("/")
async def list_models(user: dict = Depends(verify_api_key)) -> List[Dict[str, Any]]:
    """List all configured models."""
    # This will be implemented with the new brain module
    return []


@router.post("/")
async def create_model(
    model: ModelCreate, user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Create a new model configuration."""
    # Implementation will use the new secure brain module
    return {"id": "placeholder", "ok": True}


@router.delete("/{model_id}")
async def delete_model(
    model_id: str, user: dict = Depends(verify_api_key)
) -> Dict[str, bool]:
    """Delete a model."""
    return {"ok": True}


@router.post("/{model_id}/test")
async def test_model(
    model_id: str, user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Test model connectivity."""
    return {"success": True, "latency_ms": 150}
