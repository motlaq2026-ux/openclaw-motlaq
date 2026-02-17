import os
import asyncio
import logging
import gradio as gr
from fastapi import FastAPI, Request, Response
from telegram import Update, User
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import uvicorn
from brain import process_query

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ======== Telegram Handlers ========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🦞 OpenClaw Fortress جاهز!')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action="typing"
        )
        response = await process_query(user_text)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("🦞 حدث خطأ، حاول تاني!")

# ======== Telegram App ========
telegram_app: Application = None

async def build_telegram_app():
    global telegram_app
    if not TELEGRAM_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN غير موجود.")
        return

    # بناء التطبيق بدون updater (بدون polling)
    telegram_app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .updater(None)
        .build()
    )

    # ⚡ الحل الجوهري: نحقن بيانات البوت يدوياً
    # هذا يمنع initialize() من استدعاء getMe() الذي يحتاج اتصال بـ Telegram
    bot_id = int(TELEGRAM_TOKEN.split(":")[0])
    telegram_app.bot._bot = User(
        id=bot_id,
        first_name="OpenClaw",
        is_bot=True,
        username="openclaw_bot",
    )
    logger.info(f"✅ Bot info injected manually (ID: {bot_id}), skipping getMe().")

    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # initialize() الآن لن يستدعي getMe() لأن _bot محدد مسبقاً
    await telegram_app.initialize()
    await telegram_app.start()
    logger.info("✅ Telegram app started successfully (zero outbound calls).")

# ======== FastAPI ========
fast_app = FastAPI()

@fast_app.on_event("startup")
async def on_startup():
    await build_telegram_app()

@fast_app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    """يستقبل التحديثات من Telegram (inbound فقط)"""
    if token != TELEGRAM_TOKEN:
        return Response(status_code=403)
    if telegram_app is None:
        return Response(status_code=503)
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return Response(status_code=200)

@fast_app.get("/health")
async def health():
    space_host = os.getenv("SPACE_HOST", "")
    token_preview = TELEGRAM_TOKEN[:10] + "..." if TELEGRAM_TOKEN else "NOT SET"
    return {
        "status": "ok",
        "telegram_ready": telegram_app is not None,
        "token_preview": token_preview,
        "webhook_url": f"https://{space_host}/webhook/{TELEGRAM_TOKEN}" if space_host else "Set SPACE_HOST env var",
    }

# ======== Gradio ========
def web_chat(message, history):
    return asyncio.run(process_query(message))

gradio_ui = gr.ChatInterface(fn=web_chat, title="🦞 OpenClaw Fortress")
fast_app = gr.mount_gradio_app(fast_app, gradio_ui, path="/")

if __name__ == "__main__":
    uvicorn.run(fast_app, host="0.0.0.0", port=7860)
