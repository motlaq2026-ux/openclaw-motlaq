"""Base classes for configuration and data persistence."""

import json
import asyncio
from pathlib import Path
from typing import TypeVar, Generic, Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
import aiofiles
from abc import ABC, abstractmethod

T = TypeVar("T")


@dataclass
class BaseConfig:
    """Base configuration class with common fields."""

    created_at: str = None
    updated_at: str = None
    version: str = "1.0"

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at


class DataStore(Generic[T], ABC):
    """Abstract base class for data persistence."""

    def __init__(self, file_path: Path, default_data: Optional[T] = None):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._default_data = default_data
        self._cache: Optional[T] = None
        self._lock = asyncio.Lock()
        self._last_modified = 0.0

    @abstractmethod
    def _serialize(self, data: T) -> Dict[str, Any]:
        """Convert data to dict for JSON serialization."""
        pass

    @abstractmethod
    def _deserialize(self, data: Dict[str, Any]) -> T:
        """Convert dict back to data object."""
        pass

    async def load(self, force_reload: bool = False) -> T:
        """Load data from file with caching."""
        async with self._lock:
            # Check if file was modified
            if self.file_path.exists():
                mtime = self.file_path.stat().st_mtime
                if (
                    not force_reload
                    and self._cache is not None
                    and mtime == self._last_modified
                ):
                    return self._cache

            # Load from file or use default
            if self.file_path.exists():
                try:
                    async with aiofiles.open(self.file_path, "r") as f:
                        content = await f.read()
                        data = json.loads(content)
                        self._cache = self._deserialize(data)
                        self._last_modified = self.file_path.stat().st_mtime
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error loading {self.file_path}: {e}")
                    self._cache = self._default_data
            else:
                self._cache = self._default_data

            return self._cache

    async def save(self, data: T) -> bool:
        """Save data to file atomically."""
        async with self._lock:
            try:
                # Update timestamps if applicable
                if isinstance(data, dict):
                    data["updated_at"] = datetime.utcnow().isoformat()

                # Write to temp file first (atomic write)
                temp_path = self.file_path.with_suffix(".tmp")
                serialized = self._serialize(data)

                async with aiofiles.open(temp_path, "w") as f:
                    await f.write(json.dumps(serialized, indent=2))

                # Atomic rename
                temp_path.replace(self.file_path)

                self._cache = data
                self._last_modified = self.file_path.stat().st_mtime
                return True
            except Exception as e:
                print(f"Error saving {self.file_path}: {e}")
                return False

    async def update(self, updater: callable) -> bool:
        """Update data using a function."""
        data = await self.load()
        try:
            new_data = updater(data)
            return await self.save(new_data)
        except Exception as e:
            print(f"Error updating data: {e}")
            return False


class JSONStore(DataStore[Dict[str, Any]]):
    """Simple JSON file store for dict data."""

    def _serialize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    def _deserialize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data


class ConfigManager:
    """Centralized configuration management."""

    # Base paths
    BASE_DIR = Path("/app/data")

    # File paths
    CONFIG_FILE = BASE_DIR / "config.json"
    CHANNELS_FILE = BASE_DIR / "channels.json"
    TELEGRAM_ACCOUNTS_FILE = BASE_DIR / "telegram_accounts.json"
    AGENTS_FILE = BASE_DIR / "agents.json"
    MCP_SERVERS_FILE = BASE_DIR / "mcp_servers.json"
    USAGE_FILE = BASE_DIR / "usage.json"
    THREADS_FILE = BASE_DIR / "threads.json"
    ENV_FILE = BASE_DIR / ".env"

    def __init__(self):
        self._stores: Dict[str, DataStore] = {}
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all data directories exist."""
        self.BASE_DIR.mkdir(parents=True, exist_ok=True)
        (self.BASE_DIR / "logs").mkdir(exist_ok=True)
        (self.BASE_DIR / "backups").mkdir(exist_ok=True)

    def get_store(self, name: str, file_path: Path, default: Any = None) -> DataStore:
        """Get or create a data store."""
        if name not in self._stores:
            self._stores[name] = JSONStore(file_path, default)
        return self._stores[name]

    async def load_config(self) -> Dict[str, Any]:
        """Load main configuration."""
        store = self.get_store("config", self.CONFIG_FILE, {})
        return await store.load()

    async def save_config(self, config: Dict[str, Any]) -> bool:
        """Save main configuration."""
        store = self.get_store("config", self.CONFIG_FILE, {})
        return await store.save(config)

    async def load_channels(self) -> Dict[str, Any]:
        """Load channel configurations."""
        store = self.get_store("channels", self.CHANNELS_FILE, {})
        return await store.load()

    async def save_channels(self, channels: Dict[str, Any]) -> bool:
        """Save channel configurations."""
        store = self.get_store("channels", self.CHANNELS_FILE, {})
        return await store.save(channels)

    async def load_telegram_accounts(self) -> List[Dict[str, Any]]:
        """Load Telegram accounts."""
        store = self.get_store("telegram_accounts", self.TELEGRAM_ACCOUNTS_FILE, [])
        return await store.load()

    async def save_telegram_accounts(self, accounts: List[Dict[str, Any]]) -> bool:
        """Save Telegram accounts."""
        store = self.get_store("telegram_accounts", self.TELEGRAM_ACCOUNTS_FILE, [])
        return await store.save(accounts)


# Global config manager
config_manager = ConfigManager()
