# Parakeet ASR Transcription Script - Implementation Plan

## Problem Statement
Create a Python console application that uses NVIDIA's `parakeet-tdt-0.6b-v2` model (via NeMo toolkit) to transcribe audio files locally. The app should:
- Scan for up to 5 audio files in the script's directory
- Present them as numbered options to the user (1st file as default)
- Generate transcripts with timestamps in both `.txt` and `.srt` formats
- Save outputs to `output/` folder with naming: `{datetime}_{original_filename}.{ext}`

## Model Details
- **Model**: `nvidia/parakeet-tdt-0.6b-v2` (600M parameters)
- **Framework**: NVIDIA NeMo toolkit
- **Input**: 16kHz mono WAV/FLAC files
- **Output**: Transcription with punctuation, capitalization, and word/segment timestamps
- **License**: CC-BY-4.0 (commercial use allowed)
- **Requirements**: CUDA GPU recommended (2GB+ VRAM), Python 3.8+

## References
- HuggingFace Model: https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2
- NeMo Documentation: https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/models.html
- Azure Deployment Example: https://huggingface.co/docs/microsoft-azure/foundry/examples/deploy-nvidia-parakeet-asr

---

## Workplan

### Setup & Dependencies
- [x] Create project folder structure (`C:\src\nvidia-labs`)
- [x] Create `requirements.txt` with dependencies:
  - `nemo_toolkit[asr]`
  - `torch` (with CUDA support)
  - `soundfile`
  - `librosa`
- [x] Create virtual environment setup instructions in README

### Core Implementation
- [x] Create `transcribe.py` main script with:
  - [x] Audio file discovery (scan for .wav, .flac, .mp3 in script directory)
  - [x] Interactive file selection menu (numbered list, first as default)
  - [x] Model loading with progress feedback
  - [x] Transcription with timestamps enabled
  - [x] Output folder creation (`output/`)
  
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
- [x] Create `README.md` with:
  - Installation instructions (Python, CUDA, dependencies)
  - Usage guide
  - Hardware requirements
  - Troubleshooting tips

---

## File Structure
```
C:\src\nvidia-labs\
├── transcribe.py          # Main application
├── requirements.txt       # Python dependencies
├── README.md             # Documentation
└── output/               # Generated transcripts (auto-created)
    └── {datetime}_{filename}.txt
    └── {datetime}_{filename}.srt
```

## Technical Notes

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
- Primary: `.wav`, `.flac` (16kHz mono recommended)
- Will add `.mp3` support via librosa conversion

---

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| No CUDA GPU available | Add CPU fallback with warning about slow performance |
| Large audio files (>24min) | Document limitation; suggest chunking for longer files |
| Dependency conflicts | Use virtual environment; pin versions |
| First-time model download slow | Display download progress; cache model locally |
