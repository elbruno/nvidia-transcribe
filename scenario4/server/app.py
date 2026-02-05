"""
FastAPI server for NVIDIA ASR transcription service.
Provides REST API endpoints for audio transcription using the Parakeet model.
"""

import os
import shutil
import tempfile
import traceback
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from enum import Enum
import time

# Enable Hugging Face download progress in logs
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"  # Use standard download with progress
os.environ["TQDM_DISABLE"] = "0"  # Ensure tqdm progress bars are enabled

import logging
# Configure logging to show Hugging Face download progress
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
hf_logger = logging.getLogger("huggingface_hub")
hf_logger.setLevel(logging.INFO)

# Import custom NVIDIA ASR monitor
from nvidia_asr_monitor import asr_monitor

import librosa
import nemo.collections.asr as nemo_asr
import soundfile as sf
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
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
PARAKEET_MODEL = "nvidia/parakeet-tdt-0.6b-v2"
CANARY_MODEL = "nvidia/canary-1b"
TARGET_SAMPLE_RATE = 16000
AUDIO_EXTENSIONS = {'.wav', '.mp3', '.flac'}

# Supported models
SUPPORTED_MODELS = {
    'parakeet': {
        'name': PARAKEET_MODEL,
        'description': 'English-only, supports timestamps',
        'supports_languages': False,
        'supports_timestamps': True
    },
    'canary': {
        'name': CANARY_MODEL,
        'description': 'Multilingual (en, es, de, fr), no timestamps',
        'supports_languages': True,
        'supports_timestamps': False
    }
}

# Supported languages for Canary model
SUPPORTED_LANGUAGES = {'en', 'es', 'de', 'fr'}

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

# Global model instances (loaded on demand)
asr_models = {
    'parakeet': None,
    'canary': None
}
current_model_name = 'parakeet'  # Default model

# Job management storage (thread-safe with lock)
jobs: Dict[str, 'JobInfo'] = {}
jobs_lock = asyncio.Lock()


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
    model: str  # Added: which model was used
    language: Optional[str] = None  # Added: language used (for multilingual)


class TranscriptionRequest(BaseModel):
    """Request parameters for transcription (used with form data)."""
    model: str = 'parakeet'  # 'parakeet' or 'canary'
    language: Optional[str] = None  # For canary: 'en', 'es', 'de', 'fr'
    include_timestamps: bool = True  # Whether to generate timestamps
    output_format: str = 'both'  # 'txt', 'srt', or 'both'


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


async def get_or_load_model(model_key: str):
    """
    Get or load the specified model.
    Models are loaded on-demand and cached.
    """
    global asr_models
    
    if model_key not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model_key}. Supported: {list(SUPPORTED_MODELS.keys())}")
    
    # Return cached model if available
    if asr_models[model_key] is not None:
        return asr_models[model_key]
    
    # Load the model
    model_name = SUPPORTED_MODELS[model_key]['name']
    print(f"Loading model: {model_name}")
    
    try:
        model_load_start = time.time()
        asr_models[model_key] = nemo_asr.models.ASRModel.from_pretrained(model_name)
        model_load_duration = time.time() - model_load_start
        
        # Check device
        device = next(asr_models[model_key].parameters()).device
        gpu_available = torch.cuda.is_available()
        
        print(f"Model {model_key} loaded on device: {device} ({model_load_duration:.2f}s)")
        
        # Record model loading event
        asr_monitor.record_model_load(
            model_identifier=model_name,
            load_seconds=model_load_duration,
            device_name=str(device),
            gpu_detected=gpu_available
        )
        
        return asr_models[model_key]
    except Exception as e:
        print(f"Error loading model {model_key}: {e}")
        asr_monitor.record_job_error(f"model_loading_{model_key}", f"Failed to load {model_name}", e)
        raise


