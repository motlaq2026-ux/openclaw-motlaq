# syntax=docker/dockerfile:1

FROM node:22-bookworm-slim AS frontend-build
WORKDIR /app
COPY openclaw-manager-main/package*.json ./
RUN npm ci
COPY openclaw-manager-main/ ./
RUN npm run build

FROM node:22-bookworm-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860 \
    OPENCLAW_HOME=/data/.openclaw \
    MANAGER_DATA_DIR=/data/openclaw-manager

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      python3 \
      python3-pip \
      ca-certificates \
      git \
    && rm -rf /var/lib/apt/lists/*

COPY openclaw-manager-main/requirements.txt ./requirements.txt
RUN pip3 install --break-system-packages -r requirements.txt

# Best-effort CLI tooling; image stays usable even if some packages fail to install.
RUN npm install -g openclaw clawhub mcporter || true

COPY openclaw-manager-main/backend ./backend
COPY --from=frontend-build /app/dist ./dist

EXPOSE 7860
CMD ["python3", "backend/main.py"]
