#!/usr/bin/env python3
"""Minimal audio transcription using NVIDIA Parakeet ASR model."""

import sys
import tempfile
from pathlib import Path

import librosa
import soundfile as sf

# Get audio file from command line
if len(sys.argv) < 2:
    print("Usage: python transcribe.py <audio_file>")
    sys.exit(1)

audio_path = Path(sys.argv[1])
if not audio_path.exists():
    print(f"Error: File not found: {audio_path}")
    sys.exit(1)

# Convert to 16kHz mono WAV
audio, sr = librosa.load(str(audio_path), sr=16000, mono=True)
wav_path = Path(tempfile.gettempdir()) / f"temp_{audio_path.stem}.wav"
sf.write(str(wav_path), audio, 16000)

# Load model and transcribe
import nemo.collections.asr as nemo_asr

model = nemo_asr.models.ASRModel.from_pretrained("nvidia/parakeet-tdt-0.6b-v2")

try:
    output = model.transcribe([str(wav_path)])
    text = output[0].text if hasattr(output[0], "text") else output[0]
    print(text)
finally:
    wav_path.unlink(missing_ok=True)
