import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable, Literal
from pathlib import Path
import uuid

SCHEDULER_PATH = Path("/app/data/scheduler.json")


class ScheduledTask:
    def __init__(
        self,
        id: str,
        name: str,
        task_type: Literal["message", "prompt", "webhook", "script"],
        schedule: str,
        config: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        last_run: Optional[str] = None,
        next_run: Optional[str] = None,
        run_count: int = 0,
    ):
        self.id = id
        self.name = name
        self.task_type = task_type
        self.schedule = schedule
        self.config: Dict[str, Any] = config or {}
        self.enabled = enabled
        self.last_run = last_run
        self.next_run = next_run
        self.run_count = run_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "task_type": self.task_type,
            "schedule": self.schedule,
            "config": self.config,
            "enabled": self.enabled,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "run_count": self.run_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledTask":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Unnamed Task"),
            task_type=data.get("task_type", "prompt"),
            schedule=data.get("schedule", "0 9 * * *"),
            config=data.get("config", {}),
            enabled=data.get("enabled", True),
            last_run=data.get("last_run"),
            next_run=data.get("next_run"),
            run_count=data.get("run_count", 0),
        )


class Scheduler:
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._load_tasks()
        self._callbacks: Dict[str, Callable] = {}

    def _load_tasks(self):
        if SCHEDULER_PATH.exists():
            try:
                with open(SCHEDULER_PATH, "r") as f:
                    data = json.load(f)
                for task_id, task_data in data.get("tasks", {}).items():
                    self.tasks[task_id] = ScheduledTask.from_dict(task_data)
            except Exception as e:
                print(f"Error loading tasks: {e}")

    def _save_tasks(self):
        SCHEDULER_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "tasks": {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            "updated_at": datetime.utcnow().isoformat(),
        }
        with open(SCHEDULER_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def register_callback(self, task_type: str, callback: Callable):
        self._callbacks[task_type] = callback

    def list_tasks(self) -> List[Dict[str, Any]]:
        return [task.to_dict() for task in self.tasks.values()]

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        return self.tasks.get(task_id)

    def add_task(self, task: ScheduledTask) -> bool:
        if task.id in self.tasks:
            return False
        self.tasks[task.id] = task
        self._calculate_next_run(task)
        self._save_tasks()
        return True

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        if task_id not in self.tasks:
            return False
        task = self.tasks[task_id]
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        self._calculate_next_run(task)
        self._save_tasks()
        return True

    def remove_task(self, task_id: str) -> bool:
        if task_id not in self.tasks:
            return False
        del self.tasks[task_id]
        self._save_tasks()
        return True

    def toggle_task(self, task_id: str, enabled: bool) -> bool:
        if task_id not in self.tasks:
            return False
        self.tasks[task_id].enabled = enabled
        self._save_tasks()
        return True

    def _parse_schedule(self, schedule: str) -> Dict[str, Optional[int]]:
        parts = schedule.split()
        if len(parts) != 5:
            return {"minute": 0, "hour": 9, "day": None, "month": None, "weekday": None}

        minute = int(parts[0]) if parts[0] != "*" else None
        hour = int(parts[1]) if parts[1] != "*" else None
        day = int(parts[2]) if parts[2] != "*" else None
        month = int(parts[3]) if parts[3] != "*" else None
        weekday = int(parts[4]) if parts[4] != "*" else None

        return {
            "minute": minute or 0,
            "hour": hour or 0,
            "day": day,
            "month": month,
            "weekday": weekday,
        }

    def _calculate_next_run(self, task: ScheduledTask):
        now = datetime.utcnow()
        parsed = self._parse_schedule(task.schedule)

        minute = parsed["minute"] or now.minute
        hour = parsed["hour"] or now.hour

        next_run = now.replace(minute=minute, second=0, microsecond=0)
        if parsed["hour"]:
            next_run = next_run.replace(hour=hour)

        if next_run <= now:
            next_run += timedelta(hours=24)

        task.next_run = next_run.isoformat()

    async def _execute_task(self, task: ScheduledTask):
        callback = self._callbacks.get(task.task_type)
        if callback:
            try:
                await callback(task.config)
            except Exception as e:
                print(f"Error executing task {task.id}: {e}")

        task.last_run = datetime.utcnow().isoformat()
        task.run_count += 1
        self._calculate_next_run(task)
        self._save_tasks()

    async def _run_loop(self):
        while self.running:
            now = datetime.utcnow()

            for task in self.tasks.values():
                if not task.enabled:
                    continue

                if task.next_run:
                    next_run = datetime.fromisoformat(task.next_run.replace("Z", ""))
                    if now >= next_run:
                        asyncio.create_task(self._execute_task(task))

            await asyncio.sleep(60)

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

    async def run_task_now(self, task_id: str) -> Dict[str, Any]:
        if task_id not in self.tasks:
            return {"ok": False, "error": "Task not found"}

        task = self.tasks[task_id]
        await self._execute_task(task)
        return {"ok": True, "message": "Task executed"}

    def get_task_history(self, task_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return (
            [
                {
                    "task_id": task_id,
                    "run_at": self.tasks[task_id].last_run,
                    "run_count": self.tasks[task_id].run_count,
                }
            ]
            if task_id in self.tasks
            else []
        )


scheduler = Scheduler()
