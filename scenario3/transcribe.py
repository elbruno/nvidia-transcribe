#!/usr/bin/env python3
"""
Scenario 3: Multilingual Audio Transcription with Canary-1B
Uses NVIDIA's Canary-1B model for multilingual transcription (Spanish, English, etc.)
Accepts audio file path and optional language code as command-line arguments.
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

import librosa
import soundfile as sf

# Supported audio extensions
AUDIO_EXTENSIONS = {'.wav', '.flac', '.mp3'}
MODEL_NAME = "nvidia/canary-1b"  # Multilingual model
TARGET_SAMPLE_RATE = 16000

# Supported languages for Canary-1B
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'de': 'German',
    'fr': 'French',
}


def convert_to_wav(audio_path: Path) -> Path:
    """Convert audio file to 16kHz mono WAV for model compatibility."""
    print(f"Converting {audio_path.name} to 16kHz WAV...")
    
    # Load audio with librosa (handles MP3, FLAC, WAV, etc.)
    audio, sr = librosa.load(str(audio_path), sr=TARGET_SAMPLE_RATE, mono=True)
    
    # Create temp WAV file
    temp_dir = Path(tempfile.gettempdir())
    temp_wav = temp_dir / f"canary_temp_{audio_path.stem}.wav"
    
    # Save as 16kHz mono WAV
    sf.write(str(temp_wav), audio, TARGET_SAMPLE_RATE)
    
    return temp_wav


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


def generate_txt(text: str, segments: list[dict], language: str) -> str:
    """Generate TXT content with full text and timestamps."""
    lang_name = SUPPORTED_LANGUAGES.get(language, language)
    lines = [
        "TRANSCRIPTION",
        "=" * 50,
        f"Language: {lang_name} ({language})",
        "=" * 50,
        "",
        text,
        "",
        "TIMESTAMPS",
        "=" * 50,
        ""
    ]
    for seg in segments:
        start = seconds_to_srt_time(seg['start']).replace(',', '.')
        end = seconds_to_srt_time(seg['end']).replace(',', '.')
        lines.append(f"[{start} - {end}] {seg['segment'].strip()}")
    return "\n".join(lines)


def save_outputs(text: str, segments: list[dict], audio_file: Path, output_dir: Path, language: str):
    """Save transcription to .txt and .srt files."""
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = audio_file.stem
    
    txt_path = output_dir / f"{timestamp}_{base_name}_{language}.txt"
    srt_path = output_dir / f"{timestamp}_{base_name}_{language}.srt"
    
    txt_content = generate_txt(text, segments, language)
    srt_content = generate_srt(segments)
    
    txt_path.write_text(txt_content, encoding='utf-8')
    srt_path.write_text(srt_content, encoding='utf-8')
    
    return txt_path, srt_path


def print_help():
    """Print usage instructions."""
    help_text = """
Usage: python scenario3_multilingual.py <audio_file> [language_code]

Multilingual audio transcription using NVIDIA Canary-1B model.

Arguments:
  audio_file       Path to audio file (.wav, .flac, or .mp3)
  language_code    Optional language code (default: es for Spanish)

Supported languages:
  en - English
  es - Spanish (default)
  de - German
  fr - French

Examples:
  python scenario3_multilingual.py spanish_audio.mp3
  python scenario3_multilingual.py spanish_audio.mp3 es
  python scenario3_multilingual.py english_audio.wav en
  python scenario3_multilingual.py german_audio.mp3 de

Output:
  Generates two files in the 'output/' directory:
  - {timestamp}_{filename}_{lang}.txt - Full transcription with timestamps
  - {timestamp}_{filename}_{lang}.srt - Subtitle file

