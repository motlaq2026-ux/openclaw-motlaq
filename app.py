import os
import asyncio
import logging
import threading
import gradio as gr
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from brain import process_query  # استدعاء المخ الجديد

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
    response = await process_query(user_text)
    
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
    logger.info("🚀 Telegram Bot Started!")
    await app.run_polling()

# --- Web Interface ---
def web_chat(message, history):
    return asyncio.run(process_query(message))

# --- Main Execution ---
def start_services():
    # Start Telegram
    if TELEGRAM_TOKEN:
        t = threading.Thread(target=lambda: asyncio.run(run_telegram_bot()), daemon=True)
        t.start()

    # Start Web
    demo = gr.ChatInterface(
        fn=web_chat,
        title="🦞 OpenClaw Fortress (Nuclear Edition)",
        examples=["لخص لي آخر أخبار الذكاء الاصطناعي", "اشرح لي نظرية النسبية"]
    )
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)

if __name__ == "__main__":
    start_services()
