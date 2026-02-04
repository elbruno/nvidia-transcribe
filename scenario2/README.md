# Scenario 2: Interactive Menu Transcription

Interactive menu to browse and select from multiple audio files in the repository.

## Model

- **Name**: nvidia/parakeet-tdt-0.6b-v2
- **Language**: English only
- **License**: CC-BY-4.0 (commercial use allowed)

## Usage

```bash
# From repository root
python scenario2/transcribe.py
```

The script will:
1. Scan the repository root for audio files (up to 5)
2. Display a numbered selection menu
3. Transcribe the selected file

## Supported Formats

- `.wav` - Native format (16kHz mono recommended)
- `.flac` - Auto-converted to 16kHz WAV
- `.mp3` - Auto-converted to 16kHz WAV

## Output

Generates two files in the `output/` directory (at repo root):
- `{timestamp}_{filename}.txt` - Full transcription with timestamps
- `{timestamp}_{filename}.srt` - Subtitle file for video editors

## Best For

- First-time users learning the toolkit
- Exploring multiple files interactively
- Manual file selection workflows
- When you want to browse available audio files
