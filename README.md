---
title: OpenClaw Fortress
emoji: 🦞
colorFrom: red
colorTo: yellow
sdk: docker
app_file: app_secure.py
pinned: false
license: mit
short_description: Secure AI Assistant Platform - Free Forever
---

# 🦞 OpenClaw Fortress v2.1

**Secure AI Assistant Platform - Free Forever - React Dashboard**

---

## ✨ Features

### 🔐 Security First
- **API Key Authentication** - Secure access control
- **Rate Limiting** - 120 requests/minute protection
- **CORS Protection** - Configured for specific origins
- **Security Headers** - XSS, CSRF protection
- **Input Validation** - Pydantic models throughout
- **Sandboxed Code Execution** - Safe Python execution

### 🖥️ Modern Web Dashboard
- **React + TypeScript** frontend with Tailwind CSS
- **9 pages**: Dashboard, AI Config, MCP, Skills, Channels, Agents, Logs, Testing, Settings
- **Real-time updates** with WebSocket
- **Theme Customization** - 6 color presets
- **Framer Motion** animations
- **Keyboard Shortcuts** (1-9 navigation, R refresh, H home)

### 🤖 AI Provider Support
- **4 official providers**: OpenAI, Anthropic, Groq, Google Gemini
- **Secure API Key Storage** - Keys masked in responses
- **Model Management** - Full CRUD operations
- **Primary Model Selection** - Automatic fallback
- **Connection Testing** - Test provider connectivity

### 💬 Chat System
- **AI Chat** - Process queries with context
- **Web Search** - DuckDuckGo integration
- **Code Execution** - Sandboxed Python execution
- **Usage Tracking** - Request/token statistics

### 📡 Message Channels
- **Telegram** - Multi-account support
- **Discord, Slack** - Webhook support
- **5 Additional Channels** - Feishu, iMessage, WhatsApp, WeChat, DingTalk

### 🔌 MCP Servers
- **Add via Command or URL**
- **Environment Variables** support
- **Test Connectivity**
- **Enable/Disable Servers**

### 🧠 Multi-Agent System
- **Create Custom Agents** - Different personalities
- **Per-Agent Models** - Different AI per agent
- **System Prompts** - Custom instructions
- **Routing Rules** - Route messages to specific agents

### 🛡️ Nuclear Systems
- **Auto-Updater** - Keep up to date
- **Self-Healing** - Automatic recovery
- **Health Monitor** - System monitoring
- **Scheduler** - Task scheduling

---

## 🚀 Quick Start

### HuggingFace Spaces

1. **Create Space** with Docker SDK
2. **Add Secrets** (optional):
   ```
   GROQ_API_KEY=gsk_xxx
   OPENAI_API_KEY=sk-xxx
   ANTHROPIC_API_KEY=sk-ant-xxx
   GEMINI_API_KEY=xxx
   ```
3. **Deploy** - Automatic on push
4. **Get API Key** - Check logs on first run:
   ```
   🔐 Generated admin API key: oc_admin_xxxxx
   ```
5. **Login** - Enter API key in web interface

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/motlaq2026-ux/openclaw-motlaq.git
cd openclaw-motlaq

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run secure backend
python app_secure.py

# 4. In another terminal, run frontend (optional for dev)
cd frontend
npm install
npm run dev

# 5. Access application
# Frontend: http://localhost:5173
# API: http://localhost:7860
```

---

## 🔑 Authentication

On first startup, the server generates an admin API key:

```
🔐 Generated admin API key: oc_admin_xxxxx
Save this key securely - it won't be shown again!
```

**Enter this key in the web interface to access the dashboard.**

The key is stored in:
- **Backend**: `/app/data/auth.json` (hashed)
- **Frontend**: Browser localStorage

---

## 📍 Routes

| Route | Description |
|-------|-------------|
| `/` | React Dashboard (requires auth) |
| `/api/health` | Health check (no auth) |
| `/api` | API info (no auth) |

---

## 🛠️ API Endpoints (50+)

### Authentication
All endpoints require header: `X-API-Key: oc_admin_xxxxx`

### Core Endpoints
```
# Configuration
GET  /api/config                           # Get configuration
POST /api/config                           # Update configuration
GET  /api/config/providers/official        # List provider presets
GET  /api/config/providers/ai-config       # AI config overview

# Providers
POST /api/providers/save                   # Save provider
POST /api/providers/test                   # Test provider
DELETE /api/providers/{name}               # Delete provider
POST /api/providers/primary                # Set primary model

# Models (Full CRUD)
GET    /api/models                         # List models
POST   /api/models                         # Create model
GET    /api/models/{id}                    # Get model
PUT    /api/models/{id}                    # Update model
DELETE /api/models/{id}                    # Delete model
POST   /api/models/{id}/activate           # Activate model
POST   /api/models/{id}/test               # Test model

