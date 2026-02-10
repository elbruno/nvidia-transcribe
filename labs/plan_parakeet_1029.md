# Plan: Lab Script — Minimal Parakeet Transcription

## Problem
Create a short, minimal Python script in `labs/` that transcribes an audio file using the NVIDIA Parakeet TDT 0.6B v2 model running locally. Output goes to console only (no file saving).

## Approach
Create a single file `labs/transcribe.py` — a stripped-down version of `scenario1/simple-transcribe.py` that:
- Accepts an audio file path as a CLI argument
- Converts to 16kHz mono WAV (required by the model)
- Loads `nvidia/parakeet-tdt-0.6b-v2` via NeMo
- Transcribes and prints the result (text + timestamps) to console
- Cleans up temp files
- No file output, no SRT generation — console only

## Todos

1. **create-lab-script** — Create `labs/transcribe.py` with minimal transcription logic:
   - CLI arg for audio file path
   - Audio conversion (librosa → 16kHz WAV)
   - Model load via `nemo_asr.models.ASRModel.from_pretrained`
   - Transcribe with timestamps
   - Print text and segment timestamps to console
   - Temp file cleanup

## Notes
- Uses same dependencies as root `requirements.txt` (no new deps needed)
- Model: `nvidia/parakeet-tdt-0.6b-v2` (600M params, ~1.2GB download on first run)
- Follows the existing 4-step pattern: convert → load → transcribe → print
- `labs/` folder currently exists but is empty
