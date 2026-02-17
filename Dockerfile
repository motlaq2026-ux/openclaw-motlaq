FROM python:3.10-slim

LABEL maintainer="OpenClaw Fortress"

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install OpenClaw from GitHub
RUN pip install --no-cache-dir git+https://github.com/openclaw/openclaw.git

# Copy application
COPY . .

# Create directories
RUN mkdir -p /app/data /app/logs /app/.openclaw

# Environment
ENV OPENCLAW_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

EXPOSE 7860

CMD ["python", "app.py"]
