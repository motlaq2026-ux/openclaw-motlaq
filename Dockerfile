FROM python:3.10-slim

LABEL maintainer="OpenClaw Fortress"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/logs /app/.openclaw

ENV OPENCLAW_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

EXPOSE 7860

CMD ["python", "app.py"]
