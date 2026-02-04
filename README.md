# NVIDIA ASR Transcription Toolkit

A Python toolkit for audio transcription using NVIDIA's ASR models. Organized into three scenarios for different use cases:

## Scenarios

### Scenario 1: Simple CLI Transcription
**Folder**: [`scenario1/`](scenario1/)  
**Model**: nvidia/parakeet-tdt-0.6b-v2 (English)  
**Usage**: Command-line interface for quick transcription of a single file

```bash
python scenario1/transcribe.py audio_file.mp3
```

### Scenario 2: Interactive Menu Transcription
**Folder**: [`scenario2/`](scenario2/)  
**Model**: nvidia/parakeet-tdt-0.6b-v2 (English)  
**Usage**: Interactive menu to select from multiple audio files in the repository

```bash
python scenario2/transcribe.py
```

### Scenario 3: Multilingual Transcription
**Folder**: [`scenario3/`](scenario3/)  
**Model**: nvidia/canary-1b (Multilingual)  
**Usage**: Supports Spanish, English, German, French and more

```bash
python scenario3/transcribe.py audio_file.mp3 es  # Spanish
python scenario3/transcribe.py audio_file.mp3 en  # English
```

## Choosing the Right Scenario

| Your Need | Use This Scenario |
|-----------|------------------|
| 🚀 **Quick transcription of a single English file** | Scenario 1 |
| 🤖 **Batch processing / automation** | Scenario 1 |
| 📁 **Browse and select from multiple files** | Scenario 2 |
| 🎓 **Learning / first time user** | Scenario 2 |
| 🌍 **Spanish audio transcription** | Scenario 3 |
| 🗣️ **Non-English languages** | Scenario 3 |
| 💼 **Commercial project** | Scenario 1 or 2 only* |

\* *Scenario 3 uses Canary-1B which has a non-commercial license (CC-BY-NC-4.0)*

## Features

- **Local inference** - No API calls, runs entirely on your machine
- **Multiple models** - Choose between Parakeet (English) or Canary-1B (Multilingual)
- **Dual output** - Generates both `.txt` and `.srt` (subtitle) files
- **Timestamps** - Includes segment-level timestamps for subtitles
- **High accuracy** - Models with punctuation and capitalization
- **Auto-conversion** - MP3/FLAC files automatically converted to 16kHz WAV

## Requirements

- **Python 3.10 - 3.12** (Python 3.13 is NOT supported on Windows)
- NVIDIA GPU with CUDA support (recommended, 2GB+ VRAM)
- ~2.5GB disk space for model download
- CPU-only mode supported (slower)

## Installation

1. **Create a virtual environment with Python 3.12** (recommended):

   ```bash
   # Windows - use Python 3.12 specifically
   py -3.12 -m venv venv
   venv\Scripts\activate
   ```

   ```bash
   # Linux/macOS
   python3.12 -m venv venv
   source venv/bin/activate
   ```

2. **Install PyTorch** (choose GPU or CPU version):

   **With NVIDIA GPU** (recommended for 10x faster transcription):
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cu121
   ```

   **CPU-only** (slower but works without GPU):
   ```bash
   pip install torch
   ```

   > ⚠️ Install PyTorch FIRST, before other dependencies. This ensures the correct CUDA version is used.

3. **Install remaining dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   > ⚠️ First-time installation takes 5-10 minutes due to large packages.

4. **Apply lhotse compatibility fix** (required):

   ```bash
   python fix_lhotse.py
   ```

   > ⚠️ This patches a compatibility issue between lhotse and PyTorch 2.10+. Without this fix, transcription will fail with `object.__init__() takes exactly one argument` error.

5. **Validate your environment** (optional but recommended):

   ```bash
   python utils/check_environment.py
   ```

   This checks Python version, CUDA/GPU status, and all dependencies. See [`utils/`](utils/) for more validation tools.

## Quick Start

Choose the scenario that fits your needs:

### Scenario 1: Simple CLI (Single File)
```bash
# Transcribe a specific audio file (English only)
python scenario1/transcribe.py my_audio.mp3
```
**Best for**: Command-line workflows, batch processing, automation

### Scenario 2: Interactive Menu (Multiple Files)
```bash
# Browse and select from audio files in repository root (English only)
python scenario2/transcribe.py
```
**Best for**: Exploring multiple files, manual selection, beginners

### Scenario 3: Multilingual Support
```bash
# Transcribe Spanish audio
python scenario3/transcribe.py spanish_audio.mp3 es

# Transcribe English audio
python scenario3/transcribe.py english_audio.mp3 en

