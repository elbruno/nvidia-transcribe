#!/usr/bin/env python3
"""
Environment Validation Script
Checks Python version, PyTorch, CUDA, and required dependencies.
"""

import sys
import platform


def check_python_version():
    """Check if Python version is compatible (3.10-3.12)."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major == 3 and 10 <= version.minor <= 12:
        return True, version_str, "OK"
    elif version.major == 3 and version.minor >= 13:
        return False, version_str, "Python 3.13+ is NOT supported (NeMo/lhotse incompatibility)"
    else:
        return False, version_str, "Python 3.10-3.12 required"


def check_pytorch():
    """Check PyTorch installation and version."""
    try:
        import torch
        version = torch.__version__
        return True, version, "OK"
    except ImportError:
        return False, "Not installed", "Run: pip install torch"


def check_cuda():
    """Check CUDA availability and GPU info."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            cuda_version = torch.version.cuda
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            return True, f"CUDA {cuda_version}", f"{gpu_name} ({vram:.1f}GB VRAM)"
        else:
            # Check if it's a CPU-only build
            if "+cpu" in torch.__version__:
                return False, "CPU-only PyTorch", "Reinstall with: pip install torch --index-url https://download.pytorch.org/whl/cu121"
            else:
                return False, "Not available", "No CUDA-capable GPU detected or drivers not installed"
    except ImportError:
        return False, "N/A", "PyTorch not installed"


def check_nemo():
    """Check NeMo toolkit installation."""
    try:
        import nemo.collections.asr as nemo_asr
        import nemo
        version = getattr(nemo, '__version__', 'unknown')
        return True, version, "OK"
    except ImportError:
        return False, "Not installed", "Run: pip install nemo_toolkit[asr]"


def check_librosa():
    """Check librosa installation (for audio conversion)."""
    try:
        import librosa
        version = librosa.__version__
        return True, version, "OK"
    except ImportError:
        return False, "Not installed", "Run: pip install librosa"


def check_soundfile():
    """Check soundfile installation (for WAV writing)."""
    try:
        import soundfile
        version = soundfile.__version__
        return True, version, "OK"
    except ImportError:
        return False, "Not installed", "Run: pip install soundfile"


def print_status(name: str, ok: bool, version: str, detail: str):
    """Print a formatted status line."""
    status = "✓" if ok else "✗"
    color_start = "" if ok else ""
    print(f"  {status} {name:20} {version:25} {detail}")


def main():
    print("=" * 70)
    print("  NVIDIA ASR Transcription Toolkit - Environment Check")
    print("=" * 70)
    print(f"\n  Platform: {platform.system()} {platform.release()}")
    print()
    
    all_ok = True
    cuda_ok = False
    
    # Check Python
    ok, version, detail = check_python_version()
    print_status("Python", ok, version, detail)
    all_ok = all_ok and ok
    
    # Check PyTorch
    ok, version, detail = check_pytorch()
    print_status("PyTorch", ok, version, detail)
    all_ok = all_ok and ok
    
    # Check CUDA
    ok, version, detail = check_cuda()
    print_status("CUDA/GPU", ok, version, detail)
    cuda_ok = ok
    # CUDA is optional, don't fail all_ok
    
    # Check NeMo
    ok, version, detail = check_nemo()
    print_status("NeMo Toolkit", ok, version, detail)
    all_ok = all_ok and ok
    
    # Check librosa
    ok, version, detail = check_librosa()
    print_status("librosa", ok, version, detail)
    all_ok = all_ok and ok
    
    # Check soundfile
    ok, version, detail = check_soundfile()
    print_status("soundfile", ok, version, detail)
    all_ok = all_ok and ok
    
    # Summary
    print()
    print("-" * 70)
    
    if all_ok and cuda_ok:
        print("  ✓ Environment is fully configured with GPU acceleration!")
        print("    Transcription will use CUDA for fast processing.")
    elif all_ok and not cuda_ok:
        print("  ⚠ Environment is configured but running in CPU-only mode.")
        print("    Transcription will work but will be ~10x slower.")
        print("    To enable GPU: pip install torch --index-url https://download.pytorch.org/whl/cu121")
    else:
        print("  ✗ Environment has issues. Please fix the errors above.")
        print("    See README.md for installation instructions.")
    
    print("-" * 70)
    print()
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
