import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Set
from pathlib import Path
from collections import deque

LOGS_PATH = Path("/app/data/logs.json")


class LogEntry:
    def __init__(
        self,
        level: str,
        message: str,
        source: str = "system",
        timestamp: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        self.level = level
        self.message = message
        self.source = source
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.data = data or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "message": self.message,
            "source": self.source,
            "timestamp": self.timestamp,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogEntry":
        return cls(
            level=data.get("level", "INFO"),
            message=data.get("message", ""),
            source=data.get("source", "system"),
            timestamp=data.get("timestamp"),
            data=data.get("data", {}),
        )


class LogStream:
    def __init__(self, max_entries: int = 1000, persist: bool = True):
        self.max_entries = max_entries
        self.persist = persist
        self.entries: deque = deque(maxlen=max_entries)
        self.connections: Set = set()
        self._filters: Dict[str, Set[str]] = {}

        if persist:
            self._load_entries()

    def _load_entries(self):
        if LOGS_PATH.exists():
            try:
                with open(LOGS_PATH, "r") as f:
                    data = json.load(f)
                for entry_data in data.get("entries", [])[-self.max_entries :]:
                    self.entries.append(LogEntry.from_dict(entry_data))
            except Exception as e:
                print(f"Error loading logs: {e}")

    def _save_entries(self):
        if not self.persist:
            return
        LOGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "entries": [entry.to_dict() for entry in self.entries],
            "updated_at": datetime.utcnow().isoformat(),
        }
        with open(LOGS_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def log(
        self,
        level: str,
        message: str,
        source: str = "system",
        data: Optional[Dict[str, Any]] = None,
    ):
        entry = LogEntry(level=level.upper(), message=message, source=source, data=data)
        self.entries.append(entry)

        if self.persist:
            self._save_entries()

        asyncio.create_task(self._broadcast(entry))

    def debug(self, message: str, source: str = "system", **kwargs):
        self.log("DEBUG", message, source, kwargs if kwargs else None)

    def info(self, message: str, source: str = "system", **kwargs):
        self.log("INFO", message, source, kwargs if kwargs else None)

    def warning(self, message: str, source: str = "system", **kwargs):
        self.log("WARNING", message, source, kwargs if kwargs else None)

    def error(self, message: str, source: str = "system", **kwargs):
        self.log("ERROR", message, source, kwargs if kwargs else None)

    def critical(self, message: str, source: str = "system", **kwargs):
        self.log("CRITICAL", message, source, kwargs if kwargs else None)

    async def _broadcast(self, entry: LogEntry):
        if not self.connections:
            return

        message = json.dumps({"type": "log", "data": entry.to_dict()})

        for connection in list(self.connections):
            try:
                await connection.send_text(message)
            except:
                self.connections.discard(connection)

    async def connect(self, websocket):
        self.connections.add(websocket)
        for entry in list(self.entries)[-50:]:
            await websocket.send_text(
                json.dumps({"type": "log", "data": entry.to_dict()})
            )

    def disconnect(self, websocket):
        self.connections.discard(websocket)

    def get_entries(
        self,
        level: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        entries = list(self.entries)

        if level:
            entries = [e for e in entries if e.level == level.upper()]

        if source:
            entries = [e for e in entries if e.source == source]

        return [e.to_dict() for e in entries[-limit:]]

    def clear(self):
        self.entries.clear()
        if self.persist:
            self._save_entries()

    def get_stats(self) -> Dict[str, Any]:
        levels = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
        sources = {}

        for entry in self.entries:
            if entry.level in levels:
                levels[entry.level] += 1
            sources[entry.source] = sources.get(entry.source, 0) + 1

        return {
            "total": len(self.entries),
            "levels": levels,
            "sources": sources,
            "connections": len(self.connections),
        }

    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search log entries by query."""
        results = []
        query_lower = query.lower()

        for entry in reversed(list(self.entries)):
            if query_lower in entry.message.lower():
                results.append(entry.to_dict())
            if len(results) >= limit:
                break

        return results

    def disconnect_all(self) -> int:
        """Disconnect all WebSocket connections.

        Returns:
            int: Number of connections closed.
        """
        count = len(self.connections)
        for ws in list(self.connections):
            try:
                ws.close()
            except:
                pass
        self.connections.clear()
        return count

    def shutdown(self) -> None:
        """Shutdown the log stream and save state."""
        self.disconnect_all()
        self._save_entries()

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.shutdown()
        except:
            pass


log_stream = LogStream()
