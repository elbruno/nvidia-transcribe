using Aspire.Hosting;

var builder = DistributedApplication.CreateBuilder(args);

var moshiPort = int.TryParse(builder.Configuration["MOSHI_PORT"], out var mp) ? mp : 8998;
var appPort = int.TryParse(builder.Configuration["APP_PORT"], out var ap) ? ap : 8010;
var useGpu = ParseBool(builder.Configuration["USE_GPU"], defaultValue: true);
var cpuOffload = ParseBool(builder.Configuration["CPU_OFFLOAD"], defaultValue: false);
var useSsl = ParseBool(builder.Configuration["MOSHI_USE_SSL"], defaultValue: false);
var hfToken = builder.AddParameter("hf-token", secret: true);
var moshiEndpointName = useSsl ? "https" : "http";

var moshi = builder.AddDockerfile("scenario6-moshi", "..", "moshi/Dockerfile")
    .WithImageTag("latest")
    .WithEnvironment("HF_TOKEN", hfToken)
    .WithEnvironment("HF_HOME", builder.Configuration["HF_HOME"] ?? "/root/.cache/huggingface")
    .WithEnvironment("PYTHONUNBUFFERED", "1")
    .WithEnvironment("MOSHI_CPU_OFFLOAD", cpuOffload ? "1" : "0")
    .WithEnvironment("MOSHI_USE_SSL", useSsl ? "1" : "0")
    .WithEnvironment("MOSHI_HOST", "0.0.0.0")
    .WithEnvironment("MOSHI_PORT", moshiPort.ToString())
    .WithOtlpExporter()
    .WithVolume("hf-model-cache-scenario6", "/root/.cache/huggingface")
    .WithLifetime(ContainerLifetime.Persistent);

if (useSsl)
{
    moshi.WithHttpsEndpoint(port: moshiPort, targetPort: 8998, name: "https")
         .WithHttpHealthCheck("/health", endpointName: "https");
}
else
{
    moshi.WithHttpEndpoint(port: moshiPort, targetPort: 8998, name: "http")
         .WithHttpHealthCheck("/health", endpointName: "http");
}

if (useGpu)
{
    moshi.WithContainerRuntimeArgs("--gpus=all");
}

// Frontend service using hybrid orchestration:
// - DEVELOPMENT: Aspire Python integration (AddUvicornApp) for fast iteration and hot reload
// - PRODUCTION: Docker container (AddDockerfile) for consistency and deployment
// The moshi backend always uses Docker in both modes due to complexity (vendored code, custom startup)
IResourceBuilder<IResourceWithEndpoints> frontend;

if (builder.ExecutionContext.IsPublishMode)
{
    // PRODUCTION: Use Docker container for frontend
    frontend = builder.AddDockerfile("scenario6-frontend", "..", "Dockerfile")
        .WithImageTag("latest")
        .WithEnvironment("APP_PORT", appPort.ToString())
        .WithEnvironment("APP_HOST", "0.0.0.0")
        .WithEnvironment("MOSHI_WS_SCHEME", useSsl ? "wss" : "ws")
        .WithEnvironment("MOSHI_WS_URL", moshi.GetEndpoint(moshiEndpointName))
        .WithHttpEndpoint(port: appPort, targetPort: 8010, name: "http")
        .WithOtlpExporter()
        .WaitFor(moshi);
}
else
{
    // DEVELOPMENT: Use Aspire Python integration for frontend
    // Requires Python 3.10-3.12, venv setup (run setup_scenario6.py first)
    // This mode provides fast iteration, hot reload, and native debugging without Docker
    // AddUvicornApp automatically creates an HTTP endpoint
    frontend = builder.AddUvicornApp("scenario6-frontend", "..", "app:app")
        .WithVirtualEnvironment("../venv")
        .WithPip()
        .WithEnvironment("PYTHONUNBUFFERED", "1")
        .WithEnvironment("APP_HOST", "0.0.0.0")
        .WithEnvironment("APP_PORT", appPort.ToString())
        .WithEnvironment("MOSHI_HOST", "localhost")
        .WithEnvironment("MOSHI_PORT", moshiPort.ToString())
        .WithEnvironment("MOSHI_WS_SCHEME", useSsl ? "wss" : "ws")
        .WithEnvironment("MOSHI_WS_URL", moshi.GetEndpoint(moshiEndpointName))
        .WithEnvironment("HF_TOKEN", hfToken)
        .WithOtlpExporter()
        .WaitFor(moshi);
}

builder.Build().Run();

static bool ParseBool(string? value, bool defaultValue)
{
    if (string.IsNullOrWhiteSpace(value))
    {
        return defaultValue;
    }

    return value.Equals("1")
        || value.Equals("true", StringComparison.OrdinalIgnoreCase)
        || value.Equals("yes", StringComparison.OrdinalIgnoreCase);
}
