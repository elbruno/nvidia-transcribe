using Aspire.Hosting;

var builder = DistributedApplication.CreateBuilder(args);

// Application Insights for telemetry
IResourceBuilder<IResourceWithConnectionString>? appInsights;

if (builder.ExecutionContext.IsPublishMode)
{
    // PRODUCTION: Use Azure-provisioned services
    appInsights = builder.AddAzureApplicationInsights("appInsights");
}
else
{
    // DEVELOPMENT: Use connection strings from configuration
    appInsights = builder.AddConnectionString("appinsights", "APPLICATIONINSIGHTS_CONNECTION_STRING");
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
    .WithEnvironment("APPLICATIONINSIGHTS_CONNECTION_STRING", appInsights)  // App Insights (optional)
    .WithVolume("hf-model-cache", "/root/.cache/huggingface")  // Persist model downloads
    .WithContainerRuntimeArgs("--gpus=all")  // Enable GPU passthrough (requires NVIDIA Container Toolkit)
    .WithLifetime(ContainerLifetime.Persistent);

// Add server-side Blazor web client with Aspire service defaults
var webappClient = builder.AddProject<Projects.TranscriptionWebApp2>("webappClient")
    .WithEnvironment("services__apiserver__http__0", apiServer.GetEndpoint("http"))    
    .WithReference(appInsights) // App Insights (optional)
    .WaitFor(apiServer);

builder.Build().Run();
