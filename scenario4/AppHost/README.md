# .NET Aspire AppHost for NVIDIA ASR Transcription

This AppHost orchestrates the NVIDIA ASR transcription stack using .NET Aspire:
- Python FastAPI server (via Uvicorn) with GPU acceleration
- Server-side Blazor web client

**Note**: The console client is available as a standalone application and is not orchestrated by Aspire.

## Prerequisites

- **.NET 10.0 SDK** or later
- **Python 3.10-3.12** with all dependencies installed (see main [README.md](../README.md))
- **NVIDIA GPU** with CUDA support (recommended, but falls back to CPU automatically)

## Setup

1. **Install Python dependencies** (if not already done):
   ```bash
   cd ../server
   # Windows
   .\setup-venv.ps1
   # Linux/macOS
   ./setup-venv.sh
   cd ../AppHost
   ```

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
1. Launch the Aspire dashboard (typically at `http://localhost:15888`)
2. Start the Python FastAPI server (apiserver) with GPU/CPU detection
3. Start the server-side Blazor web client (webappClient)

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
┌───────────────┐    ┌──────────────────┐
│ Python Server │    │ Blazor WebApp    │
│  (FastAPI)    │◄───│ (Server-Side)    │
│  Port: 8000   │    └──────────────────┘
│  NVIDIA ASR   │              ▲
│  GPU/CPU Auto │              │
└───────────────┘         Service Discovery

  Console Client (Standalone - not orchestrated)
        │
        ▼
   API Server (http://localhost:8000)
```

## Benefits of Using Aspire

1. **Single Command Startup**: Start server and web client with `dotnet run`
2. **Service Discovery**: Web client automatically finds the API server
3. **Unified Monitoring**: Dashboard shows logs, metrics, and traces
4. **Development Productivity**: Fast iterative development with live reload
5. **Production Ready**: Generate deployment manifests for cloud deployment

## Configuration

### Python Server Configuration
The Python server is configured in `Program.cs`:
```csharp
var apiServer = builder.AddUvicornApp("apiserver", "../server", "app:app")
    .WithHttpEndpoint(port: 8000, name: "http")
    .WithExternalHttpEndpoints()
    .WithHttpHealthCheck("/health");
```

### Client Configuration
Clients automatically receive the API server endpoint via environment variables:
- Variable: `services__apiserver__http__0`
- Format: `http://host:port`

## Troubleshooting

### "Python not found"
- Ensure Python 3.10-3.12 is installed and in PATH
- Activate your virtual environment before running Aspire

### "Model not loading"
- Run `python ../utils/check_environment.py` to validate setup
- Ensure `fix_lhotse.py` was run after installing dependencies
- Check Python server logs in Aspire dashboard

### "Clients can't connect to server"
- Check Aspire dashboard for server status
- Verify server health endpoint is green
- Look for service discovery errors in logs

### "Port already in use"
- Stop other services using port 8000
- Or modify the port in `Program.cs`

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

The server can also run independently:
```bash
# Server
cd ../server && uvicorn app:app --host 0.0.0.0 --port 8000
```

## Learn More

- [.NET Aspire Documentation](https://learn.microsoft.com/en-us/dotnet/aspire/)
- [Aspire Python Support](https://learn.microsoft.com/en-us/dotnet/aspire/get-started/aspire-python)
- [Scenario 4 README](../README.md)
