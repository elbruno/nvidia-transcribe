"""Scenario 6 — PersonaPlex Real-Time Voice Conversation.

A FastAPI web app that wraps the NVIDIA PersonaPlex moshi server,
providing a beautiful web UI for full-duplex voice conversations.
The moshi backend handles the actual speech-to-speech inference;
this app provides the user-facing frontend, configuration management,
and lifecycle orchestration.
"""

import asyncio
import logging
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# Load .env configuration
# ---------------------------------------------------------------------------
_env_path = Path(__file__).parent / ".env"
load_dotenv(_env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------
HF_TOKEN = os.getenv("HF_TOKEN", "")
PERSONAPLEX_MODEL_PATH = os.getenv("PERSONAPLEX_MODEL_PATH", "")
HF_HOME = os.getenv("HF_HOME", "")
APP_PORT = int(os.getenv("APP_PORT", "8010"))
MOSHI_PORT = int(os.getenv("MOSHI_PORT", "8998"))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "NATF2")
DEFAULT_PERSONA = os.getenv(
    "DEFAULT_PERSONA",
    "You are a wise and friendly teacher. Answer questions or provide advice in a clear and engaging way.",
)
CPU_OFFLOAD = os.getenv("CPU_OFFLOAD", "false").lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------
# Validate HF_TOKEN
# ---------------------------------------------------------------------------
if not HF_TOKEN or HF_TOKEN == "hf_your_token_here":
    logger.error(
        "HF_TOKEN is not configured. Copy .env.example to .env and set your "
        "Hugging Face token. Get one at https://huggingface.co/settings/tokens"
    )
    print(
        "\n"
        "╔══════════════════════════════════════════════════════════════════╗\n"
        "║  ERROR: Hugging Face token not configured!                     ║\n"
        "║                                                                ║\n"
        "║  1. Copy .env.example to .env                                  ║\n"
        "║  2. Set HF_TOKEN=hf_your_actual_token                         ║\n"
        "║  3. Accept the model license at:                               ║\n"
        "║     https://huggingface.co/nvidia/personaplex-7b-v1            ║\n"
        "╚══════════════════════════════════════════════════════════════════╝\n",
        file=sys.stderr,
    )
    sys.exit(1)

# Export HF_TOKEN so the moshi subprocess can use it
os.environ["HF_TOKEN"] = HF_TOKEN
if HF_HOME:
    os.environ["HF_HOME"] = HF_HOME

# ---------------------------------------------------------------------------
# Available voices
# ---------------------------------------------------------------------------
VOICES = {
    "Natural Female": ["NATF0", "NATF1", "NATF2", "NATF3"],
    "Natural Male": ["NATM0", "NATM1", "NATM2", "NATM3"],
    "Variety Female": ["VARF0", "VARF1", "VARF2", "VARF3", "VARF4"],
    "Variety Male": ["VARM0", "VARM1", "VARM2", "VARM3", "VARM4"],
}

PERSONA_PRESETS = {
    "teacher": "You are a wise and friendly teacher. Answer questions or provide advice in a clear and engaging way.",
    "assistant": "You enjoy having a good conversation.",
    "customer_service": "You work for TechSupport Pro and your name is Alex. You are helpful, patient, and knowledgeable about technology products.",
    "astronaut": (
        "You enjoy having a good conversation. Have a technical discussion about "
        "fixing a reactor core on a spaceship to Mars. You are an astronaut on a "
        "Mars mission. Your name is Alex."
    ),
    "chef": (
        "You enjoy having a good conversation. Have a casual conversation about "
        "favorite foods and cooking experiences. You are a former baker now living "
        "in Boston. You enjoy cooking diverse international dishes."
    ),
}

# ---------------------------------------------------------------------------
# Real-time log broadcasting
# ---------------------------------------------------------------------------
log_clients: set[WebSocket] = set()


async def broadcast_log(message: str, level: str = "INFO", detail: str = ""):
    """Send a log entry to all connected log WebSocket clients."""
    entry = {
        "timestamp": time.strftime("%H:%M:%S"),
        "level": level,
        "message": message,
        "detail": detail,
    }
    disconnected = set()
    for client in list(log_clients):
        try:
            await client.send_json(entry)
        except Exception:
            disconnected.add(client)
    log_clients.difference_update(disconnected)


def log_and_broadcast(message: str, level: str = "INFO", detail: str = ""):
    """Log a message and schedule it to be broadcast to UI clients."""
    if level == "ERROR":
        logger.error(message)
    elif level == "WARN":
        logger.warning(message)
    else:
        logger.info(message)
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(broadcast_log(message, level, detail))
    except RuntimeError:
        pass


