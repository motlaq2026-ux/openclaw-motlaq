import os
import asyncio
import logging
import gradio as gr
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import uvicorn
from brain import process_query

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ======== Telegram Handlers ========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🦞 OpenClaw Fortress جاهز!')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        response = await process_query(user_text)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("🦞 حدث خطأ، حاول تاني!")

# ======== Telegram App (بدون أي اتصال خارجي) ========
telegram_app: Application = None

async def build_telegram_app():
    global telegram_app
    if not TELEGRAM_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN غير موجود.")
        return

    # updater=None مهم جداً → يمنع أي اتصال صادر لـ Telegram
    telegram_app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .updater(None)
        .build()
    )
    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    await telegram_app.initialize()
    await telegram_app.start()
    logger.info("Telegram app ready (webhook mode, no outbound calls).")

# ======== FastAPI ========
fast_app = FastAPI()

@fast_app.on_event("startup")
async def on_startup():
    await build_telegram_app()

@fast_app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    if token != TELEGRAM_TOKEN:
        return Response(status_code=403)
    if telegram_app is None:
        return Response(status_code=500)
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return Response(status_code=200)

@fast_app.get("/health")
async def health():
    return {"status": "ok"}

# ======== Gradio ========
def web_chat(message, history):
    return asyncio.run(process_query(message))

gradio_ui = gr.ChatInterface(fn=web_chat, title="🦞 OpenClaw Fortress")
fast_app = gr.mount_gradio_app(fast_app, gradio_ui, path="/")

if __name__ == "__main__":
    uvicorn.run(fast_app, host="0.0.0.0", port=7860)
