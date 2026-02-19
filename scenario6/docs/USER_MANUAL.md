# PersonaPlex Voice Conversation — User Manual

This guide walks you through setting up and using the PersonaPlex Voice Conversation app from start to finish.

## Table of Contents

1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [System Requirements](#system-requirements)
4. [Aspire Quickstart (Recommended)](#aspire-quickstart-recommended)
5. [Preflight Checklist](#preflight-checklist)
6. [Automated Setup (Recommended)](#automated-setup-recommended)
7. [Step-by-Step Setup](#step-by-step-setup)
8. [Configuring the Environment](#configuring-the-environment)
9. [Running the Application](#running-the-application)
10. [First-Run Verification](#first-run-verification)
11. [Using the Web Interface](#using-the-web-interface)
12. [Customizing Voice and Persona](#customizing-voice-and-persona)
13. [Theme System](#theme-system)
14. [Loading a Local Model](#loading-a-local-model)
15. [Troubleshooting](#troubleshooting)

---

## Overview

PersonaPlex Voice Conversation is a real-time, full-duplex voice AI application. Unlike traditional voice assistants that listen, think, then speak sequentially, PersonaPlex can listen and speak simultaneously — creating natural, flowing conversations just like talking on the phone.

The application consists of two components:
- **Web UI** (FastAPI, port 8010) — the browser interface you interact with
- **Moshi Backend** (port 8998) — the NVIDIA PersonaPlex speech-to-speech engine

---

## How It Works

Understanding the internals helps you troubleshoot and extend the app.

### Component Overview

```
Browser (https://localhost:8010)
        │
        │  GET  /api/config  → voices, personas, defaults
        │  WS   /ws/logs     → real-time server log streaming
        │  WS   /proxy/moshi → same-origin WebSocket proxy
        │
   FastAPI Server (app.py) — port 8010
        │
        └── Moshi Backend (port 8998, HTTPS/WSS)
            └── PersonaPlex-7B-v1 — full-duplex speech-to-speech
                ├── Audio input  → speech understanding
                ├── LLM backbone → response generation
                └── Audio output → speech synthesis
```

### The WebSocket Proxy (`/proxy/moshi`)

The browser page is served over HTTPS. The moshi backend uses a self-signed certificate on its own port (8998). A direct browser → moshi WebSocket would be blocked as a mixed-content request (or require the user to manually trust that certificate every run).

The solution: the FastAPI server exposes **`/proxy/moshi`** — a same-origin WebSocket endpoint. When the browser connects to it, the server opens a server-side WebSocket to moshi and relays raw binary frames in both directions:

```
Browser ──WS──► /proxy/moshi (FastAPI, same origin)
                     │
                     └──WS──► ws(s)://moshi-host:8998/api/chat
```

Because the proxy is on the same origin as the page, no mixed-content block occurs. The `voice_prompt` and `text_prompt` query parameters are forwarded to moshi when the proxy connection is opened.

### Connection State Machine

On page load, `fetchConfig()` automatically calls `openMoshi()`, so there is no manual Connect step.

| State | What's happening |
|-------|-----------------|
| **Connecting** | Browser WebSocket to `/proxy/moshi` is being opened |
| **Warming up…** | Proxy is open; waiting for the moshi `\x00` handshake byte |
| **Live** | Handshake received — model is ready, microphone enabled |
| **Disconnected** | Session closed; auto-reconnects after 4 s (unless user closed with code 1000) |
| **Error** | Proxy failed to reach moshi backend |

### Handshake Gate

PersonaPlex sends a single `\x00` byte once the model has finished loading. The client-side code treats this as the "ready" signal:

- Before the handshake: **Start** button is disabled (`off` class)
- After the handshake: button is enabled, microphone can be opened

This prevents sending audio before the model is ready, which would cause an immediate disconnect.

### Audio Pipeline

**Microphone → moshi:**
1. `navigator.mediaDevices.getUserMedia({ audio: true })` opens the mic
2. `MediaRecorder` encodes audio as Opus (preferring `audio/ogg;codecs=opus`, falling back to `audio/webm;codecs=opus`)
3. Chunks arrive every 100 ms and are framed: `[0x01][opus bytes…]` → sent over the proxy WS

**Moshi → speaker:**
1. Binary frames arrive with kind byte `0x01` = Opus audio, `0x02` = text token
2. Audio frames are decoded via `AudioContext.decodeAudioData` and scheduled onto a gapless playback queue (`nextPlayAt` pointer)
3. Text tokens are accumulated and displayed as `🧠` chat bubbles after a 600 ms debounce

### Auto-Reconnect

If the connection drops unexpectedly (close code ≠ 1000/1001), the client schedules `openMoshi()` again after 4 seconds. This handles transient network issues or moshi restarts without requiring page reload.

---

## System Requirements

PersonaPlex Voice Conversation is a real-time, full-duplex voice AI application. Unlike traditional voice assistants that listen, think, then speak sequentially, PersonaPlex can listen and speak simultaneously — creating natural, flowing conversations just like talking on the phone.

The application consists of two components:
- **Web UI** (FastAPI, port 8010) — the browser interface you interact with
- **Moshi Backend** (port 8998) — the NVIDIA PersonaPlex speech-to-speech engine

---

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.10 | 3.12 |
| GPU VRAM | 8 GB (with CPU offload) | 16+ GB |
| RAM | 16 GB | 32 GB |
| Disk Space | 20 GB (for model cache) | 30 GB |
| OS | Linux, Windows, macOS | Linux (Ubuntu 22.04+) |
| CUDA | 11.8+ | 12.1+ |

> **Note**: Python 3.13 is NOT supported by the moshi package.

---

## Aspire Quickstart (Recommended)

Run the full stack with Aspire:

```bash
cd scenario6/AppHost
aspire run
```

First run notes:
- Expect a large model download (~14 GB) on first startup.
- The moshi backend uses HTTPS/WSS with a self-signed cert.
- The Aspire dashboard shows logs, health, and endpoints for both services.
- Traces are sent to the Aspire dashboard automatically when using `aspire run`.

If you prefer local Python execution, continue below.

---

## Preflight Checklist

- Python 3.10-3.12 installed (3.12 recommended)
- GPU drivers + CUDA installed (if using GPU)
- Hugging Face token ready and license accepted
- 20+ GB free disk space for model cache
- Ports 8010/8998 available (or override via env vars)

## Automated Setup (Recommended)

If you want a faster setup, use the bootstrap script from the repo root:

```bash
python scenario6/setup_scenario6.py
```

Optional: write your Hugging Face token directly to `.env`:

```bash
python scenario6/setup_scenario6.py --hf-token hf_your_token_here
```

After it completes:
1. Accept the model license at https://huggingface.co/nvidia/personaplex-7b-v1
2. Run: `python scenario6/app.py`

If you prefer the full manual steps, continue below.

---

## Step-by-Step Setup

### Step 1: Install System Dependencies

The Opus audio codec library is required:

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install libopus-dev
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install opus-devel
```

**macOS:**
```bash
brew install opus
```

**Windows:**
The opus library is typically bundled with Python packages on Windows.

### Step 2: Create a Python Virtual Environment

```bash
# Use Python 3.12 (not 3.13!)
python3.12 -m venv venv

# Activate the environment
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows
```

### Step 3: Install PyTorch with CUDA

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### Step 4: Install the PersonaPlex Moshi Package (Vendored)

```bash
pip install -e scenario6/third_party/moshi
```

### Step 5: Install Scenario 6 Dependencies

```bash
pip install -r scenario6/requirements.txt
```

### Step 6: Get a Hugging Face Token

1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Click **New token**
3. Give it a name (e.g., "personaplex")
4. Select **Read** access
5. Click **Generate token**
6. Copy the token (starts with `hf_`)

### Step 7: Accept the Model License

1. Go to [huggingface.co/nvidia/personaplex-7b-v1](https://huggingface.co/nvidia/personaplex-7b-v1)
2. Log in with your HuggingFace account
3. Click **Agree and access repository**

### Step 8: Configure the Environment File

```bash
# Copy the template
cp scenario6/.env.example scenario6/.env

# Edit the file
nano scenario6/.env   # or use your preferred editor
```

Set the `HF_TOKEN` value:
```
HF_TOKEN=hf_AbCdEfGhIjKlMnOpQrStUv
```

---

## Configuring the Environment

The `.env` file controls all settings. Here's what each option does:

### Required Settings

| Setting | Description |
|---------|-------------|
| `HF_TOKEN` | Your Hugging Face API token for model download |

### Optional Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `PERSONAPLEX_MODEL_PATH` | *(empty)* | Path to a local model directory. If set, skips download |
| `HF_HOME` | `~/.cache/huggingface/hub` | Where HuggingFace stores downloaded models |
| `APP_PORT` | `8010` | Port for the web UI |
| `MOSHI_PORT` | `8998` | Port for the moshi speech engine |
| `MOSHI_HOST` | `localhost` | Moshi backend host |
| `MOSHI_WS_SCHEME` | `wss` | Moshi WebSocket scheme (`ws` or `wss`) |
| `MOSHI_WS_URL` | *(empty)* | Full Moshi WebSocket URL (overrides host/port) |
| `APP_HOST` | `0.0.0.0` | Network interface to bind to |
| `DEFAULT_VOICE` | `NATF2` | Default voice (see voice list below) |
| `DEFAULT_PERSONA` | Teacher prompt | Default AI personality |
| `CPU_OFFLOAD` | `false` | Offload model layers to CPU to save GPU memory |
| `USE_GPU` | `true` | Enable GPU passthrough for moshi when using Aspire |

### Service Discovery

- `GET /health` - basic service health and backend host/port
- `GET /api/info` - backend WebSocket URL and moshi version (if available)

---

## Running the Application

```bash
python scenario6/app.py
```

You'll see:
```
╔══════════════════════════════════════════════════════════════════╗
║  PersonaPlex Voice Conversation                                ║
║  Web UI:  http://localhost:8010                                 ║
║  Moshi:   https://localhost:8998                                ║
╚══════════════════════════════════════════════════════════════════╝
```

Start the moshi backend separately:

```bash
mkdir -p ssl
python -m moshi.server --ssl ./ssl --port 8998
```

---

## First-Run Verification

1. Start the moshi backend (see above)
2. Open the web UI at http://localhost:8010
3. The app **auto-connects** — watch the status badge change to *Warming up…*
4. Wait for the status badge to turn green (**Live**) — this means the model finished loading
5. Click **Start** and speak naturally; audio plays back in real-time
6. Click **Stop** to end the session

> **Note**: The first launch downloads the PersonaPlex model (~14 GB). Subsequent launches are fast because the model is cached.

---

## Using the Web Interface

### Opening the App

1. Open your browser and navigate to **http://localhost:8010**

<!-- Screenshot: Main interface with dark theme showing the welcome screen -->
*The main interface shows the welcome screen, sidebar configuration, and the talk button.*

### Accepting the SSL Certificate

Before connecting, you need to accept the moshi backend's self-signed SSL certificate:

1. Open a new tab and visit **https://localhost:8998** (or your configured backend host)
2. Your browser will show a security warning
3. Click **Advanced** → **Proceed to localhost** (or equivalent)
4. You can close this tab — the certificate is now accepted

### Certificate Handling

- When moshi runs with `--ssl`, the browser must trust the self-signed cert.
- Visit `https://<moshi-host>:<moshi-port>` once to accept the certificate.
- If you run moshi without SSL, set `MOSHI_WS_SCHEME=ws` or `MOSHI_WS_URL=ws://host:port`.

<!-- Screenshot: Browser SSL warning page -->
*Accept the self-signed certificate to enable the WebSocket connection.*

### Connecting to the Backend

The app **connects automatically** when the page loads — no manual Connect click is needed.

Connection states:

| Badge | Meaning |
|-------|---------|
| Waiting | Page just loaded, starting connection |
| Connecting | Establishing proxy WebSocket |
| Warming up… | Proxy open; moshi model is loading |
| **Live** (green) | Model ready; microphone enabled |
| Disconnected | Session ended; auto-reconnects in 4 s |

If you need to reconnect manually, click the **Reconnect** button that appears when disconnected.

### Having a Conversation

1. Wait for the status badge to show **Live** (green)
2. **Click Start** — the button turns active and microphone capture begins
3. **Speak naturally** — PersonaPlex listens and responds simultaneously (full-duplex)
4. **Click Stop** to end the session

> The connection is **persistent and full-duplex**: PersonaPlex can speak while you speak, just like a phone call. There is no hold-to-talk, no push-to-talk — once you click Start, the session is live.

<!-- Screenshot: Active conversation with user and agent messages -->
*Messages appear as chat bubbles. Text tokens from the model appear as "🧠" bubbles.*

---

## Customizing Voice and Persona

### Selecting a Voice

Use the **Voice** dropdown in the sidebar to choose from 18 pre-packaged voices:

| Category | Voices | Style |
|----------|--------|-------|
| Natural Female | NATF0–NATF3 | Conversational, natural-sounding |
| Natural Male | NATM0–NATM3 | Conversational, natural-sounding |
| Variety Female | VARF0–VARF4 | Diverse styles and tones |
| Variety Male | VARM0–VARM4 | Diverse styles and tones |

<!-- Screenshot: Voice selection dropdown expanded -->
*The voice dropdown groups voices by category.*

### Setting a Persona

Type a persona description in the **Persona Prompt** text area, or click a preset chip:

- **teacher** — "You are a wise and friendly teacher..."
- **assistant** — General conversational AI
- **customer_service** — Tech support agent named Alex
- **astronaut** — Mars mission crew member
- **chef** — Former baker with cooking expertise

<!-- Screenshot: Persona presets chips in sidebar -->
*Click a preset chip to quickly load a persona.*

### Custom Personas

Write your own persona prompt for any scenario:

```
You work for CloudNet Solutions which is a cloud hosting company and your
name is Jordan. You are helpful and technical. Information: Basic plan $9/mo
(10 GB storage), Pro plan $29/mo (100 GB storage), Enterprise plan $99/mo
(1 TB storage). Free migration support for all plans.
```

---

## Theme System

The app supports three themes, selectable from the top-right corner:

| Button | Theme | Description |
|--------|-------|-------------|
| 💻 | System | Automatically follows your OS light/dark preference |
| ☀️ | Light | Light background, ideal for bright environments |
| 🌙 | Dark | Dark background, easier on the eyes at night |

**System** is the default theme. Your preference is saved in browser localStorage.

<!-- Screenshot: Side-by-side comparison of light and dark themes -->
*The app adapts to your preferred theme.*

---

## Loading a Local Model

If you've already downloaded the PersonaPlex model or want to use a specific model directory:

### Method 1: Environment Variable

Set `PERSONAPLEX_MODEL_PATH` in your `.env` file:

```
PERSONAPLEX_MODEL_PATH=/home/user/models/personaplex-7b-v1
```

### Method 2: HuggingFace Cache

If you've previously downloaded the model via HuggingFace, it's already cached. Set the cache directory if it's in a non-standard location:

```
HF_HOME=/data/hf_cache
```

### Model Directory Structure

A valid model directory should contain:
```
personaplex-7b-v1/
├── config.json
├── model.safetensors (or sharded files)
├── tokenizer.json
└── ...
```

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| "HF_TOKEN not configured" | Copy `.env.example` to `.env` and add your token |
| "Access denied" on download | Accept the license at huggingface.co/nvidia/personaplex-7b-v1 |
| WebSocket won't connect | Accept the SSL cert at https://localhost:8998 first |
| `ModuleNotFoundError: moshi` | Install the moshi package: `pip install -e scenario6/third_party/moshi` |
| `libopus` not found | Install: `sudo apt install libopus-dev` |
| CUDA out of memory | Set `CPU_OFFLOAD=true` in `.env`, install `accelerate` |
| Very slow responses | Use a GPU; CPU mode is not practical for real-time use |
| Port 8010 in use | Change `APP_PORT` in `.env` |
| Port 8998 in use | Change `MOSHI_PORT` in `.env` |

### Port and Host Overrides

Use these environment variables when running behind a VPN, proxy, or custom ports:

- `MOSHI_HOST`, `MOSHI_PORT`
- `MOSHI_WS_SCHEME` or `MOSHI_WS_URL`
- `APP_HOST`, `APP_PORT`

### Aspire Common Blockers

| Problem | Fix |
|---------|-----|
| Docker not running | Start Docker Desktop/Engine and re-run `aspire run` |
| GPU not detected in container | Install NVIDIA Container Toolkit and set `USE_GPU=true` |
| Moshi TLS warnings in browser | Visit the moshi HTTPS URL and accept the self-signed certificate |

### Checking GPU Status

```bash
nvidia-smi
```

You should see your GPU with available memory. PersonaPlex requires ~14 GB VRAM without CPU offloading.

### Viewing Server Logs

The bottom panel of the web UI shows real-time server logs:
- **INFO** (blue) — Normal operation messages
- **WARN** (yellow) — Non-critical warnings
- **ERROR** (red) — Errors that need attention

Click **▶ details** on any log entry to see expanded information.

### Restarting the Backend

If the moshi backend becomes unresponsive, restart it from your process manager:

- Aspire: stop and re-run `aspire run`
- Local: stop the moshi server process and re-launch it

---

## FAQ

**Q: Can I use this commercially?**
A: The PersonaPlex code is MIT licensed. The model weights use the NVIDIA Open Model License — check the license terms for commercial use.

**Q: Does this send my voice to the cloud?**
A: No. All processing happens locally on your hardware. No data is sent to external servers (except the initial model download from HuggingFace).

**Q: Can I run this without a GPU?**
A: Yes, with `CPU_OFFLOAD=true`, but responses will be very slow. A GPU is strongly recommended for real-time conversation.

**Q: How much disk space does the model need?**
A: Approximately 14 GB for the model weights, plus some overhead for the cache.

**Q: Can I use a different model?**
A: The app is designed for PersonaPlex-7B-v1 specifically. Other models would require modifications to the moshi server.

---

## Vendoring Updates (Maintainers)

The moshi package is vendored under `scenario6/third_party/moshi`.

To update it from upstream:

```bash
# Windows
./tools/update_moshi.ps1

# Linux/macOS
./tools/update_moshi.sh
```

The update scripts will:
- Backup the previous version
- Pull the latest moshi package from the upstream repo
- Record the upstream commit in `MOSHI_VERSION`
