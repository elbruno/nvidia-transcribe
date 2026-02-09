# Scenario 4 Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │  C# Console App  │              │ Server-Side      │        │
│  │  (.NET 10.0)     │              │ Blazor Web App   │        │
│  │                  │              │                  │        │
│  │  • CLI interface │              │  • Browser UI    │        │
│  │  • File upload   │              │  • File upload   │        │
│  │  • Standalone    │              │  • Live results  │        │
│  │  • Result display│              │  • Aspire+OpenTel│        │
│  └────────┬─────────┘              └────────┬─────────┘        │
│           │                                 │                  │
│           └─────────────┬───────────────────┘                  │
│                         │                                      │
└─────────────────────────┼──────────────────────────────────────┘
                          │
                          │ HTTP/REST API
                          │ (JSON over HTTPS)
                          │
┌─────────────────────────┼──────────────────────────────────────┐
│                         │          SERVER LAYER                │
├─────────────────────────┼──────────────────────────────────────┤
│                         ▼                                      │
│           ┌──────────────────────────┐                         │
│           │   FastAPI Server         │                         │
│           │   (Python 3.10-3.12)     │                         │
│           │                          │                         │
│           │  Endpoints:              │                         │
│           │  • GET  /                │                         │
│           │  • GET  /health          │                         │
│           │  • POST /transcribe      │                         │
│           │  • POST /transcribe/async│                         │
│           │  • GET  /jobs/{id}/status│                         │
│           │                          │                         │
│           │  Features:               │                         │
│           │  • CORS enabled          │                         │
│           │  • File upload           │                         │
│           │  • Audio conversion      │                         │
│           │  • Background cleanup    │                         │
│           │  • GPU acceleration      │                         │
│           │  • CPU fallback          │                         │
│           │  • GPU memory management │                         │
│           └──────────┬───────────────┘                         │
│                      │                                         │
│                      ▼                                         │
│           ┌──────────────────────────┐                         │
│           │  NVIDIA ASR Models       │                         │
│           │                          │                         │
│           │  Parakeet (English)      │                         │
│           │  • Text + timestamps     │                         │
│           │  • CC-BY-4.0 license     │                         │
│           │                          │                         │
│           │  Canary-1B (Multilingual)│                         │
│           │  • en, es, de, fr        │                         │
│           │  • CC-BY-NC-4.0 license  │                         │
│           │  • Loaded on-demand      │                         │
│           └──────────────────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      NIM LLM LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────┐                                   │
│  │  NVIDIA NIM Container    │   Clients call NIM directly       │
│  │  (Docker)                │   via OpenAI-compatible API       │
│  │                          │                                   │
│  │  Default model:          │   Endpoint:                       │
│  │  Llama 3.2 3B Instruct   │   POST /v1/chat/completions      │
│  │  (~6 GB VRAM)            │   GET  /v1/health/ready          │
│  │                          │                                   │
│  │  Features:               │   Output:                        │
│  │  • Podcast asset gen     │   • Episode title                │
│  │  • JSON structured output│   • Episode description          │
│  │  • NGC API key auth      │   • Tags (5-8)                   │
│  │  • Persistent container  │                                   │
│  └──────────────────────────┘                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT OPTIONS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Local Development:                                             │
│  • uvicorn (Python dev server)                                  │
│  • Direct execution                                             │
│  • GPU/CPU automatic detection                                  │
│                                                                 │
│  Docker:                                                        │
│  • Containerized server                                         │
│  • GPU support via --gpus flag                                  │
│  • CPU fallback if GPU not available                            │
│  • CUDA 12.1 base image                                         │
│                                                                 │
│  .NET Aspire:                                                   │
│  • Orchestration for web client + server + NIM LLM              │
│  • Service discovery and health checks                          │
│  • OpenTelemetry integration                                    │
│  • Console client runs standalone                               │
│                                                                 │
│  Azure Cloud:                                                   │
│  • Azure Container Apps (recommended)                           │
│  • Azure Container Instances                                    │
│  • Azure Kubernetes Service                                     │
│  • Auto-scaling, managed, serverless                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Transcription Request Flow

```
1. Client Prepares Request
   └─> Select/Upload audio file (WAV, MP3, FLAC)

2. HTTP POST to /transcribe
   └─> Multipart form data with file

3. Server Processing
   ├─> Validate file format
   ├─> Save to temp location
   ├─> Convert to 16kHz WAV (if needed)
   ├─> Load into ASR model
   ├─> Transcribe with timestamps
   └─> Schedule temp file cleanup

4. Response Generation
   └─> JSON with:
       ├─> Full transcription text
       ├─> Timestamp segments
       ├─> Original filename
       └─> Processing timestamp

5. Client Display
   └─> Show results to user
       ├─> Console: Text output
       └─> Web: Interactive UI
```

