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

### 1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt install libopus-dev

# Fedora/RHEL
sudo dnf install opus-devel

# macOS
brew install opus
```

### 2. Clone and Install PersonaPlex Moshi Package

```bash
# Clone the PersonaPlex repo (contains the moshi server)
git clone https://github.com/NVIDIA/personaplex.git /tmp/personaplex

# Install the moshi package
pip install /tmp/personaplex/moshi/.
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

This starts two servers:
1. **Web UI** at [http://localhost:8010](http://localhost:8010) — the voice conversation interface
2. **Moshi Backend** at `https://localhost:8998` — the PersonaPlex speech-to-speech engine

> **First launch**: The model (~14 GB) will be automatically downloaded and cached. Subsequent starts use the cached model.

### Quick Start

1. Open [http://localhost:8010](http://localhost:8010)
2. Accept the self-signed SSL certificate by visiting `https://localhost:8998` in your browser
3. Click **Connect** to establish the WebSocket connection to the moshi backend
4. Press and hold the **Talk** button to speak
5. Release the button — PersonaPlex processes and responds with voice

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
| `MOSHI_PORT` | `8998` | Moshi backend server port |
| `APP_HOST` | `0.0.0.0` | Web server bind address |
| `DEFAULT_VOICE` | `NATF2` | Default voice prompt |
| `DEFAULT_PERSONA` | *teacher prompt* | Default persona text |
| `CPU_OFFLOAD` | `false` | Enable CPU offloading for low VRAM |

## Architecture

```
Browser (http://localhost:8010)
        │
        │  Fetch /api/config (voices, personas, settings)
        │  WebSocket /ws/logs (real-time log streaming)
        │
    FastAPI Server (app.py, port 8010)
        │  Manages moshi subprocess lifecycle
        │  Serves web UI and configuration API
        │
        ├── Moshi Backend (port 8998, HTTPS)
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

## License

The PersonaPlex code is released under the **MIT License**. The model weights are released under the **NVIDIA Open Model License**.
