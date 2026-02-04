#!/usr/bin/env python3
"""
Model Status Script
Checks if ASR models are downloaded and cached locally.
"""

import sys
from pathlib import Path


# Model information
MODELS = {
    "parakeet-tdt-0.6b-v2": {
        "name": "Parakeet TDT 0.6B v2",
        "hf_id": "nvidia/parakeet-tdt-0.6b-v2",
        "cache_folder": "models--nvidia--parakeet-tdt-0.6b-v2",
        "size": "~1.2GB",
        "scenarios": "1 & 2",
        "license": "CC-BY-4.0 (commercial OK)",
    },
    "canary-1b": {
        "name": "Canary-1B",
        "hf_id": "nvidia/canary-1b",
        "cache_folder": "models--nvidia--canary-1b",
        "size": "~1.5GB",
        "scenarios": "3",
        "license": "CC-BY-NC-4.0 (non-commercial)",
    },
}


def get_cache_dir() -> Path:
    """Get the Hugging Face cache directory."""
    # Check HF_HOME environment variable first
    import os
    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        return Path(hf_home) / "hub"
    
    # Default location
    return Path.home() / ".cache" / "huggingface" / "hub"


def check_model_cached(cache_dir: Path, model_key: str) -> tuple[bool, str]:
    """Check if a model is cached locally."""
    model_info = MODELS[model_key]
    model_folder = cache_dir / model_info["cache_folder"]
    
    if not model_folder.exists():
        return False, "Not downloaded"
    
    # Check for snapshots (actual model files)
    snapshots_dir = model_folder / "snapshots"
    if not snapshots_dir.exists():
        return False, "Incomplete download"
    
    # Check if there's at least one snapshot with .nemo file
    for snapshot in snapshots_dir.iterdir():
        if snapshot.is_dir():
            nemo_files = list(snapshot.glob("*.nemo"))
            if nemo_files:
                # Calculate size
                total_size = sum(f.stat().st_size for f in snapshot.rglob("*") if f.is_file())
                size_gb = total_size / (1024**3)
                return True, f"Cached ({size_gb:.2f}GB)"
    
    return False, "Incomplete download"


def print_status(name: str, ok: bool, status: str, detail: str):
    """Print a formatted status line."""
    icon = "✓" if ok else "○"
    print(f"  {icon} {name:30} {status:20} {detail}")


def main():
    print("=" * 70)
    print("  NVIDIA ASR Transcription Toolkit - Model Status")
    print("=" * 70)
    
    cache_dir = get_cache_dir()
    print(f"\n  Cache directory: {cache_dir}")
    
    if not cache_dir.exists():
        print(f"\n  Cache directory does not exist yet.")
        print(f"  Models will be downloaded on first use.")
    
    print()
    print("  Model                         Status               Details")
    print("-" * 70)
    
    all_downloaded = True
    
    for model_key, model_info in MODELS.items():
        ok, status = check_model_cached(cache_dir, model_key)
        detail = f"Scenarios {model_info['scenarios']} | {model_info['license']}"
        print_status(model_info["name"], ok, status, "")
        print(f"      Size: {model_info['size']} | {model_info['license']}")
        print(f"      Used by: Scenario {model_info['scenarios']}")
        print()
        
        if not ok:
            all_downloaded = False
    
    print("-" * 70)
    
    if all_downloaded:
        print("  ✓ All models are cached and ready to use!")
    else:
        print("  ○ Some models are not downloaded yet.")
        print("    They will be downloaded automatically on first use.")
        print()
        print("  To pre-download models, run the corresponding scenario once:")
        print("    python scenario1/transcribe.py --help   # Downloads Parakeet")
        print("    python scenario3/transcribe.py --help   # Downloads Canary-1B")
    
    print("-" * 70)
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
