"""字幕识别模块"""

from video_sub.exceptions import RecognitionError


def recognize_video(video_path, model="base"):
    """识别视频中的语音并返回字幕数据"""
    raise RecognitionError(
        f"识别模块尚未实现: video_path={video_path}, model={model}"
    )
