import os
import json
import io
import contextlib
import traceback
from duckduckgo_search import DDGS
from openai import OpenAI
from config import load_config, get_active_model, get_api_key

# --- 1. Python REPL ---
def python_repl(code):
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(code, {'__builtins__': __builtins__}, {})
        result = output.getvalue()
        return result if result else "Done (No Output)"
    except Exception:
        return traceback.format_exc()

# --- 2. Web Search ---
def web_search(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return f"Search Error: {str(e)}"

# --- 3. Main Brain (reads from config.json) ---
async def process_query(user_text: str) -> str:
    config = load_config()
    model_cfg = get_active_model()

    if not model_cfg:
        return "⚠️ لم يتم إعداد أي نموذج. افتح الداشبورد لإضافة نموذج."

    api_key = get_api_key(model_cfg)
    if not api_key:
        src = model_cfg.get('api_key_env', 'UNKNOWN') if model_cfg.get('api_key_source') == 'env' else 'القيمة المباشرة'
        return f"⚠️ مفتاح API غير موجود. تحقق من: {src}"

    base_url = model_cfg.get("base_url") or "https://api.groq.com/openai/v1"
    model_id = model_cfg.get("model_id", "llama3-70b-8192")
    system_prompt = config.get("system_prompt", "أنت مساعد ذكي.")
    max_tokens = model_cfg.get("max_tokens", 1024)
    temperature = model_cfg.get("temperature", 0.7)

    web_search_on = config.get("web_search_enabled", True)
    repl_on = config.get("python_repl_enabled", True)

    client = OpenAI(api_key=api_key, base_url=base_url)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text}
    ]

    for _ in range(5):
        try:
            completion = client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["Observation:"]
            )
        except Exception as e:
            return f"❌ خطأ في الاتصال بالنموذج: {e}"

        response = completion.choices[0].message.content
        messages.append({"role": "assistant", "content": response})

        if "Action:" in response and "Input:" in response:
            try:
                action = response.split("Action:")[1].split("Input:")[0].strip()
                inp = response.split("Input:")[1].strip()
                result = ""
                if action == "python_repl" and repl_on:
                    code = inp.replace("```python", "").replace("```", "").strip()
                    result = python_repl(code)
                elif action == "web_search" and web_search_on:
                    result = web_search(inp)
                else:
                    result = "هذه الأداة معطلة حالياً."
                messages.append({"role": "user", "content": f"Observation: {result}"})
            except Exception as e:
                messages.append({"role": "user", "content": f"Observation: Error: {e}"})
        else:
            return response

    return messages[-1]["content"]
