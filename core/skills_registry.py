import os
import json
import asyncio
import threading
import aiohttp
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path

SKILLS_PATH = Path("/app/data/skills.json")

BUILTIN_SKILLS = {
    "web_search": {
        "id": "web_search",
        "name": "Web Search",
        "description": "Search the web using DuckDuckGo",
        "icon": "🔍",
        "category": "search",
        "builtin": True,
        "version": "1.0.0",
        "author": "OpenClaw",
        "config": {"max_results": 5, "timeout": 30},
    },
    "python_repl": {
        "id": "python_repl",
        "name": "Python REPL",
        "description": "Execute Python code safely",
        "icon": "🐍",
        "category": "code",
        "builtin": True,
        "version": "1.0.0",
        "author": "OpenClaw",
        "config": {"timeout": 30, "memory_limit_mb": 100},
    },
    "vision": {
        "id": "vision",
        "name": "Vision",
        "description": "Analyze and understand images",
        "icon": "👁️",
        "category": "multimodal",
        "builtin": True,
        "version": "1.0.0",
        "author": "OpenClaw",
        "config": {"max_image_size_mb": 10},
    },
    "weather": {
        "id": "weather",
        "name": "Weather",
        "description": "Get weather information",
        "icon": "🌤️",
        "category": "utility",
        "builtin": True,
        "version": "1.0.0",
        "author": "OpenClaw",
        "config": {"units": "metric"},
    },
    "calculator": {
        "id": "calculator",
        "name": "Calculator",
        "description": "Perform mathematical calculations",
        "icon": "🔢",
        "category": "utility",
        "builtin": True,
        "version": "1.0.0",
        "author": "OpenClaw",
        "config": {},
    },
    "datetime_tools": {
        "id": "datetime_tools",
        "name": "DateTime Tools",
        "description": "Date and time utilities",
        "icon": "📅",
        "category": "utility",
        "builtin": True,
        "version": "1.0.0",
        "author": "OpenClaw",
        "config": {"timezone": "UTC"},
    },
}

CLAWHUB_API = "https://clawhub.ai/api/skills"


class Skill:
    def __init__(
        self,
        id: str,
        name: str,
        description: str = "",
        icon: str = "🔧",
        category: str = "general",
        builtin: bool = False,
        version: str = "1.0.0",
        author: str = "Unknown",
        source: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        enabled: bool = False,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.icon = icon
        self.category = category
        self.builtin = builtin
        self.version = version
        self.author = author
        self.source = source
        self.config = config or {}
        self.enabled = enabled

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "builtin": self.builtin,
            "version": self.version,
            "author": self.author,
            "source": self.source,
            "config": self.config,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown"),
            description=data.get("description", ""),
            icon=data.get("icon", "🔧"),
            category=data.get("category", "general"),
            builtin=data.get("builtin", False),
            version=data.get("version", "1.0.0"),
            author=data.get("author", "Unknown"),
            source=data.get("source"),
            config=data.get("config", {}),
            enabled=data.get("enabled", False),
        )


class SkillsRegistry:
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self._lock = threading.Lock()
        self._load_skills()
        self._init_builtin_skills()

    def _init_builtin_skills(self):
        with self._lock:
            for skill_id, skill_data in BUILTIN_SKILLS.items():
                if skill_id not in self.skills:
                    self.skills[skill_id] = Skill.from_dict(skill_data)

    def _load_skills(self):
        with self._lock:
            if SKILLS_PATH.exists():
                try:
                    with open(SKILLS_PATH, "r") as f:
                        data = json.load(f)
                    for skill_id, skill_data in data.get("skills", {}).items():
                        self.skills[skill_id] = Skill.from_dict(skill_data)
                except Exception as e:
                    print(f"Error loading skills: {e}")

    def _save_skills(self):
        SKILLS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "skills": {
                skill_id: skill.to_dict() for skill_id, skill in self.skills.items()
            },
            "updated_at": datetime.utcnow().isoformat(),
        }
        with open(SKILLS_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def list_skills(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        skills = []
        for skill in self.skills.values():
            if category and skill.category != category:
                continue
            skills.append(skill.to_dict())
        return skills

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        return self.skills.get(skill_id)

    def get_enabled_skills(self) -> List[str]:
        return [skill_id for skill_id, skill in self.skills.items() if skill.enabled]

    def enable_skill(self, skill_id: str) -> bool:
        with self._lock:
            if skill_id not in self.skills:
                return False
            self.skills[skill_id].enabled = True
            self._save_skills()
            return True

    def disable_skill(self, skill_id: str) -> bool:
        with self._lock:
            if skill_id not in self.skills:
                return False
            self.skills[skill_id].enabled = False
            self._save_skills()
            return True

    def toggle_skill(self, skill_id: str, enabled: bool) -> bool:
        if enabled:
            return self.enable_skill(skill_id)
        return self.disable_skill(skill_id)

    def add_skill(self, skill: Skill) -> bool:
        with self._lock:
            if skill.id in self.skills:
                return False
            self.skills[skill.id] = skill
            self._save_skills()
            return True

    def update_skill_config(self, skill_id: str, config: Dict[str, Any]) -> bool:
        with self._lock:
            if skill_id not in self.skills:
                return False
            self.skills[skill_id].config.update(config)
            self._save_skills()
            return True

    def remove_skill(self, skill_id: str) -> bool:
        with self._lock:
            if skill_id not in self.skills:
                return False
            if self.skills[skill_id].builtin:
                return False
            del self.skills[skill_id]
            self._save_skills()
            return True

    async def fetch_marketplace(
        self, query: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                params: Dict[str, Any] = {"limit": limit}
                if query:
                    params["q"] = query
                async with session.get(
                    CLAWHUB_API, params=params, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("skills", [])
        except Exception as e:
            print(f"Error fetching marketplace: {e}")
        return []

    async def install_from_marketplace(self, skill_id: str) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{CLAWHUB_API}/{skill_id}"
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        skill = Skill.from_dict(data)
                        skill.enabled = True
                        if self.add_skill(skill):
                            return {"ok": True, "skill": skill.to_dict()}
                        return {"ok": False, "error": "Skill already exists"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return {"ok": False, "error": "Skill not found"}

    def install_from_url(self, url: str, name: Optional[str] = None) -> Dict[str, Any]:
        return {
            "ok": False,
            "error": "Installation from URL requires local execution environment",
        }

    def get_categories(self) -> List[Dict[str, Any]]:
        categories = {}
        for skill in self.skills.values():
            cat = skill.category
            if cat not in categories:
                categories[cat] = {"name": cat, "count": 0, "icon": "📁"}
            categories[cat]["count"] += 1

        category_icons = {
            "search": "🔍",
            "code": "💻",
            "multimodal": "🖼️",
            "utility": "🛠️",
            "automation": "🤖",
            "general": "📁",
        }
        for cat in categories:
            categories[cat]["icon"] = category_icons.get(cat, "📁")

        return list(categories.values())


skills_registry = SkillsRegistry()
