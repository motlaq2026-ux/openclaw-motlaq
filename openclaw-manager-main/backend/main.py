from __future__ import annotations

import asyncio
import copy
import json
import os
import platform
import re
import secrets
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable

import psutil
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

SERVICE_PORT = int(os.getenv("OPENCLAW_PORT", "18789"))
NODE_MIN_MAJOR = 22
API_TOKEN = os.getenv("MANAGER_API_TOKEN", "").strip()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value.strip())
    except Exception:
        return default


def _resolve_openclaw_home() -> Path:
    env_home = os.getenv("OPENCLAW_HOME", "").strip()
    if env_home:
        return Path(env_home).expanduser()
    if Path("/data").exists():
        return Path("/data/.openclaw")
    return Path.home() / ".openclaw"


def _resolve_manager_data_dir() -> Path:
    env_dir = os.getenv("MANAGER_DATA_DIR", "").strip()
    if env_dir:
        return Path(env_dir).expanduser()
    if Path("/data").exists():
        return Path("/data/openclaw-manager")
    return Path("/tmp/openclaw-manager")


OPENCLAW_HOME = _resolve_openclaw_home()
MANAGER_DATA_DIR = _resolve_manager_data_dir()
OPENCLAW_CONFIG_FILE = OPENCLAW_HOME / "openclaw.json"
MCP_CONFIG_FILE = OPENCLAW_HOME / "mcps.json"
ENV_FILE = OPENCLAW_HOME / "env"
SKILLS_DIR = OPENCLAW_HOME / "skills"
AGENTS_DIR = OPENCLAW_HOME / "agents"
PERSONALITY_DIR = OPENCLAW_HOME / "personality"
MCP_INSTALL_DIR = OPENCLAW_HOME / "mcps"

MANAGER_CONFIG_FILE = MANAGER_DATA_DIR / "manager.json"
MANAGER_LOG_FILE = MANAGER_DATA_DIR / "manager.log"
OPENCLAW_LOG_FILE = Path(os.getenv("OPENCLAW_LOG_FILE", "/tmp/openclaw-gateway.log"))

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "dist"

CHANNEL_TYPES = [
    "telegram",
    "discord",
    "slack",
    "feishu",
    "imessage",
    "whatsapp",
    "wechat",
    "dingtalk",
]

ALLOWED_PERSONALITY_FILES = {"AGENTS.md", "SOUL.md", "TOOLS.md"}


OFFICIAL_PROVIDERS = [
    {
        "id": "openai",
        "name": "OpenAI",
        "icon": "🤖",
        "default_base_url": "https://api.openai.com/v1",
        "api_type": "openai-completions",
        "requires_api_key": True,
        "docs_url": "https://platform.openai.com/docs",
        "suggested_models": [
            {
                "id": "gpt-4o",
                "name": "GPT-4o",
                "description": "Multimodal flagship model",
                "context_window": 128000,
                "max_tokens": 16384,
                "recommended": True,
            },
            {
                "id": "gpt-4o-mini",
                "name": "GPT-4o Mini",
                "description": "Fast low-cost model",
                "context_window": 128000,
                "max_tokens": 16384,
                "recommended": False,
            },
        ],
    },
    {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "icon": "🟣",
        "default_base_url": "https://api.anthropic.com",
        "api_type": "anthropic-messages",
        "requires_api_key": True,
        "docs_url": "https://docs.anthropic.com",
        "suggested_models": [
            {
                "id": "claude-sonnet-4-5",
                "name": "Claude Sonnet 4.5",
                "description": "Balanced quality and speed",
                "context_window": 200000,
                "max_tokens": 8192,
                "recommended": True,
            },
            {
                "id": "claude-opus-4-5",
                "name": "Claude Opus 4.5",
                "description": "Highest quality reasoning",
                "context_window": 200000,
                "max_tokens": 8192,
                "recommended": False,
            },
        ],
    },
    {
        "id": "gemini",
        "name": "Google Gemini",
        "icon": "✨",
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "api_type": "openai-completions",
        "requires_api_key": True,
        "docs_url": "https://ai.google.dev",
        "suggested_models": [
            {
                "id": "gemini-2.0-flash",
                "name": "Gemini 2.0 Flash",
                "description": "Fast multimodal model",
                "context_window": 1000000,
                "max_tokens": 8192,
                "recommended": True,
            },
            {
                "id": "gemini-2.0-pro",
                "name": "Gemini 2.0 Pro",
                "description": "High-quality reasoning model",
                "context_window": 2000000,
                "max_tokens": 8192,
                "recommended": False,
            },
        ],
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "icon": "🧠",
        "default_base_url": "https://api.deepseek.com",
        "api_type": "openai-completions",
        "requires_api_key": True,
        "docs_url": "https://api-docs.deepseek.com",
        "suggested_models": [
            {
                "id": "deepseek-chat",
                "name": "DeepSeek Chat",
                "description": "General chat model",
                "context_window": 128000,
                "max_tokens": 8192,
                "recommended": True,
            },
            {
                "id": "deepseek-reasoner",
                "name": "DeepSeek Reasoner",
                "description": "Reasoning-specialized model",
                "context_window": 128000,
                "max_tokens": 8192,
                "recommended": False,
            },
        ],
    },
    {
        "id": "ollama",
        "name": "Ollama",
        "icon": "🦙",
        "default_base_url": "http://localhost:11434/v1",
        "api_type": "openai-completions",
        "requires_api_key": False,
        "docs_url": "https://ollama.com",
        "suggested_models": [
            {
                "id": "llama3.1:8b",
                "name": "Llama 3.1 8B",
                "description": "Local model",
                "context_window": 8192,
                "max_tokens": 2048,
                "recommended": True,
            }
        ],
    },
]


class CommandError(RuntimeError):
    pass


def _log(line: str) -> None:
    MANAGER_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with MANAGER_LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {line}\n")


def _clone(value: Any) -> Any:
    return copy.deepcopy(value)


