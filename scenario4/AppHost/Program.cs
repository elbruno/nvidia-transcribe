using Aspire.Hosting;
using Aspire.Hosting.Python;

var builder = DistributedApplication.CreateBuilder(args);

// Add Python FastAPI server using Uvicorn
// The server is located in the ../server directory
// IMPORTANT: Requires Python 3.12 virtual environment setup BEFORE running
// Run: ..\server\setup-venv.ps1 (Windows) or ../server/setup-venv.sh (Linux)
var apiServer = builder.AddUvicornApp("apiserver", "../server", "app:app")
    .WithHttpEndpoint(port: 8000, targetPort: 8000, name: "apiendpoint", env: "PORT", isProxied: false)
    .WithHttpHealthCheck("/health")
    .WithVirtualEnvironment(".venv")
    .WithEnvironment("PYTHONUNBUFFERED", "1");  // For real-time logging

// Add server-side Blazor web client with Aspire service defaults
var webappClient = builder.AddProject<Projects.TranscriptionWebApp2>("webappClient")
    .WithReference(apiServer)
    .WaitFor(apiServer);

builder.Build().Run();
