import os
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from pathlib import Path
import subprocess

UPDATE_CONFIG_PATH = Path("/app/data/update.json")
BACKUP_DIR = Path("/app/data/backups")


class AutoUpdater:
    def __init__(
        self,
        repo_url: str = "https://api.github.com/repos/openclaw/openclaw",
        check_interval_hours: int = 24,
        auto_update: bool = True,
        backup_before_update: bool = True,
    ):
        self.repo_url = repo_url
        self.check_interval_hours = check_interval_hours
        self.auto_update = auto_update
        self.backup_before_update = backup_before_update
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._callbacks: Dict[str, Callable] = {}
        self.current_version = "2.0.0"
        self.latest_version = "2.0.0"
        self.last_check: Optional[str] = None
        self.update_available = False
        self._load_config()

    def _load_config(self):
        if UPDATE_CONFIG_PATH.exists():
            try:
                with open(UPDATE_CONFIG_PATH, "r") as f:
                    data = json.load(f)
                self.current_version = data.get("current_version", "2.0.0")
                self.latest_version = data.get("latest_version", "2.0.0")
                self.last_check = data.get("last_check")
                self.update_available = data.get("update_available", False)
            except Exception as e:
                print(f"Error loading update config: {e}")

    def _save_config(self):
        UPDATE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "last_check": self.last_check,
            "update_available": self.update_available,
            "auto_update": self.auto_update,
            "repo_url": self.repo_url,
        }
        with open(UPDATE_CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def register_callback(self, event: str, callback: Callable):
        self._callbacks[event] = callback

    async def _emit(self, event: str, data: Any = None):
        if event in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(self._callbacks[event]):
                    await self._callbacks[event](data)
                else:
                    self._callbacks[event](data)
            except Exception as e:
                print(f"Callback error for {event}: {e}")

    async def check_for_updates(self) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.repo_url}/releases/latest"
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.latest_version = data.get("tag_name", "v2.0.0").lstrip("v")
                        self.update_available = (
                            self.latest_version != self.current_version
                        )
                        self.last_check = datetime.utcnow().isoformat()
                        self._save_config()

                        await self._emit(
                            "check_complete",
                            {
                                "current": self.current_version,
                                "latest": self.latest_version,
                                "update_available": self.update_available,
                            },
                        )

                        return {
                            "ok": True,
                            "current_version": self.current_version,
                            "latest_version": self.latest_version,
                            "update_available": self.update_available,
                            "release_notes": data.get("body", ""),
                        }
        except Exception as e:
            await self._emit("check_failed", str(e))
            return {"ok": False, "error": str(e)}

        return {"ok": False, "error": "Unknown error"}

    async def create_backup(self) -> Dict[str, Any]:
        try:
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_path = BACKUP_DIR / f"backup_{timestamp}.json"

            backup_data = {
                "created_at": datetime.utcnow().isoformat(),
                "version": self.current_version,
            }

            config_path = Path("/app/data/config.json")
            if config_path.exists():
                with open(config_path, "r") as f:
                    backup_data["config"] = json.load(f)

            usage_path = Path("/app/data/usage.json")
            if usage_path.exists():
                with open(usage_path, "r") as f:
                    backup_data["usage"] = json.load(f)

            threads_path = Path("/app/data/threads.json")
            if threads_path.exists():
                with open(threads_path, "r") as f:
                    backup_data["threads"] = json.load(f)

            with open(backup_path, "w") as f:
                json.dump(backup_data, f, indent=2)

            backups = sorted(BACKUP_DIR.glob("backup_*.json"), reverse=True)
            for old_backup in backups[10:]:
                old_backup.unlink()

            await self._emit("backup_created", str(backup_path))
            return {"ok": True, "backup_path": str(backup_path)}
        except Exception as e:
            await self._emit("backup_failed", str(e))
            return {"ok": False, "error": str(e)}

    async def perform_update(self) -> Dict[str, Any]:
        if not self.update_available:
            return {"ok": False, "error": "No update available"}

        try:
            if self.backup_before_update:
                backup_result = await self.create_backup()
                if not backup_result.get("ok"):
                    return {
                        "ok": False,
                        "error": "Backup failed",
                        "details": backup_result,
                    }

            await self._emit("update_started", self.latest_version)

            result = {"ok": True, "message": "Update signal sent. Restart required."}
            self.current_version = self.latest_version
            self.update_available = False
            self._save_config()

            await self._emit("update_complete", self.current_version)
            return result
        except Exception as e:
            await self._emit("update_failed", str(e))
            return {"ok": False, "error": str(e)}

    async def _run_loop(self):
        while self.running:
            try:
                await self.check_for_updates()
                if self.update_available and self.auto_update:
                    await self.perform_update()
            except Exception as e:
                print(f"Auto-update loop error: {e}")

            await asyncio.sleep(self.check_interval_hours * 3600)

    def start(self):
        if self.running:
            return
        self.running = True
        self._task = asyncio.create_task(self._run_loop())

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def get_status(self) -> Dict[str, Any]:
        return {
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "update_available": self.update_available,
            "last_check": self.last_check,
            "auto_update": self.auto_update,
            "running": self.running,
        }


auto_updater = AutoUpdater()
