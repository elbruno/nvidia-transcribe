# Scenario 4 Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │  C# Console App  │              │  Blazor Web App  │        │
│  │  (.NET 8.0)      │              │  (WebAssembly)   │        │
│  │                  │              │                  │        │
│  │  • CLI interface │              │  • Browser UI    │        │
│  │  • File upload   │              │  • File upload   │        │
│  │  • Result display│              │  • Live results  │        │
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
│           │                          │                         │
│           │  Features:               │                         │
│           │  • CORS enabled          │                         │
│           │  • File upload           │                         │
│           │  • Audio conversion      │                         │
│           │  • Background cleanup    │                         │
│           └──────────┬───────────────┘                         │
│                      │                                         │
│                      ▼                                         │
│           ┌──────────────────────────┐                         │
│           │  NVIDIA Parakeet Model   │                         │
│           │  (ASR - English)         │                         │
│           │                          │                         │
│           │  • Text generation       │                         │
│           │  • Timestamp extraction  │                         │
│           │  • GPU accelerated       │                         │
│           └──────────────────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT OPTIONS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Local Development:                                             │
│  • uvicorn (Python dev server)                                  │
│  • Direct execution                                             │
│                                                                 │
│  Docker:                                                        │
│  • Containerized server                                         │
│  • GPU support via --gpus flag                                  │
│  • CUDA 12.1 base image                                         │
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
- `server/app.py` - Main application (210 lines)
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
- .NET 8.0
- System.Net.Http for REST calls
- System.Text.Json for JSON parsing

**Key Files:**
- `clients/console/Program.cs` - Main application (150 lines)
- `clients/console/TranscriptionClient.csproj` - Project file

**Features:**
- Command-line arguments
- Server health check
- File upload via multipart form
- Formatted output with timestamps

### Web Client (Blazor)

**Technology Stack:**
- Blazor WebAssembly
- .NET 8.0
- Modern HTML5/CSS3

**Key Files:**
- `clients/blazor/Pages/Index.razor` - Main UI (145 lines)
- `clients/blazor/Program.cs` - App bootstrap
- `clients/blazor/wwwroot/css/app.css` - Styling

**Features:**
- File upload with InputFile component
- Async API calls
- Real-time status updates
- Responsive design

## Deployment Architectures

### Local Development

```
Developer Machine
├─> Terminal 1: uvicorn server
├─> Terminal 2: dotnet run (console)
└─> Terminal 3: dotnet run (web) → Browser
```

### Docker Deployment

```
Docker Host
├─> Container: nvidia-asr-server (port 8000)
│   └─> GPU access via --gpus flag
└─> Host: dotnet run (clients)
```

### Azure Production

```
Azure Cloud
├─> Container Apps Environment
│   └─> nvidia-asr-api container
│       ├─> Auto-scaling (1-5 instances)
│       ├─> HTTPS ingress
│       └─> Managed compute
│
├─> Azure Static Web Apps
│   └─> Blazor client (static files)
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
- Transcription: ~0.1-0.3x real-time with GPU
- Memory: ~2GB for model + ~500MB per request
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
