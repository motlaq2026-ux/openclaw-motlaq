import os
import asyncio
import logging
import gradio as gr
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
import uvicorn
from brain import process_query

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ======== FastAPI ========
fast_app = FastAPI()

@fast_app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    """
    الحل الذكي: Webhook Reply
    بدل ما نتصل بـ Telegram API لإرسال الرد (اتصال صادر = محجوب)،
    نرد على الـ webhook request نفسه بـ JSON.
    Telegram بيستلم ردنا ويوصله للمستخدم تلقائياً.
    النتيجة: صفر اتصالات صادرة لـ api.telegram.org
    """
    if token != TELEGRAM_TOKEN:
        return Response(status_code=403)

    try:
        data = await request.json()
        logger.info(f"Received update: {data.get('update_id')}")

        message = data.get("message") or data.get("edited_message")
        if not message:
            return Response(status_code=200)

        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if not text:
            return Response(status_code=200)

        # معالجة الأوامر
        if text.startswith("/start"):
            reply_text = "🦞 OpenClaw Fortress جاهز! اكتب أي سؤال."
        elif text.startswith("/"):
            reply_text = "🦞 أمر غير معروف."
        else:
            reply_text = await process_query(text)

        # ✅ الرد عبر Webhook Reply (لا يوجد اتصال صادر)
        return JSONResponse({
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": reply_text,
            "parse_mode": "Markdown"
        })

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return Response(status_code=200)  # دائماً 200 لـ Telegram

@fast_app.get("/health")
async def health():
    space_host = os.getenv("SPACE_HOST", "")
    return {
        "status": "ok",
        "outbound_calls": "ZERO - using webhook reply",
        "webhook_url": f"https://{space_host}/webhook/{TELEGRAM_TOKEN}" if space_host else "set SPACE_HOST"
    }

# ======== Gradio ========
def web_chat(message, history):
    return asyncio.run(process_query(message))

gradio_ui = gr.ChatInterface(fn=web_chat, title="🦞 OpenClaw Fortress")
fast_app = gr.mount_gradio_app(fast_app, gradio_ui, path="/")

if __name__ == "__main__":
    uvicorn.run(fast_app, host="0.0.0.0", port=7860)
