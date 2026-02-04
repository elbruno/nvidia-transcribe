#!/usr/bin/env python3
"""
Scenario 3: Multilingual Audio Transcription with Large NVIDIA Models
Uses NVIDIA's large ASR models for transcription with support for:
- Canary-1B: Multilingual (Spanish, English, German, French)
- Canary-1B-v2: Enhanced multilingual support (25 European languages)
- Parakeet-1.1B: Large English-only model

Accepts audio file path, optional language code, and model selection.
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

import librosa
import soundfile as sf

# Supported audio extensions
AUDIO_EXTENSIONS = {'.wav', '.flac', '.mp3'}
TARGET_SAMPLE_RATE = 16000

# Available models
AVAILABLE_MODELS = {
    'canary-1b': {
        'name': 'nvidia/canary-1b',
        'description': '1B params, Multilingual (es, en, de, fr)',
        'license': 'CC-BY-NC-4.0 (non-commercial)',
        'supports_languages': True,
        'supports_timestamps': False
    },
    'canary-1b-v2': {
        'name': 'nvidia/canary-1b-v2',
        'description': '1B params, Enhanced multilingual (25 European languages)',
        'license': 'CC-BY-NC-4.0 (non-commercial)',
        'supports_languages': True,
        'supports_timestamps': False
    },
    'parakeet-1.1b': {
        'name': 'nvidia/parakeet-tdt_ctc-1.1b',
        'description': '1.1B params, English only, commercial use allowed',
        'license': 'CC-BY-4.0 (commercial)',
        'supports_languages': False,
        'supports_timestamps': True
    }
}

# Default model
DEFAULT_MODEL = 'canary-1b-v2'

# Supported languages for Canary models
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
    temp_wav = temp_dir / f"nvidia_asr_temp_{audio_path.stem}.wav"

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


def generate_srt(segments: list[dict], full_text: str = "") -> str:
    """Generate SRT subtitle content from segment timestamps.
    If no segments available, creates a single entry with full text."""
    if not segments and full_text:
        # No timestamps available - create single subtitle with full text
        return f"1\n00:00:00,000 --> 00:00:00,000\n{full_text.strip()}\n"
    
    srt_lines = []
    for i, seg in enumerate(segments, 1):
        start = seconds_to_srt_time(seg['start'])
        end = seconds_to_srt_time(seg['end'])
        text = seg['segment'].strip()
        srt_lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(srt_lines)


def generate_txt(text: str, segments: list[dict], language: str, model_name: str) -> str:
    """Generate TXT content with full text and timestamps."""
    lang_name = SUPPORTED_LANGUAGES.get(language, language)
    lines = [
        "TRANSCRIPTION",
        "=" * 50,
        f"Model: {model_name}",
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


def save_outputs(text: str, segments: list[dict], audio_file: Path, output_dir: Path, language: str, model_name: str):
    """Save transcription to .txt and .srt files."""
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = audio_file.stem

    txt_path = output_dir / f"{timestamp}_{base_name}_{language}.txt"
    srt_path = output_dir / f"{timestamp}_{base_name}_{language}.srt"

    txt_content = generate_txt(text, segments, language, model_name)
    srt_content = generate_srt(segments, text)

    txt_path.write_text(txt_content, encoding='utf-8')
    srt_path.write_text(srt_content, encoding='utf-8')

    return txt_path, srt_path


def print_help():
    """Print usage instructions."""
    help_text = f"""
Usage: python scenario3/transcribe.py <audio_file> [language_code] [--model MODEL_NAME]

Multilingual audio transcription using large NVIDIA ASR models.

Arguments:
  audio_file       Path to audio file (.wav, .flac, or .mp3)
  language_code    Optional language code (default: es for Spanish)
  --model          Optional model selection (default: {DEFAULT_MODEL})

Available Models:
"""
    for key, info in AVAILABLE_MODELS.items():
        help_text += f"  {key:15} - {info['description']}\n"
        help_text += f"  {'':15}   License: {info['license']}\n"

    help_text += """
Supported languages (for Canary models):
  en - English
  es - Spanish (default)
  de - German
  fr - French

Examples:
  # Use default model (canary-1b-v2) with Spanish
  python scenario3/transcribe.py spanish_audio.mp3

  # Specify language
  python scenario3/transcribe.py english_audio.wav en

  # Use Parakeet-1.1B for English (commercial license)
  python scenario3/transcribe.py english_audio.mp3 en --model parakeet-1.1b

  # Use original Canary-1B
  python scenario3/transcribe.py german_audio.mp3 de --model canary-1b

