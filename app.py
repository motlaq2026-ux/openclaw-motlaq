import os
import asyncio
import logging
import threading
import gradio as gr
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. إعداد السجلات (Logging) ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 2. إعداد المتغيرات (Environment) ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_KEY")
CEREBRAS_KEY = os.getenv("CEREBRAS_KEY")

# --- 3. منطق الذكاء (The Core Brain) ---
# هنا سنضيف لاحقاً استدعاء الـ Skills والـ MCP
async def chat_logic(user_message):
    # محاكاة الرد مؤقتاً للتأكد من عمل النظام
    return f"🦞 OpenClaw Base: استقبلت رسالتك: {user_message}\n(النظام يعمل بنجاح وجاهز للتوسع)"

# --- 4. واجهة تيليجرام (Telegram Bot) ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🦞 أهلاً بك في قلعة OpenClaw! النظام الأساسي يعمل.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    response = await chat_logic(user_text)
    await update.message.reply_text(response)

async def run_telegram_bot():
    if not TELEGRAM_TOKEN:
        logger.warning("⚠️ Telegram Token not found! Bot will not start.")
        return
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🚀 Starting Telegram Bot...")
    await application.run_polling()

# --- 5. واجهة الويب (Gradio Web Interface) ---
def web_chat(message, history):
    # Gradio doesn't support async naturally in simple mode, doing sync wrapper
    return asyncio.run(chat_logic(message))

# --- 6. التشغيل المتوازي (Dual Launch) ---
def start_services():
    # تشغيل تيليجرام في Thread منفصل
    if TELEGRAM_TOKEN:
        telegram_thread = threading.Thread(target=lambda: asyncio.run(run_telegram_bot()))
        telegram_thread.daemon = True
        telegram_thread.start()

    # تشغيل واجهة الويب
    demo = gr.ChatInterface(
        fn=web_chat,
        title="🦞 OpenClaw Fortress (Base)",
        description="Core System Active. Ready for Skill Injection.",
        examples=["System Check", "Ping"]
    )
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)

if __name__ == "__main__":
    start_services()