## Component Details

### Server (FastAPI)

**Technology Stack:**
- Python 3.10-3.12
- FastAPI web framework
- NVIDIA NeMo toolkit
- librosa for audio processing
- PyTorch with CUDA support

**Key Files:**
- `server/app.py` - Main application (~850 lines)
- `server/requirements.txt` - Dependencies
- `server/Dockerfile` - Container image
- `server/README.md` - Documentation

**API Endpoints:**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API information |
| `/health` | GET | Health check, model status |
| `/transcribe` | POST | Audio transcription |

### Console Client (C#)

**Technology Stack:**
- .NET 10.0
- System.Net.Http for REST calls
- System.Text.Json for JSON parsing
- Standalone application (not orchestrated)

**Key Files:**
- `clients/console/Program.cs` - Main application
- `clients/console/TranscriptionClient.csproj` - Project file

**Features:**
- Command-line arguments
- Server health check
- File upload via multipart form
- Formatted output with timestamps
- Can run independently without orchestration

### Web Client (Server-Side Blazor)

**Technology Stack:**
- Server-Side Blazor
- .NET 10.0
- Modern HTML5/CSS3
- Aspire ServiceDefaults integration

**Key Files:**
- `clients/webapp/Components/Pages/Transcribe.razor` - Main UI
- `clients/webapp/Program.cs` - App bootstrap
- `clients/webapp/TranscriptionWebApp2.csproj` - Project file

**Features:**
- File upload with InputFile component
- Async API calls
- Real-time status updates
- Responsive design
- OpenTelemetry integration
- Health checks
- Service discovery via Aspire

## Deployment Architectures

### Local Development with Aspire

```
Developer Machine
├─> Aspire AppHost: dotnet run
    ├─> Python Server (uvicorn)
    ├─> Blazor Web Client
    ├─> NVIDIA NIM LLM Container (podcast assets)
    └─> Aspire Dashboard (monitoring)
└─> Console Client: standalone dotnet run
```

### Docker Deployment

```
Docker Host
├─> Container: nvidia-asr-server (port 8000)
│   ├─> GPU access via --gpus flag
│   └─> CPU fallback if no GPU
└─> Host: dotnet run (clients)
```

### Azure Production

```
Azure Cloud
├─> Container Apps Environment
│   └─> nvidia-asr-api container
│       ├─> Auto-scaling (1-5 instances)
│       ├─> HTTPS ingress
│       ├─> GPU support (optional)
│       └─> Managed compute
│
└─> Azure Container Registry
    └─> Container images
```

## Security Considerations

### Server
- CORS configuration (default: allow all, configure for production)
- File upload validation
- Background cleanup of temp files
- No persistent storage (stateless)

### Clients
- HTTPS for production
- Error handling for network failures
- File size limits
- Input validation

### Azure Deployment
- Managed identity for Azure services
- Private endpoints available
- Azure Key Vault for secrets
- Network security groups

## Performance Characteristics

### Server
- Model loading: ~10 seconds (one-time startup)
- Canary-1B: Loaded on-demand on first multilingual request (~30-60s)
- Transcription: ~0.1-0.3x real-time with GPU
- Memory: ~2GB for Parakeet + ~2GB for Canary (when loaded)
- GPU memory cleaned up after each transcription (intermediate tensors freed)
- Concurrent requests: Limited by GPU memory

### Clients
- Console: Minimal overhead
- Web: Browser-based, no local processing
- Network: Depends on file size and bandwidth

## Cost Considerations (Azure)

**Container Apps (Estimated Monthly):**
- Small (2 vCPU, 4GB): ~$100-150
- Medium (4 vCPU, 8GB): ~$200-300
- GPU instance: ~$500-800 (if available)

**Additional Services:**
- Container Registry: ~$5-20
- Static Web Apps: Free tier available
- Bandwidth: Variable based on usage

## Integration Examples

The system can be integrated with:
- Python applications (requests library)
- Node.js applications (axios/fetch)
- React/Vue/Angular frontends
- Mobile apps (REST API)
- PowerShell/Bash scripts
- CI/CD pipelines

See `USAGE_EXAMPLES.md` for detailed integration code.
