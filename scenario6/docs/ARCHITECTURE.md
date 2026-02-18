# Scenario 6 — Architecture Reference

## Overview

Scenario 6 (PersonaPlex) is a full-duplex voice conversation app with two services:

| Service | Technology | Port | Role |
|---------|-----------|------|------|
| **Frontend** | FastAPI (Python) | 8010 | Web UI, config API, log streaming |
| **Moshi Backend** | aiohttp (Python, Docker) | 8998 | PersonaPlex-7B speech-to-speech inference |

Both services run over **plain HTTP/WS** by default. SSL/TLS is optional.

## System Diagram

```
┌──────────────────────────────────────────────┐
│  Browser  (http://localhost:8010)             │
│                                               │
│  1. GET /api/config → fetch moshi WS URL      │
│  2. WS  /ws/logs   → live server log stream   │
│  3. WS  ws://host:8998/api/chat → audio I/O   │
│         ↑ direct connection, no proxy          │
└─────┬────────────────────┬───────────────────┘
      │                    │
      │ HTTP (1,2)         │ WebSocket (3)
      ▼                    ▼
┌──────────────┐    ┌─────────────────────────────┐
│  Frontend    │    │  Moshi Backend (Docker)      │
│  app.py      │    │  PersonaPlex-7B-v1           │
│  port 8010   │    │  port 8998                   │
│              │    │                               │
│  • /api/config    │  • /api/chat  (WS, audio)    │
│  • /ws/logs       │  • /health    (HTTP)         │
│  • /health        │                               │
│  • /proxy/moshi   │  Full-duplex pipeline:       │
│    (fallback)     │   Audio In → ASR → LLM →     │
│              │    │   TTS → Audio Out             │
└──────────────┘    └─────────────────────────────┘
```

## Data Flow

### Audio Conversation (Happy Path)

```
1. Browser loads page → GET /api/config
2. Config returns moshi_ws_url = "ws://localhost:8998/api/chat"
3. Browser opens WebSocket directly to moshi backend
4. Moshi loads model → sends 0x00 handshake byte → state = "Live"
5. Browser captures mic audio → sends binary frames to moshi
6. Moshi processes audio → streams response audio frames back
7. Browser plays received audio in real-time (full-duplex)
```

### Log Streaming

```
1. Browser opens WebSocket to ws://localhost:8010/ws/logs
2. Frontend app.py broadcasts server events as JSON
3. Browser renders log entries in the live log panel
```

## Aspire Orchestration

.NET Aspire (AppHost) orchestrates both services:

```
AppHost/Program.cs
    │
    ├── scenario6-moshi (Docker container, always)
    │   • Built from moshi/Dockerfile
    │   • pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime base
    │   • GPU passthrough via --gpus=all (optional)
    │   • Persistent volume for HuggingFace model cache
    │   • Health check: GET /health
    │
    └── scenario6-frontend
        • Development: Aspire Python (AddUvicornApp) — hot reload
        • Production: Docker container (AddDockerfile)
        • Waits for moshi to be healthy before starting
```

### Orchestration Modes

| Mode | Command | Frontend | Moshi | Use Case |
|------|---------|----------|-------|----------|
| **Development** | `aspire run` | Aspire Python (local venv) | Docker | Fast iteration, hot reload |
| **Production** | `dotnet publish` | Docker | Docker | Deployment |

### Environment Injection

Aspire injects these environment variables into both services:

| Variable | Injected Into | Source |
|----------|---------------|--------|
| `HF_TOKEN` | moshi, frontend | Aspire user-secrets |
| `MOSHI_WS_URL` | frontend | moshi endpoint reference |
| `MOSHI_HOST` | frontend | Hardcoded `localhost` (dev) / endpoint ref (prod) |
| `MOSHI_PORT` | moshi, frontend | Config or default `8998` |
| `APP_PORT` | frontend | Config or default `8010` |
| `MOSHI_USE_SSL` | moshi | Config or default `false` |
| `MOSHI_CPU_OFFLOAD` | moshi | Config or default `false` |

