# Scenario 4: Client-Server Architecture

A complete client-server solution for audio transcription using NVIDIA ASR models. The server runs as a containerized FastAPI application, and clients (C# console and Blazor web app) communicate with it via REST API.

## Architecture

```
┌─────────────────┐         HTTP/REST        ┌──────────────────┐
│  C# Console     │────────────────────────▶│  Python Server   │
│  Client         │                          │  (FastAPI)       │
└─────────────────┘                          │                  │
                                              │  NVIDIA ASR      │
┌─────────────────┐         HTTP/REST        │  (Parakeet)      │
│  Blazor Web     │────────────────────────▶│                  │
│  App            │                          │  Docker          │
└─────────────────┘                          └──────────────────┘
```

## Components

### Server (Python + FastAPI)
- FastAPI REST API with `/transcribe` endpoint
- NVIDIA Parakeet ASR model integration
- Supports WAV, MP3, and FLAC audio formats
- Returns JSON with transcription text and timestamps
- Containerized with Docker for easy deployment

### Console Client (C#)
- Command-line application for transcription
- Upload audio files via API
- Display results in terminal

### Web Client (Blazor WebAssembly)
- Browser-based UI for transcription
- Drag-and-drop file upload
- Real-time results display

## Quick Start

### 1. Start the Server

**Local Development:**
```bash
cd scenario4/server
pip install -r requirements.txt
python fix_lhotse.py  # Apply compatibility fix
uvicorn app:app --host 0.0.0.0 --port 8000
```

**Docker:**
```bash
cd scenario4/server
docker build -t nvidia-asr-server .
docker run -p 8000:8000 --gpus all nvidia-asr-server
```

The server will be available at `http://localhost:8000`

### 2. Use the Console Client (C#)

```bash
cd scenario4/clients/console
dotnet run audio_file.mp3
```

Optional: Specify custom API URL:
```bash
dotnet run audio_file.mp3 http://server:8000
```

### 3. Use the Web Client (Blazor)

```bash
cd scenario4/clients/blazor
dotnet run
```

Then open your browser to the displayed URL (typically `http://localhost:5000`)

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
- Python 3.10-3.12
- NVIDIA GPU with CUDA support (recommended)
- Docker (for containerized deployment)
- See `server/requirements.txt` for Python dependencies

### Console Client
- .NET 8.0 SDK
- Cross-platform (Windows, Linux, macOS)

### Web Client
- .NET 8.0 SDK
- Modern web browser

## Development

### Server Development
```bash
cd scenario4/server
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
python ../../fix_lhotse.py
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Console Client Development
```bash
cd scenario4/clients/console
dotnet build
dotnet run -- ../../test_audio.mp3
```

### Web Client Development
```bash
cd scenario4/clients/blazor
dotnet watch run
```

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
- Ensure Python 3.10-3.12 is installed (not 3.13)
- Run `python fix_lhotse.py` after installing dependencies
- Check CUDA installation for GPU support

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
