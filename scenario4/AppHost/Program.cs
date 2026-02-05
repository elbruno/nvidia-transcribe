using Aspire.Hosting;

var builder = DistributedApplication.CreateBuilder(args);

// Optional: Get Application Insights connection string from configuration
var appInsightsConnection = builder.Configuration["APPLICATIONINSIGHTS_CONNECTION_STRING"] ?? "";
var hasMonitoring = !string.IsNullOrWhiteSpace(appInsightsConnection);

if (hasMonitoring)
{
    Console.WriteLine("✅ Application Insights monitoring enabled");
}
else
{
    Console.WriteLine("ℹ️  Running without Application Insights (telemetry disabled)");
}

// Add Python FastAPI server using Docker
// The Dockerfile is located in the ../server directory
// NOTE: GPU access requires NVIDIA Container Toolkit on host - see GPU_SETUP_GUIDE.md
var apiServer = builder.AddDockerfile("apiserver", "../server")
    .WithImageTag("latest")  // Reuse cached image if unchanged
    .WithHttpEndpoint(port: 8000, targetPort: 8000, name: "http", isProxied: false)
    .WithHttpHealthCheck("/health")
    .WithEnvironment("PYTHONUNBUFFERED", "1")  // For real-time logging
    .WithEnvironment("HF_HOME", "/root/.cache/huggingface")  // Hugging Face cache location
    .WithEnvironment("APPLICATIONINSIGHTS_CONNECTION_STRING", appInsightsConnection)  // App Insights (optional)
    .WithVolume("hf-model-cache", "/root/.cache/huggingface")  // Persist model downloads
    .WithContainerRuntimeArgs("--gpus=all")  // Enable GPU passthrough (requires NVIDIA Container Toolkit)
    .WithLifetime(ContainerLifetime.Persistent);

// Add server-side Blazor web client with Aspire service defaults
var webappClient = builder.AddProject<Projects.TranscriptionWebApp2>("webappClient")
    .WithEnvironment("services__apiserver__http__0", apiServer.GetEndpoint("http"))
    .WithEnvironment("APPLICATIONINSIGHTS_CONNECTION_STRING", appInsightsConnection)  // App Insights (optional)
    .WaitFor(apiServer);

builder.Build().Run();
