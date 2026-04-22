"""video_sub 自定义异常类"""


class VideoSubError(Exception):
    """video_sub 基础异常类"""
    pass


class ConfigError(VideoSubError):
    """配置相关异常"""
    pass


class ExportError(VideoSubError):
    """导出相关异常"""
    pass


class RecognitionError(VideoSubError):
    """字幕识别相关异常"""
    pass


class TranslationError(VideoSubError):
    """翻译相关异常"""
    pass
