"""MCP routes."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from api.middleware.auth import verify_api_key

router = APIRouter()


class MCPServerCreate(BaseModel):
    name: str
    transport: str = "stdio"
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    enabled: bool = True


@router.get("/")
async def list_servers(user: dict = Depends(verify_api_key)) -> List[Dict[str, Any]]:
    """List MCP servers."""
    return []


@router.post("/")
async def create_server(
    server: MCPServerCreate, user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Create MCP server."""
    return {"ok": True}


@router.put("/{name}")
async def update_server(
    name: str, server: Dict[str, Any], user: dict = Depends(verify_api_key)
) -> Dict[str, bool]:
    """Update MCP server."""
    return {"ok": True}


@router.delete("/{name}")
async def delete_server(
    name: str, user: dict = Depends(verify_api_key)
) -> Dict[str, bool]:
    """Delete MCP server."""
    return {"ok": True}


@router.post("/{name}/toggle")
async def toggle_server(
    name: str, request: Dict[str, Any], user: dict = Depends(verify_api_key)
) -> Dict[str, bool]:
    """Toggle MCP server."""
    return {"ok": True}


@router.post("/{name}/test")
async def test_server(
    name: str, user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Test MCP server."""
    return {"success": True}
