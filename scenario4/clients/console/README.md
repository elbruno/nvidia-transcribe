# C# Console Client for NVIDIA ASR Transcription

## Description

Command-line client for sending audio files to the NVIDIA ASR transcription server.

## Requirements

- .NET 8.0 SDK

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

# Run built executable
./bin/Release/net8.0/TranscriptionClient audio.mp3
```

## Output

The client displays:
- Server health check status
- Upload progress
- Full transcription text
- First 5 timestamp segments
- Success/error messages
