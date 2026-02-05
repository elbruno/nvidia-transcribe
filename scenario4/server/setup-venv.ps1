# Setup Python 3.12 virtual environment for NVIDIA ASR Transcription Server
# Run this script BEFORE starting the Aspire host

param(
    [switch]$CpuOnly = $false,
    [string]$PythonVersion = "3.12"
)

$ErrorActionPreference = "Stop"
$ServerDir = $PSScriptRoot

Write-Host "=== NVIDIA ASR Transcription Server Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if Python 3.12 is available
Write-Host "Checking for Python $PythonVersion..." -ForegroundColor Yellow
$pythonCmd = "py -$PythonVersion"
try {
    $pythonPath = & py -$PythonVersion -c "import sys; print(sys.executable)" 2>$null
    if (-not $pythonPath) {
        throw "Python $PythonVersion not found"
    }
    Write-Host "Found Python at: $pythonPath" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python $PythonVersion is required but not found." -ForegroundColor Red
    Write-Host "Install Python 3.12 from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "Note: Python 3.13+ is NOT supported by NeMo toolkit." -ForegroundColor Red
    exit 1
}

# Create virtual environment
$venvPath = Join-Path $ServerDir ".venv"
if (Test-Path $venvPath) {
    Write-Host "Virtual environment already exists at: $venvPath" -ForegroundColor Yellow
    $response = Read-Host "Recreate virtual environment? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $venvPath
    } else {
        Write-Host "Using existing virtual environment." -ForegroundColor Green
    }
}

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment with Python $PythonVersion..." -ForegroundColor Yellow
    & py -$PythonVersion -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "Virtual environment created at: $venvPath" -ForegroundColor Green
}

# Activate virtual environment
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
. $activateScript

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install PyTorch (CUDA or CPU)
Write-Host ""
if ($CpuOnly) {
    Write-Host "Installing PyTorch (CPU-only)..." -ForegroundColor Yellow
    pip install torch
} else {
    Write-Host "Installing PyTorch with CUDA 12.1 support..." -ForegroundColor Yellow
    pip install torch --index-url https://download.pytorch.org/whl/cu121
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install PyTorch" -ForegroundColor Red
    exit 1
}
Write-Host "PyTorch installed successfully" -ForegroundColor Green

# Install Windows-specific requirements (without nemo_toolkit initially)
Write-Host ""
Write-Host "Installing base requirements..." -ForegroundColor Yellow
$requirementsPath = Join-Path $ServerDir "requirements-windows.txt"
if (Test-Path $requirementsPath) {
    pip install -r $requirementsPath
} else {
    # Fall back to installing individual packages
    pip install fastapi==0.109.1 uvicorn[standard]==0.27.0 python-multipart==0.0.22 soundfile==0.12.1 librosa==0.10.1
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install base requirements" -ForegroundColor Red
    exit 1
}

# Install NeMo toolkit (without triton dependency on Windows)
Write-Host ""
Write-Host "Installing NeMo toolkit (this may take a few minutes)..." -ForegroundColor Yellow
pip install nemo_toolkit[asr] --no-deps

# Install all NeMo dependencies that are missing due to --no-deps
Write-Host "Installing NeMo dependencies..." -ForegroundColor Yellow
pip install hydra-core omegaconf lightning pytorch-lightning webdataset huggingface-hub onnx tqdm
pip install wrapt python-dateutil sentencepiece transformers editdistance pandas scipy braceexpand lhotse
pip install ruamel.yaml tensorboard text-unidecode wget "numexpr<2.14.0"

if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: NeMo toolkit installation had issues" -ForegroundColor Yellow
} else {
    Write-Host "NeMo toolkit installed successfully" -ForegroundColor Green
}

# Apply lhotse fix
Write-Host ""
Write-Host "Applying lhotse compatibility fix..." -ForegroundColor Yellow
$fixLhotsePath = Join-Path (Split-Path $ServerDir -Parent) "..\fix_lhotse.py"
if (Test-Path $fixLhotsePath) {
    python $fixLhotsePath
    Write-Host "Lhotse fix applied" -ForegroundColor Green
} else {
    Write-Host "WARNING: fix_lhotse.py not found at $fixLhotsePath" -ForegroundColor Yellow
}

# Verify installation
Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Yellow
$verifyScript = @"
import sys
print(f'Python: {sys.version}')
try:
    import torch
    print(f'PyTorch: {torch.__version__}')
    print(f'CUDA available: {torch.cuda.is_available()}')
    if torch.cuda.is_available():
        print(f'CUDA device: {torch.cuda.get_device_name(0)}')
except ImportError as e:
    print(f'PyTorch: NOT INSTALLED - {e}')
try:
    import nemo
    print(f'NeMo: {nemo.__version__}')
except ImportError as e:
    print(f'NeMo: NOT INSTALLED - {e}')
try:
    import fastapi
    print(f'FastAPI: {fastapi.__version__}')
except ImportError as e:
    print(f'FastAPI: NOT INSTALLED - {e}')
"@
python -c $verifyScript

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "To start the Aspire host, run:" -ForegroundColor Cyan
Write-Host "  cd $ServerDir\..\AppHost" -ForegroundColor White
Write-Host "  dotnet run" -ForegroundColor White
Write-Host ""
Write-Host "Or to run the server standalone:" -ForegroundColor Cyan
Write-Host "  cd $ServerDir" -ForegroundColor White
Write-Host "  .venv\Scripts\activate" -ForegroundColor White
Write-Host "  uvicorn app:app --host 0.0.0.0 --port 8000" -ForegroundColor White
