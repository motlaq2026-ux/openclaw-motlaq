import os
import json
import asyncio
import psutil
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path

MONITOR_PATH = Path("/app/data/monitor.json")


class HealthMonitor:
    def __init__(
        self,
        check_interval_seconds: int = 30,
        alert_threshold_cpu: float = 90.0,
        alert_threshold_memory: float = 90.0,
        alert_threshold_disk: float = 90.0,
    ):
        self.check_interval_seconds = check_interval_seconds
        self.alert_threshold_cpu = alert_threshold_cpu
        self.alert_threshold_memory = alert_threshold_memory
        self.alert_threshold_disk = alert_threshold_disk
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._alerts: List[Dict[str, Any]] = []
        self._metrics_history: List[Dict[str, Any]] = []
        self._alert_handlers: List[Callable] = []
        self.start_time = datetime.utcnow()

    def register_alert_handler(self, handler: Callable):
        self._alert_handlers.append(handler)

    async def _emit_alert(self, alert: Dict[str, Any]):
        for handler in self._alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                print(f"Alert handler error: {e}")

    def get_system_metrics(self) -> Dict[str, Any]:
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "load_avg": os.getloadavg()
                    if hasattr(os, "getloadavg")
                    else [0, 0, 0],
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent,
                },
                "process": {
                    "pid": os.getpid(),
                    "threads": len(psutil.Process().threads())
                    if psutil.pid_exists(os.getpid())
                    else 0,
                },
            }
        except Exception as e:
            return {"timestamp": datetime.utcnow().isoformat(), "error": str(e)}

    def get_process_metrics(self) -> Dict[str, Any]:
        try:
            process = psutil.Process()
            with process.oneshot():
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "cpu_percent": process.cpu_percent(),
                    "memory_percent": process.memory_percent(),
                    "memory_info": {
                        "rss": process.memory_info().rss,
                        "vms": process.memory_info().vms,
                    },
                    "num_threads": process.num_threads(),
                    "num_fds": process.num_fds() if hasattr(process, "num_fds") else 0,
                    "connections": len(process.connections())
                    if process.connections()
                    else 0,
                }
        except Exception as e:
            return {"timestamp": datetime.utcnow().isoformat(), "error": str(e)}

    def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        alerts = []

        if "error" in metrics:
            return alerts

        cpu = metrics.get("cpu", {}).get("percent", 0)
        if cpu > self.alert_threshold_cpu:
            alert = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "cpu_high",
                "value": cpu,
                "threshold": self.alert_threshold_cpu,
                "message": f"CPU usage is {cpu:.1f}% (threshold: {self.alert_threshold_cpu}%)",
            }
            alerts.append(alert)

        memory_percent = metrics.get("memory", {}).get("percent", 0)
        if memory_percent > self.alert_threshold_memory:
            alert = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "memory_high",
                "value": memory_percent,
                "threshold": self.alert_threshold_memory,
                "message": f"Memory usage is {memory_percent:.1f}% (threshold: {self.alert_threshold_memory}%)",
            }
            alerts.append(alert)

        disk_percent = metrics.get("disk", {}).get("percent", 0)
        if disk_percent > self.alert_threshold_disk:
            alert = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "disk_high",
                "value": disk_percent,
                "threshold": self.alert_threshold_disk,
                "message": f"Disk usage is {disk_percent:.1f}% (threshold: {self.alert_threshold_disk}%)",
            }
            alerts.append(alert)

        return alerts

    async def collect_metrics(self) -> Dict[str, Any]:
        system_metrics = self.get_system_metrics()
        process_metrics = self.get_process_metrics()

        all_metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "system": system_metrics,
            "process": process_metrics,
        }

        self._metrics_history.append(all_metrics)
        if len(self._metrics_history) > 1000:
            self._metrics_history = self._metrics_history[-1000:]

        alerts = self.check_alerts(system_metrics)
        for alert in alerts:
            self._alerts.append(alert)
            await self._emit_alert(alert)

        if len(self._alerts) > 100:
            self._alerts = self._alerts[-100:]

        self._save_state()

        return all_metrics

    def _save_state(self):
        MONITOR_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "last_update": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "alerts": self._alerts[-20:],
            "metrics_count": len(self._metrics_history),
        }
        with open(MONITOR_PATH, "w") as f:
            json.dump(data, f, indent=2)

    async def _run_loop(self):
        while self.running:
            try:
                await self.collect_metrics()
            except Exception as e:
                print(f"Monitor loop error: {e}")

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
            "running": self.running,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "alerts_count": len(self._alerts),
            "metrics_count": len(self._metrics_history),
        }

    def get_metrics_summary(self, minutes: int = 60) -> Dict[str, Any]:
        cutoff = datetime.utcnow().timestamp() - (minutes * 60)

        recent_metrics = [
            m
            for m in self._metrics_history
            if datetime.fromisoformat(m["timestamp"]).timestamp() > cutoff
        ]

        if not recent_metrics:
            return {"error": "No metrics available"}

        cpu_values = [
            m.get("system", {}).get("cpu", {}).get("percent", 0) for m in recent_metrics
        ]
        memory_values = [
            m.get("system", {}).get("memory", {}).get("percent", 0)
            for m in recent_metrics
        ]

        return {
            "period_minutes": minutes,
            "samples": len(recent_metrics),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "max": max(cpu_values) if cpu_values else 0,
                "min": min(cpu_values) if cpu_values else 0,
            },
            "memory": {
                "avg": sum(memory_values) / len(memory_values) if memory_values else 0,
                "max": max(memory_values) if memory_values else 0,
                "min": min(memory_values) if memory_values else 0,
            },
        }


health_monitor = HealthMonitor()
