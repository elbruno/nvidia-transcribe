"""NVIDIA Voice Agent — FastAPI server with WebSocket audio streaming."""

import io
import json
import re
import asyncio
import base64
import logging
import time
import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# GPU / CUDA detection
# ---------------------------------------------------------------------------
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
if DEVICE == "cuda":
    _gpu_name = torch.cuda.get_device_name(0)
    _gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    logger.info(f"CUDA available — {_gpu_name} ({_gpu_mem:.1f} GB)")
else:
    logger.warning("CUDA is NOT available — running on CPU (slow). "
                   "Install torch+cu128: pip install torch --index-url https://download.pytorch.org/whl/cu128")

# ---------------------------------------------------------------------------
# Monkey-patch: fix lhotse / torch Sampler incompatibility
# In torch >=2.10, Sampler.__init__() no longer accepts data_source arg.
# ---------------------------------------------------------------------------
try:
    import lhotse.dataset.sampling.base as _lhotse_base
    _orig_init = _lhotse_base.CutSampler.__init__

    def _patched_cut_sampler_init(self, *args, **kwargs):
        try:
            _orig_init(self, *args, **kwargs)
        except TypeError:
            # Strip the problematic super().__init__ call's extra args
            import torch.utils.data
            torch.utils.data.Sampler.__init__(self)
            # Re-run but skip the super().__init__ by temporarily patching it
            _saved = torch.utils.data.Sampler.__init__
            torch.utils.data.Sampler.__init__ = lambda self, *a, **kw: None
            try:
                _orig_init(self, *args, **kwargs)
            finally:
                torch.utils.data.Sampler.__init__ = _saved

    _lhotse_base.CutSampler.__init__ = _patched_cut_sampler_init
    logger.info("Applied lhotse CutSampler compatibility patch for torch >=2.10")
except Exception:
    pass  # lhotse not installed or structure changed

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
    if detail:
        logger.debug(detail)
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(broadcast_log(message, level, detail))
    except RuntimeError:
        pass  # no event loop yet (startup)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="NVIDIA Voice Agent")

# Serve static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# ---------------------------------------------------------------------------
# Model loading (lazy, on first request)
# ---------------------------------------------------------------------------
asr_model = None
tts_spec_gen = None
tts_vocoder = None


def get_asr_model():
    """Load NVIDIA Parakeet-TDT-0.6B-V2 for speech-to-text."""
    global asr_model
    if asr_model is None:
        import nemo.collections.asr as nemo_asr
        log_and_broadcast("Loading Parakeet ASR model\u2026")
        asr_model = nemo_asr.models.ASRModel.from_pretrained("nvidia/parakeet-tdt-0.6b-v2")
        if DEVICE == "cuda":
            asr_model = asr_model.cuda()
        asr_model.eval()
        log_and_broadcast(f"Parakeet ASR model loaded on {DEVICE.upper()}.")
    return asr_model


def get_tts_models():
    """Load NVIDIA FastPitch + HiFiGAN for text-to-speech."""
    global tts_spec_gen, tts_vocoder
    if tts_spec_gen is None:
        from nemo.collections.tts.models import FastPitchModel, HifiGanModel

        # Patch: skip text normalizer if pynini is unavailable (Windows)
        _orig_setup = FastPitchModel._setup_normalizer

        def _safe_setup_normalizer(self, cfg):
            try:
                _orig_setup(cfg)
            except Exception:
                log_and_broadcast("Text normalizer unavailable (pynini stub) — skipping", "WARN")
                self.normalizer = None
                self.text_normalizer_call = None
                self.text_normalizer_call_kwargs = {}

        FastPitchModel._setup_normalizer = _safe_setup_normalizer

        log_and_broadcast("Loading FastPitch + HiFiGAN TTS models\u2026")
        tts_spec_gen = FastPitchModel.from_pretrained("nvidia/tts_en_fastpitch")
        tts_vocoder = HifiGanModel.from_pretrained("nvidia/tts_hifigan")
        if DEVICE == "cuda":
            tts_spec_gen = tts_spec_gen.cuda()
            tts_vocoder = tts_vocoder.cuda()
        tts_spec_gen.eval()
        tts_vocoder.eval()
        log_and_broadcast(f"TTS models loaded on {DEVICE.upper()}.")
    return tts_spec_gen, tts_vocoder


