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

# Run with local server
dotnet run audio.mp3

# Run with remote server
dotnet run audio.mp3 http://server:8000

# Build
dotnet build

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

### Test Server
```bash
# Root
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health

# Transcribe (with curl)
curl -X POST http://localhost:8000/transcribe \
  -F "file=@audio.mp3"
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
- Model: `nvidia/parakeet-tdt-0.6b-v2`
- Supported formats: WAV, MP3, FLAC

### Console Client
- API URL: Command-line argument (default: `http://localhost:8000`)

### Web Client
- API URL: `wwwroot/appsettings.json`

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
