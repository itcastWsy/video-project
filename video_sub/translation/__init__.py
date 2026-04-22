"""字幕翻译模块"""

from video_sub.exceptions import TranslationError


def translate_subtitle(subtitle_data, target_lang, backend="openai"):
    """翻译字幕数据到目标语言"""
    raise TranslationError(
        f"翻译模块尚未实现: target_lang={target_lang}, backend={backend}"
    )
