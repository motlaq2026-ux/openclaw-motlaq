import os
import json
import asyncio
from duckduckgo_search import DDGS
from groq import Groq

# --- أدوات البحث ---
def web_search(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return f"Error searching: {str(e)}"

# --- العقل المدبر (Safe Mode) ---
async def process_query(user_text):
    # تحميل المفتاح عند الطلب فقط (عشان التطبيق مايقعش في البداية)
    api_key = os.getenv("GROQ_KEY")
    if not api_key:
        return "⚠️ **خطأ:** مفتاح GROQ_KEY غير موجود! تأكد من إضافته في إعدادات Space Secrets."

    try:
        client = Groq(api_key=api_key)
        
        messages = [
            {
                "role": "system", 
                "content": "أنت OpenClaw، مساعد ذكي باللهجة المصرية. استخدم البحث عند الحاجة."
            },
            {"role": "user", "content": user_text}
        ]
        
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"🦞 حدث خطأ في المعالجة: {str(e)}"
