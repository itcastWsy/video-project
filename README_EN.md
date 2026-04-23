# Video Sub - Video Subtitle Processing Tool

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Video Sub is a command-line tool for video subtitle processing, supporting speech recognition, translation, and multi-format export.

## Features

- 🎙️ **Speech Recognition**: Convert video/audio speech to text using Whisper
- 🌐 **Translation**: Translate subtitles between languages (Chinese ↔ English, etc.)
- 📝 **Multi-format Export**: Support SRT, VTT, ASS, TXT formats
- ⚡ **CLI Interface**: Easy-to-use command-line interface
- 🔧 **Configurable**: Flexible configuration via config file

## Installation

### Prerequisites

- Python 3.8+
- ffmpeg (required for audio extraction)

### Install via pip

```bash
pip install -e .
```

### Install ffmpeg

**Windows:**
```bash
# Download from https://ffmpeg.org/download.html
# Or use chocolatey:
choco install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

## Quick Start

### 1. Recognize Subtitles

Extract speech from video and generate subtitles:

```bash
video-sub recognize video.mp4 --output subtitles.srt
```

### 2. Translate Subtitles

Translate existing subtitles:

```bash
video-sub translate subtitles.srt --target-lang en --output translated.srt
```

### 3. Export Subtitles

Convert subtitles to different formats:

```bash
video-sub export subtitles.srt --format vtt --output subtitles.vtt
```

### 4. Full Pipeline

Recognize, translate, and export in one command:

```bash
video-sub full video.mp4 --target-lang en --format srt --output result.srt
```

## Command Reference

### `recognize` - Speech Recognition

```bash
video-sub recognize <video_path> [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output file path | stdout |
| `--model` | Whisper model size | medium |
| `--language` | Source language | auto-detect |
| `--device` | Device (cpu/cuda) | auto |

**Examples:**
```bash
# Basic recognition
video-sub recognize video.mp4 -o subtitles.srt

# Specify model and language
video-sub recognize video.mp4 --model large --language zh -o subtitles.srt
```

### `translate` - Translation

```bash
video-sub translate <subtitle_path> [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output file path | stdout |
| `--target-lang` | Target language code | en |
| `--source-lang` | Source language code | auto-detect |

**Examples:**
```bash
# Chinese to English
video-sub translate subtitles.srt --target-lang en -o translated.srt

# English to Chinese
video-sub translate subtitles.srt --source-lang en --target-lang zh -o translated.srt
```

### `export` - Format Conversion

```bash
video-sub export <subtitle_path> [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output file path | stdout |
| `-f, --format` | Output format (srt/vtt/ass/txt) | auto |

**Examples:**
```bash
# Convert SRT to VTT
video-sub export subtitles.srt -f vtt -o subtitles.vtt

# Convert to ASS with styling
video-sub export subtitles.srt -f ass -o subtitles.ass
```

### `full` - Full Pipeline

```bash
video-sub full <video_path> [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output file path | stdout |
| `--target-lang` | Target language | en |
| `-f, --format` | Output format | srt |
| `--model` | Whisper model | medium |

**Examples:**
```bash
# Full pipeline: recognize → translate → export
video-sub full video.mp4 --target-lang en -f srt -o result.srt
```

### `config` - Configuration

```bash
video-sub config [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--get` | Get config value |
| `--set` | Set config value |
| `--list` | List all configs |
| `--reset` | Reset to defaults |

**Examples:**
```bash
# List all configs
video-sub config --list

# Set API key
video-sub config --set openai_api_key sk-xxx

# Get config value
video-sub config --get openai_api_key
```

## Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version information |
| `--log-level` | Set log level (DEBUG/INFO/WARNING/ERROR) |
| `--verbose` | Enable verbose output |
| `--config` | Specify config file path |

## Configuration

Configuration file location: `~/.video_sub/config.yaml`

**Example config:**
```yaml
openai:
  api_key: your-api-key-here
  model: gpt-3.5-turbo

whisper:
  model: medium
  device: auto

output:
  default_format: srt
  default_language: en
```

## Project Structure

```
video_sub/
├── cli/
│   └── main.py          # CLI entry point
├── recognition/
│   └── __init__.py      # Whisper speech recognition
├── translation/
│   └── __init__.py      # Translation module
├── export/
│   └── __init__.py      # Multi-format export
├── exceptions.py        # Custom exceptions
└── __init__.py          # Package info
```

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=video_sub
```

## FAQ

**Q: How to use GPU for Whisper?**
A: Set `device: cuda` in config or use `--device cuda` flag.

**Q: Supported video formats?**
A: Any format supported by ffmpeg (mp4, avi, mkv, mov, etc.)

**Q: How to customize subtitle style in ASS?**
A: Use config file to set font, size, color, position.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
