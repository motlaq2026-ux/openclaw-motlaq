"""Agents routes."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from api.middleware.auth import verify_api_key

router = APIRouter()


class AgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_id: Optional[str] = None


@router.get("/")
async def list_agents(user: dict = Depends(verify_api_key)) -> List[Dict[str, Any]]:
    """List all agents."""
    return []


@router.post("/")
async def create_agent(
    agent: AgentCreate, user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Create a new agent."""
    return {"id": "placeholder", "ok": True}


@router.put("/{agent_id}")
async def update_agent(
    agent_id: str, agent: Dict[str, Any], user: dict = Depends(verify_api_key)
) -> Dict[str, bool]:
    """Update an agent."""
    return {"ok": True}


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str, user: dict = Depends(verify_api_key)
) -> Dict[str, bool]:
    """Delete an agent."""
    return {"ok": True}


@router.post("/routing/test")
async def test_routing(
    request: Dict[str, Any], user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Test agent routing."""
    return {"matched": True, "agent_id": "default"}
