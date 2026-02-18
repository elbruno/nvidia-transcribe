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

- **Python** 3.10–3.12 (Python 3.13 is NOT supported by the moshi package)
- **NVIDIA GPU** with CUDA support (recommended; CPU offload available)
- **~14 GB VRAM** (or use CPU offloading)
- **Opus codec** development library (`libopus-dev` on Ubuntu)
- **Hugging Face account** — accept the [PersonaPlex model license](https://huggingface.co/nvidia/personaplex-7b-v1)

## Setup

### Aspire Quickstart (Recommended)

Run the full stack with one command from the AppHost directory:

```bash
cd scenario6/AppHost
aspire run
```

First run notes:
- Expect a large model download (~14 GB) on first startup.
- The moshi backend uses HTTPS/WSS with a self-signed cert (see Quick Start below).
- The Aspire dashboard shows logs, health, and endpoints for both services.

### Quickstart (Automated)

> **Do I need to create a venv first?**
> **No.** The setup script creates and manages the `venv/` directory at the repo root automatically.
> You do not need to follow the main README's Quick Start first.
> If you already have a venv activated, the script installs into it instead.

```powershell
# 1) Install system dependencies (see below for your OS)

# 2) Run the bootstrap script (creates venv, installs deps, copies .env)
#    Windows: use the py launcher to ensure Python 3.12 is selected (3.13 is NOT supported)
py -3.12 scenario6/setup_scenario6.py

# Optional: write your Hugging Face token directly into .env
# py -3.12 scenario6/setup_scenario6.py --hf-token hf_your_token_here

# Linux/macOS
python3.12 scenario6/setup_scenario6.py
```

Next steps:
1. **Activate the virtual environment** created by the script:
   ```powershell
   # Windows
   venv\Scripts\activate
   ```
   ```bash
   # Linux/macOS
   source venv/bin/activate
   ```
2. Set `HF_TOKEN` in `scenario6/.env` (if you did not pass `--hf-token`).
3. Accept the model license: https://huggingface.co/nvidia/personaplex-7b-v1
4. Run the app (from the repo root, with the venv active):
   ```powershell
   python scenario6/app.py
   ```

For the full manual walkthrough and troubleshooting, see [scenario6/docs/USER_MANUAL.md](scenario6/docs/USER_MANUAL.md).

### 1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt install libopus-dev

# Fedora/RHEL
sudo dnf install opus-devel

# macOS
brew install opus

# Windows (PowerShell) - requires Visual Studio Build Tools
# Install vcpkg if you do not already have it
git clone https://github.com/microsoft/vcpkg $env:USERPROFILE\vcpkg
& $env:USERPROFILE\vcpkg\bootstrap-vcpkg.bat
& $env:USERPROFILE\vcpkg\vcpkg.exe install opus:x64-windows
```

### 2. Install PersonaPlex Moshi Package (Vendored)

```bash
# Install the vendored moshi package
pip install -e scenario6/third_party/moshi
```

### 3. Install Scenario 6 Dependencies

```bash
# From the repo root, activate your venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install PyTorch with CUDA first (if not already installed)
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Install scenario 6 dependencies
pip install -r scenario6/requirements.txt
```

### 4. Configure the Environment

```bash
# Copy the example env file
cp scenario6/.env.example scenario6/.env

# Windows example
copy scenario6\.env.example scenario6\.env

# Edit .env and set your Hugging Face token
# Get a token at: https://huggingface.co/settings/tokens
```

**Required**: Set `HF_TOKEN` in `scenario6/.env`:
```
HF_TOKEN=hf_your_actual_token_here
```

**Optional**: Load model from a local path (skip download):
```
PERSONAPLEX_MODEL_PATH=/path/to/personaplex-7b-v1
```

### 5. Accept Model License

Visit [nvidia/personaplex-7b-v1](https://huggingface.co/nvidia/personaplex-7b-v1) and accept the license agreement while logged into your HuggingFace account.

## Usage

```bash
python scenario6/app.py
```

This starts the **Web UI** at [http://localhost:8010](http://localhost:8010).

Start the moshi backend separately:

```bash
mkdir -p ssl
python -m moshi.server --ssl ./ssl --port 8998
```

> **First launch**: The model (~14 GB) will be automatically downloaded and cached. Subsequent starts use the cached model.

### Quick Start

1. Start the moshi backend (see above)
2. Open [http://localhost:8010](http://localhost:8010)
3. Accept the self-signed SSL certificate by visiting `https://localhost:8998` in your browser
4. Click **Connect** to establish the WebSocket connection to the moshi backend
5. Press and hold the **Talk** button to speak
6. Release the button — PersonaPlex processes and responds with voice

### Preflight Checklist (New Users)

- Python 3.10-3.12 installed (3.12 recommended)
- GPU drivers + CUDA installed (if using GPU)
- Hugging Face token and license acceptance
- 20+ GB free disk space for model cache
- Ports 8010/8998 available (or override via env vars)

### Certificate Handling

- When moshi runs with `--ssl`, the browser must trust the self-signed cert.
- Visit `https://<moshi-host>:<moshi-port>` once to accept the certificate.
- If you run moshi without SSL, set `MOSHI_WS_SCHEME=ws` or `MOSHI_WS_URL=ws://host:port`.

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