async def process_transcription_job(job_id: str, audio_path: Path, filename: str, 
                                   model_key: str = 'parakeet', language: Optional[str] = None,
                                   include_timestamps: bool = True):
    """
    Process a transcription job in the background.
    Updates job status and stores results.
    Checks for cancellation before starting transcription.
    
    Args:
        job_id: Unique job identifier
        audio_path: Path to audio file
        filename: Original filename
        model_key: Model to use ('parakeet' or 'canary')
        language: Language code for multilingual models ('en', 'es', 'de', 'fr')
        include_timestamps: Whether to generate timestamps
    """
    temp_wav = None
    operation_start_time = time.time()
    file_size_bytes = audio_path.stat().st_size if audio_path.exists() else 0
    
    # Record job initiation
    asr_monitor.record_job_initiated(job_id, filename, file_size_bytes)
    
    try:
        # Check if job was cancelled before starting
        async with jobs_lock:
            if jobs[job_id].status == JobStatus.CANCELLED:
                print(f"[Job {job_id}] Cancelled before processing started")
                cleanup_file(audio_path)
                return
            
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
        
        # Check cancellation again before transcription
        async with jobs_lock:
            if jobs[job_id].status == JobStatus.CANCELLED:
                print(f"[Job {job_id}] Cancelled during preprocessing")
                cleanup_file(audio_path)
                if temp_wav:
                    cleanup_file(temp_wav)
                return
        
        # Transcribe
        print(f"[Job {job_id}] Transcribing: {filename} (model={model_key}, language={language})")
        transcription_start = time.time()
        
        # Load the appropriate model
        asr_model = await get_or_load_model(model_key)
        
        # Prepare transcription parameters
        transcribe_kwargs = {}
        
        # Add language parameter for Canary model
        if model_key == 'canary' and language:
            if language not in SUPPORTED_LANGUAGES:
                raise ValueError(f"Unsupported language: {language}. Supported: {sorted(SUPPORTED_LANGUAGES)}")
            transcribe_kwargs['source_lang'] = language
        
        # Add timestamps if requested and supported
        if include_timestamps and SUPPORTED_MODELS[model_key]['supports_timestamps']:
            transcribe_kwargs['timestamps'] = True
        
        # Perform transcription
        output = asr_model.transcribe([str(process_path)], **transcribe_kwargs)
        transcription_duration_ms = (time.time() - transcription_start) * 1000
        
        # Debug: Log output structure
        print(f"[Job {job_id}] Transcription output type: {type(output)}")
        if output:
            print(f"[Job {job_id}] Output length: {len(output)}")
            if len(output) > 0:
                print(f"[Job {job_id}] Output[0] type: {type(output[0])}")
                print(f"[Job {job_id}] Output[0] attributes: {dir(output[0])}")
        
        # Check if cancelled after transcription completes
        async with jobs_lock:
            if jobs[job_id].status == JobStatus.CANCELLED:
                print(f"[Job {job_id}] Cancelled after transcription")
                cleanup_file(audio_path)
                if temp_wav:
                    cleanup_file(temp_wav)
                return
        
        # Extract text and segments with defensive handling
        if not output or len(output) == 0:
            raise Exception("Transcription returned empty output")
        
        result_item = output[0]
        
        # Handle different output formats (string vs Hypothesis object)
        if isinstance(result_item, str):
            text = result_item
            segments = []
            print(f"[Job {job_id}] Output is string: {text[:100]}...")
        elif hasattr(result_item, 'text'):
            text = result_item.text
            print(f"[Job {job_id}] Extracted text: {text[:100] if text else 'empty'}...")
        else:
            raise Exception(f"Unexpected output format: {type(result_item)}")
        
        segments = []
        
        if hasattr(result_item, 'timestamp') and result_item.timestamp:
            timestamp_data = result_item.timestamp
            if isinstance(timestamp_data, dict) and 'segment' in timestamp_data:
                for seg in timestamp_data['segment']:
                    # Handle both dict format {'start': ..., 'end': ..., 'text': ...}
                    # and list/tuple format [start, end, text]
                    if isinstance(seg, dict):
                        segments.append({
                            'start': seg.get('start', 0),
                            'end': seg.get('end', 0),
                            'text': seg.get('text', '')
                        })
                    else:
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
            timestamp=datetime.now().isoformat(),
            model=model_key,
            language=language
        )
        
        async with jobs_lock:
            jobs[job_id].status = JobStatus.COMPLETED
            jobs[job_id].completed_at = datetime.now().isoformat()
            jobs[job_id].result = result
        
        # Track successful completion metrics
        total_duration_ms = (time.time() - operation_start_time) * 1000
        text_length = len(text) if text else 0
        
        # Record successful completion with monitoring
        asr_monitor.record_job_finished(
            job_identifier=job_id,
            elapsed_milliseconds=total_duration_ms,
            input_bytes=file_size_bytes,
            output_characters=text_length,
            segment_count=len(segments)
        )
        
        print(f"[Job {job_id}] Completed successfully")
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[Job {job_id}] Failed: {error_msg}")
        print(f"[Job {job_id}] Full traceback:")
        traceback.print_exc()
        
        # Record error with monitoring
        asr_monitor.record_job_error(job_id, error_msg, e)
        
        async with jobs_lock:
            jobs[job_id].status = JobStatus.FAILED
            jobs[job_id].completed_at = datetime.now().isoformat()
            jobs[job_id].error = error_msg
    
    finally:
        # Cleanup temporary files
        cleanup_file(audio_path)
        if temp_wav:
            cleanup_file(temp_wav)


