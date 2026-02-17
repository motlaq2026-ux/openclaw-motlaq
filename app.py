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

# --- Telegram Bot ---
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

async def run_telegram_bot():
    if not TELEGRAM_TOKEN:
        logger.warning("⚠️ No Telegram Token found!")
        return
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🚀 Starting Telegram Bot (Background Mode)...")
    
    # 🔥 هنا الحل السحري: stop_signals=None
    # هذا يمنع البوت من محاولة السيطرة على الـ Signals في الخلفية
    await app.run_polling(stop_signals=None, drop_pending_updates=True)

# --- Web Interface ---
def web_chat(message, history):
    return asyncio.run(process_query(message))

# --- Main Execution ---
def start_services():
    # Start Telegram in Background Thread
    if TELEGRAM_TOKEN:
        # نستخدم Loop جديد خاص بالـ Thread
        def run_async_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_telegram_bot())
            loop.close()

        t = threading.Thread(target=run_async_in_thread, daemon=True)
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
