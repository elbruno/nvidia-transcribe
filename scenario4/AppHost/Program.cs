using Aspire.Hosting;
using Aspire.Hosting.Python;

var builder = DistributedApplication.CreateBuilder(args);

// Add Python FastAPI server using Uvicorn
// The server is located in the ../server directory
// IMPORTANT: Requires Python 3.12 virtual environment setup BEFORE running
// Run: ..\server\setup-venv.ps1 (Windows) or ../server/setup-venv.sh (Linux)
var apiServer = builder.AddUvicornApp("apiserver", "../server", "app:app")
    .WithHttpEndpoint(port: 8000, name: "http", env: "PORT")
    .WithExternalHttpEndpoints()
    .WithHttpHealthCheck("/health")
    .WithVirtualEnvironment(".venv")
    .WithEnvironment("PYTHONUNBUFFERED", "1");  // For real-time logging

// Add console client project (optional - can be run separately)
var consoleClient = builder.AddProject("console-client", "../clients/console/TranscriptionClient.csproj")
    .WithReference(apiServer)
    .WaitFor(apiServer);

// Add Blazor web client
var blazorClient = builder.AddProject("blazor-client", "../clients/blazor/TranscriptionWebApp.csproj")
    .WithReference(apiServer)
    .WaitFor(apiServer);

builder.Build().Run();
