# NVIDIA ASR Transcription Toolkit

> 🎙️ Demo repository for the **[Build a Voice-Enabled AI Agent in Minutes](https://developer.microsoft.com/en-us/reactor/events/26649/)** session at [Microsoft Reactor AI Apps & Agents Dev Days](https://developer.microsoft.com/en-us/reactor/series/s-1590/) (February 10, 2026). Brought to you by Microsoft & NVIDIA.

Local audio transcription using NVIDIA ASR models via the NeMo framework, organized into four scenarios:

| Scenario | Folder | Model | Use Case |
|----------|--------|-------|----------|
| **1. Simple CLI** | [`scenario1/`](scenario1/) | Parakeet (English) | Single file transcription |
| **2. Interactive Menu** | [`scenario2/`](scenario2/) | Parakeet (English) | Browse and select from local audio files |
| **3. Multilingual** | [`scenario3/`](scenario3/) | Canary-1B (Multilingual) | Spanish, English, German, French |
| **4. Client-Server** | [`scenario4/`](scenario4/) | Parakeet + Canary | REST API, .NET Aspire, Blazor web app, NIM LLM integration |

## Quick Start

```bash
# Setup (Python 3.10-3.12 only)
py -3.12 -m venv venv && venv\Scripts\activate          # Windows
pip install torch --index-url https://download.pytorch.org/whl/cu121  # GPU
pip install -r requirements.txt && python fix_lhotse.py

# Scenario 1: Transcribe a file
python scenario1/transcribe.py audio.mp3

# Scenario 3: Multilingual
python scenario3/transcribe.py audio.mp3 es

# Scenario 4: Client-server
cd scenario4/AppHost && dotnet run
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/QUICKREF.md](docs/QUICKREF.md) | Quick command reference for all scenarios |
| [docs/USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md) | Detailed examples and workflows |
| [docs/IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md) | Implementation details (Scenarios 1–3) |
| [scenario4/README.md](scenario4/README.md) | Scenario 4 full documentation |
| [scenario4/docs/](scenario4/docs/) | Architecture, deployment, testing guides |

## Requirements

- **Python 3.10–3.12** (3.13 not supported)
- NVIDIA GPU with CUDA recommended (CPU fallback available)
- ~2.5GB disk space for models

## Slides & Link Inventory

The [`slides/`](slides/) folder contains visual references from the **Microsoft × NVIDIA** session, along with curated link inventories for each slide.

| Slide | Description |
|-------|-------------|
| [Slide 6 — Azure AI Platform with NVIDIA Technologies](slides/slide06_azure_ai_platform_nvidia.md) | Overview of the joint Microsoft + NVIDIA stack across Build, Data, Models, Deployment, and Operations |

## References

- [NVIDIA Parakeet Model](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2) — English, CC-BY-4.0
- [NVIDIA Canary-1B Model](https://huggingface.co/nvidia/canary-1b) — Multilingual, CC-BY-NC-4.0
- [NeMo ASR Documentation](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/models.html)
- [Azure Deployment Example](https://huggingface.co/docs/microsoft-azure/foundry/examples/deploy-nvidia-parakeet-asr)
