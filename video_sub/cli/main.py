"""
video_sub CLI - 视频字幕处理命令行工具

提供统一的 CLI 入口，整合字幕识别、翻译、导出功能。
支持子命令模式：recognize / translate / export / full / config
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from video_sub import __version__
from video_sub.exceptions import VideoSubError, ConfigError, ExportError, RecognitionError, TranslationError

logger = logging.getLogger("video_sub")


# ============================================================
# 自定义异常类
# ============================================================

class CLIError(Exception):
    """CLI 运行时异常"""
    def __init__(self, message, exit_code=1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(self.message)


# ============================================================
# 配置管理
# ============================================================

DEFAULT_CONFIG_PATH = Path.home() / ".video-sub-config.yaml"

DEFAULT_CONFIG = {
    "whisper": {
        "model": "base",
    },
    "translate": {
        "backend": "openai",
        "openai_api_key": "",
        "libretranslate_url": "",
    },
    "export": {
        "default_format": "srt",
    },
}


def load_config(config_path=None):
    """加载配置文件，支持环境变量覆盖"""
    config = _deep_copy_dict(DEFAULT_CONFIG)

    # 优先使用 --config 参数指定的路径
    path = config_path or os.environ.get("VIDEO_SUB_CONFIG") or DEFAULT_CONFIG_PATH

    if path and Path(path).exists():
        try:
            config = _merge_config(config, _load_yaml(str(path)))
        except Exception as exc:
            logger.warning("配置文件加载失败 %s: %s", path, exc)

    # 环境变量覆盖（优先级最高）
    env_map = {
        "VIDEO_SUB_WHISPER_MODEL": ("whisper", "model"),
        "VIDEO_SUB_TRANSLATE_BACKEND": ("translate", "backend"),
        "VIDEO_SUB_OPENAI_API_KEY": ("translate", "openai_api_key"),
        "VIDEO_SUB_LIBRETRANSLATE_URL": ("translate", "libretranslate_url"),
        "VIDEO_SUB_EXPORT_FORMAT": ("export", "default_format"),
    }
    for env_key, config_keys in env_map.items():
        val = os.environ.get(env_key)
        if val is not None:
            _set_nested(config, config_keys, val)

    return config


def _load_yaml(path):
    """简易 YAML 加载器（不依赖 pyyaml，支持基础格式）"""
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except ImportError:
        return _parse_simple_yaml(path)


def _parse_simple_yaml(path):
    """极简 YAML 解析器，支持两层嵌套键值对"""
    result = {}
    current_section = None
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.rstrip()
            if not stripped or stripped.startswith("#"):
                continue
            if not line.startswith(" ") and stripped.endswith(":"):
                current_section = stripped[:-1].strip()
                result[current_section] = {}
            elif current_section and ":" in stripped:
                key, _, value = stripped.partition(":")
                result[current_section][key.strip()] = value.strip()
    return result


def save_config(config, config_path=None):
    """保存配置到文件"""
    path = Path(config_path or DEFAULT_CONFIG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import yaml
        with open(path, "w", encoding="utf-8") as fh:
            yaml.dump(config, fh, default_flow_style=False, allow_unicode=True)
    except ImportError:
        _save_simple_yaml(config, str(path))
    logger.info("配置已保存到 %s", path)


def _save_simple_yaml(config, path):
    """简易 YAML 写入"""
    lines = []
    for section, values in config.items():
        lines.append(f"{section}:")
        if isinstance(values, dict):
            for k, v in values.items():
                lines.append(f"  {k}: {v}")
        else:
            lines.append(f"  {values}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def _deep_copy_dict(d):
    """深拷贝字典"""
    return {k: _deep_copy_dict(v) if isinstance(v, dict) else v for k, v in d.items()}


def _merge_config(base, override):
    """深度合并配置字典"""
    result = _deep_copy_dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    return result


def _set_nested(d, keys, value):
    """设置嵌套字典值"""
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


# ============================================================
# 子命令处理器
# ============================================================

def handle_recognize(args):
    """处理 recognize 子命令：从视频中识别字幕"""
    video_path = Path(args.video_path)
    if not video_path.exists():
        raise CLIError(f"视频文件不存在: {video_path}")

    config = load_config(args.config)
    model = config.get("whisper", {}).get("model", "base")

    logger.info("开始识别字幕: %s (模型: %s)", video_path, model)
    print(f"正在识别视频字幕: {video_path}")
    print(f"使用模型: {model}")

    try:
        from video_sub.recognition import recognize_video
        subtitle_data = recognize_video(str(video_path), model=model)
        output_path = args.output or str(video_path.with_suffix(".srt"))
        _save_subtitle(subtitle_data, output_path, "srt")
        print(f"字幕已保存到: {output_path}")
        return subtitle_data
    except ImportError:
        print("字幕识别模块尚未安装，请安装 video_sub.recognition 后重试")
        raise CLIError("识别模块不可用", exit_code=2)
    except RecognitionError as exc:
        raise CLIError(f"识别失败: {exc}")


def handle_translate(args):
    """处理 translate 子命令：翻译字幕文件"""
    subtitle_path = Path(args.subtitle_path)
    if not subtitle_path.exists():
        raise CLIError(f"字幕文件不存在: {subtitle_path}")

    config = load_config(args.config)
    backend = config.get("translate", {}).get("backend", "openai")
    target_lang = args.lang or "zh"

    logger.info("开始翻译字幕: %s -> %s (后端: %s)", subtitle_path, target_lang, backend)
    print(f"正在翻译字幕: {subtitle_path} -> {target_lang}")
    print(f"翻译后端: {backend}")

    try:
        from video_sub.translation import translate_subtitle
        subtitle_data = _load_subtitle(str(subtitle_path))
        translated = translate_subtitle(subtitle_data, target_lang, backend=backend)
        output_path = args.output or str(subtitle_path.with_suffix(f".{target_lang}.srt"))
        _save_subtitle(translated, output_path, "srt")
        print(f"翻译完成，已保存到: {output_path}")
        return translated
    except ImportError:
        print("翻译模块尚未安装，请安装 video_sub.translation 后重试")
        raise CLIError("翻译模块不可用", exit_code=2)
    except TranslationError as exc:
        raise CLIError(f"翻译失败: {exc}")


def handle_export(args):
    """处理 export 子命令：导出字幕为指定格式"""
    subtitle_path = Path(args.subtitle_path)
    if not subtitle_path.exists():
        raise CLIError(f"字幕文件不存在: {subtitle_path}")

    output_format = args.format or "srt"
    supported_formats = ("srt", "vtt", "ass", "txt")
    if output_format not in supported_formats:
        raise CLIError(
            f"不支持的导出格式: {output_format}，"
            f"支持的格式: {', '.join(supported_formats)}"
        )

    logger.info("导出字幕: %s -> %s", subtitle_path, output_format)
    print(f"正在导出字幕: {subtitle_path} -> {output_format}")

    try:
        from video_sub.export import export_subtitle
        subtitle_data = _load_subtitle(str(subtitle_path))
        output_path = args.output or str(subtitle_path.with_suffix(f".{output_format}"))
        export_subtitle(subtitle_data, output_format, output_path)
        print(f"导出完成，已保存到: {output_path}")
    except ImportError:
        print("导出模块尚未安装，请安装 video_sub.export 后重试")
        raise CLIError("导出模块不可用", exit_code=2)
    except ExportError as exc:
        raise CLIError(f"导出失败: {exc}")


def handle_full(args):
    """处理 full 子命令：一键完成识别+翻译+导出"""
    video_path = Path(args.video_path)
    if not video_path.exists():
        raise CLIError(f"视频文件不存在: {video_path}")

    target_lang = args.lang or "zh"
    output_format = args.format or "srt"

    logger.info("开始完整流程: %s -> %s (%s)", video_path, target_lang, output_format)
    print(f"开始完整处理流程: {video_path}")
    print(f"目标语言: {target_lang}")
    print(f"输出格式: {output_format}")

    try:
        # 步骤 1: 识别
        print("\n[1/3] 识别字幕...")
        from video_sub.recognition import recognize_video
        config = load_config(args.config)
        model = config.get("whisper", {}).get("model", "base")
        subtitle_data = recognize_video(str(video_path), model=model)
        print("  识别完成")

        # 步骤 2: 翻译
        print(f"\n[2/3] 翻译字幕 -> {target_lang}...")
        from video_sub.translation import translate_subtitle
        backend = config.get("translate", {}).get("backend", "openai")
        translated = translate_subtitle(subtitle_data, target_lang, backend=backend)
        print("  翻译完成")

        # 步骤 3: 导出
        print(f"\n[3/3] 导出字幕 ({output_format})...")
        from video_sub.export import export_subtitle
        output_path = args.output or str(video_path.with_suffix(f".{target_lang}.{output_format}"))
        export_subtitle(translated, output_format, output_path)
        print(f"  导出完成，已保存到: {output_path}")

        print(f"\n处理完成！输出文件: {output_path}")
    except ImportError as exc:
        print(f"缺少必要模块: {exc}")
        raise CLIError("模块不可用，请确保已安装所有依赖", exit_code=2)
    except (RecognitionError, TranslationError, ExportError) as exc:
        raise CLIError(f"处理失败: {exc}")


def handle_config(args):
    """处理 config 子命令：查看/设置配置"""
    config = load_config(args.config)

    action = args.config_action or "show"

    if action == "show":
        _print_config(config)
    elif action == "get":
        key = args.key
        value = _get_config_value(config, key)
        if value is None:
            print(f"配置项不存在: {key}")
            raise CLIError("", exit_code=1)
        print(value)
    elif action == "set":
        key = args.key
        value = args.value
        _set_config_value(config, key, value)
        save_config(config, args.config)
        print(f"已设置 {key} = {value}")
    elif action == "reset":
        save_config(DEFAULT_CONFIG, args.config)
        print("配置已重置为默认值")
    else:
        raise CLIError(f"未知的配置操作: {action}")


def _print_config(config):
    """打印配置信息"""
    print("当前配置:")
    print("-" * 40)
    for section, values in config.items():
        if isinstance(values, dict):
            print(f"[{section}]")
            for k, v in values.items():
                # 敏感信息脱敏
                if "key" in k.lower() or "secret" in k.lower():
                    display = "****" if v else "(未设置)"
                else:
                    display = v
                print(f"  {k}: {display}")
        else:
            print(f"  {section}: {values}")
    print("-" * 40)


def _get_config_value(config, key):
    """获取配置值（支持点号分隔）"""
    keys = key.split(".")
    current = config
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return None
    return current


def _set_config_value(config, key, value):
    """设置配置值（支持点号分隔）"""
    keys = key.split(".")
    current = config
    for k in keys[:-1]:
        current = current.setdefault(k, {})
    current[keys[-1]] = value


# ============================================================
# 字幕数据加载/保存辅助函数
# ============================================================

def _load_subtitle(path):
    """加载字幕文件，返回结构化数据"""
    from video_sub.export import load_srt, load_vtt, load_ass
    suffix = Path(path).suffix.lower()
    loaders = {
        ".srt": load_srt,
        ".vtt": load_vtt,
        ".ass": load_ass,
    }
    loader = loaders.get(suffix)
    if not loader:
        raise CLIError(f"不支持的字幕格式: {suffix}")
    return loader(path)


def _save_subtitle(subtitle_data, path, fmt):
    """保存字幕数据到文件"""
    from video_sub.export import export_subtitle
    export_subtitle(subtitle_data, fmt, path)


# ============================================================
# 日志配置
# ============================================================

def setup_logging(verbose=False, log_level="INFO"):
    """配置日志输出"""
    if verbose:
        level = logging.DEBUG
    else:
        level = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)


# ============================================================
# 参数解析器构建
# ============================================================

def build_parser():
    """构建完整的 argparse 解析器"""
    parser = argparse.ArgumentParser(
        prog="video-sub",
        description="视频字幕处理工具 - 支持字幕识别、翻译、导出",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  video-sub recognize video.mp4
  video-sub translate subtitle.srt --lang zh
  video-sub export subtitle.srt --format vtt
  video-sub full video.mp4 --lang zh --format srt
  video-sub config show
        """,
    )

    # 全局选项
    parser.add_argument(
        "--version", action="version",
        version=f"video-sub {__version__}",
        help="显示版本信息",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", default=False,
        help="输出详细日志",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别 (默认: INFO)",
    )
    parser.add_argument(
        "--config", "-c", default=None,
        help="配置文件路径 (默认: ~/.video-sub-config.yaml)",
    )

    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # --- recognize ---
    p_recognize = subparsers.add_parser(
        "recognize",
        help="从视频中识别字幕（使用 Whisper）",
        description="识别视频中的语音并生成字幕文件",
    )
    p_recognize.add_argument("video_path", help="视频文件路径")
    p_recognize.add_argument(
        "--output", "-o", default=None,
        help="输出字幕文件路径",
    )
    p_recognize.add_argument(
        "--model", default=None,
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper 模型名称",
    )

    # --- translate ---
    p_translate = subparsers.add_parser(
        "translate",
        help="翻译字幕文件",
        description="将字幕文件翻译为目标语言",
    )
    p_translate.add_argument("subtitle_path", help="字幕文件路径")
    p_translate.add_argument(
        "--lang", "-l", default="zh",
        help="目标语言代码 (默认: zh)",
    )
    p_translate.add_argument(
        "--output", "-o", default=None,
        help="输出字幕文件路径",
    )
    p_translate.add_argument(
        "--backend", default=None,
        choices=["openai", "libretranslate"],
        help="翻译后端",
    )

    # --- export ---
    p_export = subparsers.add_parser(
        "export",
        help="导出字幕为指定格式",
        description="将字幕文件转换为 SRT/VTT/ASS/TXT 格式",
    )
    p_export.add_argument("subtitle_path", help="字幕文件路径")
    p_export.add_argument(
        "--format", "-f", default="srt",
        choices=["srt", "vtt", "ass", "txt"],
        help="输出格式 (默认: srt)",
    )
    p_export.add_argument(
        "--output", "-o", default=None,
        help="输出文件路径",
    )

    # --- full ---
    p_full = subparsers.add_parser(
        "full",
        help="一键完成识别+翻译+导出",
        description="从视频到最终字幕的一键处理流程",
    )
    p_full.add_argument("video_path", help="视频文件路径")
    p_full.add_argument(
        "--lang", "-l", default="zh",
        help="目标语言 (默认: zh)",
    )
    p_full.add_argument(
        "--format", "-f", default="srt",
        choices=["srt", "vtt", "ass", "txt"],
        help="输出格式 (默认: srt)",
    )
    p_full.add_argument(
        "--output", "-o", default=None,
        help="输出文件路径",
    )

    # --- config ---
    p_config = subparsers.add_parser(
        "config",
        help="查看或修改配置",
        description="管理 video-sub 的全局配置",
    )
    p_config.add_argument(
        "config_action", nargs="?", default="show",
        choices=["show", "get", "set", "reset"],
        help="配置操作: show(查看) / get(获取) / set(设置) / reset(重置)",
    )
    p_config.add_argument("key", nargs="?", default=None, help="配置键 (点号分隔)")
    p_config.add_argument("value", nargs="?", default=None, help="配置值 (仅 set 操作)")

    return parser


# ============================================================
# 主入口
# ============================================================

def main(argv=None):
    """CLI 主入口"""
    parser = build_parser()
    args = parser.parse_args(argv)

    # 配置日志
    setup_logging(verbose=args.verbose, log_level=args.log_level)

    # 无命令时显示帮助
    if not args.command:
        parser.print_help()
        return 0

    # 命令分发
    handlers = {
        "recognize": handle_recognize,
        "translate": handle_translate,
        "export": handle_export,
        "full": handle_full,
        "config": handle_config,
    }

    handler = handlers.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    try:
        handler(args)
        return 0
    except CLIError as exc:
        if exc.message:
            print(f"错误: {exc.message}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        print("\n操作已取消", file=sys.stderr)
        return 130
    except Exception as exc:
        logger.exception("未预期的错误")
        print(f"发生未预期的错误: {exc}", file=sys.stderr)
        print("请使用 --verbose 查看详细日志", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