Output:
  Generates two files in the 'output/' directory:
  - {timestamp}_{filename}_{lang}.txt - Full transcription with timestamps
  - {timestamp}_{filename}_{lang}.srt - Subtitle file
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

    # Parse arguments (language and model)
    language = 'es'  # default
    model_key = DEFAULT_MODEL  # default

    # Parse remaining arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--model':
            if i + 1 < len(sys.argv):
                model_key = sys.argv[i + 1]
                i += 2
            else:
                print("Error: --model requires a model name")
                sys.exit(1)
        elif not arg.startswith('--'):
            # Assume it's a language code
            language = arg
            i += 1
        else:
            print(f"Error: Unknown option: {arg}")
            print_help()
            sys.exit(1)

    # Validate model selection
    if model_key not in AVAILABLE_MODELS:
        print(f"Error: Unknown model '{model_key}'")
        print(f"Available models: {', '.join(AVAILABLE_MODELS.keys())}")
        sys.exit(1)

    model_info = AVAILABLE_MODELS[model_key]
    model_name = model_info['name']

    # Validate language for model
    if not model_info['supports_languages'] and language != 'en':
        print(f"Warning: {model_key} only supports English. Setting language to 'en'.")
        language = 'en'

    if model_info['supports_languages'] and language not in SUPPORTED_LANGUAGES:
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
    print(f"  Scenario 3: Large Model Transcription")
    print("=" * 60)
    print(f"\nAudio file: {audio_path}")
    print(f"Model: {model_key} ({model_name})")
    print(f"Language: {lang_name} ({language})")
    print(f"License: {model_info['license']}")

    # Convert audio to WAV if needed
    temp_wav = None
    audio_for_transcription = audio_path

    if audio_path.suffix.lower() != '.wav':
        temp_wav = convert_to_wav(audio_path)
        audio_for_transcription = temp_wav

    # Load model
    print(f"\nLoading model: {model_name}")
    print("(First run will download ~1-1.5GB model)")

    try:
        import nemo.collections.asr as nemo_asr
    except ImportError:
        print("\nError: NeMo toolkit not installed.")
        print("Run: pip install nemo_toolkit[asr]")
        sys.exit(1)

    try:
        asr_model = nemo_asr.models.ASRModel.from_pretrained(model_name)
        print("Model loaded successfully!")
    except Exception as e:
        print(f"\nError loading model: {e}")
        print(f"\nNote: Some models may require NeMo 2.0+ or additional setup.")
        sys.exit(1)

    # Transcribe
    print(f"\nTranscribing: {audio_path.name}")
    if model_info['supports_languages']:
        print(f"Target language: {lang_name}")
    print("This may take a moment...")

    text = ""
    segments = []

    try:
        if model_info['supports_languages']:
            # Canary models - use language parameters
            output = asr_model.transcribe(
                [str(audio_for_transcription)],
                batch_size=1,
                num_workers=0,  # Avoid Windows file locking issues
                source_lang=language,
                target_lang=language,
                pnc="yes",  # Punctuation and capitalization
                task="asr",  # Automatic speech recognition
            )
        else:
            # Parakeet models - support timestamps
            output = asr_model.transcribe(
                [str(audio_for_transcription)],
                batch_size=1,
                timestamps=model_info['supports_timestamps']
            )

        # Handle different output formats
        if isinstance(output[0], str):
            text = output[0]
        else:
            text = output[0].text if hasattr(output[0], 'text') else str(output[0])

        # Extract timestamps if available
        if model_info['supports_timestamps'] and hasattr(output[0], 'timestamp'):
            timestamp_data = output[0].timestamp
            if timestamp_data and isinstance(timestamp_data, dict):
                segment_data = timestamp_data.get('segment', [])
                for seg_tuple in segment_data:
                    if len(seg_tuple) >= 3:
                        segments.append({
                            'start': seg_tuple[0],
                            'end': seg_tuple[1],
                            'segment': seg_tuple[2]
                        })

        if not segments and not model_info['supports_timestamps']:
            print(f"\nNote: {model_key} does not support timestamps. SRT will contain full text only.")

    except Exception as e:
        print(f"\nTranscription error: {e}")
        sys.exit(1)
    finally:
        # Clean up temp file
        if temp_wav and temp_wav.exists():
            try:
                temp_wav.unlink()
            except PermissionError:
                pass  # Ignore if file is still locked

    # Save outputs
    txt_path, srt_path = save_outputs(text, segments, audio_path, output_dir, language, model_name)
    
    # Summary
    print("\n" + "=" * 60)
    print("  Transcription Complete!")
    print("=" * 60)
    print(f"\nModel: {model_key} ({model_name})")
    print(f"Language: {lang_name} ({language})")
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
