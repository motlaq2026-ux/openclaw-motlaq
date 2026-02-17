import os
import json
from pathlib import Path

CONFIG_PATH = Path("/app/data/config.json")

DEFAULT_CONFIG = {
    "active_model_id": "default_groq",
    "models": [
        {
            "id": "default_groq",
            "name": "Llama3 70B",
            "provider": "groq",
            "model_id": "llama3-70b-8192",
            "api_key_source": "env",
            "api_key_env": "GROQ_KEY",
            "api_key_value": "",
            "base_url": "https://api.groq.com/openai/v1",
            "max_tokens": 1024,
            "temperature": 0.7
        }
    ],
    "system_prompt": """أنت OpenClaw، مساعد ذكاء اصطناعي متقدم 🦞
لديك قدرات بحث في الإنترنت وتنفيذ كود بايثون.
- للمعلومات الحديثة: استخدم web_search
- للحسابات والتحليل: استخدم python_repl
- رد بشكل مختصر ومفيد""",
    "telegram_enabled": True,
    "web_search_enabled": True,
    "python_repl_enabled": True
}

def load_config() -> dict:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge with defaults for any missing keys
            for key, val in DEFAULT_CONFIG.items():
                if key not in data:
                    data[key] = val
            return data
        except Exception:
            pass
    save_config(DEFAULT_CONFIG.copy())
    return DEFAULT_CONFIG.copy()

def save_config(config: dict) -> bool:
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Config save error: {e}")
        return False

def get_active_model() -> dict | None:
    config = load_config()
    active_id = config.get("active_model_id")
    for model in config.get("models", []):
        if model["id"] == active_id:
            return model
    models = config.get("models", [])
    return models[0] if models else None

def get_api_key(model: dict) -> str:
    if model.get("api_key_source") == "env":
        env_var = model.get("api_key_env", "")
        return os.getenv(env_var, "")
    return model.get("api_key_value", "")
