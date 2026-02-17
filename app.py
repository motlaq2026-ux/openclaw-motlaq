import os
import asyncio
import logging
import threading
import socket
import gradio as gr
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from brain import process_query

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- دالة اختبار الشبكة ---
def check_dns(hostname="api.telegram.org"):
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.gaierror:
        return False

# --- Telegram Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🦞 القلعة النووية متصلة الآن بالإنترنت العالمي!')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        response = await process_query(user_text)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error: {e}")

# --- نظام التعافي الآلي المطور ---
async def run_telegram_manual():
    if not TELEGRAM_TOKEN: return

    while True:
        # خطوة ذكية: انتظر لغاية ما الـ DNS يشتغل
        logger.info("📡 Checking DNS resolution...")
        if not check_dns():
            logger.warning("⚠️ DNS not ready yet. Sleeping 10s...")
            await asyncio.sleep(10)
            continue
            
        try:
            logger.info("🚀 DNS Ready! Connecting to Telegram...")
            # إعداد التطبيق مع تقليل مهلة الاتصال لزيادة السرعة
            application = Application.builder().token(TELEGRAM_TOKEN).build()
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

            await application.initialize()
            await application.start()
            await application.updater.start_polling(drop_pending_updates=True)
            
            logger.info("✅ SUCCESS! Connected to Telegram API.")
            stop_signal = asyncio.Event()
            await stop_signal.wait()
            
        except Exception as e:
            logger.error(f"❌ Connection error: {e}. Retrying...")
            await asyncio.sleep(20)

# --- Web Interface ---
def web_chat(message, history):
    return asyncio.run(process_query(message))

def start_services():
    if TELEGRAM_TOKEN:
        def thread_target():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_telegram_manual())
            loop.close()
        threading.Thread(target=thread_target, daemon=True).start()

    gr.ChatInterface(fn=web_chat, title="🦞 OpenClaw Fortress").launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    start_services()
