---
title: OpenClaw Fortress
emoji: 🦞
colorFrom: red
colorTo: yellow
sdk: docker
app_file: app.py
pinned: false
license: mit
short_description: Personal AI Assistant - Free Forever - Web Dashboard
---

# 🦞 OpenClaw Fortress

**Personal AI Assistant - Free Forever - React Dashboard**

---

## ✨ Features

### 🖥️ Modern Web Dashboard
- **React + TypeScript** frontend with Tailwind CSS
- **8 pages**: Dashboard, AI Config, MCP, Skills, Channels, Agents, Logs, Settings
- **Real-time updates** with Zustand state management
- **Dark theme** optimized

### 🤖 AI Provider Support
- **12+ providers**: Anthropic, OpenAI, Google Gemini, Groq, Cerebras, DeepSeek, Moonshot, Qwen, OpenRouter, Ollama
- **One-click setup** for each provider
- **Model management** with primary model selection

### 📡 Message Channels
- **Telegram** with multi-account support
- **Discord**, **Slack** support
- **User allowlist** management

### 🔌 MCP Servers
- Add MCP servers via command or URL
- Enable/disable servers
- Test connectivity

### 🧠 Multi-Agent System
- Create agents with custom personalities
- Set different models per agent
- System prompts per agent

---

## 🚀 Quick Start

### HuggingFace Spaces
Add these secrets:
```
GROQ_API_KEY=gsk_xxx
TELEGRAM_BOT_TOKEN=xxx (optional)
```

### Local Development
```bash
# Backend
pip install -r requirements.txt
GROQ_API_KEY=gsk_xxx uvicorn app:app --host 0.0.0.0 --port 7860

# Frontend (development)
cd frontend && npm install && npm run dev
```

---

## 📍 Routes

| Route | Description |
|-------|-------------|
| `/` | Landing page |
| `/admin` | React Dashboard |
| `/gradio` | Chat interface |
| `/api/docs` | API documentation |

---

## 🛠️ API Endpoints

- **GET /api/providers/official** - List official providers
- **GET /api/providers/ai-config** - Get AI configuration
- **POST /api/providers/save** - Save provider
- **DELETE /api/providers/{name}** - Delete provider
- **POST /api/providers/primary** - Set primary model
- **GET /api/channels** - List channels
- **POST /api/channels/{type}** - Save channel config
- **GET /api/channels/telegram/accounts** - List Telegram accounts
- **GET /api/mcp** - List MCP servers
- **GET /api/agents** - List agents
- **GET /api/logs** - Get logs
- ...and more

---

## 💰 Cost

| Service | Cost |
|---------|------|
| HF Spaces | **$0** |
| Groq API | **$0** |
| Gemini API | **$0** |
| **Total** | **$0/month** |

---

## 🔑 Get API Keys

| Provider | Link |
|----------|------|
| Groq | [console.groq.com](https://console.groq.com) |
| Gemini | [aistudio.google.com](https://aistudio.google.com) |
| Cerebras | [cloud.cerebras.ai](https://cloud.cerebras.ai) |
| OpenAI | [platform.openai.com](https://platform.openai.com) |
| Anthropic | [console.anthropic.com](https://console.anthropic.com) |

---

**Made with ❤️ by OpenClaw Team**
