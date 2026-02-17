import os
import json
import io
import contextlib
import traceback
from duckduckgo_search import DDGS
from groq import Groq

CONFIG_FILE = "config.json"

def load_config():
    """تحميل الإعدادات من ملف JSON"""
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {"api_key": "", "model": "llama3-70b-8192", "system_prompt": "أنت مساعد ذكي."}

def python_repl(code):
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(code, {'__builtins__': __builtins__}, {})
        return output.getvalue()
    except Exception:
        return traceback.format_exc()

def web_search(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return f"Search Error: {str(e)}"

async def process_query(user_text):
    config = load_config()
    api_key = config.get("api_key")
    
    # لو مفيش مفتاح، نبه المستخدم
    if not api_key:
        return "⚠️ **تنبيه:** النظام غير مفعل! اذهب إلى تبويب '⚙️ الإعدادات' بالأعلى، أضف مفتاح Groq API، واضغط حفظ."

    try:
        client = Groq(api_key=api_key)
        
        system_prompt = config.get("system_prompt", "أنت مساعد ذكي.")
        # إضافة تعليمات الأدوات للبرومبت
        full_system_prompt = system_prompt + """
        \nلديك أدوات: python_repl, web_search.
        استخدم الصيغة:
        Action: [tool_name]
        Input: [content]
        """
        
        messages = [{"role": "system", "content": full_system_prompt}, {"role": "user", "content": user_text}]

        for _ in range(5):
            completion = client.chat.completions.create(
                model=config.get("model", "llama3-70b-8192"),
                messages=messages,
                stop=["Observation:"]
            )
            response = completion.choices[0].message.content
            messages.append({"role": "assistant", "content": response})

            if "Action:" in response and "Input:" in response:
                action = response.split("Action:")[1].split("Input:")[0].strip()
                inp = response.split("Input:")[1].strip()
                
                result = ""
                if action == "python_repl":
                    code = inp.replace("```python", "").replace("```", "").strip()
                    result = python_repl(code)
                elif action == "web_search":
                    result = web_search(inp)
                
                messages.append({"role": "user", "content": f"Observation: {result}"})
            else:
                return response
                
        return messages[-1]["content"]

    except Exception as e:
        return f"System Error: {str(e)}"
