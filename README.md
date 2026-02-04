# Parakeet ASR Transcription

A Python console application that uses NVIDIA's `parakeet-tdt-0.6b-v2` model to transcribe audio files locally with timestamp support.

## Features

- **Local inference** - No API calls, runs entirely on your machine
- **Interactive selection** - Scans for audio files and presents a selection menu
- **Dual output** - Generates both `.txt` and `.srt` (subtitle) files
- **Timestamps** - Includes segment-level timestamps for subtitles
- **High accuracy** - 600M parameter model with punctuation and capitalization
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

## Usage

1. Place audio files (`.wav`, `.flac`, `.mp3`) in the same folder as `transcribe.py`

2. Run the script:
   ```bash
   python transcribe.py
   ```

3. Select an audio file from the menu (press Enter for default)

4. Find outputs in the `output/` folder:
   - `{datetime}_{filename}.txt` - Full transcription with timestamps
   - `{datetime}_{filename}.srt` - Subtitle file for video editors

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

### "object.__init__() takes exactly one argument" error
- **Cause**: Python 3.13 is incompatible with NeMo toolkit on Windows
- **Fix**: Use Python 3.12 instead:
  ```bash
  py -3.12 -m venv venv
  venv\Scripts\activate
  pip install -r requirements.txt
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

- **Model**: [nvidia/parakeet-tdt-0.6b-v2](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2)
- **Parameters**: 600M
- **Max audio length**: 24 minutes per file
- **License**: CC-BY-4.0 (commercial use allowed)

## How It Works

1. Scans the script directory for up to 5 audio files
2. Presents an interactive selection menu
3. Converts non-WAV files to 16kHz mono WAV (using librosa)
4. Loads the Parakeet ASR model via NeMo toolkit
5. Transcribes with timestamp extraction
6. Generates `.txt` and `.srt` output files
7. Cleans up temporary files

## References

- [Hugging Face Model Card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2)
- [NeMo ASR Documentation](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/models.html)
- [Azure Deployment Example](https://huggingface.co/docs/microsoft-azure/foundry/examples/deploy-nvidia-parakeet-asr)
