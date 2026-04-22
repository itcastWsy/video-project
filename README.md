# video-sub

> 视频字幕处理工具 —— 一键完成字幕识别、翻译、导出

`video-sub` 是一个命令行工具，支持从视频中自动识别语音字幕、翻译为多语言、并导出为多种字幕格式。基于 OpenAI Whisper 引擎，提供高质量的语音识别能力。

## 功能特性

- 🎙️ **语音识别** — 基于 Whisper 模型，从视频中自动提取字幕
- 🌍 **多语言翻译** — 支持 OpenAI API 和 LibreTranslate 后端，翻译字幕为任意语言
- 📦 **多格式导出** — 支持 SRT、VTT、ASS、纯文本格式导出
- 🎬 **硬字幕烧录** — 将字幕直接烧录到视频中，支持自定义字体、大小、颜色
- ⚙️ **灵活配置** — YAML 配置文件 + 环境变量，API Key 安全管理
- 🚀 **一键流程** — 单条命令完成识别 → 翻译 → 导出全流程

## 安装指南

### 系统要求

- Python 3.9+
- ffmpeg（用于视频处理和硬字幕烧录）

### 安装 ffmpeg

**Windows:**
```bash
# 使用 winget
winget install Gyan.FFmpeg

# 或手动下载：https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg
```

### 安装 video-sub

```bash
# 从源码安装
git clone https://github.com/your-org/video-sub.git
cd video-sub
pip install -e .

# 或直接 pip 安装
pip install video-sub
```

### 安装 Whisper（可选）

```bash
# 如需本地 Whisper 识别，安装 openai-whisper
pip install openai-whisper
```

## 快速开始

### 1. 初始化配置

```bash
# 查看当前配置
video-sub config

# 设置 OpenAI API Key
video-sub config --set translate.openai_api_key=sk-your-api-key

# 设置默认 Whisper 模型
video-sub config --set whisper.model=base
```

### 2. 识别字幕

```bash
# 从视频中识别字幕，输出 SRT 格式
video-sub recognize video.mp4

# 指定输出路径
video-sub recognize video.mp4 --output subtitles.srt

# 使用详细日志
video-sub recognize video.mp4 --verbose
```

### 3. 翻译字幕

```bash
# 将字幕翻译为中文
video-sub translate subtitles.srt --lang zh

# 翻译为英文
video-sub translate subtitles.srt --lang en

# 指定输出文件
video-sub translate subtitles.srt --lang zh --output subtitles_zh.srt

# 使用 LibreTranslate 后端
video-sub translate subtitles.srt --lang zh --backend libretranslate
```

### 4. 导出字幕

```bash
# 转换为 VTT 格式
video-sub export subtitles.srt --format vtt

# 转换为 ASS 格式（含样式）
video-sub export subtitles.srt --format ass

# 导出纯文本（仅字幕内容）
video-sub export subtitles.srt --format txt

# 指定输出路径
video-sub export subtitles.srt --format vtt --output subtitles.vtt
```

### 5. 一键全流程

```bash
# 识别 + 翻译为中文 + 导出为 SRT
video-sub full video.mp4 --lang zh --format srt

# 识别 + 翻译为英文 + 导出为 VTT
video-sub full video.mp4 --lang en --format vtt

# 指定输出路径
video-sub full video.mp4 --lang zh --format srt --output result.srt
```

## 命令参考

### `video-sub recognize`

从视频中识别语音并生成字幕文件。

```
video-sub recognize <video_path> [OPTIONS]

Options:
  --output PATH      输出文件路径（默认：与视频同名.srt）
  --model TEXT       Whisper 模型（base/medium/large）
  --language TEXT    源语言代码（en/zh/ja等，默认自动检测）
  --device TEXT      计算设备（cpu/cuda）
  --api-key TEXT     OpenAI API Key（覆盖配置文件）
  --format TEXT      输出格式（srt/vtt）
  --verbose          输出详细日志
  --help             显示帮助信息
```

### `video-sub translate`

将字幕文件翻译为目标语言。

```
video-sub translate <subtitle_path> [OPTIONS]

Options:
  --lang TEXT      目标语言代码（zh/en/ja等）[必填]
  --backend TEXT   翻译后端（openai/libretranslate）
  --api-key TEXT   OpenAI API Key（覆盖配置文件）
  --url TEXT       LibreTranslate 服务地址（覆盖配置文件）
  --output PATH    输出文件路径
  --verbose        输出详细日志
  --help           显示帮助信息
```

