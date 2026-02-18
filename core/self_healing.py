import os
import json
import asyncio
import traceback
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
from enum import Enum
import sys

HEALTH_PATH = Path("/app/data/health.json")
ERROR_LOG_PATH = Path("/app/data/errors.json")


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class SelfHealing:
    def __init__(
        self,
        check_interval_seconds: int = 60,
        max_errors_per_hour: int = 10,
        auto_recover: bool = True,
    ):
        self.check_interval_seconds = check_interval_seconds
        self.max_errors_per_hour = max_errors_per_hour
        self.auto_recover = auto_recover
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._recovery_handlers: Dict[str, Callable] = {}
        self._health_checks: Dict[str, Callable] = {}
        self.status = HealthStatus.HEALTHY
        self.errors: List[Dict[str, Any]] = []
        self.recoveries: List[Dict[str, Any]] = []
        self.last_check: Optional[str] = None
        self.uptime_start = datetime.utcnow()
        self._load_state()

    def _load_state(self):
        if HEALTH_PATH.exists():
            try:
                with open(HEALTH_PATH, "r") as f:
                    data = json.load(f)
                self.errors = data.get("errors", [])[-100:]
                self.recoveries = data.get("recoveries", [])[-50:]
            except Exception:
                pass

    def _save_state(self):
        HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "status": self.status.value,
            "errors": self.errors[-100:],
            "recoveries": self.recoveries[-50:],
            "last_check": self.last_check,
            "uptime_seconds": (datetime.utcnow() - self.uptime_start).total_seconds(),
        }
        with open(HEALTH_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def register_health_check(self, name: str, check_func: Callable):
        self._health_checks[name] = check_func

    def register_recovery_handler(self, error_type: str, handler: Callable):
        self._recovery_handlers[error_type] = handler

    def record_error(
        self,
        error_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        error_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": error_type,
            "message": message,
            "details": details or {},
            "traceback": traceback.format_exc() if exception else None,
        }
        self.errors.append(error_record)
        self._save_state()

        if self._should_trigger_recovery(error_type):
            asyncio.create_task(self._attempt_recovery(error_type, error_record))

    def _should_trigger_recovery(self, error_type: str) -> bool:
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_errors = [
            e
            for e in self.errors
            if datetime.fromisoformat(e["timestamp"]) > one_hour_ago
            and e["type"] == error_type
        ]
        return len(recent_errors) >= self.max_errors_per_hour

    async def _attempt_recovery(self, error_type: str, error_record: Dict[str, Any]):
        if not self.auto_recover:
            return

        if error_type in self._recovery_handlers:
            try:
                handler = self._recovery_handlers[error_type]
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(error_record)
                else:
                    result = handler(error_record)

                self.recoveries.append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "error_type": error_type,
                        "success": True,
                        "result": result,
                    }
                )
                self._save_state()
                return
            except Exception as e:
                self.recoveries.append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "error_type": error_type,
                        "success": False,
                        "error": str(e),
                    }
                )
                self._save_state()

        await self._default_recovery(error_type, error_record)

    async def _default_recovery(self, error_type: str, error_record: Dict[str, Any]):
        recovery_actions = {
            "api_connection": self._recover_api_connection,
            "memory_error": self._recover_memory,
            "config_corruption": self._recover_config,
            "disk_full": self._recover_disk,
            "model_error": self._recover_model,
            "timeout": self._recover_timeout,
        }

        action = recovery_actions.get(error_type)
        if action:
            try:
                await action(error_record)
                self.recoveries.append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "error_type": error_type,
                        "success": True,
                        "action": action.__name__,
                    }
                )
            except Exception as e:
                self.recoveries.append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "error_type": error_type,
                        "success": False,
                        "error": str(e),
                    }
                )
            self._save_state()

    async def _recover_api_connection(self, error_record: Dict[str, Any]):
        await asyncio.sleep(5)

    async def _recover_memory(self, error_record: Dict[str, Any]):
        import gc

        gc.collect()

    async def _recover_config(self, error_record: Dict[str, Any]):
        config_path = Path("/app/data/config.json")
        backup_dir = Path("/app/data/backups")
        if backup_dir.exists():
            backups = sorted(backup_dir.glob("backup_*.json"), reverse=True)
            if backups:
                with open(backups[0], "r") as f:
                    backup = json.load(f)
                if "config" in backup:
                    with open(config_path, "w") as f:
                        json.dump(backup["config"], f, indent=2)

    async def _recover_disk(self, error_record: Dict[str, Any]):
        cleanup_paths = [Path("/app/data/logs"), Path("/app/data/backups")]
        for path in cleanup_paths:
            if path.exists():
                files = sorted(
                    path.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True
                )
                for old_file in files[5:]:
                    old_file.unlink()

    async def _recover_model(self, error_record: Dict[str, Any]):
        from config import load_config, set_active_model

        config = load_config()
        models = config.get("models", [])
        if len(models) > 1:
            current_id = config.get("active_model_id")
            for model in models:
                if model.get("id") != current_id:
                    set_active_model(model.get("id"))
                    break

    async def _recover_timeout(self, error_record: Dict[str, Any]):
        await asyncio.sleep(10)

    async def run_health_checks(self) -> Dict[str, Any]:
        results = {}
        all_healthy = True

        for name, check_func in self._health_checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                results[name] = {"healthy": True, "result": result}
            except Exception as e:
                results[name] = {"healthy": False, "error": str(e)}
                all_healthy = False

        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_errors = [
            e
            for e in self.errors
            if datetime.fromisoformat(e["timestamp"]) > one_hour_ago
        ]

        if len(recent_errors) > self.max_errors_per_hour * 2:
            self.status = HealthStatus.CRITICAL
        elif len(recent_errors) > self.max_errors_per_hour:
            self.status = HealthStatus.UNHEALTHY
        elif not all_healthy:
            self.status = HealthStatus.DEGRADED
        else:
            self.status = HealthStatus.HEALTHY

        self.last_check = datetime.utcnow().isoformat()
        self._save_state()

        return {
            "status": self.status.value,
            "checks": results,
            "recent_errors": len(recent_errors),
            "uptime_seconds": (datetime.utcnow() - self.uptime_start).total_seconds(),
        }

    async def _run_loop(self):
        while self.running:
            try:
                await self.run_health_checks()
            except Exception as e:
                print(f"Health check loop error: {e}")

            await asyncio.sleep(self.check_interval_seconds)

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
            "status": self.status.value,
            "uptime_seconds": (datetime.utcnow() - self.uptime_start).total_seconds(),
            "total_errors": len(self.errors),
            "total_recoveries": len(self.recoveries),
            "last_check": self.last_check,
            "running": self.running,
        }


self_healing = SelfHealing()
