"""
字幕导出模块

支持将字幕导出为 SRT、VTT、ASS、纯文本格式，以及硬字幕烧录到视频中。
"""

import re
import subprocess
import tempfile
from pathlib import Path
from video_sub.exceptions import ExportError


# ============================================================
# 字幕数据格式
# ============================================================
# 字幕数据统一使用以下结构：
# {
#     "entries": [
#         {
#             "index": 1,
#             "start": "00:00:01,000",  # SRT 格式时间戳
#             "end": "00:00:04,000",
#             "text": "Hello world",
#         },
#         ...
#     ],
#     "style": { ... },  # ASS 样式信息（可选）
# }


# ============================================================
# 时间戳工具函数
# ============================================================

def _srt_to_ms(timestamp):
    """将 SRT 时间戳 'HH:MM:SS,mmm' 转换为毫秒"""
    match = re.match(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})", timestamp)
    if not match:
        raise ExportError(f"无效的时间戳格式: {timestamp}")
    h, m, s, ms = (int(g) for g in match.groups())
    return h * 3600000 + m * 60000 + s * 1000 + ms


def _ms_to_srt(ms):
    """将毫秒转换为 SRT 时间戳 'HH:MM:SS,mmm'"""
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _ms_to_ass(ms):
    """将毫秒转换为 ASS 时间戳 'H:MM:SS.hh'"""
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    hs = (ms % 1000) // 100
    return f"{h}:{m:02d}:{s:02d}.{hs}"


# ============================================================
# 加载函数
# ============================================================

def load_srt(path):
    """加载 SRT 字幕文件"""
    entries = []
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    blocks = re.split(r"\n\s*\n", content.strip())
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        try:
            index = int(lines[0].strip())
            time_match = re.match(
                r"(.+?)\s*-->\s*(.+)", lines[1].strip()
            )
            if not time_match:
                continue
            start = time_match.group(1).strip()
            end = time_match.group(2).strip()
            text = "\n".join(lines[2:])
            entries.append({
                "index": index,
                "start": start,
                "end": end,
                "text": text,
            })
        except (ValueError, IndexError):
            continue

    return {"entries": entries}


def load_vtt(path):
    """加载 VTT 字幕文件"""
    entries = []
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    # 移除 WEBVTT 头部
    content = re.sub(r"^WEBVTT\s*.*?\n", "", content, count=1)
    content = re.sub(r"^.*?X-TIMESTAMP-MAP.*?\n", "", content, count=1)

    blocks = re.split(r"\n\s*\n", content.strip())
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        try:
            # VTT 块可能包含 cue identifier（序号行），时间戳可能在第一行或第二行
            time_match = None
            text_start = 0
            # 先尝试第一行是否为时间戳
            time_match = re.match(
                r"(.+?)\s*-->\s*(.+)", lines[0].strip()
            )
            if time_match:
                text_start = 1
            elif len(lines) >= 3:
                # 第一行不是时间戳，尝试第二行（cue identifier 情况）
                time_match = re.match(
                    r"(.+?)\s*-->\s*(.+)", lines[1].strip()
                )
                if time_match:
                    text_start = 2

            if not time_match:
                continue
            start = time_match.group(1).strip()
            end = time_match.group(2).strip()
            text = "\n".join(lines[text_start:])
            entries.append({
                "index": len(entries) + 1,
                "start": start.replace(".", ","),
                "end": end.replace(".", ","),
                "text": text,
            })
        except (ValueError, IndexError):
            continue

    return {"entries": entries}


def load_ass(path):
    """加载 ASS 字幕文件"""
    entries = []
    style_lines = []
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    # 解析 [Events] 部分
    events_match = re.search(r"\[Events\]\s*\n(.*?)(?:\[|$)", content, re.DOTALL)
    if events_match:
        events_content = events_match.group(1)
        lines = events_content.strip().split("\n")
        if not lines:
            return {"entries": entries}

        # 查找字段定义行
        format_line = None
        for i, line in enumerate(lines):
            if line.startswith("Format:"):
                format_line = [f.strip() for f in line[7:].split(",")]
                data_start = i + 1
                break
        else:
            return {"entries": entries}

        for line in lines[data_start:]:
            if not line.strip() or line.startswith("["):
                continue
            values = line.split(",", len(format_line) - 1)
            if len(values) < len(format_line):
                continue
            entry = dict(zip(format_line, [v.strip() for v in values]))
            if "Text" in entry and "Start" in entry and "End" in entry:
                entries.append({
                    "index": len(entries) + 1,
                    "start": entry["Start"].replace(".", ","),
                    "end": entry["End"].replace(".", ","),
                    "text": entry["Text"],
                })

    # 解析样式
    style_match = re.search(r"\[V4\+ Styles\]\s*\n(.*?)(?:\[|$)", content, re.DOTALL)
    if style_match:
        style_content = style_match.group(1)
        style_lines = [l for l in style_content.strip().split("\n") if l.startswith("Style:")]

    return {
        "entries": entries,
        "style": {"styles": style_lines} if style_lines else {},
    }


# ============================================================
# 导出函数
# ============================================================

