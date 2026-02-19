# Scenario 6 Aspire AppHost

This AppHost orchestrates Scenario 6 using two services:
- `scenario6-moshi`: PersonaPlex moshi backend (Docker container)
- `scenario6-frontend`: FastAPI UI server (Aspire Python in dev, Docker in production)

## Orchestration Modes

The AppHost uses **hybrid orchestration** for the frontend service:

| Mode | When | Frontend Technology | Moshi Backend |
|------|------|---------------------|---------------|
| **Development** | `aspire run` | Aspire Python (`AddUvicornApp`) | Docker |
| **Production** | `dotnet publish` | Docker | Docker |

**Why hybrid?**
- **Development**: Fast iteration, hot reload, no Docker rebuild on frontend code changes
- **Production**: Consistent deployment, both services containerized

The moshi backend always uses Docker due to its complexity (vendored third-party code, custom startup scripts).

## Prerequisites

### All Modes

- .NET 10 SDK
- Docker (with GPU support if available)
- Hugging Face token available via Aspire parameter `HF_TOKEN` (user-secrets or env)
- NVIDIA Container Toolkit for GPU passthrough (optional but recommended)

### Development Mode (Aspire Python for Frontend)

Additional requirements for frontend Python development:

- **Python 3.10-3.12** (Python 3.13 is NOT supported)
- **Virtual environment** created and configured (see setup below)
- **System dependencies**:
  - **Linux**: `libopus-dev` (`sudo apt install libopus-dev`)
  - **macOS**: `opus` (`brew install opus`)
  - **Windows**: Visual Studio Build Tools + vcpkg opus

### Development Mode Setup

Run the setup script to create the virtual environment:

```powershell
# Windows
cd scenario6
py -3.12 setup_scenario6.py --hf-token <your-token>
```

```bash
# Linux/macOS
cd scenario6
python3.12 setup_scenario6.py --hf-token <your-token>
```

This creates a `venv` directory with all dependencies installed.

**What the setup script does:**
- Creates Python virtual environment at `scenario6/venv`
- Installs PyTorch with CUDA support
- Installs vendored moshi package from `third_party/moshi`
- Installs FastAPI, uvicorn, and other dependencies
- Creates `.env` file with HF_TOKEN

## Run

### Development Mode (Recommended)

```bash
aspire run
```

This automatically:
- Starts moshi backend via Docker (with model download on first run)
- Starts frontend via Aspire Python (hot reload enabled)
- Opens Aspire dashboard at http://localhost:15000

The frontend will be available on the port shown in the Aspire dashboard.

**Benefits:**
- Hot reload - change `app.py` and see updates instantly
- Native Python debugging
- No Docker rebuild for frontend changes
- Faster iteration cycles

### Production Mode

```bash
dotnet publish
```

Both services run as Docker containers.

## Runtime Options

Set these environment variables before running Aspire:

- `USE_GPU` (default: `true`) - enable GPU passthrough for the moshi container
- `CPU_OFFLOAD` (default: `false`) - enable moshi CPU offload mode
- `MOSHI_USE_SSL` (default: `false`) - enable SSL/TLS on moshi backend (requires cert setup)
- `APP_PORT` (default: `8010`) - frontend HTTP port
- `MOSHI_PORT` (default: `8998`) - moshi backend port

## Network Architecture

By default both services run over plain HTTP/WS:

- Browser → `http://localhost:8010` (frontend web UI)
- Browser → `ws://localhost:8998/api/chat` (direct WebSocket to moshi)
- Frontend → `http://localhost:8998/health` (Aspire health check)

OpenTelemetry (OTLP) is **disabled** to avoid blocking the async event loop during audio streaming. See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for details.

## Troubleshooting

### Development Mode Issues

| Problem | Solution |
|---------|----------|
| `venv` not found | Run `setup_scenario6.py` from scenario6 directory |
| Python version error | Ensure Python 3.10-3.12 is installed (not 3.13) |
| libopus error | Install system dependency: `sudo apt install libopus-dev` |
| Module import errors | Activate venv and re-run setup script |

### Both Modes

| Problem | Solution |
|---------|----------|
| Docker not running | Start Docker Desktop/Engine |
| GPU not detected | Install NVIDIA Container Toolkit, set `USE_GPU=true` |
| HF_TOKEN missing | Set via user-secrets: `dotnet user-secrets set "HF_TOKEN" "<your-token>"` |
| Model download slow | First run downloads ~14 GB model; subsequent runs use cache |
