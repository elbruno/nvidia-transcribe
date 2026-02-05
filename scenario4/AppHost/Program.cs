using Aspire.Hosting;

var builder = DistributedApplication.CreateBuilder(args);

// Add Python FastAPI server using Docker
// The Dockerfile is located in the ../server directory
var apiServer = builder.AddDockerfile("apiserver", "../server")
    .WithHttpEndpoint(port: 8000, targetPort: 8000, name: "apiendpoint", isProxied: false)
    .WithHttpHealthCheck("/health")
    .WithEnvironment("PYTHONUNBUFFERED", "1");  // For real-time logging

// Add server-side Blazor web client with Aspire service defaults
var webappClient = builder.AddProject<Projects.TranscriptionWebApp2>("webappClient")
    .WithEnvironment("services__apiserver__http__0", apiServer.GetEndpoint("apiendpoint"))
    .WaitFor(apiServer);

builder.Build().Run();
