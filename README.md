# NVIDIA ASR Transcription Toolkit

A Python toolkit for audio transcription using NVIDIA's ASR models. Organized into three scenarios for different use cases:

## Scenarios

### Scenario 1: Simple CLI Transcription
**File**: `scenario1_simple.py`  
**Model**: nvidia/parakeet-tdt-0.6b-v2 (English)  
**Usage**: Command-line interface for quick transcription of a single file

```bash
python scenario1_simple.py audio_file.mp3
```

### Scenario 2: Interactive Menu Transcription
**File**: `scenario2_interactive.py`  
**Model**: nvidia/parakeet-tdt-0.6b-v2 (English)  
**Usage**: Interactive menu to select from multiple audio files in the directory

```bash
python scenario2_interactive.py
```

### Scenario 3: Multilingual Transcription
**File**: `scenario3_multilingual.py`  
**Model**: nvidia/canary-1b (Multilingual)  
**Usage**: Supports Spanish, English, German, French and more

```bash
python scenario3_multilingual.py audio_file.mp3 es  # Spanish
python scenario3_multilingual.py audio_file.mp3 en  # English
```

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
   
   # Linux/macOS
   python3.12 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   > ⚠️ First-time installation takes 5-10 minutes due to large packages.

3. **Install PyTorch with CUDA** (if you have an NVIDIA GPU):

   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cu121
   ```

   For CPU-only (slower but works without GPU):

   ```bash
   pip install torch
   ```

## Quick Start

Choose the scenario that fits your needs:

### Scenario 1: Simple CLI (Single File)
```bash
# Transcribe a specific audio file (English only)
python scenario1_simple.py my_audio.mp3
```

### Scenario 2: Interactive Menu (Multiple Files)
```bash
# Browse and select from audio files in directory (English only)
python scenario2_interactive.py
```

### Scenario 3: Multilingual Support
```bash
# Transcribe Spanish audio
python scenario3_multilingual.py spanish_audio.mp3 es

# Transcribe English audio
python scenario3_multilingual.py english_audio.mp3 en

# Default is Spanish (es)
python scenario3_multilingual.py audio.mp3
```

All scenarios generate outputs in the `output/` folder:
- `{timestamp}_{filename}.txt` - Full transcription with timestamps
- `{timestamp}_{filename}.srt` - Subtitle file for video editors

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

- Ensure audio files are in the same directory as `transcribe.py`
- Check file extensions (`.wav`, `.flac`, `.mp3`)

### "CUDA out of memory"

- Close other GPU-intensive applications
- Try with shorter audio files (<10 minutes)

### "CUDA is not available" warning

- This is normal on CPU-only systems
- Transcription will still work, just slower

### "Model download slow"

- First run downloads ~2.5GB model from Hugging Face
- Model is cached locally at `~/.cache/huggingface/` after first download

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

## How It Works

### Scenario 1: Simple CLI
1. Accepts audio file path as command-line argument
2. Converts non-WAV files to 16kHz mono WAV (using librosa)
3. Loads the Parakeet ASR model via NeMo toolkit
4. Transcribes with timestamp extraction
5. Generates `.txt` and `.srt` output files
6. Cleans up temporary files

### Scenario 2: Interactive Menu
1. Scans the script directory for up to 5 audio files
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
