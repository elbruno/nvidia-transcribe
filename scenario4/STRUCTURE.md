# Scenario 4: Client-Server Architecture

## Overview

This directory contains a complete client-server implementation for audio transcription:

```
scenario4/
├── server/                 # Python FastAPI server
│   ├── app.py             # Main server application
│   ├── requirements.txt   # Python dependencies
│   ├── Dockerfile         # Container image
│   └── .dockerignore
├── clients/
│   ├── console/           # C# console client
│   │   ├── Program.cs
│   │   └── TranscriptionClient.csproj
│   └── blazor/            # Blazor web app client
│       ├── Program.cs
│       ├── App.razor
│       ├── Pages/
│       │   └── Index.razor
│       ├── wwwroot/
│       │   ├── index.html
│       │   └── css/app.css
│       └── TranscriptionWebApp.csproj
└── README.md              # Documentation

## Components

### Server
- **Technology**: Python + FastAPI
- **Model**: NVIDIA Parakeet (English)
- **Deployment**: Docker container
- **API**: REST endpoints for transcription

### Console Client
- **Technology**: C# / .NET 8.0
- **Usage**: Command-line audio transcription
- **Platform**: Cross-platform (Windows, Linux, macOS)

### Web Client
- **Technology**: Blazor WebAssembly
- **Usage**: Browser-based audio transcription
- **Features**: File upload, real-time results display

## Quick Start

See [README.md](README.md) for detailed setup and usage instructions.
