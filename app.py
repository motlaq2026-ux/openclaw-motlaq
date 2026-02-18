import os
import logging
import asyncio
from datetime import datetime
from pathlib import Path

import gradio as gr
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from config import load_config, save_config
from brain import process_query
from api import router as api_router
from core.log_stream import log_stream
from core.scheduler import scheduler
from core.auto_updater import auto_updater
from core.self_healing import self_healing
from core.health_monitor import health_monitor

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DASHBOARD_PATH = Path(__file__).parent / "static" / "index.html"

START_TIME = datetime.utcnow()

app = FastAPI(
    title="OpenClaw Fortress",
    description="🦞 Personal AI Assistant - Free Forever - Self-Healing & Auto-Updating",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def setup_health_checks():
    async def check_api_key():
        from config import get_active_model, get_api_key

        model = get_active_model()
        if model:
            api_key = get_api_key(model)
            return {"has_api_key": bool(api_key)}
        return {"has_api_key": False}

    async def check_data_dir():
        data_dir = Path("/app/data")
        return {
            "exists": data_dir.exists(),
            "writable": os.access(str(data_dir), os.W_OK)
            if data_dir.exists()
            else False,
        }

    async def check_config():
        from config import load_config

        config = load_config()
        return {
            "has_models": len(config.get("models", [])) > 0,
            "has_active_model": bool(config.get("active_model_id")),
        }

    self_healing.register_health_check("api_key", check_api_key)
    self_healing.register_health_check("data_dir", check_data_dir)
    self_healing.register_health_check("config", check_config)


def setup_recovery_handlers():
    def recover_api_connection(error):
        logger.info("Attempting API connection recovery...")

    def recover_config(error):
        logger.info("Attempting config recovery...")
        from config import load_config

        load_config()

    self_healing.register_recovery_handler("api_connection", recover_api_connection)
    self_healing.register_recovery_handler("config_corruption", recover_config)


def setup_alert_handlers():
    async def handle_health_alert(alert):
        log_stream.warning(
            f"Health alert: {alert['type']} = {alert['value']:.1f}%", source="monitor"
        )

    health_monitor.register_alert_handler(handle_health_alert)


@app.on_event("startup")
async def startup_event():
    log_stream.info("🦞 OpenClaw Fortress starting...", source="system")

    setup_health_checks()
    setup_recovery_handlers()
    setup_alert_handlers()

    scheduler.start()
    log_stream.info("✅ Scheduler started", source="system")

    self_healing.start()
    log_stream.info("✅ Self-healing started", source="system")

    health_monitor.start()
    log_stream.info("✅ Health monitor started", source="system")

    auto_updater.start()
    log_stream.info("✅ Auto-updater started", source="system")

    log_stream.info("🚀 OpenClaw Fortress ready!", source="system")


@app.on_event("shutdown")
async def shutdown_event():
    log_stream.info("🛑 OpenClaw Fortress stopping...", source="system")

    auto_updater.stop()
    health_monitor.stop()
    self_healing.stop()
    scheduler.stop()

    log_stream.info("👋 OpenClaw Fortress stopped", source="system")


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🦞 OpenClaw Fortress</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { background: #0a0a0b; color: #e6edf3; font-family: system-ui, -apple-system, sans-serif; }
            .gradient { background: linear-gradient(135deg, #f94d3a 0%, #a78bfa 100%); }
            .glow { box-shadow: 0 0 30px rgba(249, 77, 58, 0.3); }
        </style>
    </head>
    <body class="min-h-screen flex items-center justify-center">
        <div class="text-center p-8">
            <div class="text-8xl mb-6">🦞</div>
            <h1 class="text-4xl font-bold mb-4 gradient bg-clip-text text-transparent">OpenClaw Fortress</h1>
            <p class="text-xl text-gray-400 mb-2">Your Personal AI Assistant - Free Forever</p>
            <p class="text-sm text-green-400 mb-8">✨ Self-Healing • Auto-Updating • 24/7 Monitoring</p>
            <div class="flex gap-4 justify-center flex-wrap">
                <a href="/admin" class="px-6 py-3 bg-gradient-to-r from-red-500 to-orange-500 rounded-lg font-semibold hover:opacity-90 transition">
                    📊 Dashboard
                </a>
                <a href="/gradio" class="px-6 py-3 bg-gray-800 rounded-lg font-semibold hover:bg-gray-700 transition">
                    💬 Chat
                </a>
            </div>
            <div class="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div class="p-4 bg-gray-900 rounded-lg">
                    <div class="text-2xl font-bold text-green-400">✓</div>
                    <div class="text-sm text-gray-400">Free Forever</div>
                </div>
                <div class="p-4 bg-gray-900 rounded-lg">
                    <div class="text-2xl font-bold text-blue-400">14+</div>
                    <div class="text-sm text-gray-400">AI Providers</div>
                </div>
                <div class="p-4 bg-gray-900 rounded-lg">
                    <div class="text-2xl font-bold text-purple-400">∞</div>
                    <div class="text-sm text-gray-400">Auto-Update</div>
                </div>
                <div class="p-4 bg-gray-900 rounded-lg">
                    <div class="text-2xl font-bold text-orange-400">$0</div>
                    <div class="text-sm text-gray-400">Cost/Month</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/admin", response_class=HTMLResponse)
async def dashboard():
    if DASHBOARD_PATH.exists():
        return HTMLResponse(DASHBOARD_PATH.read_text(encoding="utf-8"))
    return HTMLResponse(
        "<h1>Dashboard not found. Build the frontend first.</h1>", status_code=404
    )


@app.get("/chat")
async def chat_redirect():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="0;url=/gradio">
    </head>
    <body>
        <p>Redirecting to chat...</p>
    </body>
    </html>
    """)


@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    if not TELEGRAM_TOKEN or token != TELEGRAM_TOKEN:
        return Response(status_code=403)

    cfg = load_config()
    if not cfg.get("telegram_enabled", True):
        return Response(status_code=200)

    try:
        data = await request.json()
        message = data.get("message") or data.get("edited_message")

        if not message:
            return Response(status_code=200)

        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        user_id = str(message.get("from", {}).get("id", ""))

        if not text:
            return Response(status_code=200)

        allowed_users = cfg.get("telegram_config", {}).get("allowed_users", [])
        if allowed_users and user_id not in [str(u) for u in allowed_users]:
            return JSONResponse(
                {
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "⛔ غير مصرح لك باستخدام هذا البوت.",
                }
            )

        if text.startswith("/start"):
            reply = "🦞 مرحباً! أنا OpenClaw Fortress، مساعدك الذكي.\n\nاسألني أي شيء!"
        elif text.startswith("/help"):
            reply = """🦞 **OpenClaw Fortress**

الأوامر المتاحة:
/start - بدء المحادثة
/help - المساعدة
/status - حالة النظام

يمكنك سؤالي أي شيء وسأساعدك!"""
        elif text.startswith("/status"):
            active_model = cfg.get("active_model_id", "غير محدد")
            health = health_monitor.get_status()
            reply = f"🦞 **حالة OpenClaw**\n\n🤖 النموذج: {active_model}\n⚡ المهارات: {', '.join(cfg.get('skills', {}).keys())}\n⏱️ Uptime: {int(health.get('uptime_seconds', 0))}s\n✅ يعمل بشكل طبيعي"
        elif text.startswith("/"):
            reply = "🦞 أمر غير معروف. جرب /help للمساعدة."
        else:
            try:
                reply = await process_query(text)
            except Exception as e:
                self_healing.record_error(
                    "model_error", str(e), {"text": text[:100]}, e
                )
                reply = "❌ حدث خطأ. جرب مرة أخرى."

        return JSONResponse(
            {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": reply,
                "parse_mode": "Markdown",
            }
        )
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        self_healing.record_error("webhook_error", str(e), exception=e)
        return Response(status_code=200)


def web_chat(message, history):
    import asyncio

    try:
        return asyncio.run(process_query(message))
    except Exception as e:
        self_healing.record_error("chat_error", str(e), exception=e)
        return f"❌ خطأ: {str(e)}"


with gr.Blocks(
    title="🦞 OpenClaw Chat",
    theme=gr.themes.Base(
        primary_hue="red", secondary_hue="orange", neutral_hue="slate"
    ),
    css="""
    .gradio-container { background: #0a0a0b !important; }
    .message { font-family: system-ui !important; }
    """,
) as chat_interface:
    gr.Markdown("""
    # 🦞 OpenClaw Fortress Chat
    
    مساعدك الذكي الشخصي - مجاني للأبد
    
    | 🤖 نماذج مجانية | ⚡ أدوات ذكية | 💬 محادثات غير محدودة |
    |---|---|---|
    
    ---
    """)

    gr.ChatInterface(
        fn=web_chat,
        examples=[
            "مرحباً! من أنت؟",
            "ما هو OpenClaw؟",
            "ساعدني في كتابة كود Python",
            "ابحث عن أحدث أخبار الذكاء الاصطناعي",
        ],
        cache_examples=False,
    )

    gr.Markdown("""
    ---
    
    💡 **نصائح:**
    - استخدم **Groq** للسرعة القصوى (مجاني)
    - استخدم **Gemini** لدعم الصور (مجاني)
    - 📊 [Dashboard](/admin) للإدارة المتقدمة
    
    🦞 OpenClaw Fortress v2.0 | [GitHub](https://github.com/openclaw/openclaw)
    """)


app = gr.mount_gradio_app(app, chat_interface, path="/gradio")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
