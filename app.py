import os
import asyncio
import logging
import threading
import httpx
import gradio as gr
from fastapi import FastAPI, Request, Response
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import uvicorn
from brain import process_query

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# HuggingFace توفر المتغير ده تلقائياً → مثال: username-spacename.hf.space
SPACE_HOST = os.getenv("SPACE_HOST", "")
WEBHOOK_URL = f"https://{SPACE_HOST}/webhook/{TELEGRAM_TOKEN}" if SPACE_HOST else ""

# ======== Telegram Handlers ========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🦞 القلعة متصلة عبر Webhook!')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        response = await process_query(user_text)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("🦞 حدث خطأ، حاول تاني!")

# ======== إعداد التطبيق ========
telegram_app: Application = None

async def build_telegram_app():
    global telegram_app
    if not TELEGRAM_TOKEN:
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN غير موجود، البوت معطل.")
        return

    telegram_app = Application.builder().token(TELEGRAM_TOKEN).updater(None).build()
    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await telegram_app.initialize()
    await telegram_app.start()
    logger.info("✅ Telegram Application initialized.")

# ======== FastAPI ========
fast_app = FastAPI()

@fast_app.on_event("startup")
async def on_startup():
    await build_telegram_app()

    if TELEGRAM_TOKEN and WEBHOOK_URL:
        try:
            bot = Bot(token=TELEGRAM_TOKEN)
            await bot.delete_webhook(drop_pending_updates=True)
            result = await bot.set_webhook(url=WEBHOOK_URL)
            if result:
                logger.info(f"✅ Webhook set: {WEBHOOK_URL}")
            else:
                logger.error("❌ فشل تسجيل الـ Webhook.")
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل الـ Webhook: {e}")
    else:
        logger.warning("⚠️ SPACE_HOST غير موجود، الـ Webhook لن يُسجَّل.")

@fast_app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    if token != TELEGRAM_TOKEN:
        return Response(status_code=403)
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
    return Response(status_code=200)

@fast_app.get("/health")
async def health():
    return {"status": "ok", "webhook": WEBHOOK_URL or "not configured"}

# ======== Gradio ========
def web_chat(message, history):
    return asyncio.run(process_query(message))

gradio_ui = gr.ChatInterface(fn=web_chat, title="🦞 OpenClaw Fortress")
fast_app = gr.mount_gradio_app(fast_app, gradio_ui, path="/")

# ======== Entry Point ========
if __name__ == "__main__":
    uvicorn.run(fast_app, host="0.0.0.0", port=7860)
