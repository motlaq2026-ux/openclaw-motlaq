import os
import asyncio
import logging
import gradio as gr
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
import uvicorn
from brain import process_query

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# --- FastAPI Webhook (Secure Mode) ---
fast_app = FastAPI()

# ⚠️ التعديل الأمني: استقبال التوكن كمتغير في الرابط
@fast_app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    # 1. التحقق من التوكن (Security Check)
    if token != TELEGRAM_TOKEN:
        logger.warning("⛔ محاولة وصول غير مصرح بها للويب هوك!")
        return Response(status_code=403)

    try:
        data = await request.json()
        message = data.get("message")
        if not message:
            return Response(status_code=200)

        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if text:
            # 2. المعالجة والرد
            reply_text = await process_query(text)
            
            # 3. الرد المباشر (Webhook Reply)
            return JSONResponse({
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": reply_text
            })
            
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Webhook Error: {e}")
        return Response(status_code=200)

@fast_app.get("/")
async def root():
    return {"status": "🦞 OpenClaw Fortress is Secure & Running"}

# --- Gradio Interface ---
def web_chat(message, history):
    return asyncio.run(process_query(message))

gradio_ui = gr.ChatInterface(
    fn=web_chat,
    title="🦞 OpenClaw Fortress",
    examples=["مرحبا", "من أنت؟"]
)

app = gr.mount_gradio_app(fast_app, gradio_ui, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
