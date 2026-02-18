# Scenario 6 Aspire AppHost

This AppHost runs Scenario 6 as two separate services (Docker containers):
- `scenario6-frontend`: FastAPI UI server
- `scenario6-moshi`: PersonaPlex moshi backend

## Prerequisites

- .NET 10 SDK
- Docker (with GPU support if available)
- Hugging Face token available via Aspire parameter `HF_TOKEN` (user-secrets or env)
- NVIDIA Container Toolkit for GPU passthrough (optional but recommended)

## Run

```bash
aspire run
```

The frontend will be available on the port shown in the Aspire dashboard.

## Runtime Options

Set these environment variables before running Aspire:

- `USE_GPU` (default: `true`) - enable GPU passthrough for the moshi container
- `CPU_OFFLOAD` (default: `false`) - enable moshi CPU offload mode
