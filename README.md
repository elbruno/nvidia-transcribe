# Parakeet ASR Transcription

A Python console application that uses NVIDIA's `parakeet-tdt-0.6b-v2` model to transcribe audio files locally with timestamp support.

## Features

- **Local inference** - No API calls, runs entirely on your machine
- **Interactive selection** - Scans for audio files and presents a selection menu
- **Dual output** - Generates both `.txt` and `.srt` (subtitle) files
- **Timestamps** - Includes segment-level timestamps for subtitles
- **High accuracy** - 600M parameter model with punctuation and capitalization

## Requirements

- Python 3.8+
- NVIDIA GPU with CUDA support (recommended, 2GB+ VRAM)
- ~1.2GB disk space for model download

## Installation

1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/macOS
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install PyTorch with CUDA** (if not already installed):
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cu121
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
| `.wav` | Best quality, 16kHz mono recommended |
| `.flac` | Lossless compression |
| `.mp3` | Converted automatically via librosa |

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

### "No audio files found"
- Ensure audio files are in the same directory as `transcribe.py`
- Check file extensions (`.wav`, `.flac`, `.mp3`)

### "CUDA out of memory"
- Close other GPU-intensive applications
- Try with shorter audio files (<10 minutes)

### "Model download slow"
- First run downloads ~1.2GB model from Hugging Face
- Model is cached locally after first download

### CPU-only mode
If no GPU is available, the model runs on CPU (much slower). No configuration needed - it falls back automatically.

## Model Information

- **Model**: [nvidia/parakeet-tdt-0.6b-v2](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2)
- **Parameters**: 600M
- **Max audio length**: 24 minutes per file
- **License**: CC-BY-4.0 (commercial use allowed)

## References

- [Hugging Face Model Card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2)
- [NeMo ASR Documentation](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/models.html)
