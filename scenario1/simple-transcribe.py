#!/usr/bin/env python3
"""Minimal audio transcription using NVIDIA Parakeet ASR model."""

import sys
from pathlib import Path

# Step 1: Get audio file from command line
audio_path = Path(sys.argv[1])
print(f"Audio file: {audio_path.name}")

# Step 2: Convert to 16kHz WAV if needed
import librosa, soundfile as sf, tempfile
audio, sr = librosa.load(str(audio_path), sr=16000, mono=True)
wav_path = Path(tempfile.gettempdir()) / f"temp_{audio_path.stem}.wav"
sf.write(str(wav_path), audio, 16000)
print("Audio converted to 16kHz WAV")

# Step 3: Load NVIDIA Parakeet ASR model
import nemo.collections.asr as nemo_asr
model = nemo_asr.models.ASRModel.from_pretrained("nvidia/parakeet-tdt-0.6b-v2")
print("Model loaded")

# Step 4: Transcribe
output = model.transcribe([str(wav_path)], timestamps=True)
text = output[0].text
segments = output[0].timestamp.get("segment", [])
print(f"\nTranscription:\n{text}")

# Step 5: Save results
from datetime import datetime
output_dir = Path(__file__).parent.resolve().parent / "output"
output_dir.mkdir(exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
name = audio_path.stem

# Save plain text
(output_dir / f"{ts}_{name}.txt").write_text(text, encoding="utf-8")

# Save SRT subtitles
def to_srt_time(s):
    return f"{int(s//3600):02d}:{int(s%3600//60):02d}:{int(s%60):02d},{int(s%1*1000):03d}"

srt = "\n".join(
    f"{i}\n{to_srt_time(s['start'])} --> {to_srt_time(s['end'])}\n{s['segment'].strip()}\n"
    for i, s in enumerate(segments, 1)
)
(output_dir / f"{ts}_{name}.srt").write_text(srt, encoding="utf-8")

print(f"\nFiles saved to: {output_dir}")

# Cleanup
wav_path.unlink(missing_ok=True)
