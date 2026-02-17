import os
import asyncio
import logging
import threading
import gradio as gr
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from brain import process_query

# --- إعداد السجلات ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- Telegram Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🦞 قلعة OpenClaw النووية متصلة وجاهزة! اؤمرني يا بطل.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        response = await process_query(user_text)
        
        if len(response) > 4000:
            for x in range(0, len(response), 4000):
                await update.message.reply_text(response[x:x+4000])
        else:
            await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error handling message: {e}")

# --- نظام التعافي الآلي (The Self-Healing Loop) ---
async def run_telegram_manual():
    if not TELEGRAM_TOKEN:
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN missing!")
        return

    while True:
        try:
            logger.info("📡 Connecting to Telegram (Attempting link)...")
            application = Application.builder().token(TELEGRAM_TOKEN).build()
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

            await application.initialize()
            await application.start()
            await application.updater.start_polling(drop_pending_updates=True)
            
            logger.info("✅ Telegram Bot is LIVE and Connected!")
            
            # الانتظار للأبد ما دام البوت يعمل
            stop_signal = asyncio.Event()
            await stop_signal.wait()
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}. Retrying in 15 seconds...")
            # في حالة الفشل، ننتظر 15 ثانية ونحاول مجدداً (هذا هو الإصلاح التلقائي)
            await asyncio.sleep(15)

# --- Web Interface ---
def web_chat(message, history):
    try:
        return asyncio.run(process_query(message))
    except Exception as e:
        return f"Error: {str(e)}"

# --- Main Service ---
def start_services():
    if TELEGRAM_TOKEN:
        def thread_target():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_telegram_manual())
            loop.close()
            
        t = threading.Thread(target=thread_target, daemon=True)
        t.start()

    # تشغيل واجهة الويب
    demo = gr.ChatInterface(
        fn=web_chat,
        title="🦞 OpenClaw Fortress (Auto-Healing Edition)",
        description="نظام ذكاء اصطناعي نووي بميزات البحث والبرمجة.",
        examples=["أحدث أخبار التكنولوجيا اليوم", "اكتب كود بايثون لتحليل البيانات"]
    )
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)

if __name__ == "__main__":
    start_services()
