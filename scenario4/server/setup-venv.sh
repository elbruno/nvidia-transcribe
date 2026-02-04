#!/bin/bash
# Setup Python 3.12 virtual environment for NVIDIA ASR Transcription Server
# Run this script BEFORE starting the Aspire host

set -e

# Default values
CPU_ONLY=false
PYTHON_VERSION="3.12"
SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --cpu-only)
            CPU_ONLY=true
            shift
            ;;
        --python-version)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--cpu-only] [--python-version VERSION]"
            exit 1
            ;;
    esac
done

echo -e "\033[36m=== NVIDIA ASR Transcription Server Setup ===\033[0m"
echo ""

# Check if Python 3.12 is available
echo -e "\033[33mChecking for Python ${PYTHON_VERSION}...\033[0m"
if ! command -v python${PYTHON_VERSION} &> /dev/null; then
    echo -e "\033[31mERROR: Python ${PYTHON_VERSION} is required but not found.\033[0m"
    echo -e "\033[31mInstall Python 3.12 from https://www.python.org/downloads/\033[0m"
    echo -e "\033[31mNote: Python 3.13+ is NOT supported by NeMo toolkit.\033[0m"
    exit 1
fi

PYTHON_PATH=$(which python${PYTHON_VERSION})
echo -e "\033[32mFound Python at: ${PYTHON_PATH}\033[0m"

# Create virtual environment
VENV_PATH="${SERVER_DIR}/.venv"
if [ -d "${VENV_PATH}" ]; then
    echo -e "\033[33mVirtual environment already exists at: ${VENV_PATH}\033[0m"
    read -p "Recreate virtual environment? (y/N): " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "\033[33mRemoving existing virtual environment...\033[0m"
        rm -rf "${VENV_PATH}"
    else
        echo -e "\033[32mUsing existing virtual environment.\033[0m"
    fi
fi

if [ ! -d "${VENV_PATH}" ]; then
    echo -e "\033[33mCreating virtual environment with Python ${PYTHON_VERSION}...\033[0m"
    python${PYTHON_VERSION} -m venv "${VENV_PATH}"
    echo -e "\033[32mVirtual environment created at: ${VENV_PATH}\033[0m"
fi

# Activate virtual environment
echo -e "\033[33mActivating virtual environment...\033[0m"
source "${VENV_PATH}/bin/activate"

# Upgrade pip
echo -e "\033[33mUpgrading pip...\033[0m"
python -m pip install --upgrade pip

# Install PyTorch (CUDA or CPU)
echo ""
if [ "$CPU_ONLY" = true ]; then
    echo -e "\033[33mInstalling PyTorch (CPU-only)...\033[0m"
    pip install torch
else
    echo -e "\033[33mInstalling PyTorch with CUDA 12.1 support...\033[0m"
    pip install torch --index-url https://download.pytorch.org/whl/cu121
fi
echo -e "\033[32mPyTorch installed successfully\033[0m"

# Install requirements
echo ""
echo -e "\033[33mInstalling base requirements...\033[0m"
REQUIREMENTS_PATH="${SERVER_DIR}/requirements.txt"
if [ -f "${REQUIREMENTS_PATH}" ]; then
    pip install -r "${REQUIREMENTS_PATH}"
else
    # Fall back to installing individual packages
    pip install fastapi==0.109.1 uvicorn[standard]==0.27.0 python-multipart==0.0.22 soundfile==0.12.1 librosa==0.10.1
fi

# Apply lhotse fix
echo ""
echo -e "\033[33mApplying lhotse compatibility fix...\033[0m"
FIX_LHOTSE_PATH="${SERVER_DIR}/../../fix_lhotse.py"
if [ -f "${FIX_LHOTSE_PATH}" ]; then
    python "${FIX_LHOTSE_PATH}"
    echo -e "\033[32mLhotse fix applied\033[0m"
else
    echo -e "\033[33mWARNING: fix_lhotse.py not found at ${FIX_LHOTSE_PATH}\033[0m"
fi

# Verify installation
echo ""
echo -e "\033[33mVerifying installation...\033[0m"
python -c "
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
"

echo ""
echo -e "\033[32m=== Setup Complete ===\033[0m"
echo ""
echo -e "\033[36mTo start the Aspire host, run:\033[0m"
echo -e "\033[37m  cd ${SERVER_DIR}/../AppHost\033[0m"
echo -e "\033[37m  dotnet run\033[0m"
echo ""
echo -e "\033[36mOr to run the server standalone:\033[0m"
echo -e "\033[37m  cd ${SERVER_DIR}\033[0m"
echo -e "\033[37m  source .venv/bin/activate\033[0m"
echo -e "\033[37m  uvicorn app:app --host 0.0.0.0 --port 8000\033[0m"
