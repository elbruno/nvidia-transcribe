# Azure Deployment Guide for NVIDIA ASR Server

This guide covers deploying the NVIDIA ASR transcription server to Azure with optional monitoring.

## Prerequisites
- Azure CLI installed (`az`)
- Azure subscription
- Azure Container Registry (or Docker Hub)

## Deployment Steps

### Step 1: Create Resource Group

```bash
az group create \
  --name nvidia-asr-rg \
  --location westus2
```

### Step 2: (Optional) Create Application Insights

For monitoring and telemetry, create an Application Insights resource:

```bash
# Create Application Insights
az monitor app-insights component create \
  --app nvidia-asr-insights \
  --location westus2 \
  --resource-group nvidia-asr-rg

# Get connection string
INSIGHTS_CONN=$(az monitor app-insights component show \
  --app nvidia-asr-insights \
  --resource-group nvidia-asr-rg \
  --query connectionString -o tsv)

echo "Save this connection string: $INSIGHTS_CONN"
```

### Step 3: Create Container Registry

```bash
az acr create \
  --resource-group nvidia-asr-rg \
  --name nvidiaasracr \
  --sku Basic
```

### Step 4: Build and Push Container

```bash
# Login to registry
az acr login --name nvidiaasracr

# Build and push
cd scenario4/server
docker build -t nvidiaasracr.azurecr.io/nvidia-asr:latest .
docker push nvidiaasracr.azurecr.io/nvidia-asr:latest
```

### Step 5: Create Container Apps Environment

```bash
az containerapp env create \
  --name nvidia-asr-env \
  --resource-group nvidia-asr-rg \
  --location westus2
```

### Step 6: Deploy Container App

**Without Application Insights:**
```bash
az containerapp create \
  --name nvidia-asr-api \
  --resource-group nvidia-asr-rg \
  --environment nvidia-asr-env \
  --image nvidiaasracr.azurecr.io/nvidia-asr:latest \
  --target-port 8000 \
  --ingress external \
  --cpu 2 \
  --memory 4Gi \
  --min-replicas 1 \
  --max-replicas 3
```

**With Application Insights (recommended for production):**
```bash
az containerapp create \
  --name nvidia-asr-api \
  --resource-group nvidia-asr-rg \
  --environment nvidia-asr-env \
  --image nvidiaasracr.azurecr.io/nvidia-asr:latest \
  --target-port 8000 \
  --ingress external \
  --cpu 2 \
  --memory 4Gi \
  --min-replicas 1 \
  --max-replicas 3 \
  --secrets "insights-connection=$INSIGHTS_CONN" \
  --env-vars "APPLICATIONINSIGHTS_CONNECTION_STRING=secretref:insights-connection"
```

### Step 7: Get the URL

```bash
az containerapp show \
  --name nvidia-asr-api \
  --resource-group nvidia-asr-rg \
  --query properties.configuration.ingress.fqdn \
  --output tsv
```

## Deploying the Blazor Webapp

To deploy the Blazor webapp as well:

```bash
# Build and publish the webapp
cd scenario4/clients/webapp
dotnet publish -c Release -o publish

# Create Dockerfile if not exists
cat > Dockerfile << 'EOF'
FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY publish/ .
ENTRYPOINT ["dotnet", "TranscriptionWebApp2.dll"]
EOF

# Build and push
docker build -t nvidiaasracr.azurecr.io/nvidia-asr-webapp:latest .
docker push nvidiaasracr.azurecr.io/nvidia-asr-webapp:latest

# Deploy with connection to API server
az containerapp create \
  --name nvidia-asr-webapp \
  --resource-group nvidia-asr-rg \
  --environment nvidia-asr-env \
  --image nvidiaasracr.azurecr.io/nvidia-asr-webapp:latest \
  --target-port 8080 \
  --ingress external \
  --cpu 1 \
  --memory 2Gi \
  --secrets "insights-connection=$INSIGHTS_CONN" \
  --env-vars "APPLICATIONINSIGHTS_CONNECTION_STRING=secretref:insights-connection" \
           "services__apiserver__http__0=https://$(az containerapp show --name nvidia-asr-api --resource-group nvidia-asr-rg --query properties.configuration.ingress.fqdn -o tsv)"
```

## Monitoring

If you configured Application Insights:

1. Navigate to Azure Portal → Application Insights → nvidia-asr-insights
2. View "Live Metrics" for real-time monitoring
3. Use "Logs" to query telemetry data
4. Check "Failures" for errors

Example query:
```kusto
traces
| where customDimensions.ServiceName == "nvidia-asr-api"
| order by timestamp desc
| take 100
```

## Cost Estimation

**Azure Container Apps:**
- CPU-based pricing: ~$0.000024/vCPU-second
- Memory-based pricing: ~$0.000002/GB-second
- Estimated monthly cost for low traffic: $20-50

**Application Insights:**
- First 5 GB: Free
- Additional data: ~$2.30/GB
- Typical cost: Free tier sufficient for most deployments

## Security Best Practices

1. **Use Managed Identity** for ACR access instead of admin credentials
2. **Store secrets in Azure Key Vault**, not as environment variables
3. **Enable HTTPS only** in production
4. **Configure CORS** appropriately for webapp
5. **Set up Azure Front Door** or Application Gateway for advanced routing

## GPU Support

Azure Container Apps with GPU support is in preview. To enable:

1. Create environment with GPU workload profile
  --min-replicas 1 \
  --max-replicas 3
```

6. **Get the URL:**
```bash
az containerapp show \
  --name nvidia-asr-api \
  --resource-group nvidia-asr-rg \
  --query properties.configuration.ingress.fqdn \
  --output tsv
