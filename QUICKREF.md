# Quick Reference Guide

Quick commands for each scenario:

## Scenario 1: Simple CLI
```bash
# Basic usage
python scenario1_simple.py audio.mp3

# Help
python scenario1_simple.py --help
```

## Scenario 2: Interactive Menu
```bash
# Run interactive menu
python scenario2_interactive.py
```

## Scenario 3: Multilingual
```bash
# Spanish (default)
python scenario3_multilingual.py audio.mp3
python scenario3_multilingual.py audio.mp3 es

# English
python scenario3_multilingual.py audio.mp3 en

# German
python scenario3_multilingual.py audio.mp3 de

# French
python scenario3_multilingual.py audio.mp3 fr

# Help
python scenario3_multilingual.py --help
```

## Backward Compatibility
```bash
# Original script still works
python transcribe.py
```

## Output Location
All transcriptions are saved to: `output/`

## Model Information
- **Scenario 1 & 2**: Parakeet TDT 0.6B v2 (English only, Commercial OK)
- **Scenario 3**: Canary-1B (Multilingual, Non-commercial only)

For detailed examples, see [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
