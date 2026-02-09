# NVIDIA ASR Transcription Server

FastAPI-based REST API server for audio transcription using NVIDIA Parakeet and Canary-1B models with GPU acceleration (automatic CPU fallback).

## Features

- 🎙️ Audio transcription via REST API
- 📝 Returns text and timestamp segments
- 🔄 Supports WAV, MP3, and FLAC formats
- 🌍 Dual model support: Parakeet (English) + Canary-1B (Multilingual)
- 🚀 FastAPI with automatic API documentation
- 🐳 Docker containerization with GPU support
- 🔧 Health check endpoint
- ⚡ GPU acceleration (with automatic CPU fallback)

## Requirements

- Python 3.10-3.12 (Python 3.13+ is **NOT** supported due to NeMo/lhotse incompatibility)
- NVIDIA GPU with CUDA support (recommended, but not required - automatically falls back to CPU)
- Docker (for containerized deployment)

## Installation

### Quick Setup (Windows - Recommended)

Run the setup script which handles Python 3.12 venv creation, PyTorch CUDA installation, and all dependencies:

```powershell
cd scenario4\server
.\setup-venv.ps1
```

For CPU-only installation:
```powershell
.\setup-venv.ps1 -CpuOnly
```

### Manual Setup (Windows)

1. **Create virtual environment with Python 3.12:**
```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
```

2. **Install PyTorch with CUDA:**
```powershell
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

3. **Install Windows-specific dependencies:**
```powershell
pip install -r requirements-windows.txt
```

4. **Install NeMo toolkit (without triton on Windows):**
```powershell
pip install nemo_toolkit[asr] --no-deps
pip install hydra-core omegaconf pytorch-lightning webdataset huggingface-hub onnx tqdm
```

5. **Apply lhotse compatibility fix:**
```powershell
python ..\..\fix_lhotse.py
```

6. **Start the server:**
```powershell
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Manual Setup (Linux/macOS)

1. **Create virtual environment with Python 3.12:**
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

2. **Install PyTorch with CUDA:**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Apply lhotse compatibility fix:**
```bash
python ../../fix_lhotse.py
```

5. **Start the server:**
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

The server will be available at `http://localhost:8000`

### .NET Aspire Integration

When running with .NET Aspire AppHost, **no manual setup is required**. Aspire automatically builds and runs the Docker container:

```powershell
cd scenario4\AppHost
dotnet run
```

The Aspire host uses `AddDockerfile` to build and run the server container from the Dockerfile in this directory.

### Docker Deployment

The Dockerfile uses the official **NVIDIA NeMo container** (`nvcr.io/nvidia/nemo:25.11.01`) with all ASR dependencies pre-installed.

1. **Build the container:**
```bash
docker build -t nvidia-asr-server .
```

2. **Run with GPU support:**
```bash
docker run -p 8000:8000 --gpus all nvidia-asr-server
```

3. **Run CPU-only (slower):**
```bash
docker run -p 8000:8000 nvidia-asr-server
```

**Note**: First run may take a while as Docker pulls the large NeMo base image (~15GB).

### Docker Image Management

#### Rebuilding the Docker Image

When you make changes to the server code (e.g., adding new endpoints), you need to rebuild the Docker image:

**Manual rebuild:**
```bash
# Stop and remove existing containers
docker stop nvidia-asr-server
docker rm nvidia-asr-server

# Remove the old image
docker rmi nvidia-asr-server

# Rebuild
docker build -t nvidia-asr-server .
```

**With .NET Aspire:**

Aspire automatically rebuilds the Docker image when you run `dotnet run`, but you can force a clean rebuild:

```powershell
# Stop Aspire
# Press Ctrl+C in the Aspire dashboard

# Remove the Aspire-built image (name varies, check with docker images)
docker images | grep apiserver
docker rmi <image-id>

# Restart Aspire
cd scenario4\AppHost
dotnet run
```

#### Cleaning Up Docker Resources

To free up disk space:

```bash
# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove all unused Docker resources (containers, networks, images, volumes)
docker system prune -a --volumes

# Check current Docker disk usage
docker system df
```

**Note:** The NeMo base image is ~15GB. If you frequently rebuild, consider keeping it and only removing your custom layers.

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### GET /
Root endpoint with API information

### GET /health
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "nvidia/parakeet-tdt-0.6b-v2"
}
```

### POST /transcribe
Transcribe an audio file (synchronous - waits for completion)

**Request:**
- Content-Type: `multipart/form-data`
- Fields:
  - `file` (required) - Audio file (`.wav`, `.mp3`, `.flac`)
  - `model` (optional) - `"parakeet"` (default) or `"canary"`
  - `language` (optional) - `"en"`, `"es"`, `"de"`, `"fr"` (for Canary model)
  - `include_timestamps` (optional) - `"true"` (default) or `"false"`

**Response:**
```json
{
  "text": "Full transcription text here.",
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "First segment"
    }
  ],
  "filename": "audio.mp3",
  "timestamp": "2026-02-04T19:30:00"
}
```

### POST /transcribe/async
Start an asynchronous transcription job (returns immediately with job ID)

**Request:**
- Content-Type: `multipart/form-data`
- Field name: `file`
- Supported formats: `.wav`, `.mp3`, `.flac`

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Transcription job started for audio.mp3"
}
```