# ---------------------------------------------------------------------------
# LLM for Smart Mode (multi-model, 4-bit quantised)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a voice assistant. Answer in ONE short sentence only. "
    "Never exceed 15 words. Be direct and concise."
)

LLM_CATALOGUE: dict[str, str] = {
    "tinyllama": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "phi3": "microsoft/Phi-3-mini-4k-instruct",
}

# Cache: model_key -> (model, tokenizer)
_llm_cache: dict[str, tuple] = {}


def get_llm(model_key: str = "tinyllama"):
    """Load the requested LLM with 4-bit quantisation. Cached after first load."""
    if model_key in _llm_cache:
        return _llm_cache[model_key]

    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    model_id = LLM_CATALOGUE.get(model_key, LLM_CATALOGUE["tinyllama"])
    log_and_broadcast(f"Loading {model_id} (4-bit) on {DEVICE.upper()}\u2026")

    if DEVICE == "cuda":
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map="auto",
            attn_implementation="eager",
        )
    else:
        # CPU fallback — no quantisation (bitsandbytes requires CUDA)
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float32,
            device_map="cpu",
            attn_implementation="eager",
        )
    model.eval()
    log_and_broadcast(f"{model_id} loaded on {next(model.parameters()).device}.")
    _llm_cache[model_key] = (model, tokenizer)
    return model, tokenizer


def generate_response(
    transcript: str, history: list[dict], model_key: str = "tinyllama"
) -> str:
    """Run the selected LLM on *transcript* with conversation *history*."""
    model, tokenizer = get_llm(model_key)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": transcript})

    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=60,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )

    # Decode only the new tokens
    new_tokens = output_ids[0][inputs["input_ids"].shape[1]:]
    response = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    return _sanitize_for_tts(response)


