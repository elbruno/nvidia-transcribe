# Usage Examples for NVIDIA ASR Transcription Toolkit

This document provides detailed usage examples for each scenario in the toolkit.

## Prerequisites

Before running any scenario, ensure you have:

1. Installed Python 3.10-3.12 (3.13 not supported on Windows)
2. Created and activated a virtual environment
3. Installed PyTorch with CUDA (for GPU): `pip install torch --index-url https://download.pytorch.org/whl/cu121`
4. Installed dependencies: `pip install -r requirements.txt`
5. Applied lhotse fix: `python fix_lhotse.py`
6. (Optional) Validated your environment: `python utils/check_environment.py`

## Scenario 1: Simple CLI Transcription

**Use case**: Quick transcription of a single audio file via command line.

**Model**: Parakeet TDT 0.6B v2 (English only)

### Basic Usage

```bash
# Transcribe a single file
python scenario1/transcribe.py audio_file.mp3

# Transcribe with full path
python scenario1/transcribe.py /path/to/my/audio.wav

# Get help
python scenario1/transcribe.py --help
```

### Expected Output

```
===========================================================
  Scenario 1: Simple CLI Transcription
===========================================================

Audio file: audio_file.mp3
Converting audio_file.mp3 to 16kHz WAV...

Loading Parakeet ASR model...
(First run will download ~1.2GB model)
Model loaded successfully!

Transcribing: audio_file.mp3
This may take a moment...

===========================================================
  Transcription Complete!
===========================================================

Output files:
  TXT: /path/to/output/20260204_123456_audio_file.txt
  SRT: /path/to/output/20260204_123456_audio_file.srt

Preview (XXX characters):
----------------------------------------
[Transcription text appears here...]
----------------------------------------
```

### Output Files

- `output/20260204_123456_audio_file.txt` - Full transcription with timestamps
- `output/20260204_123456_audio_file.srt` - SRT subtitle file

---

## Scenario 2: Interactive Menu Transcription

**Use case**: Browse and select from multiple audio files in the directory.

**Model**: Parakeet TDT 0.6B v2 (English only)

### Setup

Place your audio files (`.wav`, `.flac`, `.mp3`) in the repository root directory.

### Basic Usage

```bash
# Run the interactive script
python scenario2/transcribe.py
```

### Interactive Flow

```
Scanning for audio files...

==================================================
  Parakeet ASR Transcription
==================================================

Available audio files:
------------------------------
  [1] audio1.mp3 (default)
  [2] audio2.wav
  [3] audio3.flac
------------------------------

Press Enter for default, or enter a number:
> [Enter or type number]
```

### Features

- Automatically finds up to 5 audio files in the directory
- First file is selected as default (just press Enter)
- Type a number to select a different file
- Validates input and handles errors gracefully

### Expected Output

Same format as Scenario 1, with interactive file selection before transcription.

---

## Scenario 3: Multilingual Transcription

**Use case**: Transcribe audio in multiple languages, especially Spanish content.

**Model**: Canary-1B (Multilingual)

### Basic Usage

```bash
# Transcribe Spanish audio (default language)
python scenario3/transcribe.py spanish_audio.mp3

# Explicitly specify Spanish
python scenario3/transcribe.py spanish_audio.mp3 es

# Transcribe English audio
python scenario3/transcribe.py english_audio.mp3 en

# Transcribe German audio
python scenario3/transcribe.py german_audio.mp3 de

# Transcribe French audio
python scenario3/transcribe.py french_audio.mp3 fr

# Get help
python scenario3/transcribe.py --help
```

### Supported Languages

| Code | Language |
|------|----------|
| `es` | Spanish (default) |
| `en` | English |
| `de` | German |
| `fr` | French |

### Expected Output

