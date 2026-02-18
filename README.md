# 🦞 OpenClaw Fortress

<div align="center">

**Personal AI Assistant - Free Forever - Self-Healing & Auto-Updating**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-green.svg)](https://www.docker.com/)
[![Nuclear](https://img.shields.io/badge/nuclear-powered-red.svg)](https://github.com/openclaw/openclaw)

</div>

---

## ☢️ النظام النووي - يعمل 3 سنين بدون صيانة!

### 🔄 Auto-Update
- فحص تلقائي للتحديثات كل 24 ساعة
- نسخ احتياطي تلقائي قبل التحديث
- تحديث من GitHub مباشرة

### 💊 Self-Healing
- تعافي تلقائي من 6 أنواع أخطاء
- إعادة تشغيل الخدمات المتعطلة
- استعادة الإعدادات التالفة

### 📊 Health Monitor
- مراقبة CPU, Memory, Disk
- إشعارات عند تجاوز 90%
- سجل 1000 قياس

### 🔒 Thread Safety
- جميع core modules مؤمنة بـ threading.Lock
- لا race conditions
- كتابة آمنة للملفات

### 📝 Logging
- سجلات شاملة لكل عملية
- WebSocket streaming للسجلات الحية
- حفظ تلقائي على القرص

---

## 🚀 التشغيل السريع

### HuggingFace Spaces

```bash
# 1. أنشئ Space جديد (Docker SDK)
# 2. ارفع الملفات
# 3. أضف Secrets:
GROQ_API_KEY=gsk_xxx
TELEGRAM_BOT_TOKEN=xxx  # اختياري
# 4. انتظر 30 ثانية!
```

### Docker

```bash
docker build -t openclaw-fortress .
docker run -p 7860:7860 \
  -e GROQ_API_KEY=gsk_xxx \
  -v openclaw-data:/app/data \
  openclaw-fortress
```

### محلياً

```bash
pip install -r requirements.txt
GROQ_API_KEY=gsk_xxx uvicorn app:app --host 0.0.0.0 --port 7860
```

---

## 📁 هيكل المشروع

```
openclaw/
├── app.py                    # FastAPI + Gradio + Nuclear Systems
├── brain.py                  # معالج AI + Skills + Logging
├── config.py                 # إدارة الإعدادات (Thread-Safe)
│
├── api/__init__.py            # 73 API Endpoint
│
├── core/
│   ├── auto_updater.py       # 🔄 Auto-Update System
│   ├── self_healing.py       # 💊 Self-Healing System
│   ├── health_monitor.py     # 📊 Health Monitor
│   ├── mcp_manager.py        # 🔌 MCP Management (Thread-Safe)
│   ├── skills_registry.py    # ⚡ Skills Registry (Thread-Safe)
│   ├── agent_router.py       # 🧠 Multi-Agent (Thread-Safe)
│   ├── scheduler.py          # ⏰ Task Scheduler
│   └── log_stream.py         # 📋 WebSocket Logs
│
├── models/__init__.py         # Pydantic Models (29 class)
├── static/index.html         # Dashboard (12 صفحة)
│
├── data/                     # ملفات البيانات
│   ├── config.json           # الإعدادات
│   ├── usage.json            # إحصائيات الاستخدام
│   ├── health.json           # حالة النظام
│   ├── monitor.json          # مقاييس المراقبة
│   └── ...
│
└── .github/workflows/        # GitHub Actions
    ├── sync_to_hf.yml        # مزامنة تلقائية
    ├── backup.yml            # نسخ احتياطي يومي
    └── keepalive.yml         # منع السكون
```

---

## 📊 الإحصائيات النهائية

| العنصر | العدد |
|--------|-------|
| **إجمالي الملفات** | 34 |
| **ملفات Python** | 14 |
| **سطور الكود** | 4,500+ |
| **API Endpoints** | 73 |
| **Classes** | 43 |
| **Thread-Safe Modules** | 4 |
| **Nuclear Systems** | 8 |

---

## 🛠️ API Endpoints

### Core
```
GET  /api/health              - فحص الصحة
GET  /api/config              - قراءة الإعدادات
POST /api/config              - حفظ الإعدادات
```

### Models
```
GET  /api/models              - قائمة النماذج
POST /api/models              - إضافة نموذج
PUT  /api/models/{id}         - تحديث نموذج
DELETE /api/models/{id}       - حذف نموذج
POST /api/models/{id}/activate - تفعيل نموذج
```

### Nuclear Systems
```
GET  /api/system/nuclear      - حالة كل الأنظمة
GET  /api/system/updates      - حالة التحديثات
POST /api/system/updates/check - فحص التحديثات
GET  /api/system/health       - حالة Self-Healing
POST /api/system/health/check - فحص الصحة
GET  /api/system/metrics      - مقاييس النظام
GET  /api/system/alerts       - التنبيهات
```

---

## 🔑 الحصول على API Keys

### مجاني 🟢

| المزود | الرابط |
|--------|--------|
| Groq | [console.groq.com](https://console.groq.com) |
| Gemini | [aistudio.google.com](https://aistudio.google.com) |
| Cerebras | [cloud.cerebras.ai](https://cloud.cerebras.ai) |
| DeepSeek | [platform.deepseek.com](https://platform.deepseek.com) |

---

## 💰 التكلفة

| الخدمة | التكلفة |
|--------|---------|
| HF Spaces | **$0** |
| Groq API | **$0** |
| Gemini API | **$0** |
| **المجموع** | **$0/شهر** |

---

## ✅ تم تحسينه

| التحسين | الوصف |
|---------|-------|
| Thread Safety | 4 modules مؤمنة بـ Lock |
| Logging | 15+ نقطة تسجيل في brain.py |
| Resource Cleanup | disconnect_all() في log_stream |
| Error Messages | رسائل عربية واضحة |
| Docstrings | توثيق API endpoints |
| Dockerfile | إنشاء جميع ملفات data |

---

## 📜 الترخيص

MIT License - استخدمه بحرية!

---

<div align="center">

**Made with ❤️ by OpenClaw Team**

🦞 **OpenClaw Fortress v2.0 - Nuclear Edition**

</div>
