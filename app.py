import os
import asyncio
import logging
import threading
import gradio as gr
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from brain import process_query

# --- Setup ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- Telegram Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🦞 جاهز يا باشا! أنا OpenClaw النسخة النووية. اسألني في أي حاجة.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    # إظهار مؤشر الكتابة
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # المعالجة عبر المخ
    try:
        response = await process_query(user_text)
    except Exception as e:
        response = f"حدث خطأ داخلي: {str(e)}"
    
    # الرد (تقسيم الرسالة لو طويلة)
    if len(response) > 4000:
        for x in range(0, len(response), 4000):
            await update.message.reply_text(response[x:x+4000])
    else:
        await update.message.reply_text(response)

# --- Manual Telegram Runner (The Fix) ---
async def run_telegram_manual():
    """تشغيل البوت يدوياً لتجنب مشاكل الـ Loop"""
    if not TELEGRAM_TOKEN:
        logger.warning("⚠️ No Telegram Token found!")
        return

    # 1. بناء التطبيق
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 2. التهيئة والتشغيل اليدوي
    logger.info("🚀 Starting Telegram Bot (Manual Mode)...")
    await application.initialize()
    await application.start()
    
    # 3. بدء استقبال التحديثات (Polling)
    # نستخدم updater الموجود داخل التطبيق
    await application.updater.start_polling(drop_pending_updates=True)
    
    # 4. إبقاء البوت حياً للأبد
    # نستخدم Event لنجعل هذا التابع ينتظر إلى ما لا نهاية ولا يغلق
    stop_signal = asyncio.Event()
    await stop_signal.wait()  # سيبقى هنا للأبد

# --- Web Interface ---
def web_chat(message, history):
    return asyncio.run(process_query(message))

# --- Main Execution ---
def start_services():
    # Start Telegram in Background Thread
    if TELEGRAM_TOKEN:
        def thread_target():
            # إنشاء Loop جديد خاص بهذا الـ Thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # تشغيل البوت بالطريقة اليدوية
            loop.run_until_complete(run_telegram_manual())
            loop.close()
            
        t = threading.Thread(target=thread_target, daemon=True)
        t.start()

    # Start Web Interface (Main Thread)
    demo = gr.ChatInterface(
        fn=web_chat,
        title="🦞 OpenClaw Fortress (Nuclear Edition)",
        examples=["لخص لي آخر أخبار الذكاء الاصطناعي", "اشرح لي نظرية النسبية"]
    )
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)

if __name__ == "__main__":
    start_services()
