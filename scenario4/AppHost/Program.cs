using Aspire.Hosting;
using Aspire.Hosting.Python;

var builder = DistributedApplication.CreateBuilder(args);

// Add Python FastAPI server using Uvicorn
// The server is located in the ../server directory
var apiServer = builder.AddUvicornApp("apiserver", "../server", "app:app")
    .WithHttpEndpoint(port: 8000, name: "http")
    .WithExternalHttpEndpoints()
    .WithHttpHealthCheck("/health")
    .WithEnvironment("PYTHONUNBUFFERED", "1");  // For real-time logging

// Add console client project (optional - can be run separately)
var consoleClient = builder.AddProject<Projects.TranscriptionClient>("console-client")
    .WithReference(apiServer)
    .WaitFor(apiServer);

// Add Blazor web client
var blazorClient = builder.AddProject<Projects.TranscriptionWebApp>("blazor-client")
    .WithReference(apiServer)
    .WithExternalHttpEndpoints()
    .WaitFor(apiServer);

builder.Build().Run();