def export_subtitle(subtitle_data, output_format, output_path, **kwargs):
    """
    导出字幕数据到指定格式。

    Args:
        subtitle_data: 字幕数据结构（含 entries 列表）
        output_format: 输出格式 (srt/vtt/ass/txt)
        output_path: 输出文件路径
        **kwargs: 额外参数
            - font: 字体名称（ASS/硬烧录）
            - font_size: 字体大小（ASS/硬烧录）
            - primary_color: 主颜色（ASS）
            - video_path: 视频路径（硬烧录）
    """
    exporters = {
        "srt": _export_srt,
        "vtt": _export_vtt,
        "ass": _export_ass,
        "txt": _export_txt,
    }

    exporter = exporters.get(output_format.lower())
    if not exporter:
        raise ExportError(
            f"不支持的导出格式: {output_format}，"
            f"支持的格式: {', '.join(exporters.keys())}"
        )

    try:
        output = exporter(subtitle_data, **kwargs)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(output)
    except ExportError:
        raise
    except Exception as exc:
        raise ExportError(f"导出失败: {exc}")


def _export_srt(data, **kwargs):
    """导出为 SRT 格式"""
    blocks = []
    for entry in data.get("entries", []):
        block = f"{entry['index']}\n{entry['start']} --> {entry['end']}\n{entry['text']}"
        blocks.append(block)
    return "\n\n".join(blocks) + "\n" if blocks else ""


def _export_vtt(data, **kwargs):
    """导出为 VTT 格式"""
    lines = ["WEBVTT", ""]
    for entry in data.get("entries", []):
        start = entry["start"].replace(",", ".")
        end = entry["end"].replace(",", ".")
        lines.append(f"{entry['index']}")
        lines.append(f"{start} --> {end}")
        lines.append(entry["text"])
        lines.append("")
    return "\n".join(lines)


def _export_ass(data, **kwargs):
    """导出为 ASS 格式"""
    font = kwargs.get("font", "Arial")
    font_size = kwargs.get("font_size", 24)
    primary_color = kwargs.get("primary_color", "&H00FFFFFF")

    lines = [
        "[Script Info]",
        "Title: Exported Subtitle",
        "ScriptType: v4.00+",
        "WrapStyle: 0",
        "PlayResX: 640",
        "PlayResY: 480",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{font},{font_size},{primary_color},&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    for entry in data.get("entries", []):
        start = entry["start"].replace(",", ".")
        end = entry["end"].replace(",", ".")
        text = entry["text"].replace("\n", "\\N")
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    return "\n".join(lines) + "\n"


def _export_txt(data, **kwargs):
    """导出为纯文本格式（仅字幕文本，无时间轴）"""
    texts = []
    for entry in data.get("entries", []):
        texts.append(entry["text"])
    return "\n".join(texts) + "\n" if texts else ""


# ============================================================
# 硬字幕烧录
# ============================================================

def burn_subtitles(video_path, subtitle_path, output_path, **kwargs):
    """
    将字幕硬烧录到视频中（使用 ffmpeg）。

    Args:
        video_path: 输入视频路径
        subtitle_path: 字幕文件路径
        output_path: 输出视频路径
        **kwargs: 额外参数
            - font: 字体名称
            - font_size: 字体大小
            - font_color: 字体颜色
    """
    font = kwargs.get("font", "Arial")
    font_size = kwargs.get("font_size", 24)
    font_color = kwargs.get("font_color", "white")

    # 构建 ffmpeg 字幕滤镜
    # 使用 ASS 格式以获得最佳样式支持
    subtitle_ext = Path(subtitle_path).suffix.lower()
    if subtitle_ext != ".ass":
        # 临时转换为 ASS 格式
        from video_sub.export import load_srt, load_vtt, export_subtitle
        temp_ass = tempfile.NamedTemporaryFile(suffix=".ass", delete=False).name
        loaders = {".srt": load_srt, ".vtt": load_vtt}
        loader = loaders.get(subtitle_ext)
        if loader:
            data = loader(subtitle_path)
            export_subtitle(data, "ass", temp_ass, font=font, font_size=font_size, primary_color=_color_to_ass(font_color))
            subtitle_path = temp_ass

    # 转义路径中的特殊字符（ffmpeg 要求）
    escaped_path = subtitle_path.replace("\\", "/").replace(":", "\\:").replace("'", "'\\''")

    filter_complex = f"subtitles='{escaped_path}':force_style='FontName={font},FontSize={font_size},PrimaryColour={_color_to_ass(font_color)}'"

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", filter_complex,
        "-c:a", "copy",
        "-y",
        output_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,
        )
        if result.returncode != 0:
            raise ExportError(f"ffmpeg 烧录失败: {result.stderr}")
    except FileNotFoundError:
        raise ExportError("ffmpeg 未安装或不在 PATH 中")
    except subprocess.TimeoutExpired:
        raise ExportError("ffmpeg 烧录超时")


def _color_to_ass(color):
    """将颜色名称/十六进制转换为 ASS 颜色格式"""
    color_map = {
        "white": "&H00FFFFFF",
        "black": "&H00000000",
        "red": "&H000000FF",
        "green": "&H0000FF00",
        "blue": "&H00FF0000",
        "yellow": "&H0000FFFF",
    }
    if color.lower() in color_map:
        return color_map[color.lower()]
    # 假设是十六进制 #RRGGBB
    if color.startswith("#"):
        rgb = color[1:]
        return f"&H00{rgb[4:6]}{rgb[2:4]}{rgb[0:2]}"
    return "&H00FFFFFF"