# ---------------------------------------------------------------------------
# Moshi backend process management
# ---------------------------------------------------------------------------
_moshi_process: subprocess.Popen | None = None
_ssl_dir: str | None = None


def _build_moshi_command() -> list[str]:
    """Build the command to launch the moshi server."""
    cmd = [sys.executable, "-m", "moshi.server"]

    # SSL is required by the moshi server
    global _ssl_dir
    _ssl_dir = tempfile.mkdtemp(prefix="personaplex_ssl_")
    cmd.extend(["--ssl", _ssl_dir])

    if CPU_OFFLOAD:
        cmd.append("--cpu-offload")

    if PERSONAPLEX_MODEL_PATH:
        model_path = Path(PERSONAPLEX_MODEL_PATH)
        if model_path.is_dir():
            logger.info(f"Using local model from: {model_path}")
        else:
            logger.warning(
                f"PERSONAPLEX_MODEL_PATH={PERSONAPLEX_MODEL_PATH} is not a valid "
                "directory — falling back to HuggingFace download."
            )

    return cmd


def start_moshi_backend():
    """Start the PersonaPlex moshi server as a subprocess."""
    global _moshi_process

    if _moshi_process and _moshi_process.poll() is None:
        logger.info("Moshi backend already running.")
        return

    cmd = _build_moshi_command()
    env = os.environ.copy()

    logger.info(f"Starting PersonaPlex moshi backend: {' '.join(cmd)}")
    logger.info(
        "The first launch will download the model (~14 GB). "
        "Subsequent starts will use the cached model."
    )

    _moshi_process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # Start a thread to read moshi output and forward to our logs
    import threading

    def _read_moshi_output():
        if _moshi_process and _moshi_process.stdout:
            for line in _moshi_process.stdout:
                line = line.rstrip()
                if line:
                    logger.info(f"[moshi] {line}")

    threading.Thread(target=_read_moshi_output, daemon=True).start()


def stop_moshi_backend():
    """Stop the moshi backend process."""
    global _moshi_process
    if _moshi_process and _moshi_process.poll() is None:
        logger.info("Stopping moshi backend…")
        _moshi_process.terminate()
        try:
            _moshi_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _moshi_process.kill()
        _moshi_process = None


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="PersonaPlex Voice Conversation")

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static",
)


@app.on_event("startup")
async def on_startup():
    log_and_broadcast("PersonaPlex Voice Conversation server starting…")
    log_and_broadcast(
        f"Moshi backend will be available at https://localhost:{MOSHI_PORT}"
    )
    start_moshi_backend()


@app.on_event("shutdown")
async def on_shutdown():
    stop_moshi_backend()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index():
    return (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/health")
async def health():
    moshi_running = _moshi_process is not None and _moshi_process.poll() is None
    return {
        "status": "ok",
        "moshi_backend": "running" if moshi_running else "stopped",
        "moshi_port": MOSHI_PORT,
    }


@app.get("/api/config")
async def get_config():
    """Return configuration for the frontend."""
    return {
        "moshi_port": MOSHI_PORT,
        "voices": VOICES,
        "persona_presets": PERSONA_PRESETS,
        "default_voice": DEFAULT_VOICE,
        "default_persona": DEFAULT_PERSONA,
        "moshi_backend_running": (
            _moshi_process is not None and _moshi_process.poll() is None
        ),
    }


@app.post("/api/restart-backend")
async def restart_backend():
    """Restart the moshi backend server."""
    stop_moshi_backend()
    await asyncio.sleep(1)
    start_moshi_backend()
    return {"status": "restarting"}


# ---------------------------------------------------------------------------
# WebSocket endpoint for log streaming
# ---------------------------------------------------------------------------
@app.websocket("/ws/logs")
async def logs_ws(ws: WebSocket):
    await ws.accept()
    log_clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except (WebSocketDisconnect, RuntimeError):
        log_clients.discard(ws)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    print(
        f"\n"
        f"╔══════════════════════════════════════════════════════════════════╗\n"
        f"║  PersonaPlex Voice Conversation                                ║\n"
        f"║  Web UI:  http://localhost:{APP_PORT:<5}                            ║\n"
        f"║  Moshi:   https://localhost:{MOSHI_PORT:<5}                           ║\n"
        f"╚══════════════════════════════════════════════════════════════════╝\n"
    )

    # Handle Ctrl+C gracefully
    def _signal_handler(sig, frame):
        stop_moshi_backend()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)

    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
