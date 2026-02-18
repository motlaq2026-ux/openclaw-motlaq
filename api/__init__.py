"""
OpenClaw Fortress API Module
============================

This module provides the REST API for OpenClaw Fortress.

API Endpoints:
--------------
- /api/health - System health check
- /api/config - Configuration management
- /api/models - AI model management
- /api/providers - List AI providers
- /api/skills/registry - Skills management
- /api/mcp - MCP server management
- /api/agents - Agent management
- /api/scheduler/tasks - Task scheduling
- /api/prompt - System prompt editing
- /api/threads - Thread management
- /api/chat - Chat endpoint
- /api/multimodal - Multimodal chat (with images)
- /api/compare - Compare multiple models
- /api/logs - System logs
- /api/usage - Usage statistics
- /api/backup - Backup/restore
- /api/system/* - Nuclear system endpoints

Authentication:
---------------
Currently no authentication required (designed for personal use).

Response Format:
----------------
All responses are JSON with structure:
{
    "ok": true/false,
    "data": {...} or "error": "message"
}
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import JSONResponse

from config import (
    load_config,
    save_config,
    get_active_model,
    get_model_by_id,
    add_model,
    update_model,
    delete_model,
    set_active_model,
    update_skill,
    toggle_skill,
    get_enabled_skills,
    get_all_providers,
)
from brain import (
    process_query,
    process_multimodal,
    compare_models,
    get_usage_stats,
    get_threads_list,
    get_thread,
    delete_thread,
    search_threads,
    create_thread,
    add_message_to_thread,
    load_usage,
    save_usage,
    load_threads,
    save_threads,
)
from models import (
    ChatRequest,
    MultimodalRequest,
    CompareRequest,
    AddModelRequest,
    UpdateModelRequest,
    SkillToggleRequest,
    BackupData,
)
from core.mcp_manager import mcp_manager, MCPServer
from core.skills_registry import skills_registry, Skill
from core.agent_router import agent_router, Agent
from core.scheduler import scheduler, ScheduledTask
from core.log_stream import log_stream

router = APIRouter()

START_TIME = datetime.utcnow()


@router.get("/health")
async def health_check():
    """Check system health status.

    Returns:
        dict: Health status including version, active model, uptime, and enabled skills.
    """
    config = load_config()
    active = get_active_model()
    uptime = (datetime.utcnow() - START_TIME).total_seconds()

    return {
        "status": "ok",
        "version": config.get("version", "2.0.0"),
        "active_model": active.get("name") if active else None,
        "telegram_enabled": config.get("telegram_enabled", True),
        "uptime_seconds": uptime,
        "enabled_skills": get_enabled_skills(),
    }


@router.get("/config")
async def get_config():
    """Get current configuration.

    Returns:
        dict: Full configuration object.
    """
    return load_config()


@router.post("/config")
async def update_config(request: Request):
    """Update configuration.

    Args:
        request: Request body containing new configuration.

    Returns:
        dict: Success/failure response with message.
    """
    try:
        data = await request.json()
        if save_config(data):
            return {"ok": True, "message": "✅ تم حفظ الإعدادات بنجاح"}
        return JSONResponse(
            {"ok": False, "error": "❌ فشل حفظ الإعدادات. تحقق من الصلاحيات."},
            status_code=500,
        )
    except json.JSONDecodeError:
        return JSONResponse(
            {"ok": False, "error": "❌ صيغة JSON غير صالحة."}, status_code=400
        )
    except Exception as e:
        return JSONResponse(
            {"ok": False, "error": f"❌ خطأ: {str(e)}"}, status_code=400
        )


@router.get("/models")
async def list_models():
    config = load_config()
    active_id = config.get("active_model_id")
    models = config.get("models", [])

    return {"models": models, "active_model_id": active_id, "count": len(models)}


@router.post("/models")
async def create_model(req: AddModelRequest):
    model_id = req.model_id.replace("/", "-").replace(".", "-")

    providers = get_all_providers()
    provider = next((p for p in providers if p["id"] == req.provider), None)
    base_url = req.base_url or (provider["base_url"] if provider else "")

    new_model = {
        "id": f"{req.provider}-{model_id}",
        "name": req.name,
        "provider": req.provider,
        "model_id": req.model_id,
        "api_key_source": req.api_key_source,
        "api_key_env": req.api_key_env or f"{req.provider.upper()}_API_KEY",
        "api_key_value": req.api_key_value or "",
        "base_url": base_url,
        "max_tokens": req.max_tokens,
        "temperature": req.temperature,
        "capabilities": req.capabilities,
        "priority": 99,
    }

    if add_model(new_model):
        return {"ok": True, "model": new_model}
    return JSONResponse({"ok": False, "error": "Model already exists"}, status_code=400)


@router.put("/models/{model_id}")
async def update_model_endpoint(model_id: str, req: UpdateModelRequest):
    updates = {k: v for k, v in req.dict().items() if v is not None}

    if update_model(model_id, updates):
        return {"ok": True}
    return JSONResponse({"ok": False, "error": "Model not found"}, status_code=404)


@router.delete("/models/{model_id}")
async def remove_model(model_id: str):
    if delete_model(model_id):
        return {"ok": True}
    return JSONResponse(
        {"ok": False, "error": "Cannot delete last model"}, status_code=400
    )


@router.post("/models/{model_id}/activate")
async def activate_model(model_id: str):
    if set_active_model(model_id):
        return {"ok": True, "active_model_id": model_id}
    return JSONResponse({"ok": False, "error": "Model not found"}, status_code=404)


@router.get("/providers")
async def list_providers():
    return {"providers": get_all_providers()}


@router.get("/skills")
async def list_skills():
    config = load_config()
    skills = config.get("skills", {})

    available_skills = {
        "web_search": {
            "name": "Web Search",
            "description": "Search the web using DuckDuckGo",
            "icon": "🔍",
            "category": "search",
        },
        "python_repl": {
            "name": "Python REPL",
            "description": "Execute Python code",
            "icon": "🐍",
            "category": "code",
        },
        "vision": {
            "name": "Vision",
            "description": "Process and analyze images",
            "icon": "👁️",
            "category": "multimodal",
        },
    }

    result = []
    for skill_id, info in available_skills.items():
        settings = skills.get(skill_id, {"enabled": False})
        result.append(
            {
                "id": skill_id,
                **info,
                "enabled": settings.get("enabled", False),
                "settings": settings,
            }
        )

    return {"skills": result}


@router.post("/skills/{skill_id}/toggle")
async def toggle_skill_endpoint(skill_id: str, req: SkillToggleRequest):
    if toggle_skill(skill_id, req.enabled):
        return {"ok": True, "skill_id": skill_id, "enabled": req.enabled}
    return JSONResponse(
        {"ok": False, "error": "Failed to toggle skill"}, status_code=500
    )


@router.put("/skills/{skill_id}")
async def update_skill_endpoint(skill_id: str, request: Request):
    try:
        settings = await request.json()
        if update_skill(skill_id, settings):
            return {"ok": True}
        return JSONResponse({"ok": False}, status_code=500)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.post("/chat")
async def chat(req: ChatRequest):
    try:
        response = await process_query(req.message, req.model_id, req.thread_id)
        return {"response": response}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/multimodal")
async def multimodal(req: MultimodalRequest):
    try:
        response = await process_multimodal(req.text, req.image_data, req.model_id)
        return {"response": response}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/compare")
async def compare(req: CompareRequest):
    try:
        results = await compare_models(req.prompt, req.model_ids)
        return {"results": results}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/threads")
async def list_threads(limit: int = 20):
    threads = get_threads_list(limit)
    return {"threads": threads, "count": len(threads)}


@router.post("/threads")
async def new_thread(title: str = "New Chat"):
    thread = create_thread(title)
    return {"ok": True, "thread": thread}


@router.get("/threads/{thread_id}")
async def get_thread_detail(thread_id: str):
    thread = get_thread(thread_id)
    if thread:
        return thread
    return JSONResponse({"error": "Thread not found"}, status_code=404)


@router.delete("/threads/{thread_id}")
async def remove_thread(thread_id: str):
    if delete_thread(thread_id):
        return {"ok": True}
    return JSONResponse({"error": "Thread not found"}, status_code=404)


@router.get("/threads/search")
async def search_threads_endpoint(q: str = Query(..., min_length=1)):
    results = search_threads(q)
    return {"threads": results, "query": q}


@router.get("/usage")
async def usage_stats():
    return get_usage_stats()


@router.get("/usage/charts")
async def usage_charts(days: int = 7):
    stats = get_usage_stats()
    daily = stats.get("daily", {})

    chart_data = []
    for date, data in sorted(daily.items())[-days:]:
        chart_data.append(
            {
                "date": date,
                "requests": data.get("requests", 0),
                "tokens": data.get("tokens", 0),
            }
        )

    return {
        "daily": chart_data,
        "models": stats.get("models", {}),
        "total_requests": stats.get("total_requests", 0),
        "total_tokens": stats.get("total_tokens", 0),
    }


@router.get("/backup")
async def export_backup():
    config = load_config()
    usage = load_usage()
    threads = load_threads()

    backup = BackupData(
        config=config,
        usage=usage,
        threads=threads,
        exported_at=datetime.utcnow().isoformat(),
    )

    return backup.dict()


@router.post("/restore")
async def import_backup(request: Request):
    try:
        data = await request.json()

        if "config" in data:
            save_config(data["config"])

        if "usage" in data:
            save_usage(data["usage"])

        if "threads" in data:
            save_threads(data["threads"])

        return {"ok": True, "message": "Backup restored successfully"}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.post("/prompt")
async def update_prompt(request: Request):
    try:
        data = await request.json()
        prompt = data.get("prompt", "")

        config = load_config()
        config["system_prompt"] = prompt
        save_config(config)

        return {"ok": True, "message": "System prompt updated"}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.get("/prompt/templates")
async def prompt_templates():
    templates = {
        "openclaw": {
            "name": "OpenClaw Default",
            "prompt": """أنت OpenClaw، مساعد ذكاء اصطناعي متقدم 🦞

