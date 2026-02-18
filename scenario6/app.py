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
import ssl as ssl_module
import time
from urllib.parse import urlparse, quote as url_quote
from pathlib import Path

import aiohttp
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
APP_PORT = int(os.getenv("APP_PORT", "8010"))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
MOSHI_HOST = os.getenv("MOSHI_HOST", "localhost")
MOSHI_PORT = int(os.getenv("MOSHI_PORT", "8998"))
MOSHI_WS_SCHEME = os.getenv("MOSHI_WS_SCHEME", "wss")
MOSHI_WS_URL = os.getenv("MOSHI_WS_URL", "")
MOSHI_WS_PATH = "/api/chat"

if MOSHI_WS_URL:
    parsed = urlparse(MOSHI_WS_URL)
    if parsed.scheme:
        if parsed.scheme == "https":
            MOSHI_WS_SCHEME = "wss"
        elif parsed.scheme == "http":
            MOSHI_WS_SCHEME = "ws"
        else:
            MOSHI_WS_SCHEME = parsed.scheme
    if parsed.hostname:
        MOSHI_HOST = parsed.hostname
    if parsed.port:
        MOSHI_PORT = parsed.port
    if parsed.path and parsed.path != "/":
        MOSHI_WS_PATH = parsed.path
    MOSHI_WS_URL = f"{MOSHI_WS_SCHEME}://{MOSHI_HOST}:{MOSHI_PORT}{MOSHI_WS_PATH}"
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "NATF2")
DEFAULT_PERSONA = os.getenv(
    "DEFAULT_PERSONA",
    "You are a wise and friendly teacher. Answer questions or provide advice in a clear and engaging way.",
)
MOSHI_VERSION_PATH = Path(__file__).parent / "third_party" / "moshi" / "MOSHI_VERSION"
MOSHI_VERSION = MOSHI_VERSION_PATH.read_text(encoding="utf-8").strip() if MOSHI_VERSION_PATH.exists() else ""
# ---------------------------------------------------------------------------
# Warn if HF_TOKEN is missing (backend might still be external)
# ---------------------------------------------------------------------------
if not HF_TOKEN or HF_TOKEN == "hf_your_token_here":
    logger.warning(
        "HF_TOKEN is not configured. This frontend can still run, but the "
        "moshi backend may require a valid token."
    )

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


def _probe_otlp_endpoint(endpoint: str, timeout: float = 2.0) -> bool:
    """Return True if the OTLP collector is reachable (any HTTP response counts)."""
    import urllib.error
    import urllib.request
    from urllib.parse import urlparse

    parsed = urlparse(endpoint)
    probe_url = f"{parsed.scheme}://{parsed.netloc}/"
    try:
        urllib.request.urlopen(
            urllib.request.Request(probe_url, method="HEAD"), timeout=timeout
        )
        return True
    except urllib.error.HTTPError:
        # Any HTTP error (404, 405, …) means the server is alive
        return True
    except Exception as exc:
        logger.debug("OTLP probe failed (%s): %s", probe_url, exc)
        return False


def setup_telemetry(app: FastAPI) -> None:
    """Enable OpenTelemetry only when the OTLP endpoint is reachable at startup.

    If the endpoint is down (e.g. Aspire dashboard not running), telemetry is
    silently disabled so the synchronous OTLP exporter never blocks the asyncio
    event loop and causes WebSocket disconnections.
    """
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return

    if not _probe_otlp_endpoint(endpoint):
        logger.warning(
            "OTLP endpoint %s is unreachable — OpenTelemetry disabled to "
            "prevent WebSocket disconnections during audio streaming.",
            endpoint,
        )
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        service_name = os.getenv("OTEL_SERVICE_NAME", "scenario6-frontend")
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        # Short export timeout as defence-in-depth: spans are dropped rather
        # than blocking the event loop if the collector becomes unavailable
        # after startup.
        processor = BatchSpanProcessor(
            OTLPSpanExporter(endpoint=endpoint),
            export_timeout_millis=2000,
        )
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
        logger.info("OpenTelemetry enabled → %s", endpoint)
    except Exception as exc:
        logger.warning("OpenTelemetry setup failed: %s", exc)


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
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="PersonaPlex Voice Conversation")
setup_telemetry(app)

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static",
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index():
    return (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "moshi_backend": "external",
        "moshi_host": MOSHI_HOST,
        "moshi_port": MOSHI_PORT,
    }


