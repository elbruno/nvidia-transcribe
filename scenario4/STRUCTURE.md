# Scenario 4: Client-Server Architecture

## Overview

This directory contains a complete client-server implementation for audio transcription using .NET Aspire:

```
scenario4/
├── AppHost/                    # .NET Aspire orchestration
│   ├── Program.cs             # Aspire orchestration config
│   └── NvidiaTranscribe.AppHost.csproj
├── NvidiaTranscribe.ServiceDefaults/  # Shared Aspire service defaults
│   ├── Extensions.cs          # OpenTelemetry, health checks, service discovery
│   └── NvidiaTranscribe.ServiceDefaults.csproj
├── server/                     # Python FastAPI server
│   ├── app.py                 # Main server application
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Container image
│   └── setup-venv.ps1/.sh     # Virtual environment setup
├── clients/
│   ├── console/               # C# console client
│   │   ├── Program.cs
│   │   └── TranscriptionClient.csproj
│   ├── blazor/                # Blazor WebAssembly client
│   │   ├── Program.cs
│   │   ├── App.razor
│   │   ├── Pages/Index.razor
│   │   └── TranscriptionWebApp.csproj
│   └── webapp/                # Server-side Blazor client (NEW)
│       ├── Program.cs
│       ├── Components/
│       │   ├── App.razor
│       │   ├── Routes.razor
│       │   ├── Layout/
│       │   └── Pages/
│       ├── Services/
│       │   └── TranscriptionApiService.cs
│       └── TranscriptionWebApp2.csproj
├── NvidiaTranscribe.slnx      # Solution file
└── README.md                  # Documentation
```

## Components

### Aspire AppHost
- **Technology**: .NET Aspire 13.1
- **Purpose**: Orchestrates all services and clients
- **Features**: Service discovery, health checks, dashboard

### Service Defaults
- **Purpose**: Shared Aspire configuration
- **Features**: OpenTelemetry, resilience handlers, service discovery

### Python Server
- **Technology**: Python + FastAPI + Uvicorn
- **Model**: NVIDIA Parakeet (English)
- **Deployment**: Docker or local venv
- **API**: REST endpoints for transcription

### Console Client
- **Technology**: C# / .NET 10.0
- **Usage**: Command-line audio transcription
- **Features**: Aspire service discovery support

### Blazor WebAssembly Client
- **Technology**: Blazor WebAssembly / .NET 10.0
- **Usage**: Browser-based audio transcription (client-side)
- **Features**: File upload, real-time results display

### Server-Side Blazor Client (NEW)
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
1. Python FastAPI server on port 8000
2. Console client (available but not auto-launched)
3. Blazor WebAssembly client
4. Server-side Blazor client

Access the Aspire dashboard to see all services and their endpoints.

See [README.md](README.md) for detailed setup and usage instructions.