# Default is Spanish (es)
python scenario3/transcribe.py audio.mp3
```
**Best for**: Non-English content, Spanish transcription, multilingual projects

All scenarios generate outputs in the `output/` folder:
- `{timestamp}_{filename}.txt` - Full transcription with timestamps
- `{timestamp}_{filename}.srt` - Subtitle file for video editors

📖 **See [docs/USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md) for detailed examples and workflows.**

⚡ **See [docs/QUICKREF.md](docs/QUICKREF.md) for a quick command reference.**

> **Backward Compatibility**: The original `transcribe.py` script is still available and works as before (same as Scenario 2).

## Supported Audio Formats

| Format | Notes |
|--------|-------|
| `.wav` | Native format, 16kHz mono recommended |
| `.flac` | Auto-converted to 16kHz WAV via librosa |
| `.mp3` | Auto-converted to 16kHz WAV via librosa |

> **Note**: Non-WAV files are automatically converted to 16kHz mono WAV before transcription. The temporary file is cleaned up after processing.

## Output Examples

### TXT Output

```
TRANSCRIPTION
==================================================

Hello, this is a sample transcription with punctuation.

TIMESTAMPS
==================================================

[00:00:00.000 - 00:00:03.500] Hello, this is a sample
[00:00:03.500 - 00:00:07.200] transcription with punctuation.
```

### SRT Output

```
1
00:00:00,000 --> 00:00:03,500
Hello, this is a sample

2
00:00:03,500 --> 00:00:07,200
transcription with punctuation.
```

## Troubleshooting

### "object.**init**() takes exactly one argument" error

- **Cause**: Incompatibility between lhotse and PyTorch 2.10+ (or Python 3.13+)
- **Fix**: After installing dependencies, run the fix script:

  ```bash
  py -3.12 -m venv venv
  venv\Scripts\activate
  pip install -r requirements.txt
  python fix_lhotse.py
  ```

### "No audio files found"

- Ensure audio files are in the repository root directory
- Check file extensions (`.wav`, `.flac`, `.mp3`)

### "CUDA out of memory"

- Close other GPU-intensive applications
- Try with shorter audio files (<10 minutes)

### "CUDA is not available" warning

- This is normal on CPU-only systems
- Transcription will still work, just slower

### "Model download slow"

- First run downloads ~1.2-1.5GB model from Hugging Face
- Models are cached at `~/.cache/huggingface/hub/` and shared across all scenarios
- Subsequent runs load from cache instantly

### CPU-only mode

If no GPU is available, the model runs on CPU (much slower). No configuration needed - it falls back automatically. Expect ~10x slower transcription times.

## Model Information

### Parakeet TDT 0.6B v2 (Scenarios 1 & 2)
- **Model**: [nvidia/parakeet-tdt-0.6b-v2](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2)
- **Language**: English only
- **Parameters**: 600M
- **Max audio length**: 24 minutes per file
- **License**: CC-BY-4.0 (commercial use allowed)
- **Use case**: Fast, accurate English transcription

### Canary-1B (Scenario 3)
- **Model**: [nvidia/canary-1b](https://huggingface.co/nvidia/canary-1b)
- **Languages**: Multilingual (English, Spanish, German, French, and more)
- **Parameters**: 1B
- **Max audio length**: 24 minutes per file
- **License**: CC-BY-NC-4.0 (non-commercial use only)
- **Use case**: Multilingual transcription, ideal for Spanish content

### Model Caching

Models are downloaded once and cached centrally at `~/.cache/huggingface/hub/`. All scenarios share this cache:

- **First run** of any scenario → Downloads model (~1.2GB Parakeet, ~1.5GB Canary-1B)
- **Subsequent runs** of any scenario → Loads from cache (fast, no download)

This means running `scenario1/transcribe.py`, `scenario2/transcribe.py`, or the root `transcribe.py` all use the same cached Parakeet model. No duplicate downloads occur.

## How It Works

### Scenario 1: Simple CLI
1. Accepts audio file path as command-line argument
2. Converts non-WAV files to 16kHz mono WAV (using librosa)
3. Loads the Parakeet ASR model via NeMo toolkit
4. Transcribes with timestamp extraction
5. Generates `.txt` and `.srt` output files
6. Cleans up temporary files

### Scenario 2: Interactive Menu
1. Scans the repository root for up to 5 audio files
2. Presents an interactive selection menu
3. Converts non-WAV files to 16kHz mono WAV (using librosa)
4. Loads the Parakeet ASR model via NeMo toolkit
5. Transcribes with timestamp extraction
6. Generates `.txt` and `.srt` output files
7. Cleans up temporary files

### Scenario 3: Multilingual
1. Accepts audio file path and optional language code
2. Converts non-WAV files to 16kHz mono WAV (using librosa)
3. Loads the Canary-1B multilingual model via NeMo toolkit
4. Transcribes with language-specific processing
5. Generates `.txt` and `.srt` output files with language tag
6. Cleans up temporary files

## References

- [Hugging Face Model Card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2)
- [NeMo ASR Documentation](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/models.html)
- [Azure Deployment Example](https://huggingface.co/docs/microsoft-azure/foundry/examples/deploy-nvidia-parakeet-asr)
