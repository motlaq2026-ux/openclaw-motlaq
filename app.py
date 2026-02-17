#!/usr/bin/env python3
"""
OpenClaw Fortress - Fallback Gradio Interface
Direct AI chat without OpenClaw dependency
"""

import os
import asyncio
import structlog
import gradio as gr
import httpx

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.ConsoleRenderer(colors=True)
    ]
)

logger = structlog.get_logger()

# Keys from environment
CEREBRAS_KEY = os.getenv("CEREBRAS_KEY")
GROQ_KEY = os.getenv("GROQ_KEY")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

SYSTEM_PROMPT = """أنت OpenClaw Fortress - مساعد ذكي متقدم.

قواعدك:
1. تحدث بلغة المستخدم (عربي أو إنجليزي)
2. كن مفيداً وودوداً وموجزاً
3. إذا سُئلت عن شيء لا تعرفه، قل ذلك بصراحة"""


async def get_cerebras(message: str) -> str:
    if not CEREBRAS_KEY:
        return None
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            r = await client.post(
                "https://api.cerebras.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {CEREBRAS_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": message}
                    ]
                }
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("Cerebras error", error=str(e))
    return None


async def get_groq(message: str) -> str:
    if not GROQ_KEY:
        return None
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": message}
                    ]
                }
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("Groq error", error=str(e))
    return None


async def get_ai_response(message: str) -> str:
    # Try Cerebras first (fastest)
    response = await get_cerebras(message)
    if response:
        logger.info("Response from Cerebras")
        return response
    
    # Try Groq
    response = await get_groq(message)
    if response:
        logger.info("Response from Groq")
        return response
    
    return "❌ عذراً، خدمات AI غير متاحة. تأكد من إضافة API keys في Settings."


def chat(message: str, history: list) -> str:
    return asyncio.run(get_ai_response(message))


def main():
    logger.info("🦞 Starting OpenClaw Fortress...")
    
    # Check AI providers
    if not CEREBRAS_KEY and not GROQ_KEY:
        logger.warning("No AI provider configured!")
    
    # Create interface
    demo = gr.ChatInterface(
        chat,
        title="🦞 OpenClaw Fortress",
        description="""### مساعد ذكي مجاني 100%

**الميزات:**
- ✅ Cerebras AI (1M tokens/day)
- ✅ Groq AI (Fast inference)
- ✅ بدون بطاقة ائتمان

🦞 The Lobster Way""",
        examples=[
            "مرحبا! كيف حالك؟",
            "What is artificial intelligence?",
            "ساعدني في كتابة كود Python",
            "اشرح لي الذكاء الاصطناعي",
        ],
    )
    
    logger.info("Starting Gradio interface...")
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)


if __name__ == "__main__":
    main()
