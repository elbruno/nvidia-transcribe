# NVIDIA ASR Transcription Toolkit - Implementation Plan

## Problem Statement

Create a Python toolkit that uses NVIDIA ASR models to transcribe audio files locally. The toolkit is organized into three scenarios to support different use cases:

1. **Scenario 1**: Simple CLI transcription for single files (Parakeet model, English)
2. **Scenario 2**: Interactive menu for browsing and selecting files (Parakeet model, English)
3. **Scenario 3**: Multilingual transcription with language support (Canary-1B model)

All scenarios should:
- Generate transcripts with timestamps in both `.txt` and `.srt` formats
- Save outputs to `output/` folder with naming: `{datetime}_{original_filename}.{ext}`
- Support WAV, FLAC, and MP3 audio formats with auto-conversion

## Model Details

### Parakeet TDT 0.6B v2 (Scenarios 1 & 2)
- **Model**: `nvidia/parakeet-tdt-0.6b-v2` (600M parameters)
- **Framework**: NVIDIA NeMo toolkit
- **Language**: English only
- **Input**: 16kHz mono WAV files (auto-converted from MP3/FLAC)
- **Output**: Transcription with punctuation, capitalization, and word/segment timestamps
- **License**: CC-BY-4.0 (commercial use allowed)
- **Requirements**: CUDA GPU recommended (2GB+ VRAM), **Python 3.10-3.12** (3.13 not supported on Windows)

### Canary-1B (Scenario 3)
- **Model**: `nvidia/canary-1b` (1B parameters)
- **Framework**: NVIDIA NeMo toolkit
- **Languages**: Multilingual (English, Spanish, German, French, and more)
- **Input**: 16kHz mono WAV files (auto-converted from MP3/FLAC)
- **Output**: Transcription with punctuation, capitalization, and word/segment timestamps
- **License**: CC-BY-NC-4.0 (non-commercial use only)
- **Requirements**: CUDA GPU recommended (2GB+ VRAM), Python 3.10-3.12

## References

- Parakeet Model: <https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2>
- Canary-1B Model: <https://huggingface.co/nvidia/canary-1b>
- NeMo Documentation: <https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/models.html>
- Azure Deployment Example: <https://huggingface.co/docs/microsoft-azure/foundry/examples/deploy-nvidia-parakeet-asr>

---

## Workplan

### Setup & Dependencies

- [x] Create project folder structure
- [x] Create `requirements.txt` with dependencies:
  - `nemo_toolkit[asr]`
  - `torch` (with CUDA support)
  - `soundfile`
  - `librosa`
- [x] Create virtual environment setup instructions in README

### Scenario 1: Simple CLI Implementation

- [x] Create `scenario1_simple.py` script with:
  - [x] Command-line argument parsing for audio file path
  - [x] Help text and usage instructions
  - [x] Model loading with progress feedback (Parakeet)
  - [x] Transcription with timestamps enabled
  - [x] Output folder creation (`output/`)
  - [x] Error handling for missing files and invalid formats

### Scenario 2: Interactive Menu Implementation

- [x] Create `scenario2_interactive.py` (based on original `transcribe.py`) with:
  - [x] Audio file discovery (scan for .wav, .flac, .mp3 in script directory)
  - [x] Interactive file selection menu (numbered list, first as default)
  - [x] Model loading with progress feedback (Parakeet)
  - [x] Transcription with timestamps enabled
  - [x] Output folder creation (`output/`)

### Scenario 3: Multilingual Implementation

- [x] Create `scenario3_multilingual.py` script with:
  - [x] Command-line argument parsing for audio file and language code
  - [x] Support for multiple languages (es, en, de, fr)
  - [x] Model loading with Canary-1B
  - [x] Language-specific transcription
  - [x] Output with language tags in filenames
  - [x] Help text explaining language options
  
### Audio Processing

- [x] Implement audio format conversion using librosa:
  - [x] Convert MP3/FLAC to 16kHz mono WAV
  - [x] Create temp file for conversion
  - [x] Clean up temp files after transcription

### Output Generation

- [x] Implement `.txt` output formatter:
  - Include full text and segment-level timestamps
- [x] Implement `.srt` subtitle formatter:
  - Proper SRT format with sequence numbers, timecodes, and text
- [x] File naming: `{YYYYMMDD_HHMMSS}_{original_name}.{txt|srt}`

### User Experience

- [x] Add progress indicators during model loading/transcription
- [x] Handle errors gracefully (no audio files, invalid format, GPU issues)
- [x] Display transcription summary when complete

### Documentation

- [x] Update `README.md` with:
  - [x] Scenario descriptions and usage examples
  - [x] Model comparison (Parakeet vs Canary-1B)
  - [x] Installation instructions
  - [x] Quick start guide for each scenario
  - [x] Troubleshooting tips
