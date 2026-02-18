"""Skills routes."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from api.middleware.auth import verify_api_key

router = APIRouter()


class SkillInstall(BaseModel):
    name: str
    description: str = ""
    icon: str = "🔧"
    category: str = "custom"


@router.get("/registry")
async def list_skills(user: dict = Depends(verify_api_key)) -> List[Dict[str, Any]]:
    """List all skills."""
    return []


@router.post("/registry/{skill_id}/enable")
async def enable_skill(
    skill_id: str, user: dict = Depends(verify_api_key)
) -> Dict[str, bool]:
    """Enable a skill."""
    return {"ok": True}


@router.post("/registry/{skill_id}/disable")
async def disable_skill(
    skill_id: str, user: dict = Depends(verify_api_key)
) -> Dict[str, bool]:
    """Disable a skill."""
    return {"ok": True}


@router.post("/install")
async def install_skill(
    skill: SkillInstall, user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Install a skill."""
    return {"success": True, "message": f"Skill '{skill.name}' installed"}


@router.delete("/{skill_id}")
async def uninstall_skill(
    skill_id: str, user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Uninstall a skill."""
    return {"ok": True, "message": f"Skill '{skill_id}' uninstalled"}


@router.get("/categories")
async def list_categories(user: dict = Depends(verify_api_key)) -> List[Dict[str, Any]]:
    """List skill categories."""
    return []
