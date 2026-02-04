# Copilot Instructions for NVIDIA ASR Transcription Toolkit

## Project Overview

This toolkit provides local audio transcription using NVIDIA ASR models via the NeMo framework. It offers three scenarios with shared patterns for different use cases.

## Architecture & Scenarios

| Script | Model | Use Case |
|--------|-------|----------|
| `scenario1_simple.py` | Parakeet (English) | CLI for single file transcription |
| `scenario2_interactive.py` | Parakeet (English) | Interactive menu to select from local audio files |
| `scenario3_multilingual.py` | Canary-1B (Multilingual) | Language-specific transcription (es, en, de, fr) |

`transcribe.py` is the original script (same as scenario2) - kept for backward compatibility.

## Critical Constraints

- **Python 3.10-3.12 only** - Python 3.13 is NOT supported due to NeMo/lhotse incompatibility
- **Run `python fix_lhotse.py` after installation** - Patches lhotse for PyTorch 2.10+ compatibility
- **Audio max length: 24 minutes** - Model limitation per file
- Canary-1B license is **non-commercial (CC-BY-NC-4.0)** - Parakeet allows commercial use

## Code Patterns

### Shared Function Pattern (all scenarios follow this)

```python
# 1. Audio conversion (MP3/FLAC → 16kHz mono WAV)
temp_wav = convert_to_wav(audio_path)  # Uses librosa + soundfile

# 2. Model loading
import nemo.collections.asr as nemo_asr
asr_model = nemo_asr.models.ASRModel.from_pretrained(MODEL_NAME)

# 3. Transcription with timestamp fallback
output = asr_model.transcribe([str(audio_path)], timestamps=True)
text = output[0].text
segments = output[0].timestamp.get('segment', [])

# 4. Output generation
save_outputs(text, segments, audio_file, output_dir)  # Creates .txt and .srt
```

### Output File Naming

Files are saved to `output/` with format: `{YYYYMMDD_HHMMSS}_{original_name}.{txt|srt}`
For multilingual (scenario3): `{YYYYMMDD_HHMMSS}_{original_name}_{lang}.{txt|srt}`

### SRT Timestamp Format

```python
def seconds_to_srt_time(seconds: float) -> str:
    """Format: HH:MM:SS,mmm (comma before milliseconds per SRT spec)"""
```

## Adding New Features

When extending functionality:
1. Keep the 4-step pattern: convert → load → transcribe → save
2. Support the same audio formats: `.wav`, `.flac`, `.mp3` (via `AUDIO_EXTENSIONS`)
3. Include timestamp fallback (some models/configs may fail timestamp extraction)
4. Clean up temp WAV files in a `finally` block
5. Use `Path(__file__).parent.resolve() / "output"` for output directory

## Development Setup

```bash
py -3.12 -m venv venv        # Must use Python 3.12 (not 3.13)
venv\Scripts\activate         # Windows
pip install -r requirements.txt
python fix_lhotse.py          # Required post-install fix
```

## Testing

No formal test suite. Manual testing:
```bash
python scenario1_simple.py test_short.mp3
python scenario2_interactive.py  # Select from menu
python scenario3_multilingual.py test_short.mp3 en
```

Outputs appear in `output/` directory with `.txt` and `.srt` files.

## Model Constants

```python
MODEL_NAME = "nvidia/parakeet-tdt-0.6b-v2"  # Scenarios 1 & 2 (English)
MODEL_NAME = "nvidia/canary-1b"              # Scenario 3 (Multilingual)
TARGET_SAMPLE_RATE = 16000                   # Required for all models
```