```

#### GPU Support

Azure Container Apps with GPU support is in preview. To enable:

1. Create environment with GPU workload profile
2. Specify GPU requirements in deployment

```bash
az containerapp create \
  --name nvidia-asr-api \
  --resource-group nvidia-asr-rg \
  --environment nvidia-asr-env \
  --image nvidiaasracr.azurecr.io/nvidia-asr:latest \
  --target-port 8000 \
  --ingress external \
  --cpu 4 \
  --memory 8Gi \
  --gpu-type nvidia-tesla-t4 \
  --gpu-count 1
```

### Option 2: Azure Container Instances (ACI)

For simple deployments without auto-scaling:

```bash
az container create \
  --resource-group nvidia-asr-rg \
  --name nvidia-asr-aci \
  --image nvidiaasracr.azurecr.io/nvidia-asr:latest \
  --cpu 2 \
  --memory 4 \
  --registry-login-server nvidiaasracr.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --dns-name-label nvidia-asr-unique \
  --ports 8000
```

### Option 3: Azure Kubernetes Service (AKS)

For production workloads with advanced orchestration:

1. **Create AKS Cluster:**
```bash
az aks create \
  --resource-group nvidia-asr-rg \
  --name nvidia-asr-aks \
  --node-count 2 \
  --enable-managed-identity \
  --attach-acr nvidiaasracr
```

2. **Get credentials:**
```bash
az aks get-credentials \
  --resource-group nvidia-asr-rg \
  --name nvidia-asr-aks
```

3. **Deploy with Kubernetes:**

Create `deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nvidia-asr-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nvidia-asr-api
  template:
    metadata:
      labels:
        app: nvidia-asr-api
    spec:
      containers:
      - name: api
        image: nvidiaasracr.azurecr.io/nvidia-asr:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
---
apiVersion: v1
kind: Service
metadata:
  name: nvidia-asr-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: nvidia-asr-api
```

Deploy:
```bash
kubectl apply -f deployment.yaml
```

## Post-Deployment Configuration

### 1. Configure Clients

Update client applications with the deployed URL:

**Console Client:**
```bash
dotnet run audio.mp3 https://nvidia-asr-api.azurecontainerapps.io
```

**Blazor Web App:**
Edit `wwwroot/appsettings.json`:
```json
{
  "ApiUrl": "https://nvidia-asr-api.azurecontainerapps.io"
}
```

### 2. Enable HTTPS

Azure Container Apps provides automatic HTTPS. For custom domains:

```bash
az containerapp hostname add \
  --name nvidia-asr-api \
  --resource-group nvidia-asr-rg \
  --hostname api.yourdomain.com
```

### 3. Add Authentication (Optional)

Use Azure API Management or implement JWT authentication in the FastAPI app.

### 4. Monitor and Logging

Enable Application Insights:
```bash
az containerapp logs show \
  --name nvidia-asr-api \
  --resource-group nvidia-asr-rg \
  --follow
```

## Cost Optimization

### Container Apps Pricing
- **Consumption plan**: Pay per request and execution time
- **Dedicated plan**: Fixed cost for dedicated compute

### Recommendations
1. Use consumption plan for variable workloads
2. Set min replicas to 0 for development/testing
3. Use Azure Cost Management to monitor spending
4. Consider reserved instances for production

### Example Cost (Approximate)
- **Container Apps (2 vCPU, 4GB)**: ~$100-200/month
- **Container Registry**: ~$5/month (Basic tier)
- **Bandwidth**: Variable based on usage

## Monitoring and Scaling

### Auto-scaling Configuration

```bash
az containerapp update \
  --name nvidia-asr-api \
  --resource-group nvidia-asr-rg \
  --min-replicas 1 \
  --max-replicas 5 \
  --scale-rule-name http-requests \
  --scale-rule-type http \
  --scale-rule-http-concurrency 10
```

### Health Checks

Container Apps automatically uses the `/health` endpoint for health monitoring.

### Metrics

View metrics in Azure Portal:
- Request count
- Response time
- CPU/Memory usage
- Error rate

## Security Best Practices

1. **Use Managed Identity**: Connect to other Azure services without credentials
2. **Private endpoints**: Restrict public access if needed
3. **API Management**: Add rate limiting, throttling, API keys
4. **Network policies**: Configure virtual network integration
5. **Secrets**: Store sensitive data in Azure Key Vault

## Troubleshooting

### Container won't start
- Check logs: `az containerapp logs show`
- Verify image is pushed correctly
- Check resource limits

### Out of memory
- Increase memory allocation (4Gi → 8Gi)
- Check for memory leaks in logs

### Slow performance
- Add GPU support (if available)
- Increase CPU/memory resources
- Enable auto-scaling
- Use Azure CDN for static assets

### CORS errors from web client
- Verify CORS configuration in `app.py`
- Check if URL scheme matches (http vs https)

## Continuous Deployment

### GitHub Actions

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]
    paths:
      - 'scenario4/server/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Build and push
        run: |
          az acr build \
            --registry nvidiaasracr \
            --image nvidia-asr:${{ github.sha }} \
            --file scenario4/server/Dockerfile \
            scenario4/server
      
      - name: Deploy to Container Apps
        run: |
          az containerapp update \
            --name nvidia-asr-api \
            --resource-group nvidia-asr-rg \
            --image nvidiaasracr.azurecr.io/nvidia-asr:${{ github.sha }}
```

## Support

For Azure-specific issues:
- Azure Documentation: https://docs.microsoft.com/azure
- Azure Support: https://azure.microsoft.com/support

For application issues, see the main repository documentation.