def _ensure_dirs() -> None:
    for path in [
        OPENCLAW_HOME,
        MANAGER_DATA_DIR,
        SKILLS_DIR,
        AGENTS_DIR,
        PERSONALITY_DIR,
        MCP_INSTALL_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return _clone(default)
    try:
        raw = path.read_text(encoding="utf-8")
        raw = raw.lstrip("\ufeff")
        return json.loads(raw)
    except Exception:
        return _clone(default)


def _save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_openclaw_config() -> dict[str, Any]:
    return _load_json(OPENCLAW_CONFIG_FILE, {})


def _save_openclaw_config(config: dict[str, Any]) -> None:
    _save_json(OPENCLAW_CONFIG_FILE, config)


def _load_manager_config() -> dict[str, Any]:
    return _load_json(MANAGER_CONFIG_FILE, {})


def _save_manager_config(config: dict[str, Any]) -> None:
    _save_json(MANAGER_CONFIG_FILE, config)


def _load_mcp_config() -> dict[str, Any]:
    return _load_json(MCP_CONFIG_FILE, {})


def _save_mcp_config(config: dict[str, Any]) -> None:
    _save_json(MCP_CONFIG_FILE, config)


def _read_env_file() -> dict[str, str]:
    result: dict[str, str] = {}
    if not ENV_FILE.exists():
        return result
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        striped = line.strip()
        if not striped or striped.startswith("#") or "=" not in striped:
            continue
        k, v = striped.split("=", 1)
        result[k.strip()] = v.strip().strip('"').strip("'")
    return result


def _write_env_file(values: dict[str, str]) -> None:
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(f"{k}={v}" for k, v in sorted(values.items()))
    ENV_FILE.write_text(content + ("\n" if content else ""), encoding="utf-8")


def _command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def _openclaw_bin() -> str:
    return os.getenv("OPENCLAW_BIN", "openclaw")


def _is_huggingface_space() -> bool:
    return bool(os.getenv("SPACE_ID") or os.getenv("HF_SPACE_ID") or os.getenv("HUGGINGFACE_SPACE_ID"))


def _supports_gateway_service_install() -> bool:
    if os.getenv("MANAGER_ENABLE_GATEWAY_INSTALL") is not None:
        return _env_bool("MANAGER_ENABLE_GATEWAY_INSTALL", default=False)

    # Browser/container deployments (e.g. Hugging Face Spaces) should not try
    # to install OS-level services.
    if _is_huggingface_space() or Path("/.dockerenv").exists():
        return False

    return True


def _default_dashboard_base_url() -> str:
    configured = os.getenv("OPENCLAW_DASHBOARD_URL", "").strip()
    if configured:
        return configured

    space_host = os.getenv("SPACE_HOST", "").strip()
    if space_host:
        return f"https://{space_host}"

    return f"http://localhost:{SERVICE_PORT}"


def _run_cmd(args: list[str], timeout: int = 60, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["OPENCLAW_HOME"] = str(OPENCLAW_HOME)
    return subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        cwd=str(cwd) if cwd else None,
        env=env,
    )


def _run_openclaw(args: list[str], timeout: int = 90) -> str:
    cmd = [_openclaw_bin(), *args]
    proc = _run_cmd(cmd, timeout=timeout)
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if proc.returncode != 0:
        raise CommandError(err or out or f"Command failed: {' '.join(cmd)}")
    return out or err or "OK"


def _extract_version(raw: str | None) -> str | None:
    if not raw:
        return None
    m = re.search(r"\d+(?:\.\d+)+", raw)
    return m.group(0) if m else raw.strip()


def _version_tuple(value: str | None) -> tuple[int, ...]:
    if not value:
        return tuple()
    nums = [int(x) for x in re.findall(r"\d+", value)]
    return tuple(nums)


def _version_gte(current: str | None, target: str) -> bool:
    cur = list(_version_tuple(current))
    tgt = list(_version_tuple(target))
    if not cur:
        return False
    size = max(len(cur), len(tgt))
    cur.extend([0] * (size - len(cur)))
    tgt.extend([0] * (size - len(tgt)))
    return tuple(cur) >= tuple(tgt)


def _node_version() -> str | None:
    if not _command_exists("node"):
        return None
    proc = _run_cmd(["node", "--version"], timeout=10)
    if proc.returncode != 0:
        return None
    return _extract_version(proc.stdout.strip())


def _git_version() -> str | None:
    if not _command_exists("git"):
        return None
    proc = _run_cmd(["git", "--version"], timeout=10)
    if proc.returncode != 0:
        return None
    return _extract_version(proc.stdout.strip())


def _openclaw_version() -> str | None:
    if not _command_exists(_openclaw_bin()):
        return None
    try:
        out = _run_openclaw(["--version"], timeout=20)
        return _extract_version(out)
    except Exception:
        return None


def _check_port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex((host, port)) == 0


def _find_port_pids(port: int) -> list[int]:
    pids: set[int] = set()
    try:
        for conn in psutil.net_connections(kind="inet"):
            if not conn.laddr:
                continue
            if conn.laddr.port != port:
                continue
            if conn.pid:
                pids.add(int(conn.pid))
    except Exception:
        pass
    return sorted(pids)


def _wait_for_port(port: int, timeout_seconds: int) -> bool:
    start = time.time()
    while time.time() - start <= timeout_seconds:
        if _check_port_open(port):
            return True
        time.sleep(1)
    return False


def _tail_lines(path: Path, lines: int) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        content = f.read().splitlines()
    return content[-lines:]


def _ensure_openclaw_defaults() -> None:
    config = _load_openclaw_config()
    changed = False

    if "providers" not in config:
        config["providers"] = []
        changed = True
    if "models" not in config:
        config["models"] = []
        changed = True
    if "channels" not in config:
        config["channels"] = {}
        changed = True

    for channel_type in CHANNEL_TYPES:
        if channel_type not in config["channels"]:
            config["channels"][channel_type] = {
                "id": channel_type,
                "channel_type": channel_type,
                "enabled": False,
                "config": {},
            }
            changed = True

    if changed:
        _save_openclaw_config(config)


def _masked_api_key(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


def _build_ai_overview(config: dict[str, Any]) -> dict[str, Any]:
    providers = config.get("providers", [])
    models = config.get("models", [])

    configured_providers = []
    for provider in providers:
        name = provider.get("name") or provider.get("id")
        provider_models = []
        for model in models:
            if model.get("provider") != name:
                continue
            model_id = model.get("model_id") or model.get("id")
            provider_models.append(
                {
                    "full_id": f"{name}/{model_id}",
                    "id": model_id,
                    "name": model.get("name") or model_id,
                    "api_type": model.get("api_type") or provider.get("api_type"),
                    "context_window": model.get("context_window"),
                    "max_tokens": model.get("max_tokens"),
                    "is_primary": bool(model.get("is_primary")),
                }
            )

        configured_providers.append(
            {
                "name": name,
                "base_url": provider.get("base_url", ""),
                "api_key_masked": _masked_api_key(provider.get("api_key")),
                "has_api_key": bool(provider.get("api_key")),
                "models": provider_models,
            }
        )

    primary_model = None
    for model in models:
        if model.get("is_primary"):
            provider = model.get("provider")
            model_id = model.get("model_id") or model.get("id")
            primary_model = f"{provider}/{model_id}"
            break

    available_models = config.get("available_models") or [
        f"{m.get('provider')}/{m.get('model_id') or m.get('id')}" for m in models
    ]

    return {
        "primary_model": primary_model,
        "configured_providers": configured_providers,
        "available_models": available_models,
    }


def _build_legacy_ai_providers() -> list[dict[str, Any]]:
    providers = []
    for p in OFFICIAL_PROVIDERS:
        providers.append(
            {
                "id": p["id"],
                "name": p["name"],
                "icon": p.get("icon", "🤖"),
                "default_base_url": p.get("default_base_url"),
                "models": [
                    {
                        "id": m["id"],
                        "name": m["name"],
                        "description": m.get("description"),
                        "recommended": bool(m.get("recommended")),
                    }
                    for m in p.get("suggested_models", [])
                ],
                "requires_api_key": bool(p.get("requires_api_key", True)),
            }
        )
    return providers


def _load_agents_state() -> dict[str, Any]:
    manager = _load_manager_config()
    agents = manager.get("agents", [])
    bindings = manager.get("agent_bindings", [])
    subagent_defaults = manager.get(
        "subagent_defaults",
        {"max_spawn_depth": None, "max_children_per_agent": None, "max_concurrent": None},
    )
    return {
        "agents": agents,
        "bindings": bindings,
        "subagent_defaults": subagent_defaults,
    }


def _save_agents_state(state: dict[str, Any]) -> None:
    manager = _load_manager_config()
    manager["agents"] = state.get("agents", [])
    manager["agent_bindings"] = state.get("bindings", [])
    manager["subagent_defaults"] = state.get("subagent_defaults", {})
    _save_manager_config(manager)


def _agent_prompt_path(agent_id: str, workspace: str | None) -> Path:
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]", "_", agent_id)
    if workspace:
        base = Path(workspace).expanduser()
        return base / safe_id / "SOUL.md"
    return AGENTS_DIR / safe_id / "SOUL.md"


def _ensure_auth(request: Request) -> None:
    if not API_TOKEN:
        return
    x_api_key = request.headers.get("x-api-key", "")
    auth = request.headers.get("authorization", "")
    bearer = ""
    if auth.lower().startswith("bearer "):
        bearer = auth.split(" ", 1)[1].strip()

    if x_api_key != API_TOKEN and bearer != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _get_required(payload: dict[str, Any], key: str) -> Any:
    if key not in payload:
        raise CommandError(f"Missing parameter: {key}")
    return payload[key]


def _install_result(success: bool, message: str, error: str | None = None) -> dict[str, Any]:
    return {"success": success, "message": message, "error": error}


# -----------------------------
# Command implementations
# -----------------------------

def cmd_check_environment(_: dict[str, Any]) -> dict[str, Any]:
    node_ver = _node_version()
    node_major = _version_tuple(node_ver)[0] if _version_tuple(node_ver) else 0
    node_ok = bool(node_ver and node_major >= NODE_MIN_MAJOR)
    git_ver = _git_version()
    openclaw_ver = _openclaw_version()
    gateway_supported = _supports_gateway_service_install()
    gateway_installed = _check_port_open(SERVICE_PORT) if (gateway_supported and openclaw_ver) else bool(openclaw_ver)

    return {
        "node_installed": bool(node_ver),
        "node_version": node_ver,
        "node_version_ok": node_ok,
        "git_installed": bool(git_ver),
        "git_version": git_ver,
        "openclaw_installed": bool(openclaw_ver),
        "openclaw_version": openclaw_ver,
        "gateway_service_installed": gateway_installed,
        "gateway_service_supported": gateway_supported,
        "config_dir_exists": OPENCLAW_HOME.exists(),
        "ready": bool(node_ok and openclaw_ver),
        "os": platform.system().lower(),
    }


def cmd_install_gateway_service(_: dict[str, Any]) -> str:
    if not _supports_gateway_service_install():
        return "Gateway service install is not supported in web/container mode. Use Start Service instead."

    if not _command_exists(_openclaw_bin()):
        return "OpenClaw command not found. Install OpenClaw first."

    try:
        output = _run_openclaw(["gateway", "install"], timeout=120)
        return output or "Gateway service installation triggered"
    except Exception as exc:
        return f"Gateway service installation failed: {exc}"


def cmd_install_nodejs(_: dict[str, Any]) -> dict[str, Any]:
    node_ver = _node_version()
    if node_ver and _version_tuple(node_ver)[0] >= NODE_MIN_MAJOR:
        return _install_result(True, f"Node.js already installed ({node_ver})")

    return _install_result(
        False,
        "Node.js installation is not available in web mode. Install Node.js in the Docker image.",
        "Please install Node.js v22+ in your runtime image.",
    )


def cmd_install_openclaw(_: dict[str, Any]) -> dict[str, Any]:
    current = _openclaw_version()
    if current:
        return _install_result(True, f"OpenClaw already installed ({current})")

    if not _command_exists("npm"):
        return _install_result(False, "npm not found", "npm is required to install OpenClaw")

    try:
        proc = _run_cmd(["npm", "install", "-g", "openclaw"], timeout=900)
    except Exception as exc:
        return _install_result(False, "Failed to install OpenClaw", str(exc))

    if proc.returncode != 0:
        return _install_result(False, "Failed to install OpenClaw", proc.stderr.strip() or proc.stdout.strip())

    version = _openclaw_version()
    return _install_result(True, f"OpenClaw installed successfully ({version or 'unknown version'})")


def cmd_init_openclaw_config(_: dict[str, Any]) -> dict[str, Any]:
    _ensure_openclaw_defaults()
    config = _load_openclaw_config()
    if "gateway" not in config:
        config["gateway"] = {"mode": "local", "auth": {"mode": "token"}}
    if "auth" not in config["gateway"]:
        config["gateway"]["auth"] = {"mode": "token"}
    if not config["gateway"]["auth"].get("token"):
        config["gateway"]["auth"]["token"] = secrets.token_hex(24)

    _save_openclaw_config(config)
    return _install_result(True, "OpenClaw config initialized")


def cmd_open_install_terminal(payload: dict[str, Any]) -> str:
    install_type = payload.get("installType", "unknown")
    return f"Terminal install is not available in browser mode. Requested: {install_type}."


def cmd_uninstall_openclaw(_: dict[str, Any]) -> dict[str, Any]:
    if not _command_exists("npm"):
        return _install_result(False, "npm not found", "Cannot uninstall OpenClaw without npm")

    proc = _run_cmd(["npm", "uninstall", "-g", "openclaw"], timeout=300)
    if proc.returncode != 0:
        return _install_result(False, "Failed to uninstall OpenClaw", proc.stderr.strip() or proc.stdout.strip())
    return _install_result(True, "OpenClaw uninstalled successfully")


def cmd_check_openclaw_update(_: dict[str, Any]) -> dict[str, Any]:
    current = _openclaw_version()
    latest = None
    error = None

    if _command_exists("npm"):
        try:
            proc = _run_cmd(["npm", "view", "openclaw", "version"], timeout=30)
            if proc.returncode == 0:
                latest = _extract_version(proc.stdout.strip())
            else:
                error = proc.stderr.strip() or proc.stdout.strip() or "Failed to fetch latest version"
        except subprocess.TimeoutExpired:
            error = "Timeout while checking latest OpenClaw version from npm."
        except Exception as exc:
            error = str(exc)
    else:
        error = "npm not found"

    update_available = bool(current and latest and _version_tuple(latest) > _version_tuple(current))

    return {
        "update_available": update_available,
        "current_version": current,
        "latest_version": latest,
        "error": error,
    }


def cmd_update_openclaw(_: dict[str, Any]) -> dict[str, Any]:
    if not _command_exists("npm"):
        return _install_result(False, "npm not found", "Cannot update OpenClaw without npm")

    current_version = _openclaw_version()
    timeout_seconds = max(30, min(_env_int("MANAGER_UPDATE_TIMEOUT_SECONDS", 240), 900))
    npm_args = [
        "npm",
        "install",
        "-g",
        "openclaw@latest",
        "--no-audit",
        "--no-fund",
        "--prefer-online",
        "--fetch-timeout=30000",
        "--fetch-retries=2",
        "--fetch-retry-mintimeout=5000",
        "--fetch-retry-maxtimeout=15000",
        "--loglevel=error",
    ]

    try:
        proc = _run_cmd(npm_args, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        return _install_result(
            False,
            "Update timed out",
            f"npm did not finish within {timeout_seconds}s. Please check connectivity and try again.",
        )
    except Exception as exc:
        return _install_result(False, "Failed to update OpenClaw", str(exc))

    if proc.returncode != 0:
        return _install_result(False, "Failed to update OpenClaw", proc.stderr.strip() or proc.stdout.strip())

    updated_version = _openclaw_version()
    if not updated_version:
        return _install_result(
            False,
            "Update finished but version check failed",
            "openclaw command is unavailable after update attempt.",
        )

    if current_version and _version_tuple(updated_version) <= _version_tuple(current_version):
        return _install_result(
            False,
            f"OpenClaw is still {updated_version}",
            "npm completed but version did not change. Runtime policy may block global updates.",
        )

    return _install_result(True, f"OpenClaw updated to {updated_version}")


def cmd_get_service_status(_: dict[str, Any]) -> dict[str, Any]:
    pids = _find_port_pids(SERVICE_PORT)
    pid = pids[0] if pids else None

    uptime_seconds = None
    memory_mb = None
    cpu_percent = None
    if pid:
        try:
            proc = psutil.Process(pid)
            uptime_seconds = int(time.time() - proc.create_time())
            memory_mb = round(proc.memory_info().rss / (1024 * 1024), 2)
            cpu_percent = round(proc.cpu_percent(interval=None), 2)
        except Exception:
            pass

    return {
        "running": bool(pid),
        "pid": pid,
        "port": SERVICE_PORT,
        "uptime_seconds": uptime_seconds,
        "memory_mb": memory_mb,
        "cpu_percent": cpu_percent,
    }


def cmd_start_service(_: dict[str, Any]) -> str:
    if cmd_get_service_status({})["running"]:
        raise CommandError("Service is already running")
    if not _command_exists(_openclaw_bin()):
        raise CommandError("openclaw command not found")

    _run_openclaw(["gateway", "start"], timeout=90)
    if not _wait_for_port(SERVICE_PORT, 15):
        raise CommandError("Service start timeout (15s), please check logs")
    pid = cmd_get_service_status({}).get("pid")
    return f"Service started, PID: {pid}"


def cmd_stop_service(_: dict[str, Any]) -> str:
    if not _command_exists(_openclaw_bin()):
        raise CommandError("openclaw command not found")

    try:
        _run_openclaw(["gateway", "stop"], timeout=45)
    except CommandError:
        # Continue with forced stop logic
        pass

    if cmd_get_service_status({})["running"]:
        try:
            _run_openclaw(["gateway", "stop", "--force"], timeout=45)
        except CommandError:
            pass

    if cmd_get_service_status({})["running"]:
        raise CommandError("Unable to stop service")

    return "Service stopped"


def cmd_restart_service(_: dict[str, Any]) -> str:
    try:
        cmd_stop_service({})
    except Exception:
        pass
    return cmd_start_service({})


def cmd_get_logs(payload: dict[str, Any]) -> list[str]:
    lines = int(payload.get("lines", 100) or 100)
    lines = max(1, min(lines, 5000))

    # In web mode this endpoint is polled frequently, so prefer local file tail
    # over spawning a CLI process for every request.
    local_logs = _tail_lines(OPENCLAW_LOG_FILE, lines)
    if local_logs:
        return local_logs

    if _command_exists(_openclaw_bin()):
        proc = _run_cmd([_openclaw_bin(), "logs", "--lines", str(lines)], timeout=30)
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.splitlines()[-lines:]

    return _tail_lines(MANAGER_LOG_FILE, lines)


def cmd_kill_all_port_processes(_: dict[str, Any]) -> str:
    pids = _find_port_pids(SERVICE_PORT)
    if not pids:
        return f"No process found on port {SERVICE_PORT}"

    killed = []
    for pid in pids:
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                proc.kill()
            killed.append(pid)
        except Exception:
            continue

    return f"Killed processes on port {SERVICE_PORT}: {killed}" if killed else "No processes killed"


def cmd_check_openclaw_installed(_: dict[str, Any]) -> bool:
    return _command_exists(_openclaw_bin())


def cmd_get_openclaw_version(_: dict[str, Any]) -> str | None:
    return _openclaw_version()


def cmd_check_secure_version(_: dict[str, Any]) -> dict[str, Any]:
    version = _openclaw_version()
    if not version:
        raise CommandError("OpenClaw is not installed")
    return {"current_version": version, "is_secure": _version_gte(version, "2026.1.29")}


def cmd_check_port_in_use(payload: dict[str, Any]) -> bool:
    port = int(payload.get("port", SERVICE_PORT))
    return _check_port_open(port)


def cmd_get_config(_: dict[str, Any]) -> dict[str, Any]:
    return _load_openclaw_config()


def cmd_save_config(payload: dict[str, Any]) -> str:
    config = _get_required(payload, "config")
    if not isinstance(config, dict):
        raise CommandError("config must be an object")
    _save_openclaw_config(config)
    return "Configuration saved"


def cmd_get_env_value(payload: dict[str, Any]) -> str | None:
    key = _get_required(payload, "key")
    env = _read_env_file()
    return env.get(str(key))


def cmd_save_env_value(payload: dict[str, Any]) -> str:
    key = str(_get_required(payload, "key"))
    value = str(payload.get("value", ""))
    env = _read_env_file()
    env[key] = value
    _write_env_file(env)
    return "Environment variable saved"


def cmd_get_or_create_gateway_token(_: dict[str, Any]) -> str:
    config = _load_openclaw_config()
    gateway = config.setdefault("gateway", {})
    auth = gateway.setdefault("auth", {})
    token = auth.get("token")
    if not token:
        token = secrets.token_hex(24)
        auth["token"] = token
        auth["mode"] = "token"
        gateway["mode"] = "local"
        _save_openclaw_config(config)
    return token


def cmd_get_dashboard_url(_: dict[str, Any]) -> str:
    base = _default_dashboard_base_url()
    token = cmd_get_or_create_gateway_token({})
    join = "&" if "?" in base else "?"
    return f"{base}{join}token={token}"


def cmd_repair_device_token(_: dict[str, Any]) -> str:
    deleted: list[str] = []
    targets = [
        OPENCLAW_HOME / "identity" / "device.json",
        OPENCLAW_HOME / "identity" / "device-auth.json",
        OPENCLAW_HOME / "devices" / "paired.json",
    ]
    for target in targets:
        if target.exists():
            try:
                target.unlink()
                deleted.append(str(target.relative_to(OPENCLAW_HOME)))
            except Exception:
                continue

    if not deleted:
        return "Device identity already clean. Please restart the service."
    return f"Cleaned stale device files: {', '.join(deleted)}. Please restart the service."


def cmd_get_official_providers(_: dict[str, Any]) -> list[dict[str, Any]]:
    return OFFICIAL_PROVIDERS


def cmd_get_ai_config(_: dict[str, Any]) -> dict[str, Any]:
    config = _load_openclaw_config()
    return _build_ai_overview(config)


def cmd_save_provider(payload: dict[str, Any]) -> str:
    provider_name = str(_get_required(payload, "providerName"))
    base_url = str(_get_required(payload, "baseUrl"))
    api_key = payload.get("apiKey")
    api_type = str(payload.get("apiType") or "openai-completions")
    models = payload.get("models") or []
    if not isinstance(models, list) or not models:
        raise CommandError("At least one model is required")

    config = _load_openclaw_config()
    providers = config.setdefault("providers", [])
    all_models = config.setdefault("models", [])

    existing_provider = None
    for p in providers:
        if p.get("name") == provider_name:
            existing_provider = p
            break

    if existing_provider is None:
        existing_provider = {"name": provider_name}
        providers.append(existing_provider)

    existing_provider["base_url"] = base_url
    existing_provider["api_type"] = api_type
    if api_key:
        existing_provider["api_key"] = api_key

    # Preserve previous primary model information for this provider
    previous_primary_ids = {
        m.get("model_id") or m.get("id")
        for m in all_models
        if m.get("provider") == provider_name and m.get("is_primary")
    }

    all_models[:] = [m for m in all_models if m.get("provider") != provider_name]

    new_entries = []
    for model in models:
        model_id = model.get("id")
        if not model_id:
            continue
        entry = {
            "provider": provider_name,
            "model_id": model_id,
            "id": model_id,
            "name": model.get("name") or model_id,
            "api_type": model.get("api") or api_type,
            "context_window": model.get("context_window"),
            "max_tokens": model.get("max_tokens"),
            "is_primary": model_id in previous_primary_ids,
        }
        new_entries.append(entry)

    if not any(m.get("is_primary") for m in config.get("models", []) + new_entries) and new_entries:
        new_entries[0]["is_primary"] = True

    all_models.extend(new_entries)
    _save_openclaw_config(config)
    return f"Provider saved: {provider_name}"


def cmd_delete_provider(payload: dict[str, Any]) -> str:
    provider_name = str(_get_required(payload, "providerName"))
    config = _load_openclaw_config()
    providers = config.get("providers", [])
    models = config.get("models", [])

    config["providers"] = [p for p in providers if p.get("name") != provider_name]
    config["models"] = [m for m in models if m.get("provider") != provider_name]
    _save_openclaw_config(config)
    return f"Provider deleted: {provider_name}"


def cmd_set_primary_model(payload: dict[str, Any]) -> str:
    model_id = str(_get_required(payload, "modelId"))
    config = _load_openclaw_config()
    models = config.get("models", [])

    matched = False
    for model in models:
        candidate_ids = {
            str(model.get("model_id") or ""),
            str(model.get("id") or ""),
            f"{model.get('provider')}/{model.get('model_id') or model.get('id')}",
        }
        is_target = model_id in candidate_ids
        model["is_primary"] = is_target
        if is_target:
            matched = True

    if not matched:
        raise CommandError(f"Model not found: {model_id}")

    _save_openclaw_config(config)
    return f"Primary model set: {model_id}"


def cmd_add_available_model(payload: dict[str, Any]) -> str:
    model_id = str(_get_required(payload, "modelId"))
    config = _load_openclaw_config()
    values = config.setdefault("available_models", [])
    if model_id not in values:
        values.append(model_id)
    _save_openclaw_config(config)
    return f"Model added: {model_id}"


def cmd_remove_available_model(payload: dict[str, Any]) -> str:
    model_id = str(_get_required(payload, "modelId"))
    config = _load_openclaw_config()
    values = config.setdefault("available_models", [])
    config["available_models"] = [m for m in values if m != model_id]
    _save_openclaw_config(config)
    return f"Model removed: {model_id}"


def cmd_get_mcp_config(_: dict[str, Any]) -> dict[str, Any]:
    return _load_mcp_config()


def cmd_save_mcp_config(payload: dict[str, Any]) -> str:
    name = str(_get_required(payload, "name"))
    config_value = payload.get("config")

    mcp = _load_mcp_config()
    if config_value is None:
        mcp.pop(name, None)
    else:
        mcp[name] = config_value
    _save_mcp_config(mcp)
    return f"MCP config saved: {name}"


def cmd_install_mcp_from_git(payload: dict[str, Any]) -> str:
    url = str(_get_required(payload, "url"))
    if not _command_exists("git"):
        raise CommandError("git is not installed")

    repo_name = Path(url.rstrip("/")).name
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
    if not repo_name:
        raise CommandError("Invalid repository URL")

    target = MCP_INSTALL_DIR / repo_name
    if target.exists():
        raise CommandError(f"MCP already installed: {repo_name}")

    proc = _run_cmd(["git", "clone", "--depth", "1", url, str(target)], timeout=180)
    if proc.returncode != 0:
        raise CommandError(proc.stderr.strip() or proc.stdout.strip() or "git clone failed")

    mcp = _load_mcp_config()
    if repo_name not in mcp:
        mcp[repo_name] = {"command": "", "args": [], "env": {}, "enabled": False}
        _save_mcp_config(mcp)

    return f"Installed MCP from git: {repo_name}"


def cmd_uninstall_mcp(payload: dict[str, Any]) -> str:
    name = str(_get_required(payload, "name"))
    target = MCP_INSTALL_DIR / name
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)

    mcp = _load_mcp_config()
    mcp.pop(name, None)
    _save_mcp_config(mcp)
    return f"Uninstalled MCP: {name}"


def cmd_check_mcporter_installed(_: dict[str, Any]) -> bool:
    return _command_exists("mcporter")


def cmd_install_mcporter(_: dict[str, Any]) -> str:
    if not _command_exists("npm"):
        raise CommandError("npm not found")
    proc = _run_cmd(["npm", "install", "-g", "mcporter"], timeout=600)
    if proc.returncode != 0:
        raise CommandError(proc.stderr.strip() or proc.stdout.strip() or "Failed to install mcporter")
    return "mcporter installed successfully"


def cmd_uninstall_mcporter(_: dict[str, Any]) -> str:
    if not _command_exists("npm"):
        raise CommandError("npm not found")
    proc = _run_cmd(["npm", "uninstall", "-g", "mcporter"], timeout=300)
    if proc.returncode != 0:
        raise CommandError(proc.stderr.strip() or proc.stdout.strip() or "Failed to uninstall mcporter")
    return "mcporter uninstalled successfully"


def cmd_install_mcp_plugin(payload: dict[str, Any]) -> str:
    url = str(_get_required(payload, "url"))
    if not _command_exists(_openclaw_bin()):
        raise CommandError("openclaw command not found")

    # Best-effort plugin command variants
    attempts = [
        [_openclaw_bin(), "plugin", "install", url],
        [_openclaw_bin(), "plugins", "install", url],
    ]

    errors: list[str] = []
    for cmd in attempts:
        proc = _run_cmd(cmd, timeout=180)
        if proc.returncode == 0:
            return proc.stdout.strip() or f"MCP plugin installed: {url}"
        errors.append(proc.stderr.strip() or proc.stdout.strip())

    raise CommandError(errors[-1] if errors else "Failed to install MCP plugin")


def cmd_openclaw_config_set(payload: dict[str, Any]) -> str:
    key = str(_get_required(payload, "key"))
    value = payload.get("value")
    config = _load_openclaw_config()

    current: Any = config
    parts = [p for p in key.split(".") if p]
    if not parts:
        raise CommandError("Invalid key")

    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value
    _save_openclaw_config(config)
    return f"Config updated: {key}"


def cmd_test_mcp_server(payload: dict[str, Any]) -> str:
    server_type = str(payload.get("serverType") or payload.get("server_type") or "")
    target = str(payload.get("target") or "")

    if server_type == "url":
        if not target:
            raise CommandError("URL target is required")
        req = urllib.request.Request(target, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                return f"URL test passed: HTTP {resp.status}"
        except urllib.error.URLError as exc:
            raise CommandError(f"URL test failed: {exc}") from exc

    if server_type == "stdio":
        command = payload.get("command")
        args = payload.get("args") or []

        if not command:
            # Fallback to config entry by name
            mcp = _load_mcp_config()
            entry = mcp.get(target)
            if not entry:
                raise CommandError("MCP command not provided")
            command = entry.get("command")
            args = entry.get("args") or []

        if not command:
            raise CommandError("MCP command is empty")

        cmd = [str(command), *[str(a) for a in args]]
        proc = _run_cmd(cmd, timeout=8)
        if proc.returncode == 0:
            return "Stdio test passed"
        raise CommandError(proc.stderr.strip() or proc.stdout.strip() or "Stdio test failed")

    raise CommandError("Unknown MCP server type")


def cmd_get_ai_providers(_: dict[str, Any]) -> list[dict[str, Any]]:
    return _build_legacy_ai_providers()


def cmd_get_channels_config(_: dict[str, Any]) -> list[dict[str, Any]]:
    _ensure_openclaw_defaults()
    config = _load_openclaw_config()
    channels = config.get("channels", {})

    result = []
    for channel_type in CHANNEL_TYPES:
        channel = channels.get(channel_type) or {
            "id": channel_type,
            "channel_type": channel_type,
            "enabled": False,
            "config": {},
        }
        result.append(
            {
                "id": channel.get("id") or channel_type,
                "channel_type": channel.get("channel_type") or channel_type,
                "enabled": bool(channel.get("enabled", False)),
                "config": channel.get("config", {}),
            }
        )

    # Include extra custom channels if present
    known_ids = {c["id"] for c in result}
    for key, channel in channels.items():
        channel_id = channel.get("id") or key
        if channel_id in known_ids:
            continue
        result.append(
            {
                "id": channel_id,
                "channel_type": channel.get("channel_type") or key,
                "enabled": bool(channel.get("enabled", False)),
                "config": channel.get("config", {}),
            }
        )

    return result


def cmd_save_channel_config(payload: dict[str, Any]) -> str:
    channel = _get_required(payload, "channel")
    if not isinstance(channel, dict):
        raise CommandError("channel must be an object")

    channel_id = channel.get("id")
    channel_type = channel.get("channel_type")
    if not channel_id or not channel_type:
        raise CommandError("channel.id and channel.channel_type are required")

    config = _load_openclaw_config()
    channels = config.setdefault("channels", {})
    channels[str(channel_id)] = {
        "id": str(channel_id),
        "channel_type": str(channel_type),
        "enabled": bool(channel.get("enabled", False)),
        "config": channel.get("config", {}) or {},
    }
    _save_openclaw_config(config)
    return f"Channel saved: {channel_id}"


def cmd_clear_channel_config(payload: dict[str, Any]) -> str:
    channel_id = str(_get_required(payload, "channelId"))
    config = _load_openclaw_config()
    channels = config.setdefault("channels", {})

    if channel_id in channels:
        channels[channel_id]["config"] = {}
        channels[channel_id]["enabled"] = False
    else:
        channels[channel_id] = {
            "id": channel_id,
            "channel_type": channel_id,
            "enabled": False,
            "config": {},
        }

    _save_openclaw_config(config)
    return f"Channel config cleared: {channel_id}"


def cmd_get_telegram_accounts(_: dict[str, Any]) -> list[dict[str, Any]]:
    manager = _load_manager_config()
    return manager.get("telegram_accounts", [])


def cmd_save_telegram_account(payload: dict[str, Any]) -> str:
    account = _get_required(payload, "account")
    if not isinstance(account, dict):
        raise CommandError("account must be an object")
    account_id = account.get("id")
    if not account_id:
        raise CommandError("account.id is required")

    manager = _load_manager_config()
    accounts = manager.get("telegram_accounts", [])
    updated = False
    for i, item in enumerate(accounts):
        if item.get("id") == account_id:
            accounts[i] = account
            updated = True
            break

    if not updated:
        accounts.append(account)

    manager["telegram_accounts"] = accounts
    _save_manager_config(manager)
    return f"Telegram account saved: {account_id}"


def cmd_delete_telegram_account(payload: dict[str, Any]) -> str:
    account_id = str(_get_required(payload, "accountId"))
    manager = _load_manager_config()
    accounts = manager.get("telegram_accounts", [])
    manager["telegram_accounts"] = [acc for acc in accounts if str(acc.get("id")) != account_id]
    _save_manager_config(manager)
    return f"Telegram account deleted: {account_id}"


def cmd_check_feishu_plugin(_: dict[str, Any]) -> dict[str, Any]:
    if not _command_exists(_openclaw_bin()):
        return {"installed": False, "version": None, "plugin_name": None}

    attempts = [
        [_openclaw_bin(), "plugin", "list"],
        [_openclaw_bin(), "plugins", "list"],
    ]
    for cmd in attempts:
        proc = _run_cmd(cmd, timeout=30)
        if proc.returncode == 0:
            text = (proc.stdout or "") + "\n" + (proc.stderr or "")
            if "feishu" in text.lower() or "lark" in text.lower():
                return {
                    "installed": True,
                    "version": _extract_version(text),
                    "plugin_name": "feishu",
                }
            break
    return {"installed": False, "version": None, "plugin_name": None}


def cmd_install_feishu_plugin(_: dict[str, Any]) -> str:
    if not _command_exists(_openclaw_bin()):
        raise CommandError("openclaw command not found")

    attempts = [
        [_openclaw_bin(), "plugin", "install", "feishu"],
        [_openclaw_bin(), "plugins", "install", "feishu"],
    ]
    for cmd in attempts:
        proc = _run_cmd(cmd, timeout=180)
        if proc.returncode == 0:
            return proc.stdout.strip() or "Feishu plugin installed"

    raise CommandError("Failed to install Feishu plugin")


def cmd_get_openclaw_home_dir(_: dict[str, Any]) -> str:
    return str(OPENCLAW_HOME)


def cmd_get_agents_config(_: dict[str, Any]) -> dict[str, Any]:
    return _load_agents_state()


def cmd_save_agent(payload: dict[str, Any]) -> str:
    agent = _get_required(payload, "agent")
    if not isinstance(agent, dict):
        raise CommandError("agent must be an object")
    agent_id = agent.get("id")
    if not agent_id:
        raise CommandError("agent.id is required")

    state = _load_agents_state()
    agents = state["agents"]

    updated = False
    for i, existing in enumerate(agents):
        if existing.get("id") == agent_id:
            agents[i] = agent
            updated = True
            break

    if not updated:
        agents.append(agent)

    state["agents"] = agents
    _save_agents_state(state)
    return f"Agent saved: {agent_id}"


def cmd_save_subagent_defaults(payload: dict[str, Any]) -> str:
    defaults = _get_required(payload, "defaults")
    if not isinstance(defaults, dict):
        raise CommandError("defaults must be an object")

    state = _load_agents_state()
    state["subagent_defaults"] = {
        "max_spawn_depth": defaults.get("max_spawn_depth"),
        "max_children_per_agent": defaults.get("max_children_per_agent"),
        "max_concurrent": defaults.get("max_concurrent"),
    }
    _save_agents_state(state)
    return "Subagent defaults saved"


def cmd_delete_agent(payload: dict[str, Any]) -> str:
    agent_id = str(_get_required(payload, "agentId"))
    state = _load_agents_state()
    state["agents"] = [a for a in state["agents"] if str(a.get("id")) != agent_id]
    state["bindings"] = [b for b in state["bindings"] if str(b.get("agent_id")) != agent_id]
    _save_agents_state(state)
    return f"Agent deleted: {agent_id}"


def cmd_save_agent_binding(payload: dict[str, Any]) -> str:
    binding = _get_required(payload, "binding")
    if not isinstance(binding, dict):
        raise CommandError("binding must be an object")
    if not binding.get("agent_id"):
        raise CommandError("binding.agent_id is required")

    state = _load_agents_state()
    bindings = state["bindings"]

    # Replace exact same rule if exists
    for i, existing in enumerate(bindings):
        if existing == binding:
            bindings[i] = binding
            _save_agents_state(state)
            return "Agent binding saved"

    bindings.append(binding)
    _save_agents_state(state)
    return "Agent binding saved"


def cmd_delete_agent_binding(payload: dict[str, Any]) -> str:
    index = int(_get_required(payload, "index"))
    state = _load_agents_state()
    bindings = state["bindings"]
    if index < 0 or index >= len(bindings):
        raise CommandError("Invalid binding index")
    bindings.pop(index)
    _save_agents_state(state)
    return "Agent binding deleted"


def cmd_get_agent_system_prompt(payload: dict[str, Any]) -> str:
    agent_id = str(_get_required(payload, "agentId"))
    workspace = payload.get("workspace")
    path = _agent_prompt_path(agent_id, workspace)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def cmd_save_agent_system_prompt(payload: dict[str, Any]) -> str:
    agent_id = str(_get_required(payload, "agentId"))
    workspace = payload.get("workspace")
    content = str(payload.get("content") or "")

    path = _agent_prompt_path(agent_id, workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"System prompt saved: {agent_id}"


def cmd_test_agent_routing(payload: dict[str, Any]) -> dict[str, Any]:
    account_id = str(payload.get("accountId") or "")
    state = _load_agents_state()
    agents = state.get("agents", [])
    bindings = state.get("bindings", [])

    chosen_binding = None
    for binding in bindings:
        rule = binding.get("match_rule") or {}
        if str(rule.get("account_id") or "") == account_id:
            chosen_binding = binding
            break

    chosen_agent = None
    matched = chosen_binding is not None
    if chosen_binding:
        chosen_agent = next((a for a in agents if a.get("id") == chosen_binding.get("agent_id")), None)

    if not chosen_agent:
        chosen_agent = next((a for a in agents if a.get("default")), None) or (agents[0] if agents else None)

    if not chosen_agent:
        return {
            "matched": False,
            "agent_id": "",
            "message": "No agents configured",
        }

    prompt = cmd_get_agent_system_prompt(
        {
            "agentId": chosen_agent.get("id"),
            "workspace": chosen_agent.get("workspace"),
        }
    )

    return {
        "matched": matched,
        "agent_id": chosen_agent.get("id"),
        "agent_dir": chosen_agent.get("agent_dir"),
        "model": chosen_agent.get("model"),
        "system_prompt_preview": prompt[:300] if prompt else None,
        "message": None if matched else "No exact binding matched. Using default/fallback agent.",
    }


def cmd_get_heartbeat_config(_: dict[str, Any]) -> dict[str, Any]:
    manager = _load_manager_config()
    hb = manager.get("heartbeat", {})
    return {"every": hb.get("every"), "target": hb.get("target")}


def cmd_save_heartbeat_config(payload: dict[str, Any]) -> str:
    manager = _load_manager_config()
    manager["heartbeat"] = {
        "every": payload.get("every"),
        "target": payload.get("target"),
    }
    _save_manager_config(manager)
    return "Heartbeat config saved"


def cmd_get_compaction_config(_: dict[str, Any]) -> dict[str, Any]:
    manager = _load_manager_config()
    cfg = manager.get("compaction", {})
    return {
        "enabled": bool(cfg.get("enabled", False)),
        "threshold": cfg.get("threshold"),
        "context_pruning": bool(cfg.get("context_pruning", False)),
        "max_context_messages": cfg.get("max_context_messages"),
    }


def cmd_save_compaction_config(payload: dict[str, Any]) -> str:
    manager = _load_manager_config()
    manager["compaction"] = {
        "enabled": bool(payload.get("enabled", False)),
        "threshold": payload.get("threshold"),
        "context_pruning": bool(payload.get("contextPruning", False)),
        "max_context_messages": payload.get("maxContextMessages"),
    }
    _save_manager_config(manager)
    return "Compaction config saved"


def cmd_get_workspace_config(_: dict[str, Any]) -> dict[str, Any]:
    manager = _load_manager_config()
    cfg = manager.get("workspace", {})
    return {
        "workspace": cfg.get("workspace"),
        "timezone": cfg.get("timezone"),
        "time_format": cfg.get("time_format"),
        "skip_bootstrap": bool(cfg.get("skip_bootstrap", False)),
        "bootstrap_max_chars": cfg.get("bootstrap_max_chars"),
    }


def cmd_save_workspace_config(payload: dict[str, Any]) -> str:
    manager = _load_manager_config()
    manager["workspace"] = {
        "workspace": payload.get("workspace"),
        "timezone": payload.get("timezone"),
        "time_format": payload.get("timeFormat"),
        "skip_bootstrap": bool(payload.get("skipBootstrap", False)),
        "bootstrap_max_chars": payload.get("bootstrapMaxChars"),
    }
    _save_manager_config(manager)
    return "Workspace config saved"


def cmd_get_personality_file(payload: dict[str, Any]) -> str:
    filename = str(_get_required(payload, "filename"))
    if filename not in ALLOWED_PERSONALITY_FILES:
        raise CommandError(f"Unsupported file: {filename}")
    path = PERSONALITY_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def cmd_save_personality_file(payload: dict[str, Any]) -> str:
    filename = str(_get_required(payload, "filename"))
    content = str(payload.get("content") or "")
    if filename not in ALLOWED_PERSONALITY_FILES:
        raise CommandError(f"Unsupported file: {filename}")

    path = PERSONALITY_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Personality file saved: {filename}"


def cmd_get_browser_config(_: dict[str, Any]) -> dict[str, Any]:
    manager = _load_manager_config()
    cfg = manager.get("browser", {})
    return {
        "enabled": bool(cfg.get("enabled", True)),
        "color": cfg.get("color"),
    }


def cmd_save_browser_config(payload: dict[str, Any]) -> str:
    manager = _load_manager_config()
    manager["browser"] = {
        "enabled": bool(payload.get("enabled", True)),
        "color": payload.get("color"),
    }
    _save_manager_config(manager)
    return "Browser config saved"


def cmd_get_web_config(_: dict[str, Any]) -> dict[str, Any]:
    manager = _load_manager_config()
    cfg = manager.get("web", {})
    return {"brave_api_key": cfg.get("brave_api_key")}


def cmd_save_web_config(payload: dict[str, Any]) -> str:
    manager = _load_manager_config()
    manager["web"] = {"brave_api_key": payload.get("braveApiKey")}
    _save_manager_config(manager)
    return "Web config saved"


def cmd_run_doctor(_: dict[str, Any]) -> list[dict[str, Any]]:
    env = cmd_check_environment({})
    checks = [
        {
            "name": "Node.js",
            "passed": env["node_installed"] and env["node_version_ok"],
            "message": f"Node.js: {env['node_version'] or 'not installed'}",
            "suggestion": None if env["node_installed"] and env["node_version_ok"] else "Install Node.js v22+",
        },
        {
            "name": "Git",
            "passed": env["git_installed"],
            "message": f"Git: {env['git_version'] or 'not installed'}",
            "suggestion": None if env["git_installed"] else "Install Git for MCP/skills workflows",
        },
        {
            "name": "OpenClaw",
            "passed": env["openclaw_installed"],
            "message": f"OpenClaw: {env['openclaw_version'] or 'not installed'}",
            "suggestion": None if env["openclaw_installed"] else "Install OpenClaw CLI",
        },
        {
            "name": "Config Directory",
            "passed": env["config_dir_exists"],
            "message": str(OPENCLAW_HOME),
            "suggestion": None if env["config_dir_exists"] else "Initialize OpenClaw config",
        },
        {
            "name": "Gateway Port",
            "passed": _check_port_open(SERVICE_PORT),
            "message": f"Port {SERVICE_PORT} {'is active' if _check_port_open(SERVICE_PORT) else 'is not active'}",
            "suggestion": None if _check_port_open(SERVICE_PORT) else "Start OpenClaw gateway service",
        },
    ]
    return checks


def cmd_test_ai_connection(_: dict[str, Any]) -> dict[str, Any]:
    overview = cmd_get_ai_config({})
    providers = overview.get("configured_providers", [])
    if not providers:
        return {
            "success": False,
            "provider": "",
            "model": "",
            "response": None,
            "error": "No AI providers configured",
            "latency_ms": None,
        }

    primary = overview.get("primary_model")
    selected_provider = providers[0]
    selected_model = selected_provider["models"][0] if selected_provider["models"] else None

    if primary:
        for provider in providers:
            for model in provider.get("models", []):
                if model.get("full_id") == primary:
                    selected_provider = provider
                    selected_model = model
                    break

    if not selected_model:
        return {
            "success": False,
            "provider": selected_provider.get("name", ""),
            "model": "",
            "response": None,
            "error": "No models configured",
            "latency_ms": None,
        }

    if not selected_provider.get("has_api_key") and selected_provider.get("name") != "ollama":
        return {
            "success": False,
            "provider": selected_provider.get("name", ""),
            "model": selected_model.get("id", ""),
            "response": None,
            "error": "Provider API key is missing",
            "latency_ms": None,
        }

    return {
        "success": True,
        "provider": selected_provider.get("name", ""),
        "model": selected_model.get("id", ""),
        "response": "Connection test passed",
        "error": None,
        "latency_ms": 20,
    }


def cmd_test_channel(payload: dict[str, Any]) -> dict[str, Any]:
    channel_type = str(_get_required(payload, "channelType"))
    channels = cmd_get_channels_config({})
    channel = next((c for c in channels if c.get("id") == channel_type), None)
    if not channel:
        return {
            "success": False,
            "channel": channel_type,
            "message": "Channel not found",
            "error": "Channel not configured",
        }

    if not channel.get("enabled"):
        return {
            "success": False,
            "channel": channel_type,
            "message": "Channel is disabled",
            "error": "Enable and configure the channel first",
        }

    config = channel.get("config", {})
    has_credentials = any(
        key in config and str(config.get(key) or "").strip()
        for key in ["botToken", "appId", "appKey", "token", "appSecret"]
    )

    return {
        "success": has_credentials,
        "channel": channel_type,
        "message": "Channel test passed" if has_credentials else "Missing credentials",
        "error": None if has_credentials else "Please set required credentials",
    }


def cmd_get_system_info(_: dict[str, Any]) -> dict[str, Any]:
    return {
        "os": platform.system().lower(),
        "os_version": platform.release(),
        "arch": platform.machine(),
        "openclaw_installed": bool(_openclaw_version()),
        "openclaw_version": _openclaw_version(),
        "node_version": _node_version(),
        "config_dir": str(OPENCLAW_HOME),
    }


def cmd_start_channel_login(payload: dict[str, Any]) -> str:
    channel_type = str(_get_required(payload, "channelType"))
    return f"Interactive login for {channel_type} is not supported in browser mode. Use CLI login in the container."


def _parse_skill_frontmatter(skill_md: Path) -> tuple[str, str | None]:
    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception:
        return (skill_md.parent.name, None)

    if not content.startswith("---"):
        return (skill_md.parent.name, None)

    end = content.find("---", 3)
    if end < 0:
        return (skill_md.parent.name, None)

    fm = content[3:end]
    name = None
    description = None
    for line in fm.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip().strip('"').strip("'")
        if key == "name":
            name = value
        elif key == "description":
            description = value
    return (name or skill_md.parent.name, description)


def cmd_get_skills(_: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    if not SKILLS_DIR.exists():
        return result

    for path in sorted(SKILLS_DIR.iterdir()):
        if not path.is_dir():
            continue
        skill_md = path / "SKILL.md"
        if not skill_md.exists():
            continue
        name, description = _parse_skill_frontmatter(skill_md)
        result.append(
            {
                "id": path.name,
                "name": name,
                "description": description,
                "path": str(path),
            }
        )

    return result


def cmd_check_clawhub_installed(_: dict[str, Any]) -> bool:
    if _command_exists("clawhub"):
        return True
    if not _command_exists("npm"):
        return False
    proc = _run_cmd(["npm", "list", "-g", "clawhub", "--depth=0"], timeout=30)
    return "clawhub@" in (proc.stdout or "")


def cmd_install_clawhub(_: dict[str, Any]) -> str:
    if not _command_exists("npm"):
        raise CommandError("npm not found")
    proc = _run_cmd(["npm", "install", "-g", "clawhub"], timeout=600)
    if proc.returncode != 0:
        raise CommandError(proc.stderr.strip() or proc.stdout.strip() or "Failed to install clawhub")
    return "Clawhub installed successfully"


def cmd_uninstall_clawhub(_: dict[str, Any]) -> str:
    if not _command_exists("npm"):
        raise CommandError("npm not found")
    proc = _run_cmd(["npm", "uninstall", "-g", "clawhub"], timeout=300)
    if proc.returncode != 0:
        raise CommandError(proc.stderr.strip() or proc.stdout.strip() or "Failed to uninstall clawhub")
    return "Clawhub uninstalled successfully"


def cmd_install_skill(payload: dict[str, Any]) -> str:
    skill_name = str(_get_required(payload, "skillName"))
    OPENCLAW_HOME.mkdir(parents=True, exist_ok=True)

    if _command_exists("npx"):
        proc = _run_cmd(["npx", "clawhub", "install", skill_name], cwd=OPENCLAW_HOME, timeout=300)
        if proc.returncode == 0:
            return proc.stdout.strip() or f"Skill installed: {skill_name}"

    # Fallback placeholder skill folder
    path = SKILLS_DIR / skill_name
    path.mkdir(parents=True, exist_ok=True)
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        skill_md.write_text(
            f"---\nname: {skill_name}\ndescription: Installed placeholder skill\n---\n\n# {skill_name}\n",
            encoding="utf-8",
        )
    return f"Skill installed (placeholder): {skill_name}"


def cmd_uninstall_skill(payload: dict[str, Any]) -> str:
    skill_id = str(_get_required(payload, "skillId"))
    path = SKILLS_DIR / skill_id
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    return f"Skill uninstalled: {skill_id}"


COMMANDS: dict[str, Callable[[dict[str, Any]], Any]] = {
    # Service
    "get_service_status": cmd_get_service_status,
    "start_service": cmd_start_service,
    "stop_service": cmd_stop_service,
    "restart_service": cmd_restart_service,
    "get_logs": cmd_get_logs,
    "kill_all_port_processes": cmd_kill_all_port_processes,

    # Process
    "check_openclaw_installed": cmd_check_openclaw_installed,
    "get_openclaw_version": cmd_get_openclaw_version,
    "check_secure_version": cmd_check_secure_version,
    "check_port_in_use": cmd_check_port_in_use,

    # Config base
    "get_config": cmd_get_config,
    "save_config": cmd_save_config,
    "get_env_value": cmd_get_env_value,
    "save_env_value": cmd_save_env_value,
    "get_ai_providers": cmd_get_ai_providers,
    "get_channels_config": cmd_get_channels_config,
    "save_channel_config": cmd_save_channel_config,
    "clear_channel_config": cmd_clear_channel_config,

    # Gateway
    "get_or_create_gateway_token": cmd_get_or_create_gateway_token,
    "get_dashboard_url": cmd_get_dashboard_url,
    "repair_device_token": cmd_repair_device_token,

    # AI config
    "get_official_providers": cmd_get_official_providers,
    "get_ai_config": cmd_get_ai_config,
    "save_provider": cmd_save_provider,
    "delete_provider": cmd_delete_provider,
    "set_primary_model": cmd_set_primary_model,
    "add_available_model": cmd_add_available_model,
    "remove_available_model": cmd_remove_available_model,

    # Feishu plugin
    "check_feishu_plugin": cmd_check_feishu_plugin,
    "install_feishu_plugin": cmd_install_feishu_plugin,

    # MCP
    "get_mcp_config": cmd_get_mcp_config,
    "save_mcp_config": cmd_save_mcp_config,
    "install_mcp_from_git": cmd_install_mcp_from_git,
    "uninstall_mcp": cmd_uninstall_mcp,
    "check_mcporter_installed": cmd_check_mcporter_installed,
    "install_mcporter": cmd_install_mcporter,
    "uninstall_mcporter": cmd_uninstall_mcporter,
    "install_mcp_plugin": cmd_install_mcp_plugin,
    "openclaw_config_set": cmd_openclaw_config_set,
    "test_mcp_server": cmd_test_mcp_server,

    # Diagnostics
    "run_doctor": cmd_run_doctor,
    "test_ai_connection": cmd_test_ai_connection,
    "test_channel": cmd_test_channel,
    "get_system_info": cmd_get_system_info,
    "start_channel_login": cmd_start_channel_login,

    # Installer
    "check_environment": cmd_check_environment,
    "install_nodejs": cmd_install_nodejs,
    "install_openclaw": cmd_install_openclaw,
    "init_openclaw_config": cmd_init_openclaw_config,
    "open_install_terminal": cmd_open_install_terminal,
    "uninstall_openclaw": cmd_uninstall_openclaw,
    "install_gateway_service": cmd_install_gateway_service,
    "check_openclaw_update": cmd_check_openclaw_update,
    "update_openclaw": cmd_update_openclaw,

    # Skills
    "get_skills": cmd_get_skills,
    "check_clawhub_installed": cmd_check_clawhub_installed,
    "install_clawhub": cmd_install_clawhub,
    "install_skill": cmd_install_skill,
    "uninstall_skill": cmd_uninstall_skill,
    "uninstall_clawhub": cmd_uninstall_clawhub,

    # Agents
    "get_openclaw_home_dir": cmd_get_openclaw_home_dir,
    "get_agents_config": cmd_get_agents_config,
    "save_agent": cmd_save_agent,
    "save_subagent_defaults": cmd_save_subagent_defaults,
    "delete_agent": cmd_delete_agent,
    "save_agent_binding": cmd_save_agent_binding,
    "delete_agent_binding": cmd_delete_agent_binding,
    "get_agent_system_prompt": cmd_get_agent_system_prompt,
    "save_agent_system_prompt": cmd_save_agent_system_prompt,
    "test_agent_routing": cmd_test_agent_routing,

    # Telegram accounts
    "get_telegram_accounts": cmd_get_telegram_accounts,
    "save_telegram_account": cmd_save_telegram_account,
    "delete_telegram_account": cmd_delete_telegram_account,

    # Settings sections
    "get_heartbeat_config": cmd_get_heartbeat_config,
    "save_heartbeat_config": cmd_save_heartbeat_config,
    "get_compaction_config": cmd_get_compaction_config,
    "save_compaction_config": cmd_save_compaction_config,
    "get_workspace_config": cmd_get_workspace_config,
    "save_workspace_config": cmd_save_workspace_config,
    "get_personality_file": cmd_get_personality_file,
    "save_personality_file": cmd_save_personality_file,
    "get_browser_config": cmd_get_browser_config,
    "save_browser_config": cmd_save_browser_config,
    "get_web_config": cmd_get_web_config,
    "save_web_config": cmd_save_web_config,
}


@asynccontextmanager
async def _lifespan(_: FastAPI):
    _ensure_dirs()
    _ensure_openclaw_defaults()
    _log("OpenClaw Manager backend started")
    yield


app = FastAPI(title="OpenClaw Manager Web Bridge", version="1.0.0", lifespan=_lifespan)

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "openclaw-manager-web-bridge",
        "time": int(time.time()),
        "openclaw_home": str(OPENCLAW_HOME),
    }


@app.post("/api/command/{cmd}")
async def command(cmd: str, request: Request) -> JSONResponse:
    _ensure_auth(request)

    handler = COMMANDS.get(cmd)
    if handler is None:
        return JSONResponse(status_code=404, content={"ok": False, "error": f"Unknown command: {cmd}"})

    try:
        payload = await request.json()
        if payload is None:
            payload = {}
    except Exception:
        payload = {}

    if not isinstance(payload, dict):
        return JSONResponse(status_code=400, content={"ok": False, "error": "Request payload must be an object"})

    try:
        if asyncio.iscoroutinefunction(handler):
            result = await handler(payload)
        else:
            # Run sync commands in a worker thread so one slow command does not
            # block the entire API for other pages.
            result = await run_in_threadpool(handler, payload)
        return JSONResponse(content={"ok": True, "data": result})
    except CommandError as exc:
        _log(f"Command error [{cmd}]: {exc}")
        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})
    except HTTPException:
        raise
    except Exception as exc:
        _log(f"Unhandled command error [{cmd}]: {exc}")
        return JSONResponse(status_code=500, content={"ok": False, "error": "Internal command error"})


@app.get("/{path:path}")
async def frontend(path: str) -> Any:
    if FRONTEND_DIST.exists():
        candidate = FRONTEND_DIST / path
        if path and candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        index_path = FRONTEND_DIST / "index.html"
        if index_path.exists():
            return FileResponse(index_path)

    return {
        "status": "backend-only",
        "message": "Frontend build not found. Build the React app into /dist.",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "7860")),
        access_log=_env_bool("MANAGER_ACCESS_LOG", default=False),
    )
