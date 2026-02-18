import os
import json
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from pathlib import Path

AGENTS_PATH = Path("/app/data/agents.json")


class Agent:
    def __init__(
        self,
        id: str,
        name: str,
        description: str = "",
        system_prompt: str = "",
        model_id: Optional[str] = None,
        workspace: str = "",
        is_default: bool = False,
        allow_subagents: Optional[List[str]] = None,
        channels: Optional[List[str]] = None,
        max_depth: int = 3,
        enabled: bool = True,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.model_id = model_id
        self.workspace = workspace
        self.is_default = is_default
        self.allow_subagents: List[str] = allow_subagents or []
        self.channels: List[str] = channels or []
        self.max_depth = max_depth
        self.enabled = enabled

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "model_id": self.model_id,
            "workspace": self.workspace,
            "is_default": self.is_default,
            "allow_subagents": self.allow_subagents,
            "channels": self.channels,
            "max_depth": self.max_depth,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown Agent"),
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", ""),
            model_id=data.get("model_id"),
            workspace=data.get("workspace", ""),
            is_default=data.get("is_default", False),
            allow_subagents=data.get("allow_subagents", []),
            channels=data.get("channels", []),
            max_depth=data.get("max_depth", 3),
            enabled=data.get("enabled", True),
        )


class AgentRouter:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self._lock = threading.Lock()
        self._load_agents()
        self._init_default_agent()

    def _init_default_agent(self):
        with self._lock:
            if "main" not in self.agents:
                default_agent = Agent(
                    id="main",
                    name="Default Agent",
                    description="The main default agent",
                    system_prompt="أنت مساعد ذكي ومفيد.",
                    is_default=True,
                    enabled=True,
                )
                self.agents["main"] = default_agent
                self._save_agents()

    def _load_agents(self):
        with self._lock:
            if AGENTS_PATH.exists():
                try:
                    with open(AGENTS_PATH, "r") as f:
                        data = json.load(f)
                    for agent_id, agent_data in data.get("agents", {}).items():
                        self.agents[agent_id] = Agent.from_dict(agent_data)
                except Exception as e:
                    print(f"Error loading agents: {e}")

    def _save_agents(self):
        AGENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "agents": {
                agent_id: agent.to_dict() for agent_id, agent in self.agents.items()
            },
            "updated_at": datetime.utcnow().isoformat(),
        }
        with open(AGENTS_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def list_agents(self) -> List[Dict[str, Any]]:
        return [agent.to_dict() for agent in self.agents.values()]

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)

    def get_default_agent(self) -> Agent:
        for agent in self.agents.values():
            if agent.is_default:
                return agent
        return self.agents.get("main", Agent(id="main", name="Default"))

    def set_default_agent(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id not in self.agents:
                return False

            for agent in self.agents.values():
                agent.is_default = agent.id == agent_id

            self._save_agents()
            return True

    def add_agent(self, agent: Agent) -> bool:
        with self._lock:
            if agent.id in self.agents:
                return False
            self.agents[agent.id] = agent
            self._save_agents()
            return True

    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        with self._lock:
            if agent_id not in self.agents:
                return False
            agent = self.agents[agent_id]
            for key, value in updates.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
            self._save_agents()
            return True

    def remove_agent(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id not in self.agents:
                return False
            if agent_id == "main":
                return False
            if self.agents[agent_id].is_default:
                self.agents["main"].is_default = True
            del self.agents[agent_id]
            self._save_agents()
            return True

    def toggle_agent(self, agent_id: str, enabled: bool) -> bool:
        with self._lock:
            if agent_id not in self.agents:
                return False
            self.agents[agent_id].enabled = enabled
            self._save_agents()
            return True

    def route_message(
        self, message: str, channel: Optional[str] = None, user_id: Optional[str] = None
    ) -> Agent:
        if channel:
            for agent in self.agents.values():
                if channel in agent.channels and agent.enabled:
                    return agent

        return self.get_default_agent()

    def can_spawn_subagent(
        self, parent_id: str, child_id: str, current_depth: int = 0
    ) -> bool:
        if parent_id not in self.agents:
            return False
        if child_id not in self.agents:
            return False

        parent = self.agents[parent_id]
        if child_id not in parent.allow_subagents:
            return False
        if current_depth >= parent.max_depth:
            return False

        return True

    def get_routing_tree(self) -> Dict[str, Any]:
        tree = {}
        for agent_id, agent in self.agents.items():
            tree[agent_id] = {
                "name": agent.name,
                "is_default": agent.is_default,
                "enabled": agent.enabled,
                "subagents": agent.allow_subagents,
                "channels": agent.channels,
            }
        return tree

    def validate_routing(self) -> List[Dict[str, str]]:
        issues = []

        for agent_id, agent in self.agents.items():
            for subagent_id in agent.allow_subagents:
                if subagent_id not in self.agents:
                    issues.append(
                        {
                            "agent": agent_id,
                            "issue": f"Subagent '{subagent_id}' does not exist",
                        }
                    )

        default_count = sum(1 for a in self.agents.values() if a.is_default)
        if default_count == 0:
            issues.append({"agent": "system", "issue": "No default agent defined"})
        elif default_count > 1:
            issues.append(
                {"agent": "system", "issue": "Multiple default agents defined"}
            )

        return issues


agent_router = AgentRouter()
