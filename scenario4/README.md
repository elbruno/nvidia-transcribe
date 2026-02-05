# Scenario 4: Client-Server Architecture

A complete client-server solution for audio transcription using NVIDIA ASR models. The server runs as a containerized Python FastAPI application using GPU acceleration (with CPU fallback), and clients communicate with it via REST API.

**NEW**: Now with .NET Aspire orchestration using Docker containers for simplified development and deployment!

## Architecture

```
┌─────────────────┐         HTTP/REST        ┌──────────────────┐
│  C# Console     │────────────────────────▶│  Python Server   │
│  Client         │  (Standalone)            │  (FastAPI)       │
│                 │                          │                  │
└─────────────────┘                          │  NVIDIA ASR      │
                                              │  (Parakeet)      │
┌─────────────────┐         HTTP/REST        │                  │
│  Server-Side    │────────────────────────▶│  GPU/CPU         │
│  Blazor App     │  (with Aspire)           │  Docker Container│
└─────────────────┘                          └──────────────────┘
```

## Docker Image

The server uses the official **NVIDIA NeMo container** (`nvcr.io/nvidia/nemo:25.11.01`) as base image:
- All NeMo ASR dependencies pre-installed and optimized
- No manual Python environment setup required
- Tested for performance and convergence
- See: https://github.com/NVIDIA-NeMo/NeMo

## Clients

| Client | Type | Features |
|--------|------|----------|
| `clients/console/` | C# Console | Standalone CLI transcription (not in orchestration) |
| `clients/webapp/` | Server-Side Blazor | Full Aspire integration, OpenTelemetry, health checks |

## Quick Start Options

### Option 1: Using .NET Aspire (Recommended for Development)

Aspire automatically builds and runs the Docker container:

```powershell
cd scenario4/AppHost
dotnet run
```

This launches:
- Aspire dashboard with logs and metrics
- Python FastAPI server (Docker container with GPU acceleration)
- Blazor web client

**Benefits**: 
- No Python environment setup required
- Unified development experience
- Automatic service discovery
- Integrated monitoring

**Note**: The console client is available as a standalone application and is not part of the Aspire orchestration.

See [AppHost/README.md](AppHost/README.md) for detailed Aspire instructions.

### Option 2: Docker (Recommended for Production)

The server is containerized with GPU support (falls back to CPU if GPU is not available):

```bash
cd scenario4/server
docker build -t nvidia-asr-server .

# With GPU support
docker run -p 8000:8000 --gpus all nvidia-asr-server

# Without GPU (CPU fallback)
docker run -p 8000:8000 nvidia-asr-server
```

### Option 3: Local Development (Manual)

```powershell
cd scenario4/server
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements-windows.txt
pip install nemo_toolkit[asr] --no-deps
pip install hydra-core omegaconf pytorch-lightning webdataset huggingface-hub onnx tqdm
python ../../fix_lhotse.py
uvicorn app:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### GET /
Root endpoint with API information

### GET /health
Health check endpoint
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "nvidia/parakeet-tdt-0.6b-v2"
}
```

### POST /transcribe
Transcribe an audio file

**Request:** Multipart form with file upload
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

## Azure Deployment

### Deploy to Azure Container Apps

1. **Build and push container:**
```bash
# Login to Azure Container Registry
az acr login --name <your-registry>

# Build and push
cd scenario4/server
docker build -t <your-registry>.azurecr.io/nvidia-asr:latest .
docker push <your-registry>.azurecr.io/nvidia-asr:latest
```

2. **Create Container App:**
```bash
az containerapp create \
  --name nvidia-asr-api \
  --resource-group <your-rg> \
  --environment <your-env> \
  --image <your-registry>.azurecr.io/nvidia-asr:latest \
  --target-port 8000 \
  --ingress external \
  --cpu 2 \
  --memory 4Gi
```

3. **Enable GPU (if available):**
Add GPU configuration in Azure Portal or via ARM template.

4. **Configure clients:**
Update the API URL in clients to point to your Azure Container App URL.

## Requirements

### Server
- **Python 3.10-3.12** (Python 3.13+ is NOT supported due to NeMo/lhotse incompatibility)
- NVIDIA GPU with CUDA support (recommended, but falls back to CPU if not available)
- Docker (for containerized deployment)
- See `server/requirements.txt` for Python dependencies

### Console Client (Standalone)
- .NET 10.0 SDK
- Cross-platform (Windows, Linux, macOS)
- Can be run independently without Aspire orchestration

### Server-Side Blazor Web Client
- .NET 10.0 SDK
- Modern web browser
- Includes ServiceDefaults integration for Aspire

## Development

### Option A: Using .NET Aspire (Recommended)

Aspire builds the Docker container automatically and provides unified orchestration and monitoring:

```bash
cd scenario4/AppHost
dotnet run
```

Benefits:
- Docker container built and started automatically
- No Python environment setup required
- All services start with one command
- Automatic service discovery
- Unified dashboard with logs, metrics, and traces
- Hot reload for rapid development

See [AppHost/README.md](AppHost/README.md) for detailed instructions.

### Option B: Manual Server Development (Local Python)

**Windows:**
```powershell
cd scenario4/server
.\setup-venv.ps1  # Or follow manual steps in server/README.md
.venv\Scripts\activate
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Linux/macOS:**
```bash
cd scenario4/server
python3.12 -m venv .venv
source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
python ../../fix_lhotse.py
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Console Client Development

The console client runs as a standalone application:

```bash
cd scenario4/clients/console
dotnet build
dotnet run -- <audio-file-path>

# Example:
dotnet run -- ../../test_audio.mp3
```

### Web Client Development

The web client runs with Aspire orchestration:

```bash
cd scenario4/AppHost
dotnet run
```

Then navigate to the Aspire dashboard to access the web client.

## Security Considerations

- The server accepts file uploads - implement size limits and validation
- Use HTTPS in production environments
- Consider authentication/authorization for production deployments
- Validate file types and sanitize filenames

## Limitations

- Maximum audio file length: 24 minutes (model limitation)
- English language only (Parakeet model)
- Requires significant memory for model loading (~2GB)

## Troubleshooting

### Server won't start
- Ensure Python 3.10-3.12 is installed (Python 3.13+ is NOT supported)
- On Windows, use `py -3.12` to ensure correct version
- Run `python fix_lhotse.py` after installing dependencies
- Check CUDA installation for GPU support

### "No matching distribution found for triton"
- This is a Windows-specific issue (triton is Linux-only)
- Use `requirements-windows.txt` or the `setup-venv.ps1` script
- Install NeMo with `--no-deps` flag on Windows

### Clients can't connect
- Verify server is running on the expected port
- Check firewall rules
- Ensure correct API URL in client configuration

### Transcription fails
- Check audio file format (WAV, MP3, or FLAC)
- Verify file is not corrupted
- Check server logs for detailed error messages

## License

This scenario uses the Parakeet model (CC-BY-4.0), which allows commercial use.
