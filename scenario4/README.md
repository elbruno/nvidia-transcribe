# Scenario 4: Client-Server Architecture

A complete client-server solution for audio transcription using NVIDIA ASR models. The server runs as a containerized Python FastAPI application using GPU acceleration (with CPU fallback), and clients communicate with it via REST API.

**NEW**: Now with .NET Aspire orchestration using Docker containers for simplified development and deployment!

## ✨ New Features

### Dual Model Support
Choose between two ASR models based on your needs:

| Model | Languages | Timestamps | License | Best For |
|-------|-----------|------------|---------|----------|
| **Parakeet** (nvidia/parakeet-tdt-0.6b-v2) | English only | ✅ Yes | CC-BY-4.0 (Commercial) | English transcription with precise timestamps |
| **Canary-1B** (nvidia/canary-1b) | Multilingual (en, es, de, fr) | ❌ No | CC-BY-NC-4.0 (Non-commercial) | Spanish, German, French, or multilingual content |

### Configuration Options
- **Model Selection**: Choose Parakeet or Canary-1B via API, web UI, or CLI
- **Language Selection**: For Canary model, specify target language (en, es, de, fr)
- **Timestamp Control**: Enable or disable timestamp generation (Parakeet only)
- **Async Job Management**: Queue jobs and poll for results

### 🎧 Podcast Asset Generation (NIM)

Generate podcast episode titles, descriptions, and tags from any transcript using a local NVIDIA NIM LLM container.

- **Web app**: Dedicated "Podcast Assets" page with paste-a-transcript mode; also accessible via a button on the Transcribe results view
- **Console client**: `--generate-assets` flag after transcription, or standalone with `--transcript-file <path>`
- **Architecture**: Clients call the NIM container directly via its OpenAI-compatible `/v1/chat/completions` endpoint
- **Default model**: `meta/llama-3.2-3b-instruct` (3B params, ~6 GB VRAM – coexists with ASR on a 12 GB GPU)
- **Configurable**: Override the NIM image via `NIM_IMAGE` config; set `NGC_API_KEY` in user secrets

#### Prerequisites

