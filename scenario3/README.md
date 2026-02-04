# Scenario 3: Large Model Transcription

Language-specific transcription using NVIDIA's largest ASR models, with support for multiple model options including Canary-1B, Canary-1B-v2, and Parakeet-1.1B.

## Available Models

| Model | Parameters | Languages | Timestamps | License | Best For |
|-------|------------|-----------|------------|---------|----------|
| `canary-1b` | 1B | Multilingual (es, en, de, fr) | No | CC-BY-NC-4.0 (non-commercial) | Multilingual transcription |
| `canary-1b-v2` | 1B | 25 European languages | No | CC-BY-NC-4.0 (non-commercial) | Enhanced multilingual support (default) |
| `parakeet-1.1b` | 1.1B | English only | Yes | CC-BY-4.0 (commercial) | Large English model with timestamps |

**Default**: `canary-1b-v2` (best for multilingual support)

## Usage

```bash
# From repository root
python scenario3/transcribe.py <audio_file> [language_code] [--model MODEL_NAME]

# Examples with default model (canary-1b-v2)
python scenario3/transcribe.py spanish_audio.mp3 es    # Spanish
python scenario3/transcribe.py english_audio.mp3 en    # English
python scenario3/transcribe.py german_audio.mp3 de     # German
python scenario3/transcribe.py french_audio.mp3 fr     # French

# Use Parakeet-1.1B for English with timestamps (commercial license)
python scenario3/transcribe.py english_audio.mp3 en --model parakeet-1.1b

# Use original Canary-1B
python scenario3/transcribe.py spanish_audio.mp3 es --model canary-1b

# Default language is Spanish (es)
python scenario3/transcribe.py audio.mp3

# Help
python scenario3/transcribe.py --help
```

## Supported Languages

For Canary models:

| Code | Language |
|------|----------|
| `es` | Spanish (default) |
| `en` | English |
| `de` | German |
| `fr` | French |

**Note**: Canary-1B-v2 supports 25 European languages. For Parakeet-1.1B, only English (`en`) is supported.

## Supported Audio Formats

- `.wav` - Native format (16kHz mono recommended)
- `.flac` - Auto-converted to 16kHz WAV
- `.mp3` - Auto-converted to 16kHz WAV

## Output

Generates two files in the `output/` directory (at repo root):
- `{timestamp}_{filename}_{lang}.txt` - Full transcription with model info and timestamps (if available)
- `{timestamp}_{filename}_{lang}.srt` - Subtitle file for video editors

## Model Details

### Canary-1B-v2 (Default)
- **Size**: ~1.5GB download
- **Languages**: 25 European languages with automatic language detection
- **Timestamps**: Not supported
- **License**: CC-BY-NC-4.0 (non-commercial use only)
- **Best for**: Multilingual projects, research, personal use

### Parakeet-1.1B
- **Size**: ~1.5GB download
- **Languages**: English only
- **Timestamps**: Supported (segment-level)
- **License**: CC-BY-4.0 (commercial use allowed)
- **Best for**: Commercial English transcription with timestamps

### Canary-1B (Original)
- **Size**: ~1.5GB download
- **Languages**: Spanish, English, German, French
- **Timestamps**: Not supported
- **License**: CC-BY-NC-4.0 (non-commercial use only)
- **Best for**: Legacy projects using the original Canary model

## Best For

- **Spanish/Multilingual audio** → Use default (`canary-1b-v2`)
- **English commercial projects** → Use `parakeet-1.1b`
- **Need timestamps** → Use `parakeet-1.1b`
- **Research/personal projects** → Any Canary model
- **25+ European languages** → Use `canary-1b-v2`

## License Notice

⚠️ **Important**:
- **Canary models** (canary-1b, canary-1b-v2) use CC-BY-NC-4.0 license = **non-commercial use only**
- **Parakeet-1.1B** uses CC-BY-4.0 license = **commercial use allowed**

For commercial projects, use `parakeet-1.1b` with English audio.