## OpenTelemetry

**Telemetry is disabled by default.** Both services have `setup_telemetry()` functions that check for `OTEL_EXPORTER_OTLP_ENDPOINT` at startup. The Aspire AppHost intentionally does **not** call `.WithOtlpExporter()` so this variable is never injected.

### Why Disabled

The OpenTelemetry OTLP HTTP exporter (`opentelemetry-exporter-otlp-proto-http`) uses the synchronous `requests` library. When the OTLP collector is unreachable or slow, export calls block the Python `asyncio` event loop. This causes:

1. WebSocket heartbeat/ping timeouts
2. Audio frame delivery stalls
3. Frontend or moshi drops the connection
4. User experiences disconnection after speaking

### Defence-in-Depth

If the `OTEL_EXPORTER_OTLP_ENDPOINT` variable is set (e.g., manually), both services still protect themselves:

1. **Startup probe** — `_probe_otlp_endpoint()` sends a HEAD request with a 2-second timeout. If the collector is unreachable, telemetry is disabled entirely.
2. **Short export timeout** — `BatchSpanProcessor(export_timeout_millis=2000)` ensures that if the collector goes down after startup, spans are dropped after 2 seconds instead of blocking for ~30 seconds.

### Re-enabling Telemetry

To re-enable distributed tracing (e.g., if running Aspire with a healthy OTLP collector):

1. In `AppHost/Program.cs`, add `.WithOtlpExporter()` to the moshi and frontend resource builders
2. Aspire will inject the OTLP endpoint automatically
3. Both services probe the endpoint at startup and enable if reachable

## WebSocket Proxy (Fallback)

The frontend includes a `/proxy/moshi` WebSocket endpoint that tunnels browser audio frames to the moshi backend server-side. This exists for **HTTPS deployments** where the browser page is served over HTTPS but the moshi backend uses a self-signed certificate — a direct `wss://` connection would fail due to certificate validation, and a `ws://` connection would be blocked as mixed content.

**Default (HTTP):** Not used. The browser connects directly to `ws://host:8998/api/chat`.

**HTTPS deployment:** Set `MOSHI_USE_SSL=true` and the frontend will serve over HTTPS. The browser can then use `/proxy/moshi` which handles the backend TLS handshake server-side.

## Connection State Machine

```
     Page Load
         │
         ▼
   ┌─────────────┐
   │  Connecting  │  Browser opens WS to moshi
   └──────┬──────┘
          │ connected
          ▼
   ┌─────────────┐
   │ Warming up… │  Waiting for 0x00 handshake (model loading)
   └──────┬──────┘
          │ 0x00 received
          ▼
   ┌────────────┐
   │    Live    │  Full-duplex audio streaming
   └──────┬─────┘
          │ close / error
          ▼
   ┌──────────────┐
   │ Disconnected │  Auto-reconnect after 4s
   └──────────────┘
```

## Network Ports

| Port | Service | Protocol | Description |
|------|---------|----------|-------------|
| 8010 | Frontend | HTTP | Web UI, API, log WS |
| 8998 | Moshi | HTTP + WS | Health check, audio WS |
| 15000 | Aspire Dashboard | HTTP | Service monitoring (Aspire only) |

## Docker Images

### Moshi Backend (`moshi/Dockerfile`)

```
Base:   pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime
Python: 3.11 (from base image)
Deps:   libopus, vendored moshi package, OpenTelemetry SDK
Entry:  start_moshi.sh → python -m moshi.server
```

### Frontend (`Dockerfile`)

```
Base:   python:3.12-slim
Deps:   libopus, FastAPI, uvicorn, aiohttp
Entry:  python /app/app.py
```

> The frontend Dockerfile is only used in production mode. During development, Aspire runs the frontend directly via Python.

## Volume Mounts

| Volume | Mount Point | Purpose |
|--------|-------------|---------|
| `hf-model-cache-scenario6` | `/root/.cache/huggingface` | Persistent model cache across container restarts |
