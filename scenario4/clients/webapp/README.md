# NVIDIA Transcription Web App (Server-Side Blazor)

A server-side Blazor web application for NVIDIA ASR audio transcription, built with .NET Aspire service defaults.

## Features

- **Audio File Upload**: Upload WAV, MP3, or FLAC files (up to 50MB) via drag-and-drop or file picker
- **Dual Model Support**: Choose between Parakeet (English) and Canary-1B (multilingual) models
- **Side-by-Side Layout**: File selection and configuration panels in collapsible columns
- **Fixed Progress Log**: Bottom-pinned log panel with expand/collapse and entry count badge
- **Tabbed Results**: Text, SRT, and TXT output tabs with copy-to-clipboard and download buttons
- **Client-Side SRT Generation**: Generates SRT subtitle content from transcript segments
- **Async Job Management**: Background transcription with real-time status polling and cancellation
- **Aspire Integration**: Full integration with .NET Aspire service discovery and health checks
- **Modern UI**: Responsive design with collapsible sections and JS interop for copy/download

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
│       ├── Transcribe.razor   # Transcription page
│       └── PodcastAssets.razor # NIM podcast asset generation page
├── Services/
│   ├── TranscriptionApiService.cs  # ASR API client service
│   └── NimPodcastService.cs        # NIM LLM client for podcast assets
├── wwwroot/
│   ├── app.css                # Application styles
│   └── app.js                 # JS interop (copy, download, scroll)
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

## Key Differences from Standalone Console Client

| Feature | Console Client | Server-Side Blazor (webapp/) |
|---------|----------------|------------------------------|
| Interface | Command-line | Web browser |
| Orchestration | Standalone (not in Aspire) | Orchestrated by Aspire |
| Service Discovery | Manual URL | Aspire service discovery |
| Health Checks | None | Built-in via ServiceDefaults |
| OpenTelemetry | None | Full observability |
| Usage | Local files via CLI | File upload via browser |

## Dependencies

- .NET 10.0
- ServiceDefaults (Aspire shared project)
- Microsoft.Extensions.Http.Resilience (via ServiceDefaults)
- Microsoft.Extensions.ServiceDiscovery (via ServiceDefaults)
- OpenAI NuGet package (for NIM LLM integration)

## NIM Podcast Asset Generation

The web app includes a **Podcast Assets** page (`/podcast-assets`) powered by an NVIDIA NIM LLM container:

- **Paste mode**: Paste a transcript directly to generate episode title, description, and tags
- **From transcription**: Navigate from the Transcribe page results to generate assets automatically
- Uses the OpenAI-compatible API provided by the NIM container
- Requires NGC API key configured in Aspire user secrets

See the [Scenario 4 README](../../README.md) for NIM setup instructions.
