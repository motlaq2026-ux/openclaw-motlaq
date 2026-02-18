import os
import json
import io
import asyncio
import contextlib
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List, AsyncGenerator
from openai import AsyncOpenAI
from duckduckgo_search import DDGS

from config import (
    load_config,
    get_active_model,
    get_api_key,
    get_model_by_id,
    increment_request_count,
    get_enabled_skills,
)

# Lazy import to avoid circular dependency
_log_stream = None


def get_log_stream():
    """Get log stream instance (lazy import)."""
    global _log_stream
    if _log_stream is None:
        try:
            from core.log_stream import log_stream

            _log_stream = log_stream
        except ImportError:
            pass
    return _log_stream


def log_info(message: str, source: str = "brain"):
    """Log info message."""
    stream = get_log_stream()
    if stream:
        try:
            stream.info(message, source=source)
        except:
            pass


def log_error(message: str, source: str = "brain"):
    """Log error message."""
    stream = get_log_stream()
    if stream:
        try:
            stream.error(message, source=source)
        except:
            pass


def log_warning(message: str, source: str = "brain"):
    """Log warning message."""
    stream = get_log_stream()
    if stream:
        try:
            stream.warning(message, source=source)
        except:
            pass


USAGE_PATH = "/app/data/usage.json"
THREADS_PATH = "/app/data/threads.json"

DATA_DIR = os.path.dirname(USAGE_PATH)
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)


