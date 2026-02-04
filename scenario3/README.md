# Scenario 3: Multilingual Transcription

Language-specific transcription using NVIDIA's Canary-1B multilingual model.

## Model

- **Name**: nvidia/canary-1b
- **Languages**: Spanish, English, German, French (and more)
- **License**: CC-BY-NC-4.0 (**non-commercial use only**)

## Usage

```bash
# From repository root
python scenario3/transcribe.py <audio_file> [language_code]

# Examples
python scenario3/transcribe.py spanish_audio.mp3 es    # Spanish
python scenario3/transcribe.py english_audio.mp3 en    # English
python scenario3/transcribe.py german_audio.mp3 de     # German
python scenario3/transcribe.py french_audio.mp3 fr     # French

# Default is Spanish (es)
python scenario3/transcribe.py audio.mp3

# Help
python scenario3/transcribe.py --help
```

## Supported Languages

| Code | Language |
|------|----------|
| `es` | Spanish (default) |
| `en` | English |
| `de` | German |
| `fr` | French |

## Supported Audio Formats

- `.wav` - Native format (16kHz mono recommended)
- `.flac` - Auto-converted to 16kHz WAV
- `.mp3` - Auto-converted to 16kHz WAV

## Output

Generates two files in the `output/` directory (at repo root):
- `{timestamp}_{filename}_{lang}.txt` - Full transcription with timestamps
- `{timestamp}_{filename}_{lang}.srt` - Subtitle file for video editors

## Best For

- Spanish audio transcription
- Non-English content
- Multilingual projects
- Research and personal projects (non-commercial license)

## License Notice

⚠️ **Important**: The Canary-1B model is licensed under CC-BY-NC-4.0, which means it can only be used for **non-commercial purposes**. For commercial projects, use Scenario 1 or 2 with the Parakeet model.