@app.on_event("startup")
async def load_model():
    """Load the default ASR model on server startup."""
    try:
        print(f"=" * 60, flush=True)
        print(f"Starting model download: {PARAKEET_MODEL}", flush=True)
        print(f"This may take several minutes on first run (~1.2GB download)", flush=True)
        print(f"=" * 60, flush=True)
        
        # Load default model (Parakeet)
        await get_or_load_model('parakeet')
        
        print(f"=" * 60, flush=True)
        print(f"Default model loaded successfully!", flush=True)
        print(f"Server is ready to accept requests!", flush=True)
        print(f"Note: Canary model will be loaded on-demand when first requested", flush=True)
        print(f"=" * 60, flush=True)
        
    except Exception as e:
        print(f"Error loading default model: {e}", flush=True)
        raise


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "service": "NVIDIA ASR Transcription API",
        "version": "2.0.0",
        "models": {
            "parakeet": SUPPORTED_MODELS['parakeet'],
            "canary": SUPPORTED_MODELS['canary']
        },
        "default_model": "parakeet",
        "supported_languages": list(SUPPORTED_LANGUAGES),
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
    parakeet_loaded = asr_models['parakeet'] is not None
    canary_loaded = asr_models['canary'] is not None
    
    status = "healthy" if parakeet_loaded else "default_model_not_loaded"
    model_name = f"parakeet: {parakeet_loaded}, canary: {canary_loaded}"
    
    return HealthResponse(
        status=status,
        model_loaded=parakeet_loaded or canary_loaded,
        model_name=model_name
    )


