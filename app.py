import os
import json
import asyncio
import logging
import gradio as gr
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
import uvicorn
from brain import process_query, load_config

# إعدادات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CONFIG_FILE = "config.json"

# --- Webhook ---
fast_app = FastAPI()
@fast_app.post(f"/webhook/{{token}}")
async def telegram_webhook(token: str, request: Request):
    if token != TELEGRAM_TOKEN: return Response(status_code=403)
    try:
        data = await request.json()
        message = data.get("message")
        if message and "text" in message:
            reply = await process_query(message["text"])
            return JSONResponse({"method": "sendMessage", "chat_id": message["chat"]["id"], "text": reply})
    except: pass
    return Response(status_code=200)

@fast_app.get("/")
async def root(): return {"status": "Manager Dashboard Running"}

# --- دوال المانجر (Logic) ---
def get_settings():
    c = load_config()
    return c.get("api_key", ""), c.get("model", "llama3-70b-8192"), c.get("system_prompt", "")

def save_settings(key, model, prompt):
    new_conf = {"api_key": key, "model": model, "system_prompt": prompt}
    with open(CONFIG_FILE, "w") as f:
        json.dump(new_conf, f)
    return "✅ تم حفظ الإعدادات بنجاح! تم تحديث البوت."

# --- واجهة المانجر (UI) ---
with gr.Blocks(title="🦞 OpenClaw Manager", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🦞 OpenClaw Fortress Manager")
    
    with gr.Tabs():
        # التاب 1: الشات
        with gr.TabItem("💬 الشات (Chat)"):
            gr.ChatInterface(fn=lambda m, h: asyncio.run(process_query(m)))
            
        # التاب 2: الإعدادات (زي الفيديو)
        with gr.TabItem("⚙️ الإعدادات (Settings)"):
            gr.Markdown("### 🔧 إعدادات الذكاء (AI Configuration)")
            
            with gr.Row():
                api_key_input = gr.Textbox(label="Groq API Key", type="password", placeholder="gsk_...")
                model_dropdown = gr.Dropdown(
                    label="الموديل (Model)", 
                    choices=["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768", "gemma-7b-it"],
                    value="llama3-70b-8192",
                    allow_custom_value=True
                )
            
            system_prompt_input = gr.Textbox(
                label="شخصية البوت (System Prompt)", 
                value="أنت مساعد ذكي ومفيد.",
                lines=3
            )
            
            save_btn = gr.Button("💾 حفظ وتطبيق (Save)", variant="primary")
            status_output = gr.Textbox(label="الحالة", interactive=False)
            
            # تحميل الإعدادات عند الفتح
            demo.load(get_settings, outputs=[api_key_input, model_dropdown, system_prompt_input])
            # حفظ الإعدادات
            save_btn.click(save_settings, inputs=[api_key_input, model_dropdown, system_prompt_input], outputs=status_output)

app = gr.mount_gradio_app(fast_app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
