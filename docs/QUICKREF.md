# Quick Reference Guide

Quick commands for each scenario:

## Scenario 1: Simple CLI
```bash
# Basic usage
python scenario1/transcribe.py audio.mp3

# Help
python scenario1/transcribe.py --help
```

## Scenario 2: Interactive Menu
```bash
# Run interactive menu
python scenario2/transcribe.py
```

## Scenario 3: Multilingual
```bash
# Spanish (default)
python scenario3/transcribe.py audio.mp3
python scenario3/transcribe.py audio.mp3 es

# English
python scenario3/transcribe.py audio.mp3 en

# German
python scenario3/transcribe.py audio.mp3 de

# French
python scenario3/transcribe.py audio.mp3 fr

# Help
python scenario3/transcribe.py --help
```

## Scenario 4: Client-Server Architecture
```bash
# Start with Aspire (recommended - starts server + web client)
cd scenario4/AppHost
dotnet run

# Start server standalone (Docker)
cd scenario4/server
docker build -t nvidia-asr-server .
docker run -p 8000:8000 --gpus all nvidia-asr-server

# Start server standalone (local venv)
cd scenario4/server
uvicorn app:app --host 0.0.0.0 --port 8000

# Console client
cd scenario4/clients/console
dotnet run audio.mp3                            # Default (Parakeet)
dotnet run audio.mp3 --async                    # Async job mode
dotnet run audio.mp3 --model canary -l es       # Canary, Spanish
dotnet run audio.mp3 --generate-assets          # Generate podcast assets

# API (curl)
curl -X POST http://localhost:8000/transcribe -F "file=@audio.mp3"
curl -X POST http://localhost:8000/transcribe -F "file=@audio.mp3" -F "model=canary" -F "language=es"
```

## Scenario 5: Voice Agent
```bash
# Setup (separate venv recommended)
cd scenario5
pip install -r requirements.txt

# Install pynini stub (Windows only — enables TTS without C++ deps)
pip install pynini_stub/

# Run the voice agent server
python app.py
# Open http://localhost:8000 in your browser

# Hold the talk button, speak, release to get a response
# Toggle "Smart Mode" to enable LLM-powered responses
```

## Backward Compatibility
```bash
# Original script still works
python transcribe.py
```

## Environment Validation
```bash
# Check Python, PyTorch, CUDA, dependencies
python utils/check_environment.py

# Check model download status
python utils/check_models.py
```

## Output Location
All transcriptions are saved to: `output/`

## Model Information
- **Scenario 1 & 2**: Parakeet TDT 0.6B v2 (English only, Commercial OK)
- **Scenario 3**: Canary-1B (Multilingual, Non-commercial only)
- **Scenario 5 ASR**: Parakeet TDT 0.6B v2 (English only, Commercial OK)
- **Scenario 5 TTS**: FastPitch + HiFi-GAN (English, Commercial OK)
- **Scenario 5 LLM**: TinyLlama-1.1B-Chat (Smart Mode, Apache-2.0)

For detailed examples, see [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
