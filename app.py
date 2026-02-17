import os
import asyncio
import logging
import json
from pathlib import Path

import gradio as gr
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, HTMLResponse
import uvicorn

from brain import process_query
from config import load_config, save_config

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DASHBOARD_PATH = Path(__file__).parent / "dashboard.html"

fast_app = FastAPI(title="OpenClaw")

@fast_app.get("/admin", response_class=HTMLResponse)
async def dashboard():
    if DASHBOARD_PATH.exists():
        return HTMLResponse(DASHBOARD_PATH.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>dashboard.html not found</h1>", status_code=404)

@fast_app.get("/api/config")
async def get_config():
    return JSONResponse(load_config())

@fast_app.post("/api/config")
async def post_config(request: Request):
    try:
        data = await request.json()
        if save_config(data):
            return JSONResponse({"ok": True})
        return JSONResponse({"ok": False}, status_code=500)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)

@fast_app.post("/api/test-ai")
async def test_ai(request: Request):
    try:
        data = await request.json()
        msg = data.get("message", "مرحبا")
        response = await process_query(msg)
        return JSONResponse({"response": response})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@fast_app.get("/health")
async def health():
    cfg = load_config()
    active = next((m for m in cfg.get("models", []) if m["id"] == cfg.get("active_model_id")), None)
    return JSONResponse({
        "status": "ok",
        "active_model": active.get("name") if active else None,
        "telegram_enabled": cfg.get("telegram_enabled", True),
    })

@fast_app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    if not TELEGRAM_TOKEN or token != TELEGRAM_TOKEN:
        return Response(status_code=403)
    cfg = load_config()
    if not cfg.get("telegram_enabled", True):
        return Response(status_code=200)
    try:
        data = await request.json()
        message = data.get("message") or data.get("edited_message")
        if not message:
            return Response(status_code=200)
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        if not text:
            return Response(status_code=200)
        if text.startswith("/start"):
            reply = "🦞 مرحباً! أنا OpenClaw جاهز لمساعدتك."
        elif text.startswith("/"):
            reply = "🦞 أمر غير معروف."
        else:
            reply = await process_query(text)
        return JSONResponse({"method": "sendMessage", "chat_id": chat_id, "text": reply})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return Response(status_code=200)

def web_chat(message, history):
    return asyncio.run(process_query(message))

gradio_ui = gr.ChatInterface(fn=web_chat, title="🦞 OpenClaw Fortress", examples=["مرحبا", "من أنت؟"])
app = gr.mount_gradio_app(fast_app, gradio_ui, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
