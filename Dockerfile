FROM python:3.11-slim-bookworm

LABEL maintainer="OpenClaw Team"
LABEL description="OpenClaw Fortress - Personal AI Assistant - Nuclear Edition"
LABEL version="2.0.0-nuclear"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOME=/app \
    PORT=7860

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory and all default files
RUN mkdir -p /app/data /app/data/backups && \
    echo '{"version":"2.0.0","active_model_id":"groq-llama-70b","models":[{"id":"groq-llama-70b","name":"Llama 3.3 70B","provider":"groq","model_id":"llama-3.3-70b-versatile","api_key_source":"env","api_key_env":"GROQ_API_KEY","api_key_value":"","base_url":"https://api.groq.com/openai/v1","max_tokens":4096,"temperature":0.7,"capabilities":["text","tools"],"priority":1}],"system_prompt":"أنت مساعد ذكي.","skills":{"web_search":{"enabled":true},"python_repl":{"enabled":true},"vision":{"enabled":true}},"telegram_enabled":true,"telegram_config":{"allowed_users":[],"allowed_groups":[],"require_mention_in_groups":true},"limits":{"max_threads":100,"max_messages_per_thread":50,"usage_history_days":30,"max_log_size_mb":10},"backup":{"enabled":true,"interval_hours":24},"metadata":{}}' > /app/data/config.json && \
    echo '{"last_updated":null,"total_requests":0,"total_tokens":0,"daily":{},"models":{}}' > /app/data/usage.json && \
    echo '{"threads":{}}' > /app/data/threads.json && \
    echo '{"servers":{},"updated_at":null}' > /app/data/mcp.json && \
    echo '{"skills":{},"updated_at":null}' > /app/data/skills.json && \
    echo '{"agents":{},"updated_at":null}' > /app/data/agents.json && \
    echo '{"tasks":{},"updated_at":null}' > /app/data/scheduler.json && \
    echo '{"entries":[],"updated_at":null}' > /app/data/logs.json && \
    echo '{"status":"healthy","errors":[],"recoveries":[],"last_check":null,"uptime_seconds":0}' > /app/data/health.json && \
    echo '{"last_update":null,"uptime_seconds":0,"alerts":[],"metrics_count":0}' > /app/data/monitor.json && \
    echo '{"current_version":"2.0.0","latest_version":"2.0.0","last_check":null,"update_available":false,"auto_update":true}' > /app/data/update.json && \
    chmod -R 755 /app && \
    chmod -R 777 /app/data

# Create non-root user
RUN useradd -m -u 1000 openclaw && \
    chown -R openclaw:openclaw /app

USER openclaw

EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7860/api/health || exit 1

# Start application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
