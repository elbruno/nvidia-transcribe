# .NET Aspire AppHost for NVIDIA ASR Transcription

This AppHost orchestrates the NVIDIA ASR transcription stack using .NET Aspire:
- Python FastAPI server running in a Docker container (NVIDIA NeMo image) with GPU acceleration
- Server-side Blazor web client

**Note**: The console client is available as a standalone application and is not orchestrated by Aspire.

## Prerequisites

- **.NET 10.0 SDK** or later
- **Docker** (Docker Desktop on Windows/macOS, or Docker Engine on Linux)
- **NVIDIA GPU** with CUDA support (recommended, but falls back to CPU automatically)
- **NVIDIA Container Toolkit** (for GPU support in Docker)

## Setup

1. **Ensure Docker is running**

2. **Restore .NET dependencies**:
   ```bash
   dotnet restore
   ```

## Running with Aspire

Start the entire stack with one command:

```bash
dotnet run
```

This will:
1. Build the Docker image from `../server/Dockerfile` (using `nvcr.io/nvidia/nemo:25.11.01` base)
2. Launch the Aspire dashboard (typically at `http://localhost:15888`)
3. Start the Python FastAPI server container (apiserver) with GPU/CPU detection
4. Start the server-side Blazor web client (webappClient)

### Aspire Dashboard

The Aspire dashboard provides:
- **Service health monitoring** for all components
- **Logs** from Python and .NET services
- **Distributed tracing** across the stack
- **Environment variables** and configuration
- **Resource management**

Access it at `http://localhost:15888` (URL shown in console output)

## Using the Services

### Python API Server
- Automatically started by Aspire
- Available at the endpoint shown in the Aspire dashboard
- Health check: GET `/health`
- Transcription: POST `/transcribe`
- GPU acceleration with automatic CPU fallback

### Console Client (Standalone)
- **Not orchestrated by Aspire** - runs independently
- Run directly: `cd ../clients/console && dotnet run -- audio.mp3`
- Provide the API server URL when prompted, or it will use localhost:8000

### Server-Side Blazor Web Client
- Automatically started by Aspire
- Open the URL shown in the Aspire dashboard (typically `http://localhost:5xxx`)
- Upload audio files via the web interface
- Automatically connects to the API server via Aspire service discovery

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    .NET Aspire AppHost                       │
│  (Orchestration, Service Discovery, Monitoring, Logs)        │
└───────┬──────────────────────┬──────────────────────────────┘
        │                      │
        ▼                      ▼
┌───────────────────┐    ┌──────────────────┐
│ Docker Container  │    │ Blazor WebApp    │
│  (NeMo image)     │◄───│ (Server-Side)    │
│  Python FastAPI   │    └──────────────────┘
│  Port: 8000       │              ▲
│  NVIDIA ASR       │              │
│  GPU/CPU Auto     │         Service Discovery
└───────────────────┘

  Console Client (Standalone - not orchestrated)
        │
        ▼
   API Server (http://localhost:8000)
```

## Benefits of Using Aspire

1. **No Python Setup**: Docker container includes all dependencies
2. **Single Command Startup**: Start server and web client with `dotnet run`
3. **Service Discovery**: Web client automatically finds the API server
4. **Unified Monitoring**: Dashboard shows logs, metrics, and traces
5. **Development Productivity**: Fast iterative development with live reload
6. **Production Ready**: Generate deployment manifests for cloud deployment

## Configuration

### Python Server Configuration
The Python server runs as a Docker container configured in `Program.cs`:
```csharp
var apiServer = builder.AddDockerfile("apiserver", "../server")
    .WithHttpEndpoint(port: 8000, targetPort: 8000, name: "apiendpoint", isProxied: false)
    .WithHttpHealthCheck("/health")
    .WithEnvironment("PYTHONUNBUFFERED", "1");
```

The Dockerfile uses the official NVIDIA NeMo container (`nvcr.io/nvidia/nemo:25.11.01`) with all ASR dependencies pre-installed.

### Client Configuration
Clients automatically receive the API server endpoint via environment variables:
- Variable: `services__apiserver__http__0`
- Format: `http://host:port`

## Troubleshooting

### "Docker not found" or "Cannot connect to Docker daemon"
- Ensure Docker is running (Docker Desktop on Windows/macOS)
- On Linux, ensure your user is in the `docker` group

### "Model not loading"
- Check Python server logs in Aspire dashboard
- Ensure the container has enough memory (model requires ~2GB)
- If using GPU, verify NVIDIA Container Toolkit is installed

### "Clients can't connect to server"
- Check Aspire dashboard for server status
- Verify server health endpoint is green
- Look for service discovery errors in logs

### "Port already in use"
- Stop other services using port 8000
- Or modify the port in `Program.cs`

### "GPU not detected in container"
- Install NVIDIA Container Toolkit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
- Verify with: `docker run --gpus all nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi`

## Deployment

To deploy the Aspire application to Azure:

```bash
# Generate deployment manifest
dotnet aspire manifest

# Deploy to Azure Container Apps
azd init
azd up
```

See [Azure Deployment Guide](../AZURE_DEPLOYMENT.md) for detailed instructions.

## Standalone Mode

The console client runs independently:

```bash
# Console Client (standalone)
cd ../clients/console && dotnet run -- audio.mp3
```

The server can also run independently via Docker:
```bash
# Server (Docker)
cd ../server
docker build -t nvidia-asr-server .
docker run -p 8000:8000 --gpus all nvidia-asr-server
```

## Learn More

- [.NET Aspire Documentation](https://learn.microsoft.com/en-us/dotnet/aspire/)
- [Aspire Docker Support](https://aspire.dev/app-host/withdockerfile/)
- [NVIDIA NeMo](https://github.com/NVIDIA-NeMo/NeMo)
- [Scenario 4 README](../README.md)
