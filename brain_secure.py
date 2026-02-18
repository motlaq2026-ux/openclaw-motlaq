"""OpenClaw Brain - Secure AI processing engine."""

import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from pathlib import Path
import httpx

from core.utils.data_store import config_manager
from core.utils.secure_python import secure_executor


@dataclass
class Message:
    role: str
    content: str
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class Thread:
    id: str
    messages: List[Message]
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                for m in self.messages
            ],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class SecureBrain:
    """Secure AI brain with sandboxed execution."""

    def __init__(self):
        self.config = {}
        self.usage_stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "by_provider": {},
        }
        self._lock = asyncio.Lock()

    async def load_config(self):
        """Load configuration from data store."""
        self.config = await config_manager.load_config()

    async def process_query(
        self,
        user_text: str,
        model_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        context: Optional[List[Dict]] = None,
    ) -> str:
        """Process user query securely."""
        await self.load_config()

        # Get active model
        model_config = await self._get_model_config(model_id)
        if not model_config:
            return "⚠️ No AI model configured. Please add a model in Settings."

        # Track usage
        async with self._lock:
            self.usage_stats["total_requests"] += 1

        # Build messages
        messages = []
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": user_text})

        # Call AI API
        try:
            response = await self._call_ai_api(model_config, messages)

            # Track tokens if available
            if "usage" in response:
                tokens = response["usage"].get("total_tokens", 0)
                async with self._lock:
                    self.usage_stats["total_tokens"] += tokens
                    provider = model_config.get("provider", "unknown")
                    if provider not in self.usage_stats["by_provider"]:
                        self.usage_stats["by_provider"][provider] = {
                            "requests": 0,
                            "tokens": 0,
                        }
                    self.usage_stats["by_provider"][provider]["requests"] += 1
                    self.usage_stats["by_provider"][provider]["tokens"] += tokens

            # Extract response text
            if "choices" in response and len(response["choices"]) > 0:
                return response["choices"][0]["message"]["content"]
            else:
                return "⚠️ Empty response from AI model."

        except Exception as e:
            print(f"Error calling AI API: {e}")
            return f"❌ Error: Failed to get AI response. {str(e)}"

    async def _get_model_config(self, model_id: Optional[str] = None) -> Optional[Dict]:
        """Get model configuration."""
        models = self.config.get("models", [])

        if not models:
            return None

        # Use specified model or first one
        if model_id:
            for model in models:
                if model.get("id") == model_id or model.get("model_id") == model_id:
                    return model

        # Return primary model or first available
        for model in models:
            if model.get("is_primary") or model.get("enabled"):
                return model

        return models[0] if models else None

    async def _call_ai_api(self, model_config: Dict, messages: List[Dict]) -> Dict:
        """Call AI API with configuration."""
        provider = model_config.get("provider", "").lower()
        base_url = model_config.get("base_url", "")
        api_key = model_config.get("api_key", "")
        model_name = model_config.get("model_id", "gpt-3.5-turbo")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        # Adjust headers based on provider
        if provider == "anthropic" or "anthropic" in base_url:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            }
            data = {
                "model": model_name,
                "messages": messages,
                "max_tokens": model_config.get("max_tokens", 4096),
            }
        else:
            # OpenAI compatible format
            data = {
                "model": model_name,
                "messages": messages,
                "max_tokens": model_config.get("max_tokens", 4096),
                "temperature": 0.7,
            }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/chat/completions", headers=headers, json=data
            )
            response.raise_for_status()
            return response.json()

    async def execute_python(self, code: str) -> Dict[str, Any]:
        """Execute Python code securely."""
        try:
            result = secure_executor.execute(code)
            return {
                "success": True,
                "output": result.get("output", ""),
                "error": result.get("error"),
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
            }

    async def web_search(
        self, query: str, max_results: int = 5
    ) -> List[Dict[str, str]]:
        """Search web using DuckDuckGo (async)."""
        try:
            # Import here to avoid startup issues
            from duckduckgo_search import DDGS

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with DDGS() as ddgs:
                results = await loop.run_in_executor(
                    None, lambda: list(ddgs.text(query, max_results=max_results))
                )

            return [
                {
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": r.get("body", "")[:200] + "..."
                    if len(r.get("body", "")) > 200
                    else r.get("body", ""),
                }
                for r in results
            ]
        except Exception as e:
            print(f"Web search error: {e}")
            return []

    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        async with self._lock:
            return dict(self.usage_stats)


# Global brain instance
brain = SecureBrain()
