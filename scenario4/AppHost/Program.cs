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

// NVIDIA NIM LLM container – used for podcast asset generation.
// The model image can be overridden via configuration (key: NIM_IMAGE).
// Default: meta/llama-3.2-3b-instruct (3B params, ~6 GB VRAM, fits alongside ASR on 12 GB cards).
// NGC_API_KEY must be set in user-secrets or environment for the NIM container to authenticate.
var nimModelImage = builder.Configuration["NIM_IMAGE"]
    ?? "nvcr.io/nim/meta/llama-3.2-3b-instruct";

var nimLlm = builder.AddContainer("nim-llm", nimModelImage, "latest")
    .WithHttpEndpoint(port: 8001, targetPort: 8000, name: "http", isProxied: false)
    .WithHttpHealthCheck("/v1/health/ready")
    .WithEnvironment("NGC_API_KEY", builder.Configuration["NGC_API_KEY"] ?? "")
    .WithVolume("nim-model-cache", "/opt/nim/.cache")
    .WithContainerRuntimeArgs("--gpus=all")
    .WithContainerRuntimeArgs("--dns=8.8.8.8")  // Ensure DNS resolution for NGC model downloads
    .WithLifetime(ContainerLifetime.Persistent);

// Add server-side Blazor web client with Aspire service defaults.
// Both the ASR server and the NIM LLM endpoints are injected via environment variables
// so the webapp can reach them through Aspire service discovery.
var webappClient = builder.AddProject<Projects.TranscriptionWebApp2>("webappClient")
    .WithEnvironment("services__apiserver__http__0", apiServer.GetEndpoint("http"))
    .WithEnvironment("services__nim-llm__http__0", nimLlm.GetEndpoint("http"))
    .WithReference(appInsights)
    .WaitFor(apiServer);

builder.Build().Run();
