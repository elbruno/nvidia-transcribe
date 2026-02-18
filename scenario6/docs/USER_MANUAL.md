# PersonaPlex Voice Conversation — User Manual

This guide walks you through setting up and using the PersonaPlex Voice Conversation app from start to finish.

## Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Automated Setup (Recommended)](#automated-setup-recommended)
4. [Step-by-Step Setup](#step-by-step-setup)
5. [Configuring the Environment](#configuring-the-environment)
6. [Running the Application](#running-the-application)
7. [Using the Web Interface](#using-the-web-interface)
8. [Customizing Voice and Persona](#customizing-voice-and-persona)
9. [Theme System](#theme-system)
10. [Loading a Local Model](#loading-a-local-model)
11. [Troubleshooting](#troubleshooting)

---

## Overview

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

### Step 4: Install the PersonaPlex Moshi Package

```bash
# Clone the official PersonaPlex repository
git clone https://github.com/NVIDIA/personaplex.git /tmp/personaplex

# Install the moshi Python package
pip install /tmp/personaplex/moshi/.
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
| `APP_HOST` | `0.0.0.0` | Network interface to bind to |
| `DEFAULT_VOICE` | `NATF2` | Default voice (see voice list below) |
| `DEFAULT_PERSONA` | Teacher prompt | Default AI personality |
| `CPU_OFFLOAD` | `false` | Offload model layers to CPU to save GPU memory |

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

### First Launch

On the first launch, the application will:
1. Start the web UI server on port 8010
2. Start the moshi backend on port 8998
3. Download the PersonaPlex-7B-v1 model (~14 GB) from HuggingFace
4. Cache the model locally for future use

> **Tip**: The download may take 10–30 minutes depending on your internet speed. Subsequent launches will be much faster.

---

## Using the Web Interface

### Opening the App

1. Open your browser and navigate to **http://localhost:8010**

<!-- Screenshot: Main interface with dark theme showing the welcome screen -->
*The main interface shows the welcome screen, sidebar configuration, and the talk button.*

### Accepting the SSL Certificate

Before connecting, you need to accept the moshi backend's self-signed SSL certificate:

1. Open a new tab and visit **https://localhost:8998**
2. Your browser will show a security warning
3. Click **Advanced** → **Proceed to localhost** (or equivalent)
4. You can close this tab — the certificate is now accepted

<!-- Screenshot: Browser SSL warning page -->
*Accept the self-signed certificate to enable the WebSocket connection.*

### Connecting to the Backend

1. Click the **Connect** button in the bottom-right of the chat area
2. The status badge will change from "Disconnected" to "Connected" (green)
3. A system message "🟢 Connected — start speaking!" appears

<!-- Screenshot: Connected state with green status badge -->
*The status badge turns green when successfully connected.*

### Having a Conversation

1. **Press and hold** the green Talk button
2. **Speak** into your microphone
3. **Release** the button to send your audio
4. PersonaPlex processes your speech and responds with audio
5. The response plays automatically in your browser

<!-- Screenshot: Active conversation with user and agent messages -->
*Messages appear as chat bubbles — green for you, blue for PersonaPlex.*

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
| `ModuleNotFoundError: moshi` | Install the moshi package: `pip install /tmp/personaplex/moshi/.` |
| `libopus` not found | Install: `sudo apt install libopus-dev` |
| CUDA out of memory | Set `CPU_OFFLOAD=true` in `.env`, install `accelerate` |
| Very slow responses | Use a GPU; CPU mode is not practical for real-time use |
| Port 8010 in use | Change `APP_PORT` in `.env` |
| Port 8998 in use | Change `MOSHI_PORT` in `.env` |

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

If the moshi backend becomes unresponsive:
1. Click **↻ Restart** in the sidebar under "Backend"
2. Wait 5–10 seconds for the backend to restart
3. Click **Connect** again to re-establish the WebSocket connection

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
