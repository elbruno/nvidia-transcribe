"""
FastAPI server for NVIDIA ASR transcription service.
Provides REST API endpoints for audio transcription using the Parakeet model.
"""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

# Enable Hugging Face download progress in logs
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"  # Use standard download with progress
os.environ["TQDM_DISABLE"] = "0"  # Ensure tqdm progress bars are enabled

import logging
# Configure logging to show Hugging Face download progress
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
hf_logger = logging.getLogger("huggingface_hub")
hf_logger.setLevel(logging.INFO)

import librosa
import nemo.collections.asr as nemo_asr
import soundfile as sf
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from huggingface_hub import logging as hf_logging

# Enable huggingface_hub progress logging
hf_logging.set_verbosity_info()
hf_logging.enable_progress_bars()

# Constants
MODEL_NAME = "nvidia/parakeet-tdt-0.6b-v2"
TARGET_SAMPLE_RATE = 16000
AUDIO_EXTENSIONS = {'.wav', '.mp3', '.flac'}

app = FastAPI(
    title="NVIDIA ASR Transcription API",
    description="Audio transcription service using NVIDIA Parakeet model",
    version="1.0.0"
)

# Enable CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance (loaded on startup)
asr_model = None


class TranscriptionResponse(BaseModel):
    """Response model for transcription results."""
    text: str
    segments: list[dict]
    filename: str
    timestamp: str


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    model_loaded: bool
    model_name: str


def convert_to_wav(audio_path: Path) -> Optional[Path]:
    """
    Convert MP3/FLAC to 16kHz mono WAV if needed.
    Returns path to WAV file (original or converted temp file).
    """
    if audio_path.suffix.lower() == '.wav':
        return audio_path
    
    try:
        # Load audio and convert to 16kHz mono
        audio, sr = librosa.load(str(audio_path), sr=TARGET_SAMPLE_RATE, mono=True)
        
        # Create temp WAV file
        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        sf.write(temp_wav.name, audio, TARGET_SAMPLE_RATE)
        temp_wav.close()
        
        return Path(temp_wav.name)
    except Exception as e:
        print(f"Error converting audio: {e}")
        return None


def cleanup_file(file_path: Path):
    """Remove temporary file."""
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        print(f"Error cleaning up file {file_path}: {e}")


@app.on_event("startup")
async def load_model():
    """Load the ASR model on server startup."""
    global asr_model
    try:
        print(f"=" * 60, flush=True)
        print(f"Starting model download: {MODEL_NAME}", flush=True)
        print(f"This may take several minutes on first run (~1.2GB download)", flush=True)
        print(f"=" * 60, flush=True)
        
        # Model automatically uses GPU if available, falls back to CPU
        # PyTorch/NeMo will detect CUDA and use GPU without explicit configuration
        asr_model = nemo_asr.models.ASRModel.from_pretrained(MODEL_NAME)
        
        # Check if GPU is being used
        device = next(asr_model.parameters()).device
        print(f"=" * 60, flush=True)
        print(f"Model loaded successfully on device: {device}", flush=True)
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)
        else:
            print("Running on CPU (GPU not available)", flush=True)
        print(f"Server is ready to accept requests!", flush=True)
        print(f"=" * 60, flush=True)
    except Exception as e:
        print(f"Error loading model: {e}", flush=True)
        raise


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "service": "NVIDIA ASR Transcription API",
        "version": "1.0.0",
        "model": MODEL_NAME,
        "endpoints": {
            "health": "/health",
            "transcribe": "/transcribe (POST)"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if asr_model is not None else "model_not_loaded",
        model_loaded=asr_model is not None,
        model_name=MODEL_NAME
    )


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Transcribe an audio file.
    
    Args:
        file: Audio file (WAV, MP3, or FLAC)
    
    Returns:
        TranscriptionResponse with text and timestamps
    """
    if asr_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported: {', '.join(AUDIO_EXTENSIONS)}"
        )
    
    temp_upload = None
    temp_wav = None
    
    try:
        # Save uploaded file to temporary location
        temp_upload = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        with open(temp_upload.name, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        temp_upload_path = Path(temp_upload.name)
        
        # Convert to WAV if needed
        if file_ext != '.wav':
            temp_wav = convert_to_wav(temp_upload_path)
            if temp_wav is None:
                raise HTTPException(status_code=500, detail="Audio conversion failed")
            audio_path = temp_wav
        else:
            audio_path = temp_upload_path
        
        # Transcribe
        print(f"Transcribing: {file.filename}")
        output = asr_model.transcribe([str(audio_path)], timestamps=True)
        
        # Extract text and segments
        text = output[0].text
        segments = []
        
        if hasattr(output[0], 'timestamp') and output[0].timestamp:
            timestamp_data = output[0].timestamp
            if isinstance(timestamp_data, dict) and 'segment' in timestamp_data:
                for seg in timestamp_data['segment']:
                    segments.append({
                        'start': seg[0],
                        'end': seg[1],
                        'text': seg[2] if len(seg) > 2 else ''
                    })
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_file, temp_upload_path)
        if temp_wav:
            background_tasks.add_task(cleanup_file, temp_wav)
        
        return TranscriptionResponse(
            text=text,
            segments=segments,
            filename=file.filename,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Cleanup on error
        if temp_upload:
            cleanup_file(Path(temp_upload.name))
        if temp_wav:
            cleanup_file(temp_wav)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
