# Scenario 6 — PersonaPlex Real-Time Voice Conversation

A real-time, full-duplex voice conversation web app powered by **NVIDIA PersonaPlex-7B-v1**. Speak naturally with an AI that listens and responds simultaneously — just like a phone call. Customize the AI's persona and voice through the web interface.

> **Model**: [nvidia/personaplex-7b-v1](https://huggingface.co/nvidia/personaplex-7b-v1) — a 7B parameter speech-to-speech model based on the Moshi architecture.

## Features

- **Full-duplex voice conversation** — simultaneous listening and speaking
- **Customizable personas** — define the AI's role, personality, and background via text prompts
- **Multiple voice options** — choose from 18 pre-packaged voice embeddings (natural and variety)
- **Theme support** — Light, Dark, and System (auto-detect) themes
- **Auto-download** — model is automatically downloaded from HuggingFace on first launch and cached
- **Local model loading** — optionally load from a local directory path
- **Secure token management** — Hugging Face token stored in `.env` file (gitignored)
- **Real-time server log** — live log panel with expandable details
- **Low latency** — response time as low as 170ms
- **Fully local** — all inference runs on your hardware, no cloud API calls

## Models

| Component | Details |
|-----------|---------|
| Model | PersonaPlex-7B-v1 (7B parameters) |
| Architecture | Full-duplex speech-to-speech (based on Moshi) |
| License | NVIDIA Open Model License |
| VRAM Required | ~14 GB (or use `--cpu-offload` for lower VRAM) |

## Prerequisites

### All Paths

- **Python 3.10–3.12** (Python 3.13 is NOT supported)
- **~14 GB VRAM** on GPU (or CPU offload available; will be slow)
- **20+ GB free disk space** for model cache
- **Hugging Face account** with [license accepted](https://huggingface.co/nvidia/personaplex-7b-v1)
- **Hugging Face token** (get one at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens))

### For Aspire Path (Recommended)

- **.NET 9 SDK** or later ([download](https://learn.microsoft.com/dotnet/core/install/))
- **Docker** Desktop or Engine (running)
- **NVIDIA Container Toolkit** (optional, for GPU support in containers)

### For Manual Setup Path

- **Opus development library**:
  - Ubuntu/Debian: `sudo apt install libopus-dev`
  - Fedora/RHEL: `sudo dnf install opus-devel`
  - macOS: `brew install opus`
  - Windows: NVIDIA Container Toolkit or Visual Studio Build Tools + vcpkg
- **GPU drivers + CUDA** (if using GPU; CPU mode available but slow)

## Quick Start (Choose Your Path)

### 🚀 Path 1: Aspire (Recommended — 3 Steps, ~5 Minutes)

**The easiest way to get started:** One command launches everything. Aspire handles all setup, dependencies, containers, and certificates automatically.

#### Step 1: Set Environment

Copy `.env.example` to `.env` and add your Hugging Face token:

```powershell
copy scenario6\.env.example scenario6\.env
# Edit scenario6\.env and set: HF_TOKEN=hf_your_token_here
```

#### Step 2: Accept the Model License

Visit [huggingface.co/nvidia/personaplex-7b-v1](https://huggingface.co/nvidia/personaplex-7b-v1) and click **Accept** (while logged in).

#### Step 3: Launch with Aspire

Navigate to AppHost and run one command:

```powershell
# Windows
cd scenario6\AppHost
aspire run
```

```bash
# Linux/macOS
cd scenario6/AppHost
aspire run
```

The **Aspire Dashboard** opens automatically at `http://localhost:15000`. Click the **Web UI endpoint** link (usually `http://localhost:8010`) to open the app.

#### What Aspire Handles

You don't need to do anything else. Aspire automatically:

✅ Installs Python dependencies (PyTorch, NVIDIA NeMo, Moshi, FastAPI)  
✅ Downloads the PersonaPlex model (~14 GB) on first run  
✅ Spins up Docker containers for the Moshi backend and FastAPI server  
✅ Configures SSL/TLS certificates for secure WebSocket connections  
✅ Provides a dashboard with live logs, health checks, and distributed traces  
✅ Loads your `.env` configuration automatically

#### First Run Timeline

| Step | Time |
|------|------|
| Build Docker images | 2–3 minutes |
| Download model | 5–10 minutes (depends on internet) |
| Start services | 1–2 minutes |
| **Total** | **~10–15 minutes** (one-time only) |
| **Subsequent runs** | **~30–60 seconds** (using cached model) |

### 📋 Path 2: Manual Setup (Alternative)

**If you can't or don't want to use Docker/Aspire**, use this path.

#### Step 1: Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt install libopus-dev

# Fedora/RHEL
sudo dnf install opus-devel

# macOS
brew install opus

# Windows (PowerShell) - requires Visual Studio Build Tools
git clone https://github.com/microsoft/vcpkg $env:USERPROFILE\vcpkg
& $env:USERPROFILE\vcpkg\bootstrap-vcpkg.bat
& $env:USERPROFILE\vcpkg\vcpkg.exe install opus:x64-windows
```

#### Step 2: Run Setup Script

The setup script creates a venv, installs dependencies, and configures `.env`:

```powershell
# Windows
py -3.12 scenario6/setup_scenario6.py

# Or with token inline
py -3.12 scenario6/setup_scenario6.py --hf-token hf_your_token_here
```

```bash
# Linux/macOS
python3.12 scenario6/setup_scenario6.py
```

#### Step 3: Activate Virtual Environment

```powershell
# Windows
venv\Scripts\activate
```

```bash
# Linux/macOS
source venv/bin/activate
```

#### Step 4: Accept Model License

Visit [huggingface.co/nvidia/personaplex-7b-v1](https://huggingface.co/nvidia/personaplex-7b-v1) and accept the license (while logged in).

#### Step 5: Run the App

Two terminals needed:

**Terminal 1 — Moshi backend:**
```bash
mkdir -p ssl
python -m moshi.server --ssl ./ssl --port 8998
```

**Terminal 2 — Web server (from repo root, with venv active):**
```bash
python scenario6/app.py
```

Then open [http://localhost:8010](http://localhost:8010).

📚 Full manual guide: [scenario6/docs/USER_MANUAL.md](scenario6/docs/USER_MANUAL.md)

## ▶️ Using Scenario 6

**Great! Your app is running.** Here's how to use it:

### Your First Conversation

1. **Open the Web UI** at [http://localhost:8010](http://localhost:8010)
2. **Select a voice** from the left sidebar (default: NATF2 — female, natural)
3. **Choose a persona** (default: teacher) or write your own
4. **Press and hold the Talk button** to speak
5. **Release** — PersonaPlex listens and responds with voice
6. **Listen** — Audio plays in real-time

### Dashboard (Aspire Only)

When using Aspire:

| Feature | What to Look For |
|---------|------------------|
| **Dashboard** | http://localhost:15000 (auto-opens) |
| **Service Health** | Green checkmarks = all good |
| **Live Logs** | Click a service name to see logs in real-time |
| **Traces** | View request traces for debugging |
| **Endpoints** | Click the Web UI link to open the app |

### Certificate Handling (Manual Setup Only)

- First time only: Visit `https://localhost:8998` and accept the self-signed certificate
- Or disable SSL by setting `MOSHI_WS_SCHEME=ws` in `.env`

### Port and Host Overrides

Use these environment variables when running behind a VPN, proxy, or custom ports:

- `MOSHI_HOST`, `MOSHI_PORT`
- `MOSHI_WS_SCHEME` or `MOSHI_WS_URL`
- `APP_HOST`, `APP_PORT`

### Voice Selection

Choose from 18 voices in the sidebar:

| Category | Voices |
|----------|--------|
| Natural Female | NATF0, NATF1, NATF2, NATF3 |
| Natural Male | NATM0, NATM1, NATM2, NATM3 |
| Variety Female | VARF0, VARF1, VARF2, VARF3, VARF4 |
| Variety Male | VARM0, VARM1, VARM2, VARM3, VARM4 |

### Persona Presets

Select from built-in presets or write your own:

- **teacher** — Wise and friendly teacher
- **assistant** — General conversational assistant
- **customer_service** — Tech support agent
- **astronaut** — Mars mission crew member
- **chef** — Former baker and cooking enthusiast

### Theme Support

Use the theme switcher in the top-right corner:

| Theme | Description |
|-------|-------------|
| 💻 System | Follows your OS preference (default) |
| ☀️ Light | Light background with dark text |
| 🌙 Dark | Dark background for low-light environments |

## Configuration

All configuration is in `scenario6/.env` (copy from `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_TOKEN` | *(required)* | Hugging Face API token |
| `PERSONAPLEX_MODEL_PATH` | *(empty)* | Local model directory path |
| `HF_HOME` | `~/.cache/huggingface/hub` | HuggingFace cache directory |
| `APP_PORT` | `8010` | Web UI server port |
| `MOSHI_HOST` | `localhost` | Moshi backend host |
| `MOSHI_PORT` | `8998` | Moshi backend port |
| `MOSHI_WS_SCHEME` | `wss` | Moshi WebSocket scheme (`ws` or `wss`) |
| `MOSHI_WS_URL` | *(empty)* | Full Moshi WebSocket URL (overrides host/port) |
| `APP_HOST` | `0.0.0.0` | Web server bind address |
| `DEFAULT_VOICE` | `NATF2` | Default voice prompt |
| `DEFAULT_PERSONA` | *teacher prompt* | Default persona text |
| `CPU_OFFLOAD` | `false` | Enable CPU offloading for low VRAM |
| `USE_GPU` | `true` | Enable GPU passthrough for moshi when using Aspire |

### Service Discovery

- `GET /health` - basic service health and backend host/port
- `GET /api/info` - backend WebSocket URL and moshi version (if available)

## Architecture

```
Browser (http://localhost:8010)
        │
        │  Fetch /api/config (voices, personas, settings)
        │  WebSocket /ws/logs (real-time log streaming)
        │
   FastAPI Server (app.py, port 8010)
      │  Serves web UI and configuration API
      │
      ├── Moshi Backend (port 8998, HTTPS/WSS)
      │   └── PersonaPlex-7B-v1 (full-duplex speech-to-speech)
      │       ├── Audio Input  → Speech Understanding
      │       ├── LLM Backbone → Response Generation
      │       └── Audio Output → Speech Synthesis
      │
Browser ←──── WSS connection to moshi backend
           (full-duplex audio streaming)
```

## Project Structure

```
scenario6/
├── app.py                 # FastAPI orchestration server
├── requirements.txt       # Python dependencies
├── .env.example           # Environment configuration template
├── static/
│   ├── index.html         # Web UI markup
│   ├── styles.css         # Theme system & styling
│   └── app.js             # Client-side application logic
├── docs/
│   └── USER_MANUAL.md     # Detailed setup and usage guide
└── README.md              # This file
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `HF_TOKEN not configured` | Copy `.env.example` to `.env` and set your token |
| `Access denied` on model download | Accept the license at [huggingface.co/nvidia/personaplex-7b-v1](https://huggingface.co/nvidia/personaplex-7b-v1) |
| WebSocket connection fails | Visit `https://localhost:8998` first to accept the self-signed SSL certificate |
| `libopus` not found | Install the Opus codec: `sudo apt install libopus-dev` |
| Out of GPU memory | Set `CPU_OFFLOAD=true` in `.env` and install `accelerate` package |
| Slow on CPU | GPU is strongly recommended; CPU mode will be very slow |
| Model download is slow | First download is ~14 GB. Set `HF_HOME` to a fast drive |
| Port already in use | Change `APP_PORT` or `MOSHI_PORT` in `.env` |

### Aspire Common Blockers

| Problem | Fix |
|---------|-----|
| Docker not running | Start Docker Desktop/Engine and re-run `aspire run` |
| GPU not detected in container | Install NVIDIA Container Toolkit and set `USE_GPU=true` |
| Moshi TLS warnings in browser | Visit the moshi HTTPS URL and accept the self-signed certificate |

## License

The PersonaPlex code is released under the **MIT License**. The model weights are released under the **NVIDIA Open Model License**.
