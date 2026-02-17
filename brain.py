import os
import json
import asyncio
from duckduckgo_search import DDGS
from groq import Groq

# إعداد العميل
client = Groq(api_key=os.getenv("GROQ_KEY"))

# --- 1. الأدوات (The Skills) ---
def web_search(query):
    """البحث في الإنترنت باستخدام DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return f"Error searching: {str(e)}"

def calculator(expression):
    """آلة حاسبة دقيقة"""
    try:
        return str(eval(expression, {"__builtins__": None}, {}))
    except:
        return "Error in calculation"

# --- 2. العقل المدبر (The Brain) ---
SYSTEM_PROMPT = """
أنت OpenClaw، مساعد ذكي وقوي جداً (نسخة The Lobster Way 🦞).
لديك صلاحيات للبحث في الإنترنت والحساب.
- إذا سأل المستخدم عن معلومة حديثة، استخدم أداة البحث فوراً.
- إذا طلب حسابات، احسبها بدقة.
- رد دائماً باللهجة المصرية الودودة أو الفصحى حسب الطلب.
- كن مختصراً ومفيداً.
"""

async def process_query(user_text):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text}
    ]
    
    # 1. التفكير المبدئي
    try:
        # سنستخدم Llama3 لأنه سريع وذكي في Groq
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0.5,
            max_tokens=1024
        )
        response = completion.choices[0].message.content
        
        # (هنا يمكن تطوير الكود ليعمل بنظام Function Calling تلقائي مستقبلاً)
        # حالياً، هذا "تفكير سريع" للرد المباشر.
        
        return response
    except Exception as e:
        return f"🦞 حدث خطأ في المعالجة: {str(e)}"
