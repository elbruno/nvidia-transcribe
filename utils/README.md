# Utils - Environment Validation Tools

Helper scripts to validate your environment setup before running transcriptions.

## Scripts

### check_environment.py

Validates your Python environment, dependencies, and GPU/CUDA setup.

```bash
python utils/check_environment.py
```

**Checks:**
- Python version (3.10-3.12 required)
- PyTorch installation and version
- CUDA availability and GPU info
- NeMo toolkit installation
- librosa and soundfile for audio processing

**Example output:**
```
======================================================================
  NVIDIA ASR Transcription Toolkit - Environment Check
======================================================================

  Platform: Windows 10

  ✓ Python               3.12.0                    OK
  ✓ PyTorch              2.5.1+cu121               OK
  ✓ CUDA/GPU             CUDA 12.1                 NVIDIA GeForce RTX 3080 (10.0GB VRAM)
  ✓ NeMo Toolkit         2.6.1                     OK
  ✓ librosa              0.10.2                    OK
  ✓ soundfile            0.12.1                    OK

----------------------------------------------------------------------
  ✓ Environment is fully configured with GPU acceleration!
    Transcription will use CUDA for fast processing.
----------------------------------------------------------------------
```

### check_models.py

Shows which ASR models are downloaded and cached locally.

```bash
python utils/check_models.py
```

**Checks:**
- Parakeet TDT 0.6B v2 (Scenarios 1 & 2)
- Canary-1B (Scenario 3)

**Example output:**
```
======================================================================
  NVIDIA ASR Transcription Toolkit - Model Status
======================================================================

  Cache directory: C:\Users\username\.cache\huggingface\hub

  Model                         Status               Details
----------------------------------------------------------------------
  ✓ Parakeet TDT 0.6B v2        Cached (1.18GB)
      Size: ~1.2GB | CC-BY-4.0 (commercial OK)
      Used by: Scenario 1 & 2

  ○ Canary-1B                   Not downloaded
      Size: ~1.5GB | CC-BY-NC-4.0 (non-commercial)
      Used by: Scenario 3

----------------------------------------------------------------------
  ○ Some models are not downloaded yet.
    They will be downloaded automatically on first use.
----------------------------------------------------------------------
```

## Quick Validation

Run both checks at once:

```bash
python utils/check_environment.py && python utils/check_models.py
```

## Troubleshooting

### CUDA Not Available

If `check_environment.py` shows CUDA is not available but you have an NVIDIA GPU:

1. Reinstall PyTorch with CUDA support:
   ```bash
   pip uninstall torch -y
   pip install torch --index-url https://download.pytorch.org/whl/cu121
   ```

2. Run `check_environment.py` again to verify

### Models Not Downloaded

Models are downloaded automatically on first use. To pre-download:

```bash
# This will trigger Parakeet download (show help, no transcription)
python -c "import nemo.collections.asr as nemo_asr; nemo_asr.models.ASRModel.from_pretrained('nvidia/parakeet-tdt-0.6b-v2')"

# This will trigger Canary-1B download
python -c "import nemo.collections.asr as nemo_asr; nemo_asr.models.ASRModel.from_pretrained('nvidia/canary-1b')"
```