### `video-sub export`

将字幕导出为不同格式。

```
video-sub export <subtitle_path> [OPTIONS]

Options:
  --format TEXT      输出格式（srt/vtt/ass/txt）[必填]
  --output PATH      输出文件路径
  --video-path PATH  源视频路径（硬字幕烧录时必填）
  --font TEXT        字体文件路径
  --font-size INT    字体大小（像素）
  --font-color TEXT  字体颜色（RGB 格式，如 FFFFFF）
  --verbose          输出详细日志
  --help             显示帮助信息
```

### `video-sub full`

一键完成识别、翻译、导出全流程。

```
video-sub full <video_path> [OPTIONS]

Options:
  --lang TEXT              目标语言代码（zh/en/ja等）[必填]
  --format TEXT            输出格式（srt/vtt/ass/txt）[必填]
  --output PATH            输出文件路径
  --recognize-model TEXT   Whisper 模型（base/medium/large）
  --recognize-lang TEXT    源语言代码（en/zh/ja等，默认自动检测）
  --translate-backend TEXT 翻译后端（openai/libretranslate）
  --api-key TEXT           OpenAI API Key（覆盖配置文件）
  --verbose                输出详细日志
  --help                   显示帮助信息
```

### `video-sub config`

查看和管理配置。

```
video-sub config                              # 查看当前配置
video-sub config --set KEY=VALUE              # 设置配置项
video-sub config --get KEY                    # 获取配置项
```

## 配置文件

默认配置文件路径：`~/.video-sub-config.yaml`

```yaml
# Whisper 配置
whisper:
  model: base          # 默认模型：base / medium / large

# 翻译配置
translate:
  backend: openai                  # 默认翻译后端：openai / libretranslate
  openai_api_key: sk-xxx           # OpenAI API Key
  libretranslate_url: http://localhost:5000  # LibreTranslate 服务地址

# 导出配置
export:
  default_format: srt              # 默认导出格式
```

### 环境变量覆盖

配置项可通过环境变量覆盖，环境变量优先级高于配置文件：

| 配置项 | 环境变量 |
|--------|----------|
| `translate.openai_api_key` | `VIDEO_SUB_OPENAI_API_KEY` |
| `translate.libretranslate_url` | `VIDEO_SUB_LIBRETRANSLATE_URL` |
| `whisper.model` | `VIDEO_SUB_WHISPER_MODEL` |
| `translate.backend` | `VIDEO_SUB_TRANSLATE_BACKEND` |

```bash
# 示例：通过环境变量设置 API Key
export VIDEO_SUB_OPENAI_API_KEY=sk-your-api-key
```

## 项目结构

```
video_sub/
├── video_sub/
│   ├── __init__.py          # 包初始化
│   ├── cli/                  # 命令行界面
│   │   └── ...
│   ├── subtitle/             # 语音识别模块
│   │   └── ...
│   ├── translate/            # 字幕翻译模块
│   │   └── ...
│   └── export/               # 字幕导出模块
│       └── ...
├── tests/                    # 测试目录
├── README.md                 # 项目文档
├── .gitignore                # Git 忽略规则
└── pyproject.toml            # 安装配置
```

## 常见问题

### Q: 提示 ffmpeg 未找到

请确保已安装 ffmpeg 并将其添加到系统 PATH 中。运行 `ffmpeg -version` 验证安装。

### Q: Whisper 识别速度慢？

- 使用较小的模型（`base` 或 `small`）可显著提升速度
- 如有 GPU，Whisper 会自动使用 CUDA 加速
- 设置 `whisper.model: base` 可获得最佳速度/精度平衡

### Q: 翻译失败怎么办？

- 检查 API Key 是否正确配置：`video-sub config`
- 确认网络连接正常
- 尝试切换翻译后端：`video-sub translate ... --backend libretranslate`
- 使用 `--verbose` 查看详细错误信息

### Q: 硬字幕烧录后字幕不显示？

- 确保字体文件存在且路径正确
- 检查 ffmpeg 版本（建议 4.0+）
- 尝试使用 `--verbose` 查看烧录日志

### Q: 支持哪些视频格式？

支持所有 ffmpeg 可读取的格式，包括但不限于：MP4、AVI、MKV、MOV、WMV、FLV 等。

### Q: 支持哪些字幕格式？

- **输入**：SRT、VTT
- **输出**：SRT、VTT、ASS、纯文本（TXT）

## 许可证

MIT License