def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo."""
    log_info(f"Web search: {query[:50]}...", source="web_search")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            log_warning("No results found", source="web_search")
            return "No results found."

        formatted = []
        for r in results:
            formatted.append(
                f"**{r.get('title', 'No title')}**\n{r.get('body', '')}\nURL: {r.get('href', '')}\n"
            )
        log_info(f"Found {len(results)} results", source="web_search")
        return "\n".join(formatted)
    except Exception as e:
        log_error(f"Search error: {str(e)}", source="web_search")
        return f"Search error: {str(e)}"


def python_repl(code: str, timeout: int = 30) -> str:
    """Execute Python code safely."""
    log_info(f"Executing Python code ({len(code)} chars)", source="python_repl")
    output = io.StringIO()
    try:
        safe_builtins = {
            "print": print,
            "len": len,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "int": int,
            "float": float,
            "str": str,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "bool": bool,
            "type": type,
            "isinstance": isinstance,
            "hasattr": hasattr,
            "getattr": getattr,
            "open": open,
            "__import__": __import__,
        }

        with contextlib.redirect_stdout(output):
            with contextlib.redirect_stderr(output):
                exec(code, {"__builtins__": safe_builtins}, {})

        result = output.getvalue()
        log_info(f"Code executed successfully", source="python_repl")
        return result if result.strip() else "Done (no output)"
    except Exception:
        error = traceback.format_exc()
        log_error(f"Code execution error", source="python_repl")
        return error


def load_usage() -> Dict[str, Any]:
    try:
        if os.path.exists(USAGE_PATH):
            with open(USAGE_PATH, "r") as f:
                return json.load(f)
    except:
        pass
    return {
        "last_updated": datetime.utcnow().isoformat(),
        "total_requests": 0,
        "total_tokens": 0,
        "daily": {},
        "models": {},
    }


def save_usage(usage: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(USAGE_PATH), exist_ok=True)
    usage["last_updated"] = datetime.utcnow().isoformat()
    with open(USAGE_PATH, "w") as f:
        json.dump(usage, f, indent=2)


def track_usage(model_id: str, input_tokens: int, output_tokens: int) -> None:
    usage = load_usage()

    usage["total_requests"] = usage.get("total_requests", 0) + 1
    usage["total_tokens"] = usage.get("total_tokens", 0) + input_tokens + output_tokens

    today = datetime.utcnow().strftime("%Y-%m-%d")
    daily = usage.setdefault("daily", {})
    if today not in daily:
        daily[today] = {"requests": 0, "tokens": 0}
    daily[today]["requests"] += 1
    daily[today]["tokens"] += input_tokens + output_tokens

    models = usage.setdefault("models", {})
    if model_id not in models:
        models[model_id] = {"requests": 0, "tokens": 0}
    models[model_id]["requests"] += 1
    models[model_id]["tokens"] += input_tokens + output_tokens

    cutoff = datetime.utcnow().strftime("%Y-%m-%d")
    daily_keys = list(daily.keys())
    for key in daily_keys:
        if key < cutoff[:8] + "01":
            del daily[key]

    save_usage(usage)


def load_threads() -> Dict[str, Any]:
    try:
        if os.path.exists(THREADS_PATH):
            with open(THREADS_PATH, "r") as f:
                return json.load(f)
    except:
        pass
    return {"threads": {}}


def save_threads(threads_data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(THREADS_PATH), exist_ok=True)
    with open(THREADS_PATH, "w") as f:
        json.dump(threads_data, f, ensure_ascii=False, indent=2)


def create_thread(title: str = "New Chat") -> Dict[str, Any]:
    threads_data = load_threads()
    thread_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    thread = {
        "id": thread_id,
        "title": title,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "messages": [],
    }

    threads_data["threads"][thread_id] = thread

    thread_ids = sorted(threads_data["threads"].keys(), reverse=True)
    if len(thread_ids) > 100:
        for old_id in thread_ids[100:]:
            del threads_data["threads"][old_id]

    save_threads(threads_data)
    return thread


def add_message_to_thread(thread_id: str, role: str, content: str) -> bool:
    threads_data = load_threads()

    if thread_id not in threads_data["threads"]:
        return False

    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
    }

    threads_data["threads"][thread_id]["messages"].append(message)
    threads_data["threads"][thread_id]["updated_at"] = datetime.utcnow().isoformat()

    if role == "user" and len(threads_data["threads"][thread_id]["messages"]) == 1:
        threads_data["threads"][thread_id]["title"] = content[:50] + (
            "..." if len(content) > 50 else ""
        )

    messages = threads_data["threads"][thread_id]["messages"]
    if len(messages) > 50:
        threads_data["threads"][thread_id]["messages"] = messages[-50:]

    save_threads(threads_data)
    return True


async def process_query(
    user_text: str, model_id: Optional[str] = None, thread_id: Optional[str] = None
) -> str:
    """Process a user query using the configured AI model."""
    log_info(f"Processing query: {user_text[:50]}...", source="query")

    config = load_config()

    if model_id:
        model_cfg = get_model_by_id(model_id)
    else:
        model_cfg = get_active_model()

    if not model_cfg:
        log_error("No model configured", source="query")
        return "⚠️ لا يوجد نموذج مُعد. أضف نموذجاً من لوحة التحكم."

    api_key = get_api_key(model_cfg)
    if not api_key:
        src = (
            model_cfg.get("api_key_env", "API_KEY")
            if model_cfg.get("api_key_source") == "env"
            else "القيمة المباشرة"
        )
        log_error(f"API key missing: {src}", source="query")
        return f"⚠️ مفتاح API غير موجود. تحقق من: {src}"

    base_url = model_cfg.get("base_url", "https://api.groq.com/openai/v1")
    model_name = model_cfg.get("model_id", "llama-3.3-70b-versatile")
    system_prompt = config.get("system_prompt", "أنت مساعد ذكي.")
    max_tokens = model_cfg.get("max_tokens", 4096)
    temperature = model_cfg.get("temperature", 0.7)

    enabled_skills = get_enabled_skills()
    web_search_on = "web_search" in enabled_skills
    python_repl_on = "python_repl" in enabled_skills

    log_info(f"Using model: {model_name}", source="query")

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    messages = [{"role": "system", "content": system_prompt}]

    if thread_id:
        threads_data = load_threads()
        if thread_id in threads_data.get("threads", {}):
            for msg in threads_data["threads"][thread_id].get("messages", []):
                messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_text})

    if thread_id:
        add_message_to_thread(thread_id, "user", user_text)

    for iteration in range(10):
        try:
            completion = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["Observation:"],
            )
        except Exception as e:
            error_msg = f"❌ خطأ في الاتصال: {str(e)}"
            log_error(f"API error: {str(e)}", source="query")
            if thread_id:
                add_message_to_thread(thread_id, "assistant", error_msg)
            return error_msg

        response = completion.choices[0].message.content
        input_tokens = completion.usage.prompt_tokens if completion.usage else 0
        output_tokens = completion.usage.completion_tokens if completion.usage else 0

        track_usage(model_cfg.get("id", "unknown"), input_tokens, output_tokens)
        increment_request_count()

        messages.append({"role": "assistant", "content": response})

        if "Action:" in response and "Input:" in response:
            try:
                action_part = response.split("Action:")[1].split("Input:")[0].strip()
                input_part = response.split("Input:")[1].strip()

                log_info(f"Tool call: {action_part}", source="tools")
                result = ""

                if action_part == "web_search" and web_search_on:
                    result = web_search(input_part)
                elif action_part == "python_repl" and python_repl_on:
                    code = (
                        input_part.replace("```python", "").replace("```", "").strip()
                    )
                    result = python_repl(code)
                else:
                    log_warning(f"Tool disabled: {action_part}", source="tools")
                    result = "⚠️ هذه الأداة غير مفعّلة."

                messages.append({"role": "user", "content": f"Observation: {result}"})
            except Exception as e:
                log_error(f"Tool error: {str(e)}", source="tools")
                messages.append(
                    {"role": "user", "content": f"Observation: Error: {str(e)}"}
                )
        else:
            log_info(f"Response generated", source="query")
            if thread_id:
                add_message_to_thread(thread_id, "assistant", response)
            return response

    final_response = (
        messages[-1]["content"] if messages else "⚠️ تم الوصول للحد الأقصى من التكرارات."
    )
    log_warning("Max iterations reached", source="query")
    if thread_id:
        add_message_to_thread(thread_id, "assistant", final_response)
    return final_response


async def process_multimodal(
    text: str, image_data: Optional[str] = None, model_id: Optional[str] = None
) -> str:
    config = load_config()

    if model_id:
        model_cfg = get_model_by_id(model_id)
    else:
        model_cfg = get_active_model()

    if not model_cfg:
        return "⚠️ لا يوجد نموذج مُعد."

    capabilities = model_cfg.get("capabilities", [])
    if "vision" not in capabilities and image_data:
        return "⚠️ النموذج الحالي لا يدعم الصور. استخدم نموذج يدعم Vision."

    api_key = get_api_key(model_cfg)
    if not api_key:
        return "⚠️ مفتاح API غير موجود."

    base_url = model_cfg.get("base_url", "https://api.groq.com/openai/v1")
    model_name = model_cfg.get("model_id", "gemini-2.0-flash")
    system_prompt = config.get("system_prompt", "أنت مساعد ذكي.")
    max_tokens = model_cfg.get("max_tokens", 4096)
    temperature = model_cfg.get("temperature", 0.7)

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    messages = [{"role": "system", "content": system_prompt}]

    user_content = []
    if text:
        user_content.append({"type": "text", "text": text})

    if image_data:
        if image_data.startswith("http"):
            user_content.append({"type": "image_url", "image_url": {"url": image_data}})
        else:
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                }
            )

    messages.append(
        {"role": "user", "content": user_content if len(user_content) > 1 else text}
    )

    try:
        completion = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        input_tokens = completion.usage.prompt_tokens if completion.usage else 0
        output_tokens = completion.usage.completion_tokens if completion.usage else 0
        track_usage(model_cfg.get("id", "unknown"), input_tokens, output_tokens)
        increment_request_count()

        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


async def compare_models(prompt: str, model_ids: List[str]) -> Dict[str, str]:
    results = {}

    tasks = [process_query(prompt, model_id) for model_id in model_ids]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    for model_id, response in zip(model_ids, responses):
        if isinstance(response, Exception):
            results[model_id] = f"Error: {str(response)}"
        else:
            results[model_id] = response

    return results


def get_usage_stats() -> Dict[str, Any]:
    usage = load_usage()
    config = load_config()

    return {
        "total_requests": usage.get("total_requests", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "daily": usage.get("daily", {}),
        "models": usage.get("models", {}),
        "active_model": config.get("active_model_id"),
        "enabled_skills": get_enabled_skills(),
    }


def get_threads_list(limit: int = 20) -> List[Dict[str, Any]]:
    threads_data = load_threads()
    threads = list(threads_data.get("threads", {}).values())
    threads.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return threads[:limit]


def get_thread(thread_id: str) -> Optional[Dict[str, Any]]:
    threads_data = load_threads()
    return threads_data.get("threads", {}).get(thread_id)


def delete_thread(thread_id: str) -> bool:
    threads_data = load_threads()
    if thread_id in threads_data.get("threads", {}):
        del threads_data["threads"][thread_id]
        save_threads(threads_data)
        return True
    return False


def search_threads(query: str) -> List[Dict[str, Any]]:
    threads_data = load_threads()
    results = []
    query_lower = query.lower()

    for thread in threads_data.get("threads", {}).values():
        if query_lower in thread.get("title", "").lower():
            results.append(thread)
            continue

        for msg in thread.get("messages", []):
            if query_lower in msg.get("content", "").lower():
                results.append(thread)
                break

    results.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return results[:20]