لديك قدرات بحث في الإنترنت وتنفيذ كود Python.

## المهارات المتاحة:
- **web_search**: للبحث في الإنترنت عن معلومات حديثة
- **python_repl**: للحسابات والتحليل والتنفيذ

## صيغة استخدام الأداة:
```
Action: [اسم_الأداة]
Input: [البحث أو الكود]
```

## قواعد:
- رد بشكل مختصر ومفيد
- استخدم الأدوات عند الحاجة
- كن ودوداً ومحترفاً""",
        },
        "assistant": {
            "name": "مساعد عام",
            "prompt": "أنت مساعد ذكاء اصطناعي مفيد. أجب على الأسئلة بدقة ووضوح.",
        },
        "programmer": {
            "name": "مبرمج خبير",
            "prompt": "أنت مبرمج خبير متعدد اللغات. ساعد في كتابة وتصحيح الكود. استخدم python_repl للمسائل الحسابية.",
        },
        "arabic": {
            "name": "مساعد عربي",
            "prompt": "أنت مساعد ذكي تتحدث العربية بطلاقة. اللهجة المصرية مفضلة. كن ودوداً ومختصراً وعملياً.",
        },
    }

    return {"templates": templates}


@router.post("/test-ai")
async def test_ai(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "مرحبا، قل مرحباً في جملة واحدة")
        model_id = data.get("model_id")

        response = await process_query(message, model_id)
        return {"ok": True, "response": response}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@router.get("/system/status")
async def system_status():
    config = load_config()
    active = get_active_model()

    env_vars = {
        "GROQ_API_KEY": bool(os.getenv("GROQ_API_KEY")),
        "GOOGLE_API_KEY": bool(os.getenv("GOOGLE_API_KEY")),
        "CEREBRAS_API_KEY": bool(os.getenv("CEREBRAS_API_KEY")),
        "TELEGRAM_BOT_TOKEN": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
    }

    return {
        "version": config.get("version", "2.0.0"),
        "active_model": active.get("name") if active else None,
        "models_count": len(config.get("models", [])),
        "skills_enabled": get_enabled_skills(),
        "env_configured": env_vars,
        "telegram_enabled": config.get("telegram_enabled", True),
    }


# === MCP Endpoints ===


@router.get("/mcp")
async def list_mcp_servers():
    return {"servers": mcp_manager.list_servers()}


@router.post("/mcp")
async def add_mcp_server(request: Request):
    try:
        data = await request.json()
        server = MCPServer(
            name=data.get("name", "unnamed"),
            transport=data.get("transport", "stdio"),
            command=data.get("command"),
            args=data.get("args", []),
            url=data.get("url"),
            env=data.get("env", {}),
            enabled=data.get("enabled", True),
        )
        if mcp_manager.add_server(server):
            return {"ok": True, "server": server.to_dict()}
        return JSONResponse(
            {"ok": False, "error": "Server already exists"}, status_code=400
        )
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.get("/mcp/{name}")
async def get_mcp_server(name: str):
    server = mcp_manager.get_server(name)
    if server:
        return server.to_dict()
    return JSONResponse({"error": "Server not found"}, status_code=404)


@router.put("/mcp/{name}")
async def update_mcp_server(name: str, request: Request):
    try:
        updates = await request.json()
        if mcp_manager.update_server(name, updates):
            return {"ok": True}
        return JSONResponse({"ok": False, "error": "Server not found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.delete("/mcp/{name}")
async def remove_mcp_server(name: str):
    if mcp_manager.remove_server(name):
        return {"ok": True}
    return JSONResponse({"ok": False, "error": "Server not found"}, status_code=404)


@router.post("/mcp/{name}/toggle")
async def toggle_mcp_server(name: str, request: Request):
    data = await request.json()
    enabled = data.get("enabled", True)
    if mcp_manager.toggle_server(name, enabled):
        return {"ok": True, "enabled": enabled}
    return JSONResponse({"ok": False, "error": "Server not found"}, status_code=404)


@router.post("/mcp/{name}/start")
async def start_mcp_server(name: str):
    result = await mcp_manager.start_server(name)
    return result


@router.post("/mcp/{name}/stop")
async def stop_mcp_server(name: str):
    result = mcp_manager.stop_server(name)
    return result


@router.post("/mcp/{name}/test")
async def test_mcp_server(name: str):
    result = await mcp_manager.test_server(name)
    return result


# === Skills Registry Endpoints ===


@router.get("/skills/registry")
async def list_skills_registry(category: Optional[str] = None):
    return {"skills": skills_registry.list_skills(category)}


@router.get("/skills/registry/{skill_id}")
async def get_skill_registry(skill_id: str):
    skill = skills_registry.get_skill(skill_id)
    if skill:
        return skill.to_dict()
    return JSONResponse({"error": "Skill not found"}, status_code=404)


@router.post("/skills/registry/{skill_id}/enable")
async def enable_skill_registry(skill_id: str):
    if skills_registry.enable_skill(skill_id):
        return {"ok": True}
    return JSONResponse({"ok": False, "error": "Skill not found"}, status_code=404)


@router.post("/skills/registry/{skill_id}/disable")
async def disable_skill_registry(skill_id: str):
    if skills_registry.disable_skill(skill_id):
        return {"ok": True}
    return JSONResponse({"ok": False, "error": "Skill not found"}, status_code=404)


@router.get("/skills/marketplace")
async def fetch_skills_marketplace(q: Optional[str] = None, limit: int = 20):
    skills = await skills_registry.fetch_marketplace(q, limit)
    return {"skills": skills}


@router.post("/skills/marketplace/{skill_id}/install")
async def install_skill_from_marketplace(skill_id: str):
    result = await skills_registry.install_from_marketplace(skill_id)
    return result


@router.get("/skills/categories")
async def get_skill_categories():
    return {"categories": skills_registry.get_categories()}


# === Agent Router Endpoints ===


@router.get("/agents")
async def list_agents():
    return {"agents": agent_router.list_agents()}


@router.post("/agents")
async def add_agent(request: Request):
    try:
        data = await request.json()
        agent = Agent(
            id=data.get("id", f"agent-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
            name=data.get("name", "New Agent"),
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
        if agent_router.add_agent(agent):
            return {"ok": True, "agent": agent.to_dict()}
        return JSONResponse(
            {"ok": False, "error": "Agent already exists"}, status_code=400
        )
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    agent = agent_router.get_agent(agent_id)
    if agent:
        return agent.to_dict()
    return JSONResponse({"error": "Agent not found"}, status_code=404)


@router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, request: Request):
    try:
        updates = await request.json()
        if agent_router.update_agent(agent_id, updates):
            return {"ok": True}
        return JSONResponse({"ok": False, "error": "Agent not found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.delete("/agents/{agent_id}")
async def remove_agent(agent_id: str):
    if agent_router.remove_agent(agent_id):
        return {"ok": True}
    return JSONResponse({"ok": False, "error": "Cannot remove agent"}, status_code=400)


@router.post("/agents/{agent_id}/activate")
async def activate_agent(agent_id: str):
    if agent_router.set_default_agent(agent_id):
        return {"ok": True}
    return JSONResponse({"ok": False, "error": "Agent not found"}, status_code=404)


@router.get("/agents/routing/tree")
async def get_routing_tree():
    return {"tree": agent_router.get_routing_tree()}


@router.get("/agents/routing/validate")
async def validate_routing():
    issues = agent_router.validate_routing()
    return {"valid": len(issues) == 0, "issues": issues}


# === Scheduler Endpoints ===


@router.get("/scheduler/tasks")
async def list_scheduled_tasks():
    return {"tasks": scheduler.list_tasks()}


@router.post("/scheduler/tasks")
async def add_scheduled_task(request: Request):
    try:
        data = await request.json()
        task = ScheduledTask(
            id=data.get("id", f"task-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
            name=data.get("name", "New Task"),
            task_type=data.get("task_type", "prompt"),
            schedule=data.get("schedule", "0 9 * * *"),
            config=data.get("config", {}),
            enabled=data.get("enabled", True),
        )
        if scheduler.add_task(task):
            return {"ok": True, "task": task.to_dict()}
        return JSONResponse(
            {"ok": False, "error": "Task already exists"}, status_code=400
        )
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.get("/scheduler/tasks/{task_id}")
async def get_scheduled_task(task_id: str):
    task = scheduler.get_task(task_id)
    if task:
        return task.to_dict()
    return JSONResponse({"error": "Task not found"}, status_code=404)


@router.put("/scheduler/tasks/{task_id}")
async def update_scheduled_task(task_id: str, request: Request):
    try:
        updates = await request.json()
        if scheduler.update_task(task_id, updates):
            return {"ok": True}
        return JSONResponse({"ok": False, "error": "Task not found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.delete("/scheduler/tasks/{task_id}")
async def remove_scheduled_task(task_id: str):
    if scheduler.remove_task(task_id):
        return {"ok": True}
    return JSONResponse({"ok": False, "error": "Task not found"}, status_code=404)


@router.post("/scheduler/tasks/{task_id}/toggle")
async def toggle_scheduled_task(task_id: str, request: Request):
    data = await request.json()
    enabled = data.get("enabled", True)
    if scheduler.toggle_task(task_id, enabled):
        return {"ok": True, "enabled": enabled}
    return JSONResponse({"ok": False, "error": "Task not found"}, status_code=404)


@router.post("/scheduler/tasks/{task_id}/run")
async def run_scheduled_task(task_id: str):
    result = await scheduler.run_task_now(task_id)
    return result


# === Log Endpoints ===


@router.get("/logs")
async def get_logs(
    level: Optional[str] = None, source: Optional[str] = None, limit: int = 100
):
    entries = log_stream.get_entries(level, source, limit)
    return {"logs": entries, "count": len(entries)}


@router.get("/logs/stats")
async def get_log_stats():
    return log_stream.get_stats()


@router.delete("/logs")
async def clear_logs():
    log_stream.clear()
    return {"ok": True}


@router.get("/logs/search")
async def search_logs(q: str = Query(..., min_length=1), limit: int = 50):
    results = log_stream.search(q, limit)
    return {"logs": results, "query": q}


# === Auto-Updater Endpoints ===


@router.get("/system/updates")
async def get_update_status():
    from core.auto_updater import auto_updater

    return auto_updater.get_status()


@router.post("/system/updates/check")
async def check_for_updates():
    from core.auto_updater import auto_updater

    result = await auto_updater.check_for_updates()
    return result


@router.post("/system/updates/backup")
async def create_system_backup():
    from core.auto_updater import auto_updater

    result = await auto_updater.create_backup()
    return result


# === Self-Healing Endpoints ===


@router.get("/system/health")
async def get_system_health():
    from core.self_healing import self_healing

    return self_healing.get_status()


@router.post("/system/health/check")
async def run_health_checks():
    from core.self_healing import self_healing

    result = await self_healing.run_health_checks()
    return result


@router.get("/system/errors")
async def get_system_errors(limit: int = 50):
    from core.self_healing import self_healing

    return {
        "errors": self_healing.errors[-limit:],
        "recoveries": self_healing.recoveries[-limit:],
    }


# === Health Monitor Endpoints ===


@router.get("/system/metrics")
async def get_system_metrics():
    from core.health_monitor import health_monitor

    return await health_monitor.collect_metrics()


@router.get("/system/metrics/summary")
async def get_metrics_summary(minutes: int = 60):
    from core.health_monitor import health_monitor

    return health_monitor.get_metrics_summary(minutes)


@router.get("/system/alerts")
async def get_system_alerts(limit: int = 20):
    from core.health_monitor import health_monitor

    return {
        "alerts": health_monitor._alerts[-limit:],
        "count": len(health_monitor._alerts),
    }


# === Nuclear System Status ===


@router.get("/system/nuclear")
async def get_nuclear_status():
    from core.auto_updater import auto_updater
    from core.self_healing import self_healing
    from core.health_monitor import health_monitor
    from core.scheduler import scheduler
    from core.log_stream import log_stream

    return {
        "version": "2.0.0-nuclear",
        "uptime": (datetime.utcnow() - START_TIME).total_seconds(),
        "systems": {
            "auto_updater": auto_updater.get_status(),
            "self_healing": self_healing.get_status(),
            "health_monitor": health_monitor.get_status(),
            "scheduler": {"running": scheduler.running, "tasks": len(scheduler.tasks)},
            "log_stream": log_stream.get_stats(),
        },
        "features": {
            "auto_update": True,
            "self_healing": True,
            "health_monitoring": True,
            "auto_backup": True,
            "error_recovery": True,
            "real_time_logs": True,
        },
    }