1. **NGC API Key** – Sign up at [build.nvidia.com](https://build.nvidia.com), generate an API key
2. **Authenticate Docker with NVIDIA NGC** (required before pulling NIM images):
   ```bash
   docker login nvcr.io
   # Username: $oauthtoken
   # Password: <your-ngc-api-key>
   ```
3. **Pull the NIM image** (recommended before first Aspire run — the image is large):
   ```bash
   docker pull nvcr.io/nim/meta/llama-3.2-3b-instruct:latest
   ```
4. **Add the NGC API Key to Aspire user secrets** (used by the NIM container at runtime):
   ```bash
   cd scenario4/AppHost
   dotnet user-secrets set "NGC_API_KEY" "<your-key>"
   ```
5. Run the Aspire AppHost — it will use the locally cached NIM image

#### NIM Resources

Official NVIDIA documentation for NIM containers:
- [NIM Overview](https://docs.nvidia.com/nim/large-language-models/latest/introduction.html) - Introduction to NVIDIA NIM
- [NIM Getting Started Guide](https://docs.nvidia.com/nim/large-language-models/latest/getting-started.html) - Docker deployment and configuration
- [NGC Catalog](https://catalog.ngc.nvidia.com/) - Browse available NIM models
- [Llama 3.2 3B Instruct NIM](https://catalog.ngc.nvidia.com/orgs/nim/teams/meta/containers/llama-3.2-3b-instruct) - Default LLM container used for podcast asset generation
- [Build with NVIDIA](https://build.nvidia.com/) - Sign up and manage API keys

## 🎙️ Using the Transcription Feature

The Blazor web app includes a complete file upload interface with model/language selection:

1. Start Aspire (from repository root): `cd scenario4/AppHost && dotnet run`
2. Open the webapp from the Aspire dashboard
3. Navigate to the **Transcribe** page (menu or button on home page)
4. Select your preferred model and language
   - **Parakeet**: English with timestamps
   - **Canary-1B**: Multilingual (choose en, es, de, fr)
5. Upload audio files via:
   - Drag and drop into the upload zone
   - Click to browse and select files
6. Supported formats: WAV, MP3, FLAC (up to 50MB)

The transcription interface provides:
- **Side-by-side layout**: File selection and configuration panels in collapsible columns
- Model and language selection dropdowns
- Timestamp generation toggle (Parakeet only)
- **Fixed bottom progress log**: Real-time log with expand/collapse and entry count badge
- **Tabbed results**: Text, SRT, and TXT tabs with copy-to-clipboard and download buttons
- Timestamp segments (when available)
- Client-side SRT subtitle generation from transcript segments
- Metadata (filename, model used, processing time)

**Note**: The webapp now uses **async job mode** with status polling for better handling of long-running transcriptions. You can also cancel jobs in progress.

## 🔄 Job Management

The server now supports **asynchronous job management** for better handling of long-running transcriptions:

### Features
- **Job Queue**: Submit transcription jobs and get a Job ID immediately
- **Status Tracking**: Poll job status without blocking the client
- **Job Cancellation**: Cancel in-progress jobs
- **Result Retrieval**: Download transcription results when jobs complete

### API Endpoints
- `POST /transcribe/async` - Start a new job (returns Job ID)
- `GET /jobs/{job_id}/status` - Check job status
- `GET /jobs/{job_id}/result` - Get completed transcription
- `POST /jobs/{job_id}/cancel` - Cancel a job

### Client Support
- **Blazor Web App**: Automatically uses async mode with real-time progress updates. Includes UI for model/language selection.
- **Console Client**: Use `--async` flag for async mode, plus new model/language options:
  ```bash
  # Basic usage (default: Parakeet, English)
  TranscriptionClient audio.mp3 --async
  
  # Use Canary model with Spanish
  TranscriptionClient audio.mp3 --model canary --language es --async
  
  # Use Canary with German, sync mode
  TranscriptionClient audio.flac --model canary -l de
  
  # Disable timestamps (Parakeet only supports timestamps)
  TranscriptionClient audio.wav --no-timestamps
  ```

### Benefits
- No HTTP timeouts for long files
- Better user experience with progress feedback
- Support for concurrent transcription jobs
- Ability to cancel long-running jobs

For detailed API documentation, see [server/README.md](server/README.md).

## ⚡ GPU Configuration

**Important**: By default, GPU acceleration is enabled in the AppHost configuration, but requires NVIDIA Container Toolkit on the host machine.

See **[GPU_SETUP_GUIDE.md](docs/GPU_SETUP_GUIDE.md)** for:
- Installing NVIDIA Container Toolkit
- Verifying GPU access
- Troubleshooting GPU detection issues
- Understanding CPU fallback behavior

The application works in both GPU and CPU modes - GPU is an optimization, not a requirement.

## Architecture

```
┌─────────────────┐         HTTP/REST        ┌──────────────────┐
│  C# Console     │────────────────────────▶│  Python Server   │
│  Client         │  (Standalone)            │  (FastAPI)       │
│                 │                          │                  │
└────────┬────────┘                          │  NVIDIA ASR      │
         │                                   │  (Parakeet)      │
         │            HTTP/REST              │                  │
         ├──────────────────────────────────▶│  GPU/CPU         │
         │                                   │  Docker Container│
┌────────┴────────┐         HTTP/REST        └──────────────────┘
│  Server-Side    │────────────────────────▶
│  Blazor App     │  (with Aspire)
└────────┬────────┘
         │
         │        OpenAI-compat API          ┌──────────────────┐
         ├──────────────────────────────────▶│  NVIDIA NIM      │
         │                                   │  LLM Container   │
         │                                   │  (Llama 3.2 3B)  │
         │                                   │                  │
         │                                   │  Podcast Asset   │
         │                                   │  Generation      │
         │                                   │  Docker Container│
         └──────────────────────────────────▶└──────────────────┘
         (Console also calls NIM directly)
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

**Optional**: Enable Azure Application Insights monitoring - see [docs/APPLICATION_INSIGHTS.md](docs/APPLICATION_INSIGHTS.md)
- **Persistent model cache** - downloads only on first run

**Note**: The console client is available as a standalone application and is not part of the Aspire orchestration.

See [AppHost/README.md](AppHost/README.md) for detailed Aspire instructions.

#### Model Caching

The Parakeet model (~1.2GB) is downloaded from Hugging Face on first startup. Aspire uses a persistent Docker volume (`hf-model-cache`) to cache the model, so subsequent runs start much faster.

- **First run**: ~5-10 minutes (model download + loading)
- **Subsequent runs**: ~30-60 seconds (model loading only)

To manage the cache:
```powershell
# List volumes
docker volume ls

# Remove cache to force re-download (if needed)
docker volume rm hf-model-cache
```

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
- Parakeet: English only; Canary-1B: en, es, de, fr (non-commercial license)
- Requires significant memory for model loading (~2-4GB depending on models loaded)
- GPU memory is automatically cleaned up after each transcription job
- First startup is slow (~5-10 min) due to model download; subsequent runs use cached model
- **NIM LLM VRAM**: The default 3B model needs ~6 GB VRAM in addition to ~1.5 GB for ASR; a 12 GB GPU can run both concurrently. Larger models (7B/8B) require 16-24 GB cards.

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

### HTTP request timeout during transcription
- **RESOLVED**: The webapp now uses extended HTTP resilience timeouts (5 minutes)
- This handles long-running transcription operations (especially on CPU)
- Configuration is in `ServiceDefaults/Extensions.cs`
- After updating, restart Aspire: `cd AppHost && dotnet run`
- See [OPTION2_IMPLEMENTATION.md](docs/OPTION2_IMPLEMENTATION.md) for technical details

### First startup is very slow
- This is expected - the Parakeet model (~1.2GB) is being downloaded from Hugging Face
- Wait for "Server is ready to accept requests!" in the logs
- Subsequent runs will be much faster due to model caching
- If using Aspire, model is cached in `hf-model-cache` Docker volume

## GPU Memory Management

The server automatically manages GPU memory to prevent leaks across multiple transcription requests:
- GPU VRAM is cleaned up after each transcription job (`gc.collect()`, `torch.cuda.empty_cache()`, `torch.cuda.ipc_collect()`)
- Models are set to evaluation mode (`model.eval()`) to reduce memory overhead
- Memory usage is logged before and after cleanup for monitoring

## PyTorch Compatibility

The server includes a compatibility patch for PyTorch 2.9+ where `torch.load` defaults to `weights_only=True`. This is incompatible with NeMo model checkpoints, so the server unconditionally overrides this setting when loading models.

## License

This scenario uses the Parakeet model (CC-BY-4.0), which allows commercial use. The Canary-1B model uses CC-BY-NC-4.0 (non-commercial use only).
