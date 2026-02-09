# GPU Configuration for NVIDIA Transcription Server

## Current Situation

When running the Aspire orchestration, you may see logs indicating:
- "NVIDIA Driver was not detected"  
- "GPU not available - running on CPU"

This happens because the Docker container needs explicit GPU passthrough configuration.

## Understanding the File Upload Feature

**Important**: The file upload functionality is already fully implemented in the Blazor webapp.

To use it:
1. Start Aspire: `cd scenario4/AppHost && dotnet run`
2. Open the webapp from the Aspire dashboard
3. Click "Transcribe" in the navigation menu (or "Start Transcribing" button on home page)
4. You'll see a drag-and-drop file upload interface

The transcription page (`/transcribe`) includes:
- Drag and drop file upload zone
- Support for WAV, MP3, FLAC formats (up to 50MB)
- Real-time processing with progress indicator
- Results display with timestamps

## Enabling GPU Acceleration in Aspire

The Aspire AppHost configuration in `scenario4/AppHost/Program.cs` needs modification to pass GPU access to the Docker container.

### Prerequisites on Host Machine

1. **NVIDIA GPU drivers** must be installed
2. **NVIDIA Container Toolkit** must be installed
   - Windows: [NVIDIA Container Toolkit Windows](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#installation-on-windows)
   - Linux: [NVIDIA Container Toolkit Linux](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#installation-on-linux)

Verify installation:
```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Modifying AppHost Configuration

Edit `scenario4/AppHost/Program.cs`:

Find this section:
```csharp
var apiServer = builder.AddDockerfile("apiserver", "../server")
    .WithHttpEndpoint(port: 8000, targetPort: 8000, name: "http", isProxied: false)
    .WithHttpHealthCheck("/health")
    .WithEnvironment("PYTHONUNBUFFERED", "1")
    .WithEnvironment("HF_HOME", "/root/.cache/huggingface")
    .WithVolume("hf-model-cache", "/root/.cache/huggingface");
```

Add GPU runtime argument:
```csharp
var apiServer = builder.AddDockerfile("apiserver", "../server")
    .WithHttpEndpoint(port: 8000, targetPort: 8000, name: "http", isProxied: false)
    .WithHttpHealthCheck("/health")
    .WithEnvironment("PYTHONUNBUFFERED", "1")
    .WithEnvironment("HF_HOME", "/root/.cache/huggingface")
    .WithVolume("hf-model-cache", "/root/.cache/huggingface")
    .WithContainerRuntimeArgs("--gpus=all");  // ADD THIS LINE
```

### Alternative: Environment Variable Approach

You can also set GPU devices via environment variable:
```csharp
    .WithEnvironment("NVIDIA_VISIBLE_DEVICES", "all")
```

However, the `WithContainerRuntimeArgs` method is preferred as it explicitly passes Docker runtime flags.

## Verifying GPU is Active

After starting Aspire with GPU configuration:

1. Check the API server logs in Aspire dashboard
2. Look for startup message showing device:
   ```
   Model loaded successfully on device: cuda:0
   GPU: NVIDIA GeForce RTX 3080
   ```

3. Test the health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```
   
   Response should show GPU information (if endpoint is enhanced).

## CPU Fallback Behavior

If GPU is not available, the system automatically falls back to CPU mode:
- Transcription still works correctly
- Processing is significantly slower
- No code changes needed - PyTorch/NeMo handle fallback automatically

Typical performance difference:
- **GPU**: ~5-15 seconds for 1 minute of audio
- **CPU**: ~30-90 seconds for 1 minute of audio

## Troubleshooting

### "NVIDIA Driver was not detected"
- Verify drivers on host: `nvidia-smi`
- Check Container Toolkit installation
- Restart Docker service after installing Container Toolkit

### Container starts but no GPU in logs
- Verify `WithContainerRuntimeArgs("--gpus=all")` is added
- Check Aspire dashboard for container runtime errors
- Try running container manually: `docker run --gpus all nvcr.io/nvidia/nemo:25.11.01 nvidia-smi`

### "docker: Error response from daemon: could not select device driver"
- NVIDIA Container Toolkit not installed correctly
- Follow installation guide for your OS
- Windows: May require Docker Desktop with WSL2 backend

## Development vs Production

### Development (Aspire)
- Add `WithContainerRuntimeArgs("--gpus=all")` to AppHost
- Good for testing GPU acceleration locally

### Production (Azure Container Apps, etc.)
- Check cloud provider's GPU instance offerings
- Azure: Use GPU-enabled Container Apps SKUs
- AWS: Use GPU-enabled Fargate or ECS instances
- May require different container runtime configurations per provider

## Summary

The key changes needed:
1. **No changes to file upload** - it already exists at `/transcribe` page
2. **Add one line to AppHost/Program.cs** - `WithContainerRuntimeArgs("--gpus=all")`
3. **Ensure host prerequisites** - NVIDIA drivers + Container Toolkit

The application gracefully handles both GPU and CPU modes, so GPU is an optimization, not a requirement.
