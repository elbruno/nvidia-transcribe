# Application Insights Integration

This document explains how to add Azure Application Insights monitoring to scenario 4.

## Overview

Both the Python FastAPI server and .NET Blazor webapp can be configured to send telemetry to Azure Application Insights. This is optional - the services work without it.

## Setup Steps

### 1. Create Application Insights Resource

Using Azure Portal or CLI:

```bash
# Create resource group if needed
az group create --name nvidia-transcription-rg --location eastus

# Create Application Insights  
az monitor app-insights component create \
  --app nvidia-transcription-monitor \
  --location eastus \
  --resource-group nvidia-transcription-rg

# Get the connection string
az monitor app-insights component show \
  --app nvidia-transcription-monitor \
  --resource-group nvidia-transcription-rg \
  --query connectionString -o tsv
```

Save the connection string - it looks like:
```
InstrumentationKey=xxx;IngestionEndpoint=https://xxx.applicationinsights.azure.com/
```

### 2. Configure Python Server

**Install Azure Monitor package:**
```bash
cd scenario4/server
pip install opencensus-ext-azure
```

**Add to requirements.txt:**
```txt
opencensus-ext-azure==1.1.13
```

**Set environment variable:**
```bash
export APPLICATIONINSIGHTS_CONNECTION_STRING="your-connection-string-here"
```

**In Docker/Container Apps:**
```bash
docker run -e APPLICATIONINSIGHTS_CONNECTION_STRING="..." nvidia-asr-server
```

The Python server will automatically detect this environment variable and send logs/metrics to Application Insights.

### 3. Configure .NET Blazor Webapp

**Add NuGet package to webapp project:**
```bash
cd scenario4/clients/webapp
dotnet add package Azure.Monitor.OpenTelemetry.AspNetCore
```

**Update Program.cs** to check for the connection string and enable Azure Monitor when available.

**Set environment variable:**
```bash
export APPLICATIONINSIGHTS_CONNECTION_STRING="your-connection-string-here"
```

### 4. Configure via Aspire AppHost

Update `scenario4/AppHost/Program.cs` to pass the connection string to both services:

```csharp
var insightsConnectionString = builder.Configuration["APPLICATIONINSIGHTS_CONNECTION_STRING"];

var apiServer = builder.AddDockerfile("apiserver", "../server")
    // ... existing configuration ...
    .WithEnvironment("APPLICATIONINSIGHTS_CONNECTION_STRING", insightsConnectionString ?? "");

var webappClient = builder.AddProject<Projects.TranscriptionWebApp2>("webappClient")
    .WithEnvironment("APPLICATIONINSIGHTS_CONNECTION_STRING", insightsConnectionString ?? "")
    // ... existing configuration ...
```

## What Gets Monitored

### Python Server
- HTTP request traces
- Custom events (job started, completed, failed)
- Exception tracking
- Performance metrics

### Blazor Webapp
- Page views
- HTTP requests to API server
- Client-side exceptions
- User interactions

## Viewing Telemetry

In Azure Portal:
1. Navigate to your Application Insights resource
2. Use "Logs" to query telemetry
3. Use "Live Metrics" for real-time monitoring
4. Use "Failures" to see errors
5. Use "Performance" to analyze response times

Example query for transcription jobs:
```kusto
traces
| where message contains "transcription"
| project timestamp, message, severityLevel
| order by timestamp desc
```

## Local Development

For local development, you can either:
- Set the environment variable locally
- Or skip it - services work fine without Application Insights

## Cost Considerations

- First 5 GB/month: Free
- Additional data: ~$2-3/GB
- Typical small deployment stays within free tier

## Security

- Never commit connection strings to source control
- Use Azure Key Vault for production
- Reference as secrets in Container Apps

## Additional Resources

- [Azure Application Insights Overview](https://learn.microsoft.com/azure/azure-monitor/app/app-insights-overview)
- [OpenCensus Python with Azure](https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-azure)
- [Azure Monitor for .NET](https://learn.microsoft.com/azure/azure-monitor/app/opentelemetry-enable?tabs=aspnetcore)