def _sanitize_for_tts(text: str) -> str:
    """Clean LLM output so it is safe for the TTS model.

    - Collapse to a single line
    - Strip numbered-list prefixes (1. 2. etc.)
    - Remove characters the vocoder cannot pronounce
    - Truncate to the first two sentences to keep audio short
    """
    # Collapse whitespace / newlines
    text = re.sub(r"\s+", " ", text).strip()
    # Remove list-item prefixes like "1." "2."
    text = re.sub(r"\b\d+\.\s*", "", text)
    # Remove characters TTS cannot handle
    text = re.sub(r"[^a-zA-Z0-9 .,!?;:'\"-]", "", text)
    # Keep at most two sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)
    text = " ".join(sentences[:2]).strip()
    return text if text else "Sorry, I could not generate a response."


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index():
    return (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# WebSocket endpoint for log streaming
# ---------------------------------------------------------------------------
@app.websocket("/ws/logs")
async def logs_ws(ws: WebSocket):
    await ws.accept()
    log_clients.add(ws)
    try:
        while True:
            await ws.receive_text()  # keep alive
    except (WebSocketDisconnect, RuntimeError):
        log_clients.discard(ws)


# ---------------------------------------------------------------------------
# WebSocket endpoint for voice interaction
# ---------------------------------------------------------------------------
@app.websocket("/ws/voice")
async def voice_ws(ws: WebSocket):
    await ws.accept()
    log_and_broadcast("WebSocket client connected")
    smart_mode = False
    smart_model = "tinyllama"
    chat_history: list[dict] = []
    try:
        while True:
            msg = await ws.receive()

            # Handle text frames (config messages)
            if "text" in msg:
                try:
                    payload = json.loads(msg["text"])
                    if payload.get("type") == "config":
                        smart_mode = payload.get("smart_mode", False)
                        smart_model = payload.get("smart_model", "tinyllama")
                        log_and_broadcast(
                            f"Smart Mode {'enabled' if smart_mode else 'disabled'}"
                            f" | model={smart_model}"
                        )
                    elif payload.get("type") == "clear_history":
                        chat_history.clear()
                        log_and_broadcast("Chat history cleared (models remain loaded)")
                except (json.JSONDecodeError, TypeError):
                    pass
                continue

            data = msg.get("bytes", b"")
            if not data:
                continue

            log_and_broadcast(
                f"Received {len(data)} bytes of audio",
                detail=f"sample_rate: will be resampled to 16 kHz\nraw size: {len(data):,} bytes",
            )

            # --- ASR: speech → text ---
            audio_array, sample_rate = sf.read(io.BytesIO(data))
            if audio_array.ndim > 1:
                audio_array = audio_array.mean(axis=1)  # mono
            if sample_rate != 16000:
                from scipy.signal import resample
                num_samples = int(len(audio_array) * 16000 / sample_rate)
                audio_array = resample(audio_array, num_samples)
                sample_rate = 16000

            tmp_buf = io.BytesIO()
            sf.write(tmp_buf, audio_array, sample_rate, format="WAV")
            tmp_buf.seek(0)
            import tempfile, os
            tmp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_file.write(tmp_buf.read())
            tmp_file.flush()
            tmp_path = tmp_file.name
            tmp_file.close()

            try:
                log_and_broadcast("Running ASR inference\u2026")
                model = get_asr_model()
                hypotheses = model.transcribe([tmp_path], batch_size=1)
                transcript = hypotheses[0].text if hasattr(hypotheses[0], "text") else str(hypotheses[0])
            except Exception as e:
                log_and_broadcast(f"ASR error: {e}", "ERROR")
                transcript = ""
            finally:
                os.unlink(tmp_path)

            log_and_broadcast(
                f"Transcript: {transcript}",
                detail=f"model: Parakeet-TDT-0.6B-V2\nraw hypotheses: {hypotheses[0] if hypotheses else 'none'}",
            )

            # Send user transcript immediately (before TTS)
            await ws.send_json({
                "type": "transcript",
                "transcript": transcript,
            })

            # --- Smart Mode: generate LLM response ---
            if smart_mode and transcript.strip():
                log_and_broadcast(
                    "Running LLM inference (Smart Mode)\u2026",
                    detail=f"model: {smart_model} ({LLM_CATALOGUE.get(smart_model, '?')})\nhistory turns: {len(chat_history) // 2}\ntranscript: {transcript}",
                )
                await ws.send_json({"type": "thinking"})
                try:
                    response_text = await asyncio.get_running_loop().run_in_executor(
                        None, generate_response, transcript, list(chat_history), smart_model
                    )
                    # Update conversation history (keep last 10 turns)
                    chat_history.append({"role": "user", "content": transcript})
                    chat_history.append({"role": "assistant", "content": response_text})
                    if len(chat_history) > 20:  # 10 turns × 2 messages
                        chat_history = chat_history[-20:]
                    log_and_broadcast(
                        f"LLM response: {response_text}",
                        detail=f"model: {smart_model}\nraw length: {len(response_text)} chars\nhistory: {len(chat_history) // 2 + 1} turns",
                    )
                except Exception as e:
                    log_and_broadcast(f"LLM error: {e}", "ERROR")
                    response_text = transcript  # fall back to echo
            else:
                response_text = transcript

            # --- TTS: text → speech ---
            if response_text.strip():
                log_and_broadcast("Running TTS inference\u2026")
                spec_gen, vocoder = get_tts_models()
                with torch.no_grad():
                    parsed = spec_gen.parse(response_text)
                    spectrogram = spec_gen.generate_spectrogram(tokens=parsed)
                    audio_out = vocoder.convert_spectrogram_to_audio(spec=spectrogram)

                audio_np = audio_out.cpu().numpy()[0]
                wav_buf = io.BytesIO()
                sf.write(wav_buf, audio_np, 22050, format="WAV")
                wav_buf.seek(0)
                audio_b64 = base64.b64encode(wav_buf.read()).decode("utf-8")
                log_and_broadcast(
                    f"TTS audio generated: {len(audio_np)} samples",
                    detail=f"duration: {len(audio_np) / 22050:.1f}s @ 22050 Hz\ntext sent to TTS: {response_text}",
                )
            else:
                audio_b64 = ""
                log_and_broadcast("Empty response — skipping TTS", "WARN")

            await ws.send_json({
                "type": "response",
                "transcript": transcript,
                "response": response_text,
                "audio": audio_b64,
            })
            log_and_broadcast("Response sent to client")

    except (WebSocketDisconnect, RuntimeError):
        log_and_broadcast("WebSocket client disconnected")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
