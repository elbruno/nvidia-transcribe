# NVIDIA ASR Transcription Server

FastAPI-based REST API server for audio transcription using NVIDIA Parakeet model.

## Features

- 🎙️ Audio transcription via REST API
- 📝 Returns text and timestamp segments
- 🔄 Supports WAV, MP3, and FLAC formats
- 🚀 FastAPI with automatic API documentation
- 🐳 Docker containerization
- 🔧 Health check endpoint

## Requirements

- Python 3.10-3.12 (Python 3.13+ is **NOT** supported due to NeMo/lhotse incompatibility)
- NVIDIA GPU with CUDA support (recommended)
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

When running with .NET Aspire AppHost, the virtual environment must be set up **before** running `dotnet run`:

1. **Set up the Python environment first:**
```powershell
cd scenario4\server
.\setup-venv.ps1
```

2. **Then run Aspire:**
```powershell
cd ..\AppHost
dotnet run
```

The Aspire host is configured to use the `.venv` virtual environment in the server directory.

### Docker Deployment

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
Transcribe an audio file

**Request:**
- Content-Type: `multipart/form-data`
- Field name: `file`
- Supported formats: `.wav`, `.mp3`, `.flac`

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

## Testing

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

## Configuration

### Environment Variables

- `MODEL_NAME`: Model to use (default: `nvidia/parakeet-tdt-0.6b-v2`)
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
3. Use proper resource limits in Docker/Kubernetes
4. Consider request queuing for high traffic

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

## Security Considerations

⚠️ **Important for production deployments:**

1. **File Upload Validation**: The server validates file extensions but you should add additional checks
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Authentication**: Add API key or OAuth authentication
4. **File Size Limits**: FastAPI has default limits, but configure appropriately
5. **HTTPS**: Use HTTPS in production (configure reverse proxy)
6. **CORS**: Restrict allowed origins in production

## License

This server uses the Parakeet model (CC-BY-4.0), which allows commercial use.
