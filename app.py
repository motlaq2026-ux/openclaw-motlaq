#!/usr/bin/env python3
"""
OpenClaw Fortress - Main Entry
Installs and runs OpenClaw automatically
"""

import os
import sys
import subprocess
import asyncio
import threading
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.ConsoleRenderer(colors=True)
    ]
)

logger = structlog.get_logger()


def ensure_openclaw_installed():
    """Ensure OpenClaw is installed and updated"""
    try:
        import openclaw
        logger.info("OpenClaw already installed")
    except ImportError:
        logger.info("Installing OpenClaw...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openclaw"])
        logger.info("OpenClaw installed")


def check_environment():
    """Check required secrets"""
    missing = []
    if not os.getenv("CEREBRAS_KEY") and not os.getenv("GROQ_KEY") and not os.getenv("DEEPSEEK_KEY"):
        missing.append("AI Provider (CEREBRAS_KEY, GROQ_KEY, or DEEPSEEK_KEY)")
    
    if missing:
        logger.warning("Missing environment", missing=missing)


def main():
    logger.info("🦞 Starting OpenClaw Fortress...")
    
    # Ensure OpenClaw is installed
    ensure_openclaw_installed()
    
    # Check environment
    check_environment()
    
    # Start OpenClaw Gateway
    logger.info("Starting OpenClaw Gateway...")
    
    os.environ["OPENCLAW_HOST"] = "0.0.0.0"
    os.environ["OPENCLAW_PORT"] = "7860"
    
    try:
        subprocess.run([
            sys.executable, "-m", "openclaw", 
            "gateway", "start", 
            "--host", "0.0.0.0", 
            "--port", "7860"
        ])
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error("Error starting OpenClaw", error=str(e))
        # Fallback: start simple gradio interface
        start_fallback_interface()


def start_fallback_interface():
    """Fallback Gradio interface if OpenClaw fails"""
    import gradio as gr
    import httpx
    
    async def get_ai_response(message: str) -> str:
        # Try Cerebras first
        cerebras_key = os.getenv("CEREBRAS_KEY")
        if cerebras_key:
            async with httpx.AsyncClient(timeout=60.0) as client:
                try:
                    r = await client.post(
                        "https://api.cerebras.ai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {cerebras_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "llama-3.3-70b",
                            "messages": [
                                {"role": "system", "content": "أنت مساعد ذكي. تحدث بلغة المستخدم."},
                                {"role": "user", "content": message}
                            ]
                        }
                    )
                    if r.status_code == 200:
                        return r.json()["choices"][0]["message"]["content"]
                except Exception as e:
                    logger.error("Cerebras error", error=str(e))
        
        # Try Groq
        groq_key = os.getenv("GROQ_KEY")
        if groq_key:
            async with httpx.AsyncClient(timeout=60.0) as client:
                try:
                    r = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {groq_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "llama-3.1-8b-instant",
                            "messages": [
                                {"role": "system", "content": "أنت مساعد ذكي. تحدث بلغة المستخدم."},
                                {"role": "user", "content": message}
                            ]
                        }
                    )
                    if r.status_code == 200:
                        return r.json()["choices"][0]["message"]["content"]
                except Exception as e:
                    logger.error("Groq error", error=str(e))
        
        return "❌ عذراً، خدمات AI غير متاحة حالياً."
    
    def chat(message, history):
        return asyncio.run(get_ai_response(message))
    
    demo = gr.ChatInterface(
        chat,
        title="🦞 OpenClaw Fortress",
        description="### مساعد ذكي مجاني 100%\n\n🦞 The Lobster Way",
    )
    
    logger.info("Starting fallback Gradio interface...")
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)


if __name__ == "__main__":
    main()
