import os
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

CONFIG_PATH = Path("/app/data/config.json")
DATA_DIR = Path("/app/data")

DEFAULT_CONFIG = {
    "version": "2.0.0",
    "active_model_id": "groq-llama-70b",
    "models": [
        {
            "id": "groq-llama-70b",
            "name": "Llama 3.3 70B",
            "provider": "groq",
            "model_id": "llama-3.3-70b-versatile",
            "api_key_source": "env",
            "api_key_env": "GROQ_API_KEY",
            "api_key_value": "",
            "base_url": "https://api.groq.com/openai/v1",
            "max_tokens": 4096,
            "temperature": 0.7,
            "capabilities": ["text", "tools"],
            "priority": 1,
        },
        {
            "id": "groq-llama-8b",
            "name": "Llama 3.3 8B",
            "provider": "groq",
            "model_id": "llama-3.3-8b-instant",
            "api_key_source": "env",
            "api_key_env": "GROQ_API_KEY",
            "api_key_value": "",
            "base_url": "https://api.groq.com/openai/v1",
            "max_tokens": 4096,
            "temperature": 0.7,
            "capabilities": ["text", "tools"],
            "priority": 2,
        },
        {
            "id": "gemini-flash",
            "name": "Gemini 2.0 Flash",
            "provider": "google",
            "model_id": "gemini-2.0-flash",
            "api_key_source": "env",
            "api_key_env": "GOOGLE_API_KEY",
            "api_key_value": "",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
            "max_tokens": 8192,
            "temperature": 0.7,
            "capabilities": ["text", "vision", "tools"],
            "priority": 3,
        },
        {
            "id": "cerebras-llama",
            "name": "Cerebras Llama 3.3",
            "provider": "cerebras",
            "model_id": "llama-3.3-70b",
            "api_key_source": "env",
            "api_key_env": "CEREBRAS_API_KEY",
            "api_key_value": "",
            "base_url": "https://api.cerebras.ai/v1",
            "max_tokens": 4096,
            "temperature": 0.7,
            "capabilities": ["text", "tools"],
            "priority": 4,
        },
    ],
    "system_prompt": """أنت OpenClaw، مساعد ذكاء اصطناعي متقدم 🦞

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
    "skills": {
        "web_search": {"enabled": True, "max_results": 5},
        "python_repl": {"enabled": True, "timeout": 30},
        "vision": {"enabled": True},
    },
    "telegram_enabled": True,
    "telegram_config": {
        "allowed_users": [],
        "allowed_groups": [],
        "require_mention_in_groups": True,
    },
    "limits": {
        "max_threads": 100,
        "max_messages_per_thread": 50,
        "usage_history_days": 30,
        "max_log_size_mb": 10,
    },
    "backup": {"enabled": True, "interval_hours": 24},
    "metadata": {"created_at": None, "updated_at": None, "total_requests": 0},
}

_config_cache: Dict[str, Any] = {}
_config_lock = threading.Lock()
_last_config_load: float = 0


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    global _config_cache, _last_config_load

    with _config_lock:
        ensure_data_dir()

        if not CONFIG_PATH.exists():
            config = DEFAULT_CONFIG.copy()
            config["metadata"]["created_at"] = datetime.utcnow().isoformat()
            config["metadata"]["updated_at"] = datetime.utcnow().isoformat()
            save_config(config)
            _config_cache = config
            return config

        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)

            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value

            _config_cache = config
            _last_config_load = datetime.utcnow().timestamp()
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    global _config_cache

    with _config_lock:
        try:
            ensure_data_dir()

            if "metadata" not in config:
                config["metadata"] = {}
            config["metadata"]["updated_at"] = datetime.utcnow().isoformat()

            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            _config_cache = config
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False


def get_active_model() -> Optional[Dict[str, Any]]:
    config = load_config()
    active_id = config.get("active_model_id")

    for model in config.get("models", []):
        if model.get("id") == active_id:
            return model

    models = config.get("models", [])
    return models[0] if models else None


def get_api_key(model: Dict[str, Any]) -> Optional[str]:
    if model.get("api_key_source") == "env":
        env_var = model.get("api_key_env", "")
        return os.getenv(env_var, "")
    return model.get("api_key_value", "")


def get_model_by_id(model_id: str) -> Optional[Dict[str, Any]]:
    config = load_config()
    for model in config.get("models", []):
        if model.get("id") == model_id:
            return model
    return None


def add_model(model: Dict[str, Any]) -> bool:
    config = load_config()

    for existing in config.get("models", []):
        if existing.get("id") == model.get("id"):
            return False

    config.setdefault("models", []).append(model)
    return save_config(config)


def update_model(model_id: str, updates: Dict[str, Any]) -> bool:
    config = load_config()

    for i, model in enumerate(config.get("models", [])):
        if model.get("id") == model_id:
            config["models"][i].update(updates)
            return save_config(config)

    return False


def delete_model(model_id: str) -> bool:
    config = load_config()
    models = config.get("models", [])

    if len(models) <= 1:
        return False

    config["models"] = [m for m in models if m.get("id") != model_id]

    if config.get("active_model_id") == model_id:
        config["active_model_id"] = (
            config["models"][0].get("id") if config["models"] else None
        )

    return save_config(config)


def set_active_model(model_id: str) -> bool:
    config = load_config()

    for model in config.get("models", []):
        if model.get("id") == model_id:
            config["active_model_id"] = model_id
            return save_config(config)

    return False


def update_skill(skill_name: str, settings: Dict[str, Any]) -> bool:
    config = load_config()
    config.setdefault("skills", {})[skill_name] = settings
    return save_config(config)


def toggle_skill(skill_name: str, enabled: bool) -> bool:
    config = load_config()
    if skill_name in config.get("skills", {}):
        config["skills"][skill_name]["enabled"] = enabled
    else:
        config.setdefault("skills", {})[skill_name] = {"enabled": enabled}
    return save_config(config)


def get_enabled_skills() -> List[str]:
    config = load_config()
    skills = config.get("skills", {})
    return [
        name
        for name, settings in skills.items()
        if isinstance(settings, dict) and settings.get("enabled", False)
    ]


def increment_request_count() -> None:
    config = load_config()
    config.setdefault("metadata", {})
    config["metadata"]["total_requests"] = (
        config["metadata"].get("total_requests", 0) + 1
    )
    save_config(config)


def get_all_providers() -> List[Dict[str, Any]]:
    return [
        {
            "id": "groq",
            "name": "Groq",
            "icon": "⚡",
            "base_url": "https://api.groq.com/openai/v1",
            "free": True,
            "models": [
                "llama-3.3-70b-versatile",
                "llama-3.3-8b-instant",
                "llama-3.1-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
                "gemma2-9b-it",
            ],
        },
        {
            "id": "cerebras",
            "name": "Cerebras",
            "icon": "🚀",
            "base_url": "https://api.cerebras.ai/v1",
            "free": True,
            "models": ["llama-3.3-70b", "llama-3.1-70b", "llama-3.1-8b"],
        },
        {
            "id": "google",
            "name": "Google Gemini",
            "icon": "🔵",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
            "free": True,
            "models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
        },
        {
            "id": "openai",
            "name": "OpenAI",
            "icon": "🟢",
            "base_url": "https://api.openai.com/v1",
            "free": False,
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        },
        {
            "id": "anthropic",
            "name": "Anthropic",
            "icon": "🟠",
            "base_url": "https://api.anthropic.com/v1",
            "free": False,
            "models": [
                "claude-sonnet-4-20250514",
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
            ],
        },
        {
            "id": "deepseek",
            "name": "DeepSeek",
            "icon": "🐋",
            "base_url": "https://api.deepseek.com/v1",
            "free": True,
            "models": ["deepseek-chat", "deepseek-reasoner"],
        },
        {
            "id": "mistral",
            "name": "Mistral",
            "icon": "🌊",
            "base_url": "https://api.mistral.ai/v1",
            "free": False,
            "models": [
                "mistral-large-latest",
                "mistral-small-latest",
                "codestral-latest",
            ],
        },
        {
            "id": "openrouter",
            "name": "OpenRouter",
            "icon": "🔄",
            "base_url": "https://openrouter.ai/api/v1",
            "free": False,
            "models": [
                "anthropic/claude-sonnet-4",
                "openai/gpt-4o",
                "google/gemini-pro-1.5",
            ],
        },
        {
            "id": "custom",
            "name": "Custom",
            "icon": "🔧",
            "base_url": "",
            "free": None,
            "models": [],
        },
    ]