@app.post("/transcribe/async", response_model=JobStartResponse)
async def transcribe_audio_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model: str = Form('parakeet'),
    language: Optional[str] = Form(None),
    include_timestamps: bool = Form(True)
):
    """
    Start an asynchronous transcription job.
    
    Args:
        file: Audio file (WAV, MP3, or FLAC)
        model: Model to use ('parakeet' or 'canary', default: 'parakeet')
        language: Language code for multilingual models ('en', 'es', 'de', 'fr', default: None)
        include_timestamps: Whether to generate timestamps (default: True)
    
    Returns:
        JobStartResponse with job_id to track the job
    """
    # Validate model
    if model not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model: {model}. Supported: {list(SUPPORTED_MODELS.keys())}"
        )
    
    # Validate language for Canary model
    if model == 'canary':
        if language and language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {language}. Supported: {sorted(SUPPORTED_LANGUAGES)}"
            )
        if not language:
            language = 'en'  # Default to English for Canary
    
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
        
        async with jobs_lock:
            jobs[job_id] = job_info
        
        # Start background processing
        background_tasks.add_task(
            process_transcription_job,
            job_id,
            temp_upload_path,
            file.filename,
            model,
            language,
            include_timestamps
        )
        
        print(f"[Job {job_id}] Started for file: {file.filename} (model={model}, language={language})")
        
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
    async with jobs_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Return a copy to avoid race conditions
        return jobs[job_id].model_copy()


@app.get("/jobs/{job_id}/result", response_model=TranscriptionResponse)
async def get_job_result(job_id: str):
    """
    Get the result of a completed transcription job.
    
    Args:
        job_id: The unique job identifier
    
    Returns:
        TranscriptionResponse with transcription text and timestamps
    """
    async with jobs_lock:
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
    
    Marks the job as cancelled. The background task will check this status
    and stop processing at the next checkpoint.
    
    Args:
        job_id: The unique job identifier
    
    Returns:
        Message confirming cancellation
    """
    async with jobs_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = jobs[job_id]
        
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel job with status: {job.status}"
            )
        
        # Mark as cancelled - the background task will check this and stop
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now().isoformat()
    
    print(f"[Job {job_id}] Cancellation requested")
    
    return {"message": f"Job {job_id} cancellation requested", "status": JobStatus.CANCELLED}


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model: str = Form('parakeet'),
    language: Optional[str] = Form(None),
    include_timestamps: bool = Form(True)
):
    """
    Transcribe an audio file synchronously.
    
    Args:
        file: Audio file (WAV, MP3, or FLAC)
        model: Model to use ('parakeet' or 'canary', default: 'parakeet')
        language: Language code for multilingual models ('en', 'es', 'de', 'fr', default: None)
        include_timestamps: Whether to generate timestamps (default: True)
    
    Returns:
        TranscriptionResponse with text and timestamps
    """
    # Validate model
    if model not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model: {model}. Supported: {list(SUPPORTED_MODELS.keys())}"
        )
    
    # Validate language for Canary model
    if model == 'canary':
        if language and language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {language}. Supported: {sorted(SUPPORTED_LANGUAGES)}"
            )
        if not language:
            language = 'en'  # Default to English for Canary
    
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
        print(f"Transcribing: {file.filename} (model={model}, language={language})")
        
        # Load the appropriate model
        asr_model = await get_or_load_model(model)
        
        # Prepare transcription parameters
        transcribe_kwargs = {}
        
        # Add language parameter for Canary model
        if model == 'canary' and language:
            transcribe_kwargs['source_lang'] = language
        
        # Add timestamps if requested and supported
        if include_timestamps and SUPPORTED_MODELS[model]['supports_timestamps']:
            transcribe_kwargs['timestamps'] = True
        
        # Perform transcription
        output = asr_model.transcribe([str(audio_path)], **transcribe_kwargs)
        
        # Extract text and segments
        text = output[0].text
        segments = []
        
        if hasattr(output[0], 'timestamp') and output[0].timestamp:
            timestamp_data = output[0].timestamp
            if isinstance(timestamp_data, dict) and 'segment' in timestamp_data:
                for seg in timestamp_data['segment']:
                    # Handle both dict format {'start': ..., 'end': ..., 'text': ...}
                    # and list/tuple format [start, end, text]
                    if isinstance(seg, dict):
                        segments.append({
                            'start': seg.get('start', 0),
                            'end': seg.get('end', 0),
                            'text': seg.get('text', '')
                        })
                    else:
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
            timestamp=datetime.now().isoformat(),
            model=model,
            language=language
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
