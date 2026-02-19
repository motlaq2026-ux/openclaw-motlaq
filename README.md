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

If `MANAGER_API_TOKEN` is enabled, the web UI will prompt once for the token and store it in browser localStorage.

## Notes

- The frontend keeps original command names and calls backend through an invoke shim.
- Desktop-only operations are re-implemented with container-safe behavior.
