import os
import json
import asyncio
import subprocess
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from pathlib import Path

MCP_PATH = Path("/app/data/mcp.json")


class MCPServer:
    """Represents an MCP server configuration."""

    def __init__(
        self,
        name: str,
        transport: Literal["stdio", "sse"] = "stdio",
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        url: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        enabled: bool = True,
    ):
        self.name = name
        self.transport = transport
        self.command = command
        self.args: List[str] = args or []
        self.url = url
        self.env: Dict[str, str] = env or {}
        self.enabled = enabled
        self.status: Literal["running", "stopped", "error"] = "stopped"
        self.process: Optional[subprocess.Popen] = None
        self.last_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert server to dictionary."""
        return {
            "name": self.name,
            "transport": self.transport,
            "command": self.command,
            "args": self.args,
            "url": self.url,
            "env": self.env,
            "enabled": self.enabled,
            "status": self.status,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServer":
        """Create server from dictionary."""
        return cls(
            name=data.get("name", "unnamed"),
            transport=data.get("transport", "stdio"),
            command=data.get("command"),
            args=data.get("args", []),
            url=data.get("url"),
            env=data.get("env", {}),
            enabled=data.get("enabled", True),
        )


class MCPManager:
    """Manages MCP server configurations and lifecycle."""

    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self._lock = threading.Lock()
        self._load_servers()

    def _load_servers(self) -> None:
        """Load servers from disk."""
        with self._lock:
            if MCP_PATH.exists():
                try:
                    with open(MCP_PATH, "r") as f:
                        data = json.load(f)
                    for name, server_data in data.get("servers", {}).items():
                        self.servers[name] = MCPServer.from_dict(server_data)
                except Exception as e:
                    print(f"Error loading MCP servers: {e}")

    def _save_servers(self) -> None:
        """Save servers to disk."""
        MCP_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "servers": {
                name: server.to_dict() for name, server in self.servers.items()
            },
            "updated_at": datetime.utcnow().isoformat(),
        }
        with open(MCP_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def _stop_server_internal(self, name: str) -> Dict[str, Any]:
        """Stop server without acquiring lock (internal use)."""
        server = self.servers.get(name)
        if not server:
            return {"ok": False, "error": "Server not found"}
        if server.process:
            server.process.terminate()
            server.process = None
        server.status = "stopped"
        return {"ok": True, "message": "Server stopped"}

    def list_servers(self) -> List[Dict[str, Any]]:
        """List all servers."""
        return [server.to_dict() for server in self.servers.values()]

    def get_server(self, name: str) -> Optional[MCPServer]:
        """Get a server by name."""
        return self.servers.get(name)

    def add_server(self, server: MCPServer) -> bool:
        """Add a new server."""
        with self._lock:
            if server.name in self.servers:
                return False
            self.servers[server.name] = server
            self._save_servers()
            return True

    def update_server(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update server configuration."""
        with self._lock:
            if name not in self.servers:
                return False
            server = self.servers[name]
            for key, value in updates.items():
                if hasattr(server, key):
                    setattr(server, key, value)
            self._save_servers()
            return True

    def remove_server(self, name: str) -> bool:
        """Remove a server."""
        with self._lock:
            if name not in self.servers:
                return False
            server = self.servers[name]
            if server.status == "running":
                self._stop_server_internal(name)
            del self.servers[name]
            self._save_servers()
            return True

    def toggle_server(self, name: str, enabled: bool) -> bool:
        """Toggle server enabled state."""
        with self._lock:
            if name not in self.servers:
                return False
            self.servers[name].enabled = enabled
            self._save_servers()
            return True

    async def start_server(self, name: str) -> Dict[str, Any]:
        """Start a server."""
        if name not in self.servers:
            return {"ok": False, "error": "Server not found"}

        server = self.servers[name]
        if not server.enabled:
            return {"ok": False, "error": "Server is disabled"}

        if server.status == "running":
            return {"ok": True, "message": "Already running"}

        try:
            if server.transport == "stdio" and server.command:
                env = os.environ.copy()
                env.update(server.env)
                server.process = subprocess.Popen(
                    [server.command] + server.args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                )
                server.status = "running"
                server.last_error = None
                return {"ok": True, "message": "Server started"}
            elif server.transport == "sse" and server.url:
                server.status = "running"
                return {"ok": True, "message": "SSE server ready"}
            else:
                return {"ok": False, "error": "Invalid configuration"}
        except Exception as e:
            server.status = "error"
            server.last_error = str(e)
            return {"ok": False, "error": str(e)}

    def stop_server(self, name: str) -> Dict[str, Any]:
        """Stop a server."""
        with self._lock:
            return self._stop_server_internal(name)

    async def test_server(self, name: str) -> Dict[str, Any]:
        """Test if a server is operational."""
        if name not in self.servers:
            return {"ok": False, "error": "Server not found"}

        server = self.servers[name]
        if server.status != "running":
            result = await self.start_server(name)
            if not result.get("ok"):
                return result

        return {"ok": True, "message": f"Server {name} is operational"}

    def get_tools(self, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tools from servers."""
        tools = []
        for name, server in self.servers.items():
            if server_name and name != server_name:
                continue
            if server.enabled and server.status == "running":
                tools.append({"server": name, "tools": []})
        return tools

    def install_from_url(self, url: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Install server from URL."""
        return {
            "ok": False,
            "error": "Installation from URL requires local execution environment",
        }


mcp_manager = MCPManager()
