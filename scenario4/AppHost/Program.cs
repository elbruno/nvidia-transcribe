using Aspire.Hosting;
using Aspire.Hosting.Python;

var builder = DistributedApplication.CreateBuilder(args);

// Add Python FastAPI server using Uvicorn
// The server is located in the ../server directory
var apiServer = builder.AddPythonApp("apiserver", "../server", "app.py")
    .WithHttpEndpoint(port: 8000, name: "http")
    .WithExternalHttpEndpoints()
    .WithHttpHealthCheck("/health")
    .WithEnvironment("PYTHONUNBUFFERED", "1");  // For real-time logging

// Add console client project (optional - can be run separately)
var consoleClient = builder.AddProject("console-client", "../clients/console/TranscriptionClient.csproj")
    .WithReference(apiServer)
    .WaitFor(apiServer);

// Add Blazor web client
var blazorClient = builder.AddProject("blazor-client", "../clients/blazor/TranscriptionWebApp.csproj")
    .WithReference(apiServer)
    .WithExternalHttpEndpoints()
    .WaitFor(apiServer);

builder.Build().Run();
