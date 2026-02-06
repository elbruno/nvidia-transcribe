# Scenario 4 Quick Reference

## Server Commands

### Local Development
```bash
# Setup
cd scenario4/server
python3.12 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
python ../../fix_lhotse.py

# Run server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Docker
```bash
# Build
cd scenario4/server
docker build -t nvidia-asr-server .

# Run with GPU
docker run -p 8000:8000 --gpus all nvidia-asr-server

# Run CPU-only
docker run -p 8000:8000 nvidia-asr-server
```

### Azure Deployment
```bash
# Build and push to ACR
az acr build --registry <registry> --image nvidia-asr:latest scenario4/server

# Deploy to Container Apps
az containerapp create \
  --name nvidia-asr-api \
  --resource-group <rg> \
  --environment <env> \
  --image <registry>.azurecr.io/nvidia-asr:latest \
  --target-port 8000 \
  --ingress external \
  --cpu 2 \
  --memory 4Gi
```

## Client Commands

### C# Console Client
```bash
cd scenario4/clients/console

# Run with local server (synchronous mode, default Parakeet model)
dotnet run audio.mp3

# Run with async job mode
dotnet run audio.mp3 --async

# Run with Canary model and Spanish language
dotnet run audio.mp3 --model canary --language es

# Run with Canary model, German language, async mode
dotnet run audio.mp3 --model canary -l de --async

# Run with remote server
dotnet run audio.mp3 http://server:8000

# Run with all options combined
dotnet run audio.mp3 http://server:8000 --model canary -l fr --async

# Disable timestamps (only affects Parakeet model)
dotnet run audio.wav --no-timestamps

# Build
dotnet build
```

**Console Client Options:**
- `--async, -a` - Use async job mode with status polling
- `--model, -m <model>` - Model: 'parakeet' (default) or 'canary'
- `--language, -l <lang>` - Language: en, es, de, fr (for Canary model)
- `--no-timestamps` - Disable timestamp generation

### Server-Side Blazor Web App
```bash
cd scenario4/AppHost

# Run with Aspire (recommended)
dotnet run

# This starts both the Python server and web client
```

### Console Client (Standalone)
```bash
cd scenario4/clients/console

# Run
dotnet run -- <audio-file-path>

# Example
dotnet run -- ../../test_audio.mp3

# Publish
dotnet publish -c Release -r win-x64 --self-contained
```

## API Endpoints

### Health & Info
```bash
# Root
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health
```

### Synchronous Transcription
```bash
# Transcribe with default model (Parakeet, English)
curl -X POST http://localhost:8000/transcribe \
  -F "file=@audio.mp3"

# Transcribe with Canary model, Spanish language
curl -X POST http://localhost:8000/transcribe \
  -F "file=@audio.mp3" \
  -F "model=canary" \
  -F "language=es"

# Transcribe with Canary model, German, no timestamps
curl -X POST http://localhost:8000/transcribe \
  -F "file=@audio.mp3" \
  -F "model=canary" \
  -F "language=de" \
  -F "include_timestamps=false"
```

**Parameters:**
- `file` (required) - Audio file (.wav, .mp3, .flac)
- `model` (optional) - "parakeet" (default) or "canary"
- `language` (optional) - "en", "es", "de", "fr" (for Canary model)
- `include_timestamps` (optional) - "true" (default) or "false"

### Async Job Management
```bash
# Start async job with default model
curl -X POST http://localhost:8000/transcribe/async \
  -F "file=@audio.mp3"
# Returns: {"job_id": "...", "status": "pending", "message": "..."}

# Start async job with Canary model, French
curl -X POST http://localhost:8000/transcribe/async \
  -F "file=@audio.mp3" \
  -F "model=canary" \
  -F "language=fr"

# Check job status
curl http://localhost:8000/jobs/{job_id}/status

# Get job result (when completed)
curl http://localhost:8000/jobs/{job_id}/result

# Cancel job
curl -X POST http://localhost:8000/jobs/{job_id}/cancel
```

### Example Workflow
```bash
# 1. Start job
JOB_ID=$(curl -X POST http://localhost:8000/transcribe/async \
  -F "file=@audio.mp3" | jq -r '.job_id')

# 2. Poll status
while true; do
  STATUS=$(curl http://localhost:8000/jobs/$JOB_ID/status | jq -r '.status')
  echo "Status: $STATUS"
  if [ "$STATUS" = "completed" ]; then break; fi
  sleep 5
done

# 3. Get result
curl http://localhost:8000/jobs/$JOB_ID/result
```

## Quick Test

```bash
# Test server is working
cd scenario4
python test_server.py

# Test with custom URL
python test_server.py http://server:8000
```

## Configuration

### Server
- Port: 8000 (default)
- Models: 
  - `nvidia/parakeet-tdt-0.6b-v2` (English, with timestamps)
  - `nvidia/canary-1b` (Multilingual: en, es, de, fr)
- Supported formats: WAV, MP3, FLAC
- Default model: Parakeet (loaded at startup)
- Canary model: Loaded on-demand when first requested

### Console Client
- API URL: Command-line argument (default: `http://localhost:8000`)
- Model: `--model` flag (default: parakeet)
- Language: `--language` flag (for Canary model)

### Web Client
- API URL: Configured via Aspire service discovery
- Model/Language: Selected via UI dropdowns

## Common Issues

### Server won't start
- Check Python version (3.10-3.12)
- Run `python ../../fix_lhotse.py`
- Check GPU/CUDA if using GPU mode

### Client can't connect
- Verify server is running: `curl http://localhost:8000/health`
- Check firewall rules
- Verify API URL in client config

### CORS errors (web client)
- Server has CORS enabled for all origins by default
- For production, configure in `server/app.py`

## Documentation

- Main README: `scenario4/README.md`
- Server docs: `scenario4/server/README.md`
- Azure deployment: `scenario4/AZURE_DEPLOYMENT.md`
- Console client: `scenario4/clients/console/README.md`
- Web client: `scenario4/clients/webapp/README.md`
- Aspire orchestration: `scenario4/AppHost/README.md`