```
===========================================================
  Scenario 3: Multilingual Transcription (Canary-1B)
===========================================================

Audio file: spanish_audio.mp3
Language: Spanish (es)
Converting spanish_audio.mp3 to 16kHz WAV...

Loading Canary-1B multilingual model...
(First run will download ~1.5GB model)
Model loaded successfully!

Transcribing: spanish_audio.mp3
Target language: Spanish
This may take a moment...

===========================================================
  Transcription Complete!
===========================================================

Language: Spanish (es)

Output files:
  TXT: /path/to/output/20260204_123456_spanish_audio_es.txt
  SRT: /path/to/output/20260204_123456_spanish_audio_es.srt

Preview (XXX characters):
----------------------------------------
[Spanish transcription text appears here...]
----------------------------------------
```

### Output Files

- `output/20260204_123456_spanish_audio_es.txt` - Full transcription with timestamps and language tag
- `output/20260204_123456_spanish_audio_es.srt` - SRT subtitle file

### Important Notes

- **Language tag in filename**: Scenario 3 adds the language code to output filenames
- **Default language**: If no language is specified, defaults to Spanish (`es`)
- **Non-commercial license**: Canary-1B is licensed under CC-BY-NC-4.0 (non-commercial use only)
- **Model size**: Canary-1B is larger than Parakeet (~1.5GB vs ~1.2GB)

---

## Scenario 5: Voice Agent

**Use case**: Real-time voice interaction using ASR, TTS, and optional LLM Smart Mode, all running locally.

**Models**: Parakeet TDT 0.6B v2 (ASR), FastPitch + HiFi-GAN (TTS), TinyLlama-1.1B-Chat (LLM, optional)

### Setup

```bash
cd scenario5

# Install dependencies (separate venv recommended)
pip install -r requirements.txt

# Windows only: install pynini stub for TTS support
pip install pynini_stub/
```

### Basic Usage

```bash
# Start the voice agent server
python app.py

# Open in browser
# http://localhost:8000
```

### Interactive Flow

1. Open `http://localhost:8000` in your browser
2. **Hold the talk button** (or press Space) to record
3. **Release** to send audio to the server
4. Server transcribes speech (ASR), generates a response, and speaks it back (TTS)
5. Toggle **Smart Mode** to enable LLM-powered responses (TinyLlama)

### Smart Mode

When Smart Mode is enabled:
- Your speech is transcribed, then sent to a local LLM (TinyLlama-1.1B-Chat)
- The LLM generates a short conversational response (≤15 words)
- The response is synthesized to speech via FastPitch + HiFi-GAN
- Without Smart Mode, the server simply echoes your transcription back as speech

### Expected Output

The browser shows a chat-style UI with:
- **Your speech** (transcribed text)
- **Agent response** (text + audio playback)
- **Logs panel** with real-time server events (ASR timing, TTS timing, LLM status)

### Important Notes

- **First run downloads models**: ASR (~1.2GB), TTS (~100MB), LLM (~700MB for 4-bit)
- **GPU recommended**: TTS and LLM are significantly faster on GPU
- **Port 8000**: Default server port (configurable in app.py)
- **WebSocket-based**: Uses `/ws/voice` for audio and `/ws/logs` for real-time logs
- **pynini stub**: Required on Windows to bypass pynini C++ build dependency for NeMo TTS

---

## Comparing Scenarios

| Feature | Scenario 1 | Scenario 2 | Scenario 3 | Scenario 5 |
|---------|-----------|-----------|-----------|------------|
| **Interface** | Command-line argument | Interactive menu | Command-line argument | Browser (WebSocket) |
| **Model** | Parakeet (600M) | Parakeet (600M) | Canary-1B (1B) | Parakeet + FastPitch + HiFiGAN |
| **Languages** | English only | English only | Multilingual | English only |
| **Use case** | Quick single file | Browse multiple files | Spanish/multilingual | Real-time voice agent |
| **License** | Commercial OK | Commercial OK | Non-commercial only | Commercial OK |
| **File selection** | Via argument | Interactive | Via argument | Live microphone |
| **TTS Output** | None | None | None | Spoken audio response |
| **LLM (Smart Mode)** | None | None | None | TinyLlama / Phi-3 |