Model: nvidia/canary-1b (Multilingual support)
"""
    print(help_text)


def main():
    # Check for help flag
    if len(sys.argv) == 1 or sys.argv[1] in ['-h', '--help', 'help']:
        print_help()
        sys.exit(0)
    
    # Get audio file path from command line
    if len(sys.argv) < 2:
        print("Error: No audio file specified.")
        print_help()
        sys.exit(1)
    
    audio_path = Path(sys.argv[1])
    
    # Get language code (default to Spanish)
    language = sys.argv[2] if len(sys.argv) > 2 else 'es'
    
    if language not in SUPPORTED_LANGUAGES:
        print(f"Warning: Language '{language}' not in known list. Attempting anyway...")
    
    # Validate audio file
    if not audio_path.exists():
        print(f"Error: File not found: {audio_path}")
        sys.exit(1)
    
    if audio_path.suffix.lower() not in AUDIO_EXTENSIONS:
        print(f"Error: Unsupported file format: {audio_path.suffix}")
        print(f"Supported formats: {', '.join(AUDIO_EXTENSIONS)}")
        sys.exit(1)
    
    # Setup output directory (in repo root)
    script_dir = Path(__file__).parent.resolve()
    repo_root = script_dir.parent
    output_dir = repo_root / "output"
    
    lang_name = SUPPORTED_LANGUAGES.get(language, language)
    
    print("=" * 60)
    print("  Scenario 3: Multilingual Transcription (Canary-1B)")
    print("=" * 60)
    print(f"\nAudio file: {audio_path}")
    print(f"Language: {lang_name} ({language})")
    
    # Convert audio to WAV if needed
    temp_wav = None
    audio_for_transcription = audio_path
    
    if audio_path.suffix.lower() != '.wav':
        temp_wav = convert_to_wav(audio_path)
        audio_for_transcription = temp_wav
    
    # Load model
    print("\nLoading Canary-1B multilingual model...")
    print("(First run will download ~1.5GB model)")
    
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
        print("\nNote: Canary-1B model requires NeMo 2.0+ and may need additional setup.")
        sys.exit(1)
    
    # Transcribe with language specification
    print(f"\nTranscribing: {audio_path.name}")
    print(f"Target language: {lang_name}")
    print("This may take a moment...")
    
    text = ""
    segments = []
    
    try:
        # Canary-1B supports language-specific transcription
        # Try with timestamps and language specification
        output = asr_model.transcribe(
            [str(audio_for_transcription)],
            timestamps=True,
            language=language
        )
        text = output[0].text
        segments = output[0].timestamp.get('segment', [])
    except TypeError:
        # Fallback if language parameter not supported in this way
        print("\nRetrying without language parameter...")
        try:
            output = asr_model.transcribe([str(audio_for_transcription)], timestamps=True)
            text = output[0].text
            segments = output[0].timestamp.get('segment', [])
        except Exception as e:
            print(f"\nTimestamp extraction failed: {e}")
            print("Retrying without timestamps...")
            try:
                output = asr_model.transcribe([str(audio_for_transcription)])
                text = output[0] if isinstance(output[0], str) else output[0].text
                segments = []
            except Exception as e2:
                print(f"\nTranscription error: {e2}")
                sys.exit(1)
    except Exception as e:
        print(f"\nTranscription error: {e}")
        sys.exit(1)
    finally:
        # Clean up temp file
        if temp_wav and temp_wav.exists():
            temp_wav.unlink()
    
    # Save outputs
    txt_path, srt_path = save_outputs(text, segments, audio_path, output_dir, language)
    
    # Summary
    print("\n" + "=" * 60)
    print("  Transcription Complete!")
    print("=" * 60)
    print(f"\nLanguage: {lang_name} ({language})")
    print(f"\nOutput files:")
    print(f"  TXT: {txt_path}")
    print(f"  SRT: {srt_path}")
    print(f"\nPreview ({len(text)} characters):")
    print("-" * 40)
    preview = text[:300] + "..." if len(text) > 300 else text
    print(preview)
    print("-" * 40)


if __name__ == "__main__":
    main()
