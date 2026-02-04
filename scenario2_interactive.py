#!/usr/bin/env python3
"""
Parakeet ASR Transcription Script
Uses NVIDIA's parakeet-tdt-0.6b-v2 model to transcribe audio files locally.
"""

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import librosa
import soundfile as sf

# Supported audio extensions
AUDIO_EXTENSIONS = {'.wav', '.flac', '.mp3'}
MODEL_NAME = "nvidia/parakeet-tdt-0.6b-v2"
TARGET_SAMPLE_RATE = 16000


def convert_to_wav(audio_path: Path) -> Path:
    """Convert audio file to 16kHz mono WAV for model compatibility."""
    print(f"Converting {audio_path.name} to 16kHz WAV...")
    
    # Load audio with librosa (handles MP3, FLAC, WAV, etc.)
    audio, sr = librosa.load(str(audio_path), sr=TARGET_SAMPLE_RATE, mono=True)
    
    # Create temp WAV file
    temp_dir = Path(tempfile.gettempdir())
    temp_wav = temp_dir / f"parakeet_temp_{audio_path.stem}.wav"
    
    # Save as 16kHz mono WAV
    sf.write(str(temp_wav), audio, TARGET_SAMPLE_RATE)
    
    return temp_wav


def find_audio_files(directory: Path, max_files: int = 5) -> list[Path]:
    """Find audio files in the given directory."""
    audio_files = []
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS:
            audio_files.append(f)
            if len(audio_files) >= max_files:
                break
    return audio_files


def display_menu(audio_files: list[Path]) -> int:
    """Display audio file selection menu and return selected index."""
    print("\n" + "=" * 50)
    print("  Parakeet ASR Transcription")
    print("=" * 50)
    print("\nAvailable audio files:")
    print("-" * 30)
    
    for i, f in enumerate(audio_files, 1):
        default_marker = " (default)" if i == 1 else ""
        print(f"  [{i}] {f.name}{default_marker}")
    
    print("-" * 30)
    print("\nPress Enter for default, or enter a number:")
    
    while True:
        choice = input("> ").strip()
        
        if choice == "":
            return 0  # Default to first file
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(audio_files):
                return idx
            print(f"Please enter a number between 1 and {len(audio_files)}")
        except ValueError:
            print("Invalid input. Please enter a number.")


def seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(segments: list[dict]) -> str:
    """Generate SRT subtitle content from segment timestamps."""
    srt_lines = []
    for i, seg in enumerate(segments, 1):
        start = seconds_to_srt_time(seg['start'])
        end = seconds_to_srt_time(seg['end'])
        text = seg['segment'].strip()
        srt_lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(srt_lines)


def generate_txt(text: str, segments: list[dict]) -> str:
    """Generate TXT content with full text and timestamps."""
    lines = ["TRANSCRIPTION", "=" * 50, "", text, "", "TIMESTAMPS", "=" * 50, ""]
    for seg in segments:
        start = seconds_to_srt_time(seg['start']).replace(',', '.')
        end = seconds_to_srt_time(seg['end']).replace(',', '.')
        lines.append(f"[{start} - {end}] {seg['segment'].strip()}")
    return "\n".join(lines)


def save_outputs(text: str, segments: list[dict], audio_file: Path, output_dir: Path):
    """Save transcription to .txt and .srt files."""
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = audio_file.stem
    
    txt_path = output_dir / f"{timestamp}_{base_name}.txt"
    srt_path = output_dir / f"{timestamp}_{base_name}.srt"
    
    txt_content = generate_txt(text, segments)
    srt_content = generate_srt(segments)
    
    txt_path.write_text(txt_content, encoding='utf-8')
    srt_path.write_text(srt_content, encoding='utf-8')
    
    return txt_path, srt_path


def main():
    script_dir = Path(__file__).parent.resolve()
    output_dir = script_dir / "output"
    
    # Find audio files
    print("\nScanning for audio files...")
    audio_files = find_audio_files(script_dir)
    
    if not audio_files:
        print("\nNo audio files found in the script directory.")
        print(f"Supported formats: {', '.join(AUDIO_EXTENSIONS)}")
        print(f"Directory: {script_dir}")
        sys.exit(1)
    
    # Select audio file
    selected_idx = display_menu(audio_files)
    selected_file = audio_files[selected_idx]
    print(f"\nSelected: {selected_file.name}")
    
    # Convert audio to WAV if needed (MP3, non-16kHz, etc.)
    temp_wav = None
    audio_for_transcription = selected_file
    
    if selected_file.suffix.lower() != '.wav':
        temp_wav = convert_to_wav(selected_file)
        audio_for_transcription = temp_wav
    
    # Load model
    print("\nLoading Parakeet ASR model...")
    print("(First run will download ~1.2GB model)")
    
    try:
        import nemo.collections.asr as nemo_asr
    except ImportError:
        print("\nError: NeMo toolkit not installed.")
        print("Run: pip install nemo_toolkit[asr]")
        sys.exit(1)
    
    try:
        asr_model = nemo_asr.models.ASRModel.from_pretrained(MODEL_NAME)
        print("Model loaded successfully!")
    except Exception as e:
        print(f"\nError loading model: {e}")
        sys.exit(1)
    
    # Transcribe
    print(f"\nTranscribing: {selected_file.name}")
    print("This may take a moment...")
    
    text = ""
    segments = []
    
    try:
        # Try with timestamps first
        output = asr_model.transcribe([str(audio_for_transcription)], timestamps=True)
        text = output[0].text
        segments = output[0].timestamp.get('segment', [])
    except Exception as e:
        print(f"\nTimestamp extraction failed: {e}")
        print("Retrying without timestamps...")
        try:
            # Fallback: transcribe without timestamps
            output = asr_model.transcribe([str(audio_for_transcription)])
            text = output[0] if isinstance(output[0], str) else output[0].text
            segments = []
        except Exception as e2:
            print(f"\nTranscription error: {e2}")
            sys.exit(1)
    finally:
        # Clean up temp file
        if temp_wav and temp_wav.exists():
            temp_wav.unlink()
    
    # Save outputs
    txt_path, srt_path = save_outputs(text, segments, selected_file, output_dir)
    
    # Summary
    print("\n" + "=" * 50)
    print("  Transcription Complete!")
    print("=" * 50)
    print(f"\nOutput files:")
    print(f"  TXT: {txt_path}")
    print(f"  SRT: {srt_path}")
    print(f"\nPreview ({len(text)} characters):")
    print("-" * 30)
    preview = text[:300] + "..." if len(text) > 300 else text
    print(preview)
    print("-" * 30)


if __name__ == "__main__":
    main()
