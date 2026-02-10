# Scenario 5 — Real-Time Voice Agent

A real-time, web-based voice agent powered by **local NVIDIA NeMo models**. Speak into your microphone, get an instant transcription via state-of-the-art ASR, and hear the response played back through neural TTS — all running on your own hardware.

> **Source**: Adapted from [elbruno/nvidia-voiceagent](https://github.com/elbruno/nvidia-voiceagent) (MIT License).

## Features

- **Real-time voice interaction** via WebSocket streaming
- **Speech-to-Text** using NVIDIA Parakeet-TDT-0.6B-V2
- **Text-to-Speech** using NVIDIA FastPitch + HiFiGAN
- **Smart Mode toggle** — switch between echo mode and LLM-powered smart responses (TinyLlama-1.1B-Chat)
- **Live server log** — real-time log panel in the browser with auto-scroll
- **User transcript display** — see what you said as a text bubble after ASR
- **Browser-based UI** — no client installation required
- **Fully local** — no cloud API calls, all inference runs on your hardware

## Models

| Task | Model | Parameters | Description |
|------|-------|-----------|-------------|
| Speech-to-Text (ASR) | Parakeet-TDT-0.6B-V2 | 600M | English ASR with Token-and-Duration Transducer |
| Text-to-Speech (Spectrogram) | FastPitch | 45M | Parallel text-to-spectrogram model |
| Text-to-Speech (Vocoder) | HiFiGAN | 14M | Neural vocoder for natural-sounding waveforms |
| Smart Mode (LLM) | TinyLlama-1.1B-Chat | 1.1B | Compact chat LLM loaded in 4-bit quantisation (~0.7 GB VRAM) |

## Prerequisites

- **Python** 3.10–3.12 (Python 3.13 is NOT supported)
- **NVIDIA GPU** with CUDA support (recommended for real-time performance)
- **CUDA Toolkit** installed and configured
- **~5 GB VRAM** minimum (ASR + TTS + Smart Mode LLM); ~4 GB without Smart Mode

## Setup

```bash
# From the repo root, activate the venv
venv\Scripts\activate   # Windows

# Install PyTorch with CUDA first
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Windows: install pynini stub (required before nemo_toolkit)
pip install ./scenario5/pynini_stub

# Install scenario 5 dependencies
pip install -r scenario5/requirements.txt

# Run the lhotse compatibility fix
python fix_lhotse.py
```

## Usage

```bash
python scenario5/app.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

> **Note:** The first request will download and cache the NVIDIA NeMo models (~2–3 GB). Subsequent starts will be faster.

### Voice Interaction

1. Click and hold the **Hold to Talk** button to record your voice
2. Release the button to send audio to the server
3. The ASR model transcribes your speech — you'll see a text bubble showing what you said
4. The TTS model generates an audio response that plays automatically

### Smart Mode

Toggle **Smart Mode** in the top-right corner:

- **Off (default)**: Echo mode — the agent responds with "You just said: [your words]" with audio playback
- **On**: Smart mode — your speech is processed by a local LLM (TinyLlama-1.1B-Chat, 4-bit) that generates a conversational reply, which is then spoken back via TTS

Smart Mode maintains a rolling conversation history (last 10 turns) so the LLM has context across exchanges.

### Server Log

The bottom panel shows a real-time server log with timestamped entries, color-coded levels (INFO, WARN, ERROR), auto-scrolling, and a collapsible panel.

## How It Works

1. **Recording**: Browser captures audio via MediaRecorder API
2. **Encoding**: Audio is converted to 16kHz WAV in the browser
3. **Streaming**: WAV audio is sent to the FastAPI server via WebSocket
4. **ASR**: Parakeet-TDT-0.6B-V2 transcribes speech to text
5. **Transcript Display**: The transcript is sent back immediately as a user text bubble
6. **Smart Mode (optional)**: If enabled, TinyLlama-1.1B-Chat generates a conversational response
7. **TTS**: FastPitch generates a mel spectrogram from the response, HiFiGAN converts it to audio
8. **Playback**: Audio response is base64-encoded and played in the browser

## Architecture

```
Browser (mic / speaker)
        │
        │  WebSocket
        │  ├── binary audio ↑ (WAV)
        │  ├── config ↑ (JSON: type=config, smart_mode)
        │  ├── transcript ↓ (JSON: type=transcript)
        │  ├── thinking ↓ (JSON: type=thinking)
        │  └── response ↓ (JSON: type=response + base64 audio)
        │
   FastAPI Server (app.py)
        ├── /ws/voice   — Voice interaction pipeline
        │   ├── Parakeet-TDT-0.6B-V2  →  Speech-to-Text (ASR)
        │   ├── TinyLlama-1.1B-Chat   →  Smart Mode LLM (optional)
        │   └── FastPitch + HiFiGAN   →  Text-to-Speech (TTS)
        ├── /ws/logs    — Real-time log streaming
        └── /health     — Health check endpoint
```

## Project Structure

```
scenario5/
├── app.py                # FastAPI server with ASR/TTS/LLM pipeline
├── static/
│   └── index.html        # Browser UI (recording, chat, log panel)
├── pynini_stub/          # Windows compatibility stub for pynini
│   ├── setup.py
│   └── pynini/
│       └── __init__.py
├── requirements.txt      # Python dependencies
└── README.md
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `pynini` build fails on Windows | Install the stub first: `pip install ./scenario5/pynini_stub` |
| `TypeError: object.__init__()` during ASR | The app includes an automatic lhotse/torch compatibility patch |
| TTS fails with `Normalizer` import error | The app patches FastPitch to skip text normalization on Windows |
| CUDA not available warnings | Works on CPU but will be slower; install CUDA for GPU acceleration |
| `bitsandbytes` install fails on Windows | Use `pip install bitsandbytes` (v0.42+ ships Windows wheels) |

## License

The original [nvidia-voiceagent](https://github.com/elbruno/nvidia-voiceagent) is licensed under the **MIT License**.
Parakeet-TDT-0.6B-V2 allows commercial use. TinyLlama-1.1B-Chat is Apache-2.0 licensed.