### GET /jobs/{job_id}/status
Get the status of a transcription job

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",  // pending, processing, completed, failed, cancelled
  "filename": "audio.mp3",
  "created_at": "2026-02-04T19:30:00",
  "completed_at": null,
  "error": null,
  "result": null
}
```

### GET /jobs/{job_id}/result
Get the result of a completed transcription job

**Response:**
```json
{
  "text": "Full transcription text here.",
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "First segment"
    }
  ],
  "filename": "audio.mp3",
  "timestamp": "2026-02-04T19:30:00"
}
```

**Error Responses:**
- `400`: Job not yet completed (still pending/processing)
- `404`: Job not found
- `500`: Job failed (includes error message)

### POST /jobs/{job_id}/cancel
Cancel a transcription job

**Response:**
```json
{
  "message": "Job 550e8400-e29b-41d4-a716-446655440000 cancelled",
  "status": "cancelled"
}
```

**Error Responses:**
- `400`: Cannot cancel job (already completed/failed/cancelled)
- `404`: Job not found

## Testing

### Synchronous Mode (Traditional)

**Using curl:**
```bash
curl -X POST "http://localhost:8000/transcribe" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.mp3"
```

**Using Python:**
```python
import requests

with open('audio.mp3', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/transcribe', files=files)
    print(response.json())
```

### Asynchronous Job Mode

**Start a job:**
```bash
curl -X POST "http://localhost:8000/transcribe/async" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.mp3"
```

**Check job status:**
```bash
curl "http://localhost:8000/jobs/{job_id}/status"
```

**Get job result (when completed):**
```bash
curl "http://localhost:8000/jobs/{job_id}/result"
```

**Cancel a job:**
```bash
curl -X POST "http://localhost:8000/jobs/{job_id}/cancel"
```

**Using Python with async jobs:**
```python
import requests
import time

# Start job
with open('audio.mp3', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/transcribe/async', files=files)
    job = response.json()
    job_id = job['job_id']
    print(f"Job started: {job_id}")

# Poll for completion
while True:
    response = requests.get(f'http://localhost:8000/jobs/{job_id}/status')
    status = response.json()
    
    if status['status'] == 'completed':
        result = requests.get(f'http://localhost:8000/jobs/{job_id}/result')
        print(result.json())
        break
    elif status['status'] == 'failed':
        print(f"Job failed: {status['error']}")
        break
    
    print(f"Status: {status['status']}")
    time.sleep(5)
```

## Job Management Workflow

The async job mode is ideal for:
- Long-running transcriptions that may timeout with synchronous requests
- Client applications that need to handle multiple concurrent jobs
- Web applications that want to provide better user experience with progress updates

**Job Lifecycle:**
1. `pending` - Job created, waiting to start
2. `processing` - Transcription in progress
3. `completed` - Transcription finished successfully (result available)
4. `failed` - Transcription failed (error details available)
5. `cancelled` - Job was cancelled by user

**Note:** Jobs are stored in-memory. Restarting the server will clear all job data.

## Configuration

### Environment Variables

- `MODEL_NAME`: Default model to load at startup (default: `nvidia/parakeet-tdt-0.6b-v2`). Canary-1B is loaded on-demand when first requested.
- `PORT`: Server port (default: 8000)

### CORS

The server has CORS enabled for all origins by default. For production, configure in `app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Performance

### GPU vs CPU
- **GPU**: ~10x faster, requires CUDA-capable NVIDIA GPU
- **CPU**: Slower but works without GPU

### Memory Requirements
- Model loading: ~2GB RAM/VRAM
- Audio processing: ~500MB per request

### Optimization Tips
1. Use GPU for production workloads
2. Keep the model loaded (it persists across requests)
3. GPU memory is automatically cleaned up after each transcription
4. Models are loaded in eval mode to reduce memory overhead
5. Use proper resource limits in Docker/Kubernetes
6. Consider request queuing for high traffic

## Troubleshooting

### "Model not loaded" error
Wait a few seconds after startup for the model to load. Check `/health` endpoint.

### "CUDA out of memory" error
- Reduce concurrent requests
- Use smaller batch sizes
- Try CPU-only mode

### Audio conversion fails
- Ensure ffmpeg is installed (included in Docker image)
- Check audio file is valid and not corrupted
- Verify file format is supported

### Slow startup
First run downloads the model (~1.2GB) from Hugging Face. Subsequent runs use cached model.

## GPU Memory Management

The server automatically manages GPU memory between transcription requests:

- **Post-transcription cleanup**: After each job, the server runs `gc.collect()`, `torch.cuda.empty_cache()`, and `torch.cuda.ipc_collect()` to free intermediate tensors and CUDA caches
- **Eval mode**: Models are set to `model.eval()` after loading to disable gradient tracking and reduce memory usage
- **Memory logging**: GPU memory usage is logged before and after cleanup for monitoring
- **Model persistence**: Models remain loaded in memory across requests — only intermediate computation tensors are freed

## PyTorch Compatibility

The server includes a compatibility patch for **PyTorch 2.9+** where `torch.load` defaults to `weights_only=True`. NeMo model checkpoints require `weights_only=False`, but NeMo itself passes `weights_only=True` explicitly. The server applies an unconditional monkey-patch to override this parameter, ensuring both Parakeet and Canary models load correctly.

## Security Considerations

⚠️ **Important for production deployments:**

1. **File Upload Validation**: The server validates file extensions but you should add additional checks
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Authentication**: Add API key or OAuth authentication
4. **File Size Limits**: FastAPI has default limits, but configure appropriately
5. **HTTPS**: Use HTTPS in production (configure reverse proxy)
6. **CORS**: Restrict allowed origins in production

## License

- **Parakeet model** (CC-BY-4.0): Allows commercial use
- **Canary-1B model** (CC-BY-NC-4.0): Non-commercial use only
