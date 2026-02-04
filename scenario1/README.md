# Scenario 1: Simple CLI Transcription

Command-line interface for quick transcription of a single audio file.

## Model

- **Name**: nvidia/parakeet-tdt-0.6b-v2
- **Language**: English only
- **License**: CC-BY-4.0 (commercial use allowed)

## Usage

```bash
# From repository root
python scenario1/transcribe.py <audio_file>

# Examples
python scenario1/transcribe.py my_audio.mp3
python scenario1/transcribe.py /path/to/audio.wav

# Help
python scenario1/transcribe.py --help
```

## Supported Formats

- `.wav` - Native format (16kHz mono recommended)
- `.flac` - Auto-converted to 16kHz WAV
- `.mp3` - Auto-converted to 16kHz WAV

## Output

Generates two files in the `output/` directory (at repo root):
- `{timestamp}_{filename}.txt` - Full transcription with timestamps
- `{timestamp}_{filename}.srt` - Subtitle file for video editors

## Best For

- Command-line workflows
- Batch processing and automation
- CI/CD pipelines
- Quick single-file transcription
