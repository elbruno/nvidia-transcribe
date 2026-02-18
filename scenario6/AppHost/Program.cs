using Aspire.Hosting;

var builder = DistributedApplication.CreateBuilder(args);

var moshiPort = int.TryParse(builder.Configuration["MOSHI_PORT"], out var mp) ? mp : 8998;
var appPort = int.TryParse(builder.Configuration["APP_PORT"], out var ap) ? ap : 8010;
var useGpu = ParseBool(builder.Configuration["USE_GPU"], defaultValue: true);
var cpuOffload = ParseBool(builder.Configuration["CPU_OFFLOAD"], defaultValue: false);

var moshi = builder.AddDockerfile("scenario6-moshi", "..", "moshi/Dockerfile")
    .WithImageTag("latest")
    .WithEnvironment("HF_TOKEN", builder.Configuration["HF_TOKEN"] ?? "")
    .WithEnvironment("HF_HOME", builder.Configuration["HF_HOME"] ?? "/root/.cache/huggingface")
    .WithEnvironment("PYTHONUNBUFFERED", "1")
    .WithEnvironment("MOSHI_CPU_OFFLOAD", cpuOffload ? "1" : "0")
    .WithHttpsEndpoint(port: moshiPort, targetPort: 8998, name: "https")
    .WithHttpHealthCheck("/health", endpointName: "https")
    .WithVolume("hf-model-cache-scenario6", "/root/.cache/huggingface")
    .WithLifetime(ContainerLifetime.Persistent);

if (useGpu)
{
    moshi.WithContainerRuntimeArgs("--gpus=all");
}

var frontend = builder.AddDockerfile("scenario6-frontend", "..", "Dockerfile")
    .WithImageTag("latest")
    .WithEnvironment("APP_PORT", appPort.ToString())
    .WithEnvironment("APP_HOST", "0.0.0.0")
    .WithEnvironment("MOSHI_WS_URL", moshi.GetEndpoint("https"))
    .WithHttpEndpoint(port: appPort, targetPort: 8010, name: "http")
    .WaitFor(moshi);

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
