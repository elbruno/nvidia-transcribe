# Scenario 4 Usage Examples

This guide shows practical examples of using the client-server architecture for audio transcription.

## Example 1: Local Development with Console Client

**Scenario**: Developer testing transcription locally

### Step 1: Start the Server
```bash
cd scenario4/server

# Create virtual environment (first time only)
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies (first time only)
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
python ../../fix_lhotse.py

# Start server
uvicorn app:app --host 0.0.0.0 --port 8000
```

Wait for the model to load (you'll see "Model loaded successfully").

### Step 2: Test with Console Client
```bash
# In a new terminal
cd scenario4/clients/console

# Transcribe an audio file
dotnet run my_podcast.mp3
```

**Output:**
```
=== NVIDIA ASR Transcription Client ===

Checking server at http://localhost:8000...
Server is healthy ✓

Uploading and transcribing: my_podcast.mp3

=== TRANSCRIPTION RESULT ===
File: my_podcast.mp3
Timestamp: 2026-02-04T19:45:00

Text:
Hello and welcome to today's podcast...

=== SEGMENTS (5) ===
[00:00:00.000 - 00:00:03.500] Hello and welcome
[00:00:03.500 - 00:00:07.200] to today's podcast
...

✓ Transcription completed successfully
```

## Example 2: Docker Deployment with Web Client

**Scenario**: Team deployment using Docker and web interface

### Step 1: Build and Run Server in Docker
```bash
cd scenario4/server

# Build container
docker build -t nvidia-asr-server .

# Run with GPU support
docker run -d -p 8000:8000 --gpus all --name asr-server nvidia-asr-server

# Check logs
docker logs -f asr-server
```

### Step 2: Access via Aspire
```bash
cd scenario4/AppHost

# Start Aspire orchestration
dotnet run
```

This will start:
1. The Python server (already running in Docker)
2. The Blazor web client
3. Aspire dashboard for monitoring

Access the web client via the URL shown in the Aspire dashboard.

### Step 2b: Access Console Client (Standalone)
```bash
cd scenario4/clients/console

# Run with audio file
dotnet run -- ../../test_audio.mp3
```

## Example 3: Azure Production Deployment

**Scenario**: Production deployment on Azure with web client

### Step 1: Deploy Server to Azure Container Apps
```bash
# Create resource group
az group create --name nvidia-asr-rg --location westus2

# Create container registry
az acr create --resource-group nvidia-asr-rg --name myasracr --sku Basic

# Build and push image
az acr build \
  --registry myasracr \
  --image nvidia-asr:latest \
  --file scenario4/server/Dockerfile \
  scenario4/server

# Create Container Apps environment
az containerapp env create \
  --name asr-env \
  --resource-group nvidia-asr-rg \
  --location westus2

# Deploy container app
az containerapp create \
  --name asr-api \
  --resource-group nvidia-asr-rg \
  --environment asr-env \
  --image myasracr.azurecr.io/nvidia-asr:latest \
  --target-port 8000 \
  --ingress external \
  --cpu 2 \
  --memory 4Gi

# Get the URL
az containerapp show \
  --name asr-api \
  --resource-group nvidia-asr-rg \
  --query properties.configuration.ingress.fqdn
```

### Step 2: Use the API

With the server deployed to Azure, you can use either client:

**Console Client (Standalone):**
```bash
cd scenario4/clients/console
dotnet run -- audio.mp3
# When prompted, provide the Azure API URL: https://asr-api.azurecontainerapps.io
```

**Web Client (via Aspire locally, connecting to Azure server):**
Configure the API endpoint to point to your Azure Container App URL in the Aspire configuration.
dotnet publish -c Release -o ./publish

# Deploy to Azure Static Web Apps
az staticwebapp create \
  --name asr-webapp \
  --resource-group nvidia-asr-rg \
  --source ./publish/wwwroot \
  --location westus2
```

## Example 4: Batch Processing with Console Client

**Scenario**: Process multiple audio files

### Create Batch Script

**Windows (PowerShell):**
```powershell
# process-batch.ps1
$files = Get-ChildItem -Path ".\audio" -Filter "*.mp3"
foreach ($file in $files) {
    Write-Host "Processing: $($file.Name)"
    dotnet run $file.FullName
}
```

**Linux/macOS (Bash):**
```bash
#!/bin/bash
# process-batch.sh
for file in audio/*.mp3; do
    echo "Processing: $file"
    dotnet run "$file"
done
```

### Run Batch Processing
```bash
# Make script executable (Linux/macOS)
chmod +x process-batch.sh

# Run
./process-batch.sh  # Linux/macOS
# or
./process-batch.ps1  # Windows
```

## Example 5: Integration with Python Application

**Scenario**: Use the API from a Python application

```python
import requests

def transcribe_audio(file_path, api_url="http://localhost:8000"):
    """Transcribe an audio file using the API."""
    
    # Check server health
    health = requests.get(f"{api_url}/health").json()
    if not health['model_loaded']:
        raise Exception("Server model not loaded")
    
    # Upload and transcribe
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{api_url}/transcribe", files=files)
        response.raise_for_status()
        return response.json()

# Usage
result = transcribe_audio('audio.mp3')
print(f"Transcription: {result['text']}")
print(f"Segments: {len(result['segments'])}")
```

## Example 6: Integration with JavaScript/Node.js

**Scenario**: Use the API from a Node.js application

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function transcribeAudio(filePath, apiUrl = 'http://localhost:8000') {
    // Check health
    const health = await axios.get(`${apiUrl}/health`);
    if (!health.data.model_loaded) {
        throw new Error('Server model not loaded');
    }
    
    // Upload and transcribe
    const formData = new FormData();
    formData.append('file', fs.createReadStream(filePath));
    
    const response = await axios.post(`${apiUrl}/transcribe`, formData, {
        headers: formData.getHeaders()
    });
    
    return response.data;
}

// Usage
transcribeAudio('audio.mp3')
    .then(result => {
        console.log('Transcription:', result.text);
        console.log('Segments:', result.segments.length);
    })
    .catch(err => console.error('Error:', err));
```

## Example 7: Custom Web Client with React

**Scenario**: Build a custom React frontend

```jsx
import React, { useState } from 'react';
import axios from 'axios';

function TranscriptionUpload() {
    const [file, setFile] = useState(null);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    
    const API_URL = 'http://localhost:8000';
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) return;
        
        setLoading(true);
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await axios.post(`${API_URL}/transcribe`, formData);
            setResult(response.data);
        } catch (error) {
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <div>
            <h1>Audio Transcription</h1>
            <form onSubmit={handleSubmit}>
                <input 
                    type="file" 
                    accept=".wav,.mp3,.flac"
                    onChange={(e) => setFile(e.target.files[0])}
                />
                <button type="submit" disabled={loading}>
                    {loading ? 'Processing...' : 'Transcribe'}
                </button>
            </form>
            
            {result && (
                <div>
                    <h2>Result</h2>
                    <p>{result.text}</p>
                    <h3>Segments ({result.segments.length})</h3>
                    {result.segments.map((seg, i) => (
                        <div key={i}>
                            [{seg.start.toFixed(2)} - {seg.end.toFixed(2)}] {seg.text}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default TranscriptionUpload;
```

## Performance Tips

### Server Optimization
1. Keep model loaded (it persists across requests)
2. Use GPU for production workloads
3. Consider request queuing for high concurrency
4. Set appropriate resource limits

### Client Optimization
1. Implement retry logic for network errors
2. Show upload progress for large files
3. Cache results when appropriate
4. Handle timeout scenarios gracefully

## Security Best Practices

1. **Authentication**: Add API keys or OAuth
2. **Rate Limiting**: Prevent abuse
3. **File Validation**: Check file size and type
4. **HTTPS**: Use TLS in production
5. **CORS**: Restrict to known origins

## Troubleshooting

### Issue: "Connection refused"
**Solution**: Ensure server is running and accessible
```bash
curl http://localhost:8000/health
```

### Issue: "Model not loaded"
**Solution**: Wait for model to load on server startup (check logs)

### Issue: "CORS error" in web client
**Solution**: Verify CORS is enabled in `server/app.py` and origins are allowed

### Issue: Slow transcription
**Solution**: 
- Use GPU mode
- Increase server resources
- Reduce concurrent requests

## Additional Resources

- Main README: `../README.md`
- API Documentation: `http://localhost:8000/docs` (when server is running)
- Azure Deployment Guide: `../AZURE_DEPLOYMENT.md`
- Quick Reference: `../QUICKREF.md`
