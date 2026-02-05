# NVIDIA Transcription Web App (Server-Side Blazor)

A server-side Blazor web application for NVIDIA ASR audio transcription, built with .NET Aspire service defaults.

## Features

- **Audio File Upload**: Upload WAV, MP3, or FLAC files (up to 50MB)
- **Real-time Transcription**: Get transcription results with timestamps
- **Aspire Integration**: Full integration with .NET Aspire service discovery and health checks
- **Modern UI**: Responsive design with Bootstrap styling

## Architecture

This is a **server-side Blazor** application that:
- Uses Aspire service defaults for OpenTelemetry, health checks, and service discovery
- Communicates with the Python FastAPI backend via HTTP
- Provides a rich, interactive UI without WebAssembly

## Project Structure

```
webapp/
├── Components/
│   ├── App.razor              # Main app component
│   ├── Routes.razor           # Routing configuration
│   ├── _Imports.razor         # Global usings
│   ├── Layout/
│   │   ├── MainLayout.razor   # Main layout with sidebar
│   │   └── NavMenu.razor      # Navigation menu
│   └── Pages/
│       ├── Home.razor         # Landing page
│       └── Transcribe.razor   # Transcription page
├── Services/
│   └── TranscriptionApiService.cs  # API client service
├── wwwroot/
│   └── app.css                # Application styles
├── Program.cs                 # Application entry point
└── TranscriptionWebApp2.csproj
```

## Running with Aspire

The recommended way to run this application is via the Aspire AppHost:

```bash
cd scenario4/AppHost
dotnet run
```

This will:
1. Start the Python FastAPI server
2. Start this web application
3. Configure service discovery automatically

## Standalone Mode

To run standalone (requires API server running separately):

```bash
cd scenario4/clients/webapp
dotnet run
```

Configure the API endpoint in `appsettings.json` if not using Aspire.

## Key Differences from Blazor WebAssembly Client

| Feature | Blazor WebAssembly (blazor/) | Server-Side Blazor (webapp/) |
|---------|------------------------------|------------------------------|
| Rendering | Client-side | Server-side |
| Service Discovery | Manual URL config | Aspire service discovery |
| Health Checks | None | Built-in via ServiceDefaults |
| OpenTelemetry | None | Full observability |
| Load | Downloaded to browser | Runs on server |

## Dependencies

- .NET 10.0
- NvidiaTranscribe.ServiceDefaults (Aspire shared project)
- Microsoft.Extensions.Http.Resilience (via ServiceDefaults)
- Microsoft.Extensions.ServiceDiscovery (via ServiceDefaults)