# Chat
POST /api/chat                             # Chat with AI
POST /api/chat/web-search                  # Web search
POST /api/chat/execute-code                # Execute Python

# Channels
GET  /api/channels                         # List channels
POST /api/channels/{type}                  # Save channel
POST /api/channels/{type}/test             # Test channel
GET  /api/channels/telegram/accounts       # Telegram accounts

# Agents
GET    /api/agents                         # List agents
POST   /api/agents                         # Create agent
PUT    /api/agents/{id}                    # Update agent
DELETE /api/agents/{id}                    # Delete agent

# MCP
GET    /api/mcp                            # List MCP servers
POST   /api/mcp                            # Add MCP
PUT    /api/mcp/{name}                     # Update MCP
DELETE /api/mcp/{name}                     # Delete MCP

# Skills
GET  /api/skills/registry                  # List skills
POST /api/skills/install                   # Install skill
DELETE /api/skills/{id}                    # Uninstall skill

# System
GET  /api/system/status                    # System status
GET  /api/system/usage                     # Usage statistics
GET  /api/system/diagnostics               # Run diagnostics
POST /api/system/service                   # Service control

# Logs
GET  /api/logs                             # Get logs
WS   /api/logs/stream                      # WebSocket logs
DELETE /api/logs                           # Clear logs

# Backup
GET  /api/backup                           # Export backup
POST /api/restore                          # Restore backup
```

---

## 💰 Cost

| Service | Cost |
|---------|------|
| HuggingFace Spaces | **$0** |
| Groq API | **$0** (free tier) |
| Gemini API | **$0** (free tier) |
| Cerebras API | **$0** (free tier) |
| **Total** | **$0/month** |

---

## 🔑 Get API Keys

| Provider | Link | Free Tier |
|----------|------|-----------|
| Groq | [console.groq.com](https://console.groq.com) | ✅ Yes |
| Gemini | [aistudio.google.com](https://aistudio.google.com) | ✅ Yes |
| Cerebras | [cloud.cerebras.ai](https://cloud.cerebras.ai) | ✅ Yes |
| OpenAI | [platform.openai.com](https://platform.openai.com) | Paid |
| Anthropic | [console.anthropic.com](https://console.anthropic.com) | Paid |

---

## 🛡️ Security Features

- **API Key Authentication** - SHA256 hashed storage
- **Rate Limiting** - 120 requests/minute
- **Brute Force Protection** - Lockout after 5 failed attempts
- **CORS Protection** - Specific origins only
- **Security Headers** - X-Content-Type-Options, X-Frame-Options, etc.
- **Input Validation** - All inputs validated with Pydantic
- **Sandboxed Code Execution** - Python runs in isolated subprocess
- **API Key Masking** - Keys never exposed in responses
- **Error Sanitization** - No stack traces in production

---

## 🔧 Configuration

### Environment Variables (Optional)
```bash
# AI Provider API Keys (can also be set via UI)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=...

# Telegram (optional)
TELEGRAM_BOT_TOKEN=...

# HuggingFace
SPACE_ID=your-username/openclaw
```

### Data Directory
All configuration stored in `/app/data/`:
- `config.json` - Main configuration
- `auth.json` - API keys (hashed)
- `channels.json` - Channel settings
- `agents.json` - Agent configurations
- `mcp.json` - MCP server settings
- `skills.json` - Installed skills
- `usage.json` - Usage statistics

---

## 🐛 Troubleshooting

### "API key not configured"
Check server console for the generated key on first startup

### "Rate limit exceeded"
Wait 1 minute, or increase limit in `api/middleware/auth.py`

### "Module not found"
Run `pip install -r requirements.txt`

### "Build failed"
```bash
cd frontend
npm install
npm run build
```

---

## 📚 Documentation

- **API Docs:** Available at `/api` endpoint
- **Project Status:** See `PROJECT_COMPLETE.md`
- **Rewrite Progress:** See `REWRITE_PROGRESS.md`

---

## 🏗️ Architecture

```
OpenClaw Fortress v2.1
│
├── api/                     # REST API
│   ├── middleware/         # Auth & security
│   ├── routes/             # 11 route modules
│   └── routes_legacy.py    # Backup
│
├── core/                   # Core systems
│   └── utils/              # Async I/O, sandbox
│
├── frontend/               # React app
│   └── src/
│       ├── lib/            # API client
│       └── components/     # UI components
│
├── brain_secure.py         # AI processing
├── app_secure.py           # FastAPI app
└── static/                 # Built frontend
```

---

## 📝 License

MIT License - Free for personal and commercial use

---

**Made with ❤️ by OpenClaw Team**

**Version 2.1 - Production Ready 🚀**
