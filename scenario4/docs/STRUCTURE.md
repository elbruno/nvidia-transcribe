# Scenario 4: Client-Server Architecture

## Overview

This directory contains a complete client-server implementation for audio transcription using .NET Aspire:

```
scenario4/
├── AppHost/                    # .NET Aspire orchestration
│   ├── Program.cs             # Aspire orchestration config
│   └── NvidiaTranscribe.AppHost.csproj
├── ServiceDefaults/           # Shared Aspire service defaults
│   ├── Extensions.cs          # OpenTelemetry, health checks, service discovery
│   ├── TranscriptionTelemetry.cs  # Custom telemetry definitions
│   └── ServiceDefaults.csproj
├── server/                    # Python FastAPI server
│   ├── app.py                 # Main server application
│   ├── nvidia_asr_monitor.py  # NVIDIA ASR monitoring utilities
│   ├── requirements.txt       # Python dependencies (Linux/Docker)
│   ├── requirements-windows.txt  # Python dependencies (Windows)
│   ├── Dockerfile             # Container image with GPU support
│   └── setup-venv.ps1/.sh     # Virtual environment setup
├── clients/
│   ├── console/               # C# console client (standalone)
│   │   ├── Program.cs
│   │   └── TranscriptionClient.csproj
│   └── webapp/                # Server-side Blazor client
│       ├── Program.cs
│       ├── Components/
│       │   ├── App.razor
│       │   ├── Routes.razor
│       │   ├── _Imports.razor
│       │   ├── Layout/
│       │   └── Pages/
│       │       ├── Home.razor
│       │       ├── Transcribe.razor
│       │       └── PodcastAssets.razor
│       ├── Services/
│       │   ├── TranscriptionApiService.cs
│       │   └── NimPodcastService.cs
│       └── TranscriptionWebApp2.csproj
├── Directory.Build.props      # Shared MSBuild properties
├── NvidiaTranscribe.slnx      # Solution file
├── test_server.py             # Server integration test
└── README.md                  # Documentation
```

## Components

### Aspire AppHost
- **Technology**: .NET Aspire 13.1
- **Purpose**: Orchestrates Python server and web client
- **Features**: Service discovery, health checks, dashboard

### Service Defaults
- **Purpose**: Shared Aspire configuration
- **Features**: OpenTelemetry, resilience handlers, service discovery

### Python Server
- **Technology**: Python + FastAPI + Uvicorn
- **Model**: NVIDIA Parakeet + Canary (English + Multilingual)
- **Deployment**: Docker (with GPU support) or local venv
- **API**: REST endpoints for transcription
- **GPU**: Automatic GPU acceleration with CPU fallback

### Console Client
- **Technology**: C# / .NET 10.0
- **Usage**: Standalone command-line audio transcription
- **Features**: Independent of orchestration

### Server-Side Blazor Client
- **Technology**: Server-side Blazor / .NET 10.0
- **Usage**: Browser-based audio transcription (server-side)
- **Features**: Full Aspire integration, OpenTelemetry, health checks

## Quick Start

```bash
# From scenario4 directory
cd AppHost
dotnet run
```

This starts:
1. Python FastAPI server on port 8000 (with GPU/CPU detection)
2. Server-side Blazor web client
3. Aspire dashboard for monitoring

The console client can be run independently:
```bash
cd clients/console
dotnet run -- <audio-file-path>
```

Access the Aspire dashboard to see all services and their endpoints.

See [README.md](../README.md) for detailed setup and usage instructions.