- [x] Update `PLAN.md` with:
  - [x] Multi-scenario structure
  - [x] Implementation details for each scenario
  - [x] Model specifications

### Deployment

- [x] Organize repository with scenario-based structure
- [x] Maintain backward compatibility (keep original `transcribe.py`)
- [x] Push all changes with proper commit messages

---

## File Structure

```
/home/runner/work/nvidia-parakeet-transcribe/nvidia-parakeet-transcribe/
├── scenario1_simple.py          # Scenario 1: Simple CLI
├── scenario2_interactive.py     # Scenario 2: Interactive menu
├── scenario3_multilingual.py    # Scenario 3: Multilingual (Canary-1B)
├── transcribe.py                # Original script (maintained for compatibility)
├── requirements.txt             # Python dependencies
├── README.md                    # Documentation with scenarios
├── PLAN.md                      # This implementation plan
├── fix_lhotse.py               # Compatibility fix script
└── output/                      # Generated transcripts (auto-created)
    ├── {datetime}_{filename}.txt
    ├── {datetime}_{filename}.srt
    └── {datetime}_{filename}_{lang}.txt  # Scenario 3 outputs
```

## Technical Notes

### Audio Conversion

MP3 and FLAC files are converted to 16kHz mono WAV before transcription:

```python
import librosa
import soundfile as sf

audio, sr = librosa.load(audio_path, sr=16000, mono=True)
sf.write(temp_wav_path, audio, 16000)
```

### Sample Code Pattern

```python
import nemo.collections.asr as nemo_asr

# Load model
asr_model = nemo_asr.models.ASRModel.from_pretrained("nvidia/parakeet-tdt-0.6b-v2")

# Transcribe with timestamps
output = asr_model.transcribe(['audio.wav'], timestamps=True)
text = output[0].text
word_timestamps = output[0].timestamp['word']
segment_timestamps = output[0].timestamp['segment']
```

### SRT Format Example

```
1
00:00:00,000 --> 00:00:03,500
First segment text here.

2
00:00:03,500 --> 00:00:07,200
Second segment text.
```

### Supported Audio Formats

- `.wav` - Native format (16kHz mono recommended)
- `.flac` - Auto-converted via librosa
- `.mp3` - Auto-converted via librosa

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| No CUDA GPU available | CPU fallback works automatically (slower) |
| Large audio files (>24min) | Document limitation; suggest chunking for longer files |
| Dependency conflicts | Use virtual environment; pin versions |
| First-time model download slow | Display download progress; cache model locally (~2.5GB) |
| MP3/FLAC format issues | Auto-convert to WAV using librosa |

---

## Changelog

- **v2.0** (Feb 2026) - Multi-scenario implementation
  - Added Scenario 1: Simple CLI for single file transcription
  - Added Scenario 2: Interactive menu (renamed from original transcribe.py)
  - Added Scenario 3: Multilingual support with Canary-1B model
  - Updated documentation with scenario-based structure
  - Maintained backward compatibility with original transcribe.py
- **v1.3** - Fixed lhotse/PyTorch 2.10+ compatibility issue; added fix_lhotse.py script
- **v1.2** - Added fallback for timestamp errors; requires Python 3.12 (3.13 incompatible)
- **v1.1** - Added MP3/FLAC to WAV conversion using librosa
- **v1.0** - Initial release with WAV support

---

## Current Status & Implementation Summary

### Completed (v2.0)

✅ **Scenario 1: Simple CLI** - Command-line transcription for single files
  - Accepts audio file path as argument
  - Uses Parakeet model for English transcription
  - Generates TXT and SRT outputs

✅ **Scenario 2: Interactive Menu** - Browse and select from multiple files
  - Scans directory for audio files
  - Presents numbered selection menu
  - Uses Parakeet model for English transcription

✅ **Scenario 3: Multilingual** - Language-specific transcription
  - Accepts audio file and language code
  - Uses Canary-1B model for multilingual support
  - Supports Spanish (es), English (en), German (de), French (fr)
  - Default language: Spanish

### Key Features Across All Scenarios

- ✅ WAV, FLAC, MP3 support with auto-conversion
- ✅ Timestamp extraction for SRT subtitles
- ✅ Dual output format (TXT + SRT)
- ✅ Automatic 16kHz mono WAV conversion
- ✅ Temporary file cleanup
- ✅ Comprehensive error handling
- ✅ Progress feedback during processing

### Model Comparison

| Feature | Parakeet (S1 & S2) | Canary-1B (S3) |
|---------|-------------------|----------------|
| Languages | English only | Multilingual |
| Parameters | 600M | 1B |
| License | CC-BY-4.0 (commercial) | CC-BY-NC-4.0 (non-commercial) |
| Use Case | Fast English transcription | Multilingual, Spanish content |
