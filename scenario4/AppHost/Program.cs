using Aspire.Hosting;

var builder = DistributedApplication.CreateBuilder(args);

// Add Python FastAPI server using Docker
// The Dockerfile is located in the ../server directory
// NOTE: GPU access requires NVIDIA Container Toolkit on host - see GPU_SETUP_GUIDE.md
var apiServer = builder.AddDockerfile("apiserver", "../server")
    .WithImageTag("nvidia-transcription-api:latest")  // Reuse cached image if unchanged
    .WithHttpEndpoint(port: 8000, targetPort: 8000, name: "http", isProxied: false)
    .WithHttpHealthCheck("/health")
    .WithEnvironment("PYTHONUNBUFFERED", "1")  // For real-time logging
    .WithEnvironment("HF_HOME", "/root/.cache/huggingface")  // Hugging Face cache location
    .WithVolume("hf-model-cache", "/root/.cache/huggingface")  // Persist model downloads
    .WithContainerRuntimeArgs("--gpus=all");  // Enable GPU passthrough (requires NVIDIA Container Toolkit)

// Add server-side Blazor web client with Aspire service defaults
var webappClient = builder.AddProject<Projects.TranscriptionWebApp2>("webappClient")
    .WithEnvironment("services__apiserver__http__0", apiServer.GetEndpoint("http"))
    .WaitFor(apiServer);

builder.Build().Run();