@app.get("/api/info")
async def info():
    return {
        "service": "scenario6-frontend",
        "moshi_ws_url": MOSHI_WS_URL or f"{MOSHI_WS_SCHEME}://{MOSHI_HOST}:{MOSHI_PORT}{MOSHI_WS_PATH}",
        "moshi_version": MOSHI_VERSION,
    }


@app.get("/api/config")
async def get_config():
    """Return configuration for the frontend."""
    return {
        "moshi_host": MOSHI_HOST,
        "moshi_port": MOSHI_PORT,
        "moshi_ws_scheme": MOSHI_WS_SCHEME,
        "moshi_ws_url": MOSHI_WS_URL or f"{MOSHI_WS_SCHEME}://{MOSHI_HOST}:{MOSHI_PORT}{MOSHI_WS_PATH}",
        "moshi_version": MOSHI_VERSION,
        "voices": VOICES,
        "persona_presets": PERSONA_PRESETS,
        "default_voice": DEFAULT_VOICE,
        "default_persona": DEFAULT_PERSONA,
        "moshi_backend_running": None,
        "moshi_backend_status": "External",
    }


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
# WebSocket proxy — tunnels browser WSS → moshi WS/WSS backend
# Solves mixed-content: the browser page is HTTPS, moshi runs plain HTTP.
# The proxy is same-origin so the browser upgrade always succeeds.
# ---------------------------------------------------------------------------
@app.websocket("/proxy/moshi")
async def ws_moshi_proxy(ws_client: WebSocket):
    voice_prompt = ws_client.query_params.get("voice_prompt", "NATF2.pt")
    text_prompt = ws_client.query_params.get("text_prompt", "")

    await ws_client.accept()

    # Build backend URL (use aiohttp-compatible scheme)
    backend_scheme = "wss" if MOSHI_WS_SCHEME in ("wss", "https") else "ws"
    backend_url = (
        f"{backend_scheme}://{MOSHI_HOST}:{MOSHI_PORT}{MOSHI_WS_PATH}"
        f"?voice_prompt={url_quote(voice_prompt)}"
        f"&text_prompt={url_quote(text_prompt)}"
    )
    log_and_broadcast(f"Proxy → {backend_url}")

    # Build SSL context for self-signed certs (accept all)
    connector_ssl: bool | ssl_module.SSLContext = False
    if backend_scheme == "wss":
        ctx = ssl_module.SSLContext(ssl_module.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl_module.CERT_NONE
        connector_ssl = ctx

    stop_event = asyncio.Event()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(backend_url, ssl=connector_ssl) as ws_backend:
                log_and_broadcast("Proxy: backend connected")

                async def client_to_backend():
                    try:
                        while not stop_event.is_set():
                            try:
                                raw = await asyncio.wait_for(ws_client.receive(), timeout=60.0)
                                if raw.get("type") == "websocket.disconnect":
                                    break
                                if raw.get("bytes"):
                                    await ws_backend.send_bytes(raw["bytes"])
                            except asyncio.TimeoutError:
                                continue
                            except Exception:
                                break
                    finally:
                        stop_event.set()
                        await ws_backend.close()

                async def backend_to_client():
                    try:
                        async for msg in ws_backend:
                            if stop_event.is_set():
                                break
                            if msg.type == aiohttp.WSMsgType.BINARY:
                                await ws_client.send_bytes(msg.data)
                            elif msg.type in (
                                aiohttp.WSMsgType.CLOSE,
                                aiohttp.WSMsgType.CLOSED,
                                aiohttp.WSMsgType.ERROR,
                            ):
                                log_and_broadcast("Proxy: backend closed", level="WARN")
                                break
                    finally:
                        stop_event.set()

                await asyncio.gather(
                    client_to_backend(),
                    backend_to_client(),
                    return_exceptions=True,
                )
    except Exception as exc:
        log_and_broadcast(f"Proxy error: {exc}", level="ERROR")
    finally:
        log_and_broadcast("Proxy: session ended")
        try:
            await ws_client.close()
        except Exception:
            pass


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

    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
