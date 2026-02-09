# C# Console Client for NVIDIA ASR Transcription

## Description

Command-line client for sending audio files to the NVIDIA ASR transcription server.

## Requirements

- .NET 10.0 SDK

## Installation

```bash
cd scenario4/clients/console
dotnet restore
```

## Usage

**Basic usage:**
```bash
dotnet run audio_file.mp3
```

**Custom server URL:**
```bash
dotnet run audio_file.mp3 http://server-url:8000
```

**Async job mode (for long audio files):**
```bash
dotnet run audio.mp3 --async
```

**Model selection (Canary for multilingual):**
```bash
dotnet run audio.mp3 --model canary --language es
```

**All available CLI flags:**

| Flag | Short | Description |
|------|-------|-------------|
| `--async` | `-a` | Use async job mode with status polling |
| `--model` | `-m` | Model: `parakeet` (default) or `canary` |
| `--language` | `-l` | Language: `en`, `es`, `de`, `fr` (for Canary model) |
| `--no-timestamps` | | Disable timestamp generation (Parakeet only) |
| `--generate-assets` | | Generate podcast assets (title, description, tags) via NIM |
| `--transcript-file` | | Path to a transcript file for standalone asset generation |
| `--nim-url` | | NIM endpoint URL (default: from Aspire service discovery) |

## Building

**Build:**
```bash
dotnet build
```

**Publish (self-contained):**
```bash
dotnet publish -c Release -r win-x64 --self-contained
dotnet publish -c Release -r linux-x64 --self-contained
```

## Examples

```bash
# Transcribe a WAV file
dotnet run audio.wav

# Transcribe an MP3 file with custom server
dotnet run podcast.mp3 http://api.example.com:8000

# Async mode with Canary model and German language
dotnet run audio.mp3 --model canary -l de --async

# Generate podcast assets after transcription
dotnet run audio.mp3 --generate-assets

# Generate assets from an existing transcript file
dotnet run --generate-assets --transcript-file transcript.txt

# Run built executable
./bin/Release/net10.0/TranscriptionClient audio.mp3
```

## Output

The client displays:
- Server health check status
- Upload progress
- Full transcription text
- First 5 timestamp segments
- Success/error messages