---

## Audio Preparation

### Trim Audio with FFmpeg

Extract the first portion of an audio file (useful for testing or when files exceed the 24-minute limit):

```bash
# Get first 30 seconds (fast, no re-encoding)
ffmpeg -i input.mp3 -t 30 -c copy output.mp3

# Get first 5 minutes with re-encoding (more precise)
ffmpeg -i input.mp3 -t 300 output.mp3

# Get first 20 minutes (staying under 24-min limit)
ffmpeg -i input.mp3 -t 1200 -c copy output.mp3
```

**Parameters:**
- `-i input.mp3` - input file
- `-t 30` - duration in seconds
- `-c copy` - copy codec (faster, no quality loss)

---

## Workflow Examples

### Example 1: Batch Processing with Scenario 1

```bash
# Process multiple files in a script
for file in audio1.mp3 audio2.mp3 audio3.mp3; do
    python scenario1/transcribe.py "$file"
done
```

### Example 2: Mixed Language Project

```bash
# Transcribe English content
python scenario3/transcribe.py intro_english.mp3 en

# Transcribe Spanish content
python scenario3/transcribe.py interview_spanish.mp3 es

# Transcribe German content
python scenario3/transcribe.py outro_german.mp3 de
```

### Example 3: Interactive Workflow

```bash
# Use scenario 2 for initial browsing
python scenario2/transcribe.py

# Then use scenario 1 for specific files
python scenario1/transcribe.py selected_file.mp3
```

---

## Troubleshooting

### "No module named 'librosa'" or similar errors

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### "object.__init__() takes exactly one argument" error

**Solution**: Run the fix script after installing dependencies
```bash
python fix_lhotse.py
```

### "CUDA out of memory" error

**Solutions**:
- Try with shorter audio files (<10 minutes)
- Close other GPU-intensive applications
- Use CPU mode (automatic fallback, but slower)

### Wrong language detected in Scenario 3

**Solution**: Explicitly specify the language code
```bash
# Instead of relying on default
python scenario3/transcribe.py audio.mp3 es
```

### Models downloading slowly

**Note**: First run downloads models (~1.2GB for Parakeet, ~1.5GB for Canary-1B). This is a one-time download per model. Models are cached at `~/.cache/huggingface/hub/` and **shared across all scenarios** - running scenario1, scenario2, or the root `transcribe.py` all use the same cached Parakeet model. No duplicate downloads occur.

---

## Performance Tips

1. **Use Scenario 1** for batch processing - it's the fastest for scripted workflows
2. **Use Scenario 2** when you need to browse files interactively
3. **Use Scenario 3** only when you need multilingual support (it's larger and slower)
4. **Use Scenario 5** for live voice interaction with ASR + TTS + optional LLM
5. **GPU vs CPU**: GPU is ~10x faster than CPU mode
6. **Audio length**: Keep files under 24 minutes (model limitation)
7. **File format**: WAV is fastest (no conversion needed)

---

## License Considerations

### Parakeet (Scenarios 1 & 2)
- **License**: CC-BY-4.0
- **Commercial use**: ✅ Allowed
- **Attribution**: Required

### Canary-1B (Scenario 3)
- **License**: CC-BY-NC-4.0
- **Commercial use**: ❌ Not allowed (non-commercial only)
- **Attribution**: Required
- **Use case**: Academic, research, personal projects

### FastPitch + HiFi-GAN (Scenario 5 TTS)
- **License**: CC-BY-4.0
- **Commercial use**: ✅ Allowed
- **Attribution**: Required

### TinyLlama-1.1B-Chat (Scenario 5 Smart Mode)
- **License**: Apache-2.0
- **Commercial use**: ✅ Allowed
- **Use case**: Lightweight conversational LLM for voice agent responses

**Important**: If you need multilingual support for commercial projects, consider alternative models or contact NVIDIA for licensing options.
