---
title: OpenClaw Manager Web
emoji: 🦞
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
license: mit
short_description: OpenClaw Manager web dashboard for Hugging Face
---

# OpenClaw Manager Web (Hugging Face)

This repository runs the `openclaw-manager` UI as a web app on Hugging Face Spaces.

## Architecture

- Frontend: React + TypeScript (ported from Tauri UI)
- Backend: FastAPI command bridge at `/api/command/{cmd}`
- Runtime: Docker Space

## Local run

```bash
docker build -t openclaw-manager-web .
docker run --rm -p 7860:7860 openclaw-manager-web
```

Open: `http://localhost:7860`

## Optional secrets

- `MANAGER_API_TOKEN`: if set, backend requires `Authorization: Bearer <token>` or `X-API-Key`.
- `OPENCLAW_HOME`: override OpenClaw home directory (default `/data/.openclaw` when available).
- `MANAGER_DATA_DIR`: manager data directory (default `/data/openclaw-manager` when available).

### One-time runtime bootstrap (safe way to prefill secrets)

Set these HF Space secrets/variables to pre-create provider + Telegram config on startup (written to runtime config files, not Git):

- `MANAGER_BOOTSTRAP_ENABLED=true`
- `MANAGER_BOOTSTRAP_PROVIDER_NAME=groq`
- `MANAGER_BOOTSTRAP_PROVIDER_BASE_URL=https://api.groq.com/openai/v1`
- `MANAGER_BOOTSTRAP_PROVIDER_API_TYPE=openai-completions`
- `MANAGER_BOOTSTRAP_PROVIDER_MODELS=llama-3.3-70b-versatile`
- `MANAGER_BOOTSTRAP_PROVIDER_API_KEY=...`
- `MANAGER_BOOTSTRAP_TELEGRAM_BOT_TOKEN=...`
- `MANAGER_BOOTSTRAP_TELEGRAM_USER_ID=...`

Behavior:
- Bootstrap runs once, then sets `bootstrap_applied` in manager state.
- You can still edit/delete everything from the UI normally.
- Use `MANAGER_BOOTSTRAP_FORCE=true` only if you intentionally want to re-apply bootstrap.

If `MANAGER_API_TOKEN` is enabled, the web UI will prompt once for the token and store it in browser localStorage.

## Notes

- The frontend keeps original command names and calls backend through an invoke shim.
- Desktop-only operations are re-implemented with container-safe behavior.
- AI provider config supports broad presets plus custom OpenAI/Anthropic-compatible endpoints with model auto-discovery.
