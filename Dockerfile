# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --silent

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend
FROM python:3.11-slim-bookworm

LABEL maintainer="OpenClaw Team"
LABEL description="OpenClaw Fortress - Personal AI Assistant - Nuclear Edition"
LABEL version="2.0.0-nuclear"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOME=/app \
    PORT=7860

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY --from=frontend-builder /app/frontend/dist /app/static

RUN mkdir -p /app/data /app/data/backups && \
    echo '{"version":"2.0.0","active_model_id":null,"models":[],"system_prompt":"You are OpenClaw, a helpful AI assistant.","skills":{"web_search":{"enabled":true},"python_repl":{"enabled":true},"vision":{"enabled":false}},"telegram_enabled":false,"telegram_config":{"allowed_users":[],"allowed_groups":[],"require_mention_in_groups":true},"limits":{"max_threads":100,"max_messages_per_thread":50,"usage_history_days":30,"max_log_size_mb":10},"backup":{"enabled":true,"interval_hours":24},"metadata":{"setup_required":true}}' > /app/data/config.json && \
    echo '{"last_updated":null,"total_requests":0,"total_tokens":0,"daily":{},"models":{}}' > /app/data/usage.json && \
    echo '{"threads":{}}' > /app/data/threads.json && \
    echo '{}' > /app/data/mcp.json && \
    echo '{}' > /app/data/skills.json && \
    echo '[]' > /app/data/agents.json && \
    echo '[]' > /app/data/scheduler.json && \
    echo '[]' > /app/data/logs.json && \
    echo '{}' > /app/data/channels.json && \
    echo '[]' > /app/data/telegram_accounts.json && \
    chmod -R 755 /app && \
    chmod -R 777 /app/data

RUN useradd -m -u 1000 openclaw && \
    chown -R openclaw:openclaw /app

USER openclaw

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7860/api/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
