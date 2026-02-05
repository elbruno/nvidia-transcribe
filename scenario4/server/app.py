"""
FastAPI server for NVIDIA ASR transcription service.
Provides REST API endpoints for audio transcription using the Parakeet model.
"""

import os
import shutil
import tempfile
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from enum import Enum

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
# Enable huggingface_hub progress logging (if available)
try:
    from huggingface_hub import logging as hf_logging
    hf_logging.set_verbosity_info()
    if hasattr(hf_logging, 'enable_progress_bars'):
        hf_logging.enable_progress_bars()
except (ImportError, AttributeError):
    pass  # Older versions may not have these functions

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

# Job management storage
jobs: Dict[str, 'JobInfo'] = {}


class JobStatus(str, Enum):
    """Status of a transcription job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobInfo(BaseModel):
    """Information about a transcription job."""
    job_id: str
    status: JobStatus
    filename: str
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional['TranscriptionResponse'] = None


class JobStartResponse(BaseModel):
    """Response when starting a new job."""
    job_id: str
    status: JobStatus
    message: str


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


async def process_transcription_job(job_id: str, audio_path: Path, filename: str):
    """
    Process a transcription job in the background.
    Updates job status and stores results.
    """
    temp_wav = None
    
    try:
        # Update status to processing
        jobs[job_id].status = JobStatus.PROCESSING
        
        # Convert to WAV if needed
        file_ext = audio_path.suffix.lower()
        if file_ext != '.wav':
            temp_wav = convert_to_wav(audio_path)
            if temp_wav is None:
                raise Exception("Audio conversion failed")
            process_path = temp_wav
        else:
            process_path = audio_path
        
        # Transcribe
        print(f"[Job {job_id}] Transcribing: {filename}")
        output = asr_model.transcribe([str(process_path)], timestamps=True)
        
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
        
        # Store result
        result = TranscriptionResponse(
            text=text,
            segments=segments,
            filename=filename,
            timestamp=datetime.now().isoformat()
        )
        
        jobs[job_id].status = JobStatus.COMPLETED
        jobs[job_id].completed_at = datetime.now().isoformat()
        jobs[job_id].result = result
        
        print(f"[Job {job_id}] Completed successfully")
        
    except Exception as e:
        print(f"[Job {job_id}] Failed: {str(e)}")
        jobs[job_id].status = JobStatus.FAILED
        jobs[job_id].completed_at = datetime.now().isoformat()
        jobs[job_id].error = str(e)
    
    finally:
        # Cleanup temporary files
        cleanup_file(audio_path)
        if temp_wav:
            cleanup_file(temp_wav)


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
            "transcribe": "/transcribe (POST) - Synchronous transcription",
            "transcribe_async": "/transcribe/async (POST) - Start async job",
            "job_status": "/jobs/{job_id}/status (GET) - Check job status",
            "job_result": "/jobs/{job_id}/result (GET) - Get job result",
            "job_cancel": "/jobs/{job_id}/cancel (POST) - Cancel job"
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


@app.post("/transcribe/async", response_model=JobStartResponse)
async def transcribe_audio_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Start an asynchronous transcription job.
    
    Args:
        file: Audio file (WAV, MP3, or FLAC)
    
    Returns:
        JobStartResponse with job_id to track the job
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
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    try:
        # Save uploaded file to temporary location
        temp_upload = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        with open(temp_upload.name, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        temp_upload_path = Path(temp_upload.name)
        
        # Create job info
        job_info = JobInfo(
            job_id=job_id,
            status=JobStatus.PENDING,
            filename=file.filename,
            created_at=datetime.now().isoformat()
        )
        jobs[job_id] = job_info
        
        # Start background processing
        background_tasks.add_task(
            process_transcription_job,
            job_id,
            temp_upload_path,
            file.filename
        )
        
        print(f"[Job {job_id}] Started for file: {file.filename}")
        
        return JobStartResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message=f"Transcription job started for {file.filename}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start job: {str(e)}")


@app.get("/jobs/{job_id}/status", response_model=JobInfo)
async def get_job_status(job_id: str):
    """
    Get the status of a transcription job.
    
    Args:
        job_id: The unique job identifier
    
    Returns:
        JobInfo with current status and details
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]


@app.get("/jobs/{job_id}/result", response_model=TranscriptionResponse)
async def get_job_result(job_id: str):
    """
    Get the result of a completed transcription job.
    
    Args:
        job_id: The unique job identifier
    
    Returns:
        TranscriptionResponse with transcription text and timestamps
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job.status == JobStatus.PENDING or job.status == JobStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="Job not yet completed")
    
    if job.status == JobStatus.FAILED:
        raise HTTPException(status_code=500, detail=f"Job failed: {job.error}")
    
    if job.status == JobStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Job was cancelled")
    
    if job.result is None:
        raise HTTPException(status_code=500, detail="Job completed but result not available")
    
    return job.result


@app.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """
    Cancel a transcription job.
    
    Args:
        job_id: The unique job identifier
    
    Returns:
        Message confirming cancellation
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel job with status: {job.status}"
        )
    
    # Mark as cancelled
    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.now().isoformat()
    
    print(f"[Job {job_id}] Cancelled")
    
    return {"message": f"Job {job_id} cancelled", "status": job.status}


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
