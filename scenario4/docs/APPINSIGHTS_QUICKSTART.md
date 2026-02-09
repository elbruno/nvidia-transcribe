# Application Insights - Quick Setup

This is a condensed guide for quickly enabling Application Insights monitoring.

## 1. Create Resource (Azure CLI)

```bash
# Set variables
RG_NAME="nvidia-transcription-rg"
LOCATION="eastus"
INSIGHTS_NAME="nvidia-transcription-monitor"

# Create
az group create --name $RG_NAME --location $LOCATION
az monitor app-insights component create \
  --app $INSIGHTS_NAME \
  --location $LOCATION \
  --resource-group $RG_NAME

# Get connection string
CONN_STR=$(az monitor app-insights component show \
  --app $INSIGHTS_NAME \
  --resource-group $RG_NAME \
  --query connectionString -o tsv)

echo "Connection String: $CONN_STR"
```

## 2. Local Development with Aspire

```bash
# Set environment variable
export APPLICATIONINSIGHTS_CONNECTION_STRING="$CONN_STR"

# Run Aspire
cd scenario4/AppHost
dotnet run
```

You'll see: ✅ `Application Insights monitoring enabled`

## 3. Azure Container Apps Deployment

```bash
# Deploy with secrets
az containerapp create \
  --name my-transcription-api \
  --resource-group $RG_NAME \
  --environment my-env \
  --image myregistry.azurecr.io/nvidia-asr:latest \
  --secrets "insights-conn=$CONN_STR" \
  --env-vars "APPLICATIONINSIGHTS_CONNECTION_STRING=secretref:insights-conn" \
  --target-port 8000 \
  --ingress external
```

## 4. Verify It's Working

**In Azure Portal:**
1. Go to Application Insights resource
2. Click "Live Metrics"
3. Trigger a transcription job
4. Watch telemetry appear in real-time

**Query recent traces:**
```kusto
traces
| where timestamp > ago(1h)
| project timestamp, message, severityLevel
| order by timestamp desc
```

## 5. Disable Monitoring

Simply remove or unset the environment variable:
```bash
unset APPLICATIONINSIGHTS_CONNECTION_STRING
```

Services continue to work normally without telemetry.

## Package Requirements

### Python Server
Already configured - no code changes needed. Just ensure `opencensus-ext-azure` is installed:
```bash
pip install opencensus-ext-azure==1.1.13
```

### .NET Blazor Webapp
Add package:
```bash
dotnet add package Azure.Monitor.OpenTelemetry.AspNetCore
```

## Common Issues

**"Telemetry not appearing"**
- Wait 2-3 minutes for data to appear
- Check connection string format (should start with `InstrumentationKey=`)
- Verify environment variable is set correctly

**"Package not found"**
- Python: `pip install opencensus-ext-azure`
- .NET: `dotnet add package Azure.Monitor.OpenTelemetry.AspNetCore`

**"Want to disable logging"**
- Unset `APPLICATIONINSIGHTS_CONNECTION_STRING` 
- Services work fine without it

## More Information

- Full setup guide: [docs/APPLICATION_INSIGHTS.md](APPLICATION_INSIGHTS.md)
- Azure deployment: [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)
- Scenario 4 overview: [README.md](../README.md)
