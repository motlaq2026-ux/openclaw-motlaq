import os
import json
import asyncio
import io
import sys
import contextlib
import traceback
from duckduckgo_search import DDGS
from groq import Groq

# --- 1. أداة تشغيل الكود (Python REPL) ---
def python_repl(code):
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(code, {'__builtins__': __builtins__}, {})
        return output.getvalue()
    except Exception:
        return traceback.format_exc()

# --- 2. أداة البحث ---
def web_search(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return f"Search Error: {str(e)}"

# --- 3. العقل المدبر (ReAct Agent) ---
SYSTEM_PROMPT = """
أنت OpenClaw (نسخة المبرمج 🦞).
لديك أداة 'python_repl' لتنفيذ كود بايثون، وأداة 'web_search' للبحث.
- للحسابات أو تحليل البيانات: اكتب كود بايثون.
- للمعلومات الحديثة: ابحث في الويب.
- الصيغة المطلوبة لاستخدام أداة:
Action: [python_repl أو web_search]
Input: [الكود أو البحث]
"""

async def process_query(user_text):
    api_key = os.getenv("GROQ_KEY")
    if not api_key: return "⚠️ GROQ_KEY missing"

    client = Groq(api_key=api_key)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_text}]

    for _ in range(5): # محاولات التفكير
        try:
            completion = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages,
                stop=["Observation:"]
            )
        except Exception as e:
            return f"Error: {e}"

        response = completion.choices[0].message.content
        messages.append({"role": "assistant", "content": response})

        if "Action:" in response and "Input:" in response:
            try:
                action = response.split("Action:")[1].split("Input:")[0].strip()
                inp = response.split("Input:")[1].strip()
                
                result = ""
                if action == "python_repl":
                    code = inp.replace("```python", "").replace("```", "").strip()
                    result = python_repl(code)
                    if not result: result = "Done (No Output)"
                elif action == "web_search":
                    result = web_search(inp)
                
                messages.append({"role": "user", "content": f"Observation: {result}"})
            except Exception as e:
                messages.append({"role": "user", "content": f"Observation: Error: {e}"})
        else:
            return response

    return messages[-1]["content"]
