"""集成测试 - 验证各模块协同工作"""

import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path

import pytest

# 确保项目路径在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_srt_content():
    """标准 SRT 字幕内容"""
    return """1
00:00:01,000 --> 00:00:04,000
Hello world

2
00:00:05,500 --> 00:00:08,000
This is a test subtitle

3
00:00:09,000 --> 00:00:12,500
Third line of text
"""


@pytest.fixture
def sample_srt_file(temp_dir, sample_srt_content):
    """创建临时 SRT 文件"""
    path = temp_dir / "test.srt"
    path.write_text(sample_srt_content, encoding="utf-8")
    return path


@pytest.fixture
def sample_vtt_content():
    """标准 VTT 字幕内容"""
    return """WEBVTT

1
00:00:01.000 --> 00:00:04.000
Hello world

2
00:00:05.500 --> 00:00:08.000
This is a test subtitle
"""


@pytest.fixture
def sample_vtt_file(temp_dir, sample_vtt_content):
    """创建临时 VTT 文件"""
    path = temp_dir / "test.vtt"
    path.write_text(sample_vtt_content, encoding="utf-8")
    return path


@pytest.fixture
def sample_ass_content():
    """标准 ASS 字幕内容"""
    return """[Script Info]
Title: Test
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,24,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,Hello world
Dialogue: 0,0:00:05.50,0:00:08.00,Default,,0,0,0,,This is a test subtitle
"""


@pytest.fixture
def sample_ass_file(temp_dir, sample_ass_content):
    """创建临时 ASS 文件"""
    path = temp_dir / "test.ass"
    path.write_text(sample_ass_content, encoding="utf-8")
    return path


@pytest.fixture
def mock_config_file(temp_dir):
    """创建临时配置文件"""
    config_path = temp_dir / "test-config.yaml"
    config_path.write_text(
        "whisper:\n  model: base\ntranslate:\n  backend: openai\n  openai_api_key: test-key-123\nexport:\n  default_format: vtt\n",
        encoding="utf-8",
    )
    return config_path


# ============================================================
# CLI 命令测试
# ============================================================

class TestCLIHelp:
    """测试 CLI 帮助信息"""

    def test_main_help(self):
        """主帮助信息正常显示"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "--help"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "视频字幕处理工具" in result.stdout
        assert "recognize" in result.stdout
        assert "translate" in result.stdout
        assert "export" in result.stdout
        assert "full" in result.stdout
        assert "config" in result.stdout

    def test_version(self):
        """版本信息正常显示"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "--version"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "video-sub" in result.stdout
        assert "1.0.0" in result.stdout

    def test_recognize_help(self):
        """recognize 子命令帮助正常"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "recognize", "--help"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "video_path" in result.stdout

    def test_translate_help(self):
        """translate 子命令帮助正常"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "translate", "--help"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "subtitle_path" in result.stdout

    def test_export_help(self):
        """export 子命令帮助正常"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "export", "--help"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "subtitle_path" in result.stdout

    def test_full_help(self):
        """full 子命令帮助正常"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "full", "--help"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "video_path" in result.stdout

    def test_config_help(self):
        """config 子命令帮助正常"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "config", "--help"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "show" in result.stdout


class TestCLIConfig:
    """测试 config 子命令"""

    def test_config_show(self):
        """config show 正常显示"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "config", "show"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "当前配置" in result.stdout
        assert "whisper" in result.stdout
        assert "translate" in result.stdout
        assert "export" in result.stdout

    def test_config_show_with_file(self, mock_config_file):
        """config show 使用指定配置文件"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "--config", str(mock_config_file), "config", "show"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "当前配置" in result.stdout

    def test_config_get(self, mock_config_file):
        """config get 获取配置值"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "--config", str(mock_config_file), "config", "get", "whisper.model"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "base" in result.stdout

    def test_config_get_nested(self, mock_config_file):
        """config get 获取嵌套配置值"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "--config", str(mock_config_file), "config", "get", "translate.backend"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "openai" in result.stdout

    def test_config_get_nonexistent(self, mock_config_file):
        """config get 获取不存在的配置项"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "--config", str(mock_config_file), "config", "get", "nonexistent.key"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 1
        assert "不存在" in result.stdout

    def test_config_set(self, temp_dir):
        """config set 设置配置值"""
        config_path = temp_dir / "set-test.yaml"
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "--config", str(config_path), "config", "set", "whisper.model", "large"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "已设置" in result.stdout
        assert config_path.exists()

    def test_config_reset(self, temp_dir):
        """config reset 重置配置"""
        config_path = temp_dir / "reset-test.yaml"
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "--config", str(config_path), "config", "reset"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "重置" in result.stdout


class TestCLIExport:
    """测试 export 子命令"""

    def test_export_srt_to_vtt(self, sample_srt_file, temp_dir):
        """SRT → VTT 格式转换"""
        output_path = temp_dir / "output.vtt"
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "export", str(sample_srt_file), "--format", "vtt", "--output", str(output_path)],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "WEBVTT" in content

    def test_export_srt_to_ass(self, sample_srt_file, temp_dir):
        """SRT → ASS 格式转换"""
        output_path = temp_dir / "output.ass"
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "export", str(sample_srt_file), "--format", "ass", "--output", str(output_path)],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "[Script Info]" in content
        assert "[V4+ Styles]" in content

    def test_export_srt_to_txt(self, sample_srt_file, temp_dir):
        """SRT → TXT 纯文本导出"""
        output_path = temp_dir / "output.txt"
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "export", str(sample_srt_file), "--format", "txt", "--output", str(output_path)],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "Hello world" in content
        assert "00:00" not in content  # 纯文本不应有时间轴

    def test_export_srt_to_srt(self, sample_srt_file, temp_dir):
        """SRT → SRT 自身转换"""
        output_path = temp_dir / "output.srt"
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "export", str(sample_srt_file), "--format", "srt", "--output", str(output_path)],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "00:00:01,000 --> 00:00:04,000" in content

    def test_export_nonexistent_file(self, temp_dir):
        """导出不存在文件时给出错误提示"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "export", str(temp_dir / "nonexistent.srt"), "--format", "vtt"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 1
        assert "不存在" in result.stdout or "不存在" in result.stderr

    def test_export_unsupported_format(self, sample_srt_file):
        """不支持的格式给出错误提示"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "export", str(sample_srt_file), "--format", "xml"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 2


class TestCLIErrorHandling:
    """测试 CLI 错误处理"""

    def test_no_command_shows_help(self):
        """无命令时显示帮助"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "视频字幕处理工具" in result.stdout

    def test_verbose_flag(self):
        """--verbose 标志正常工作"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "--verbose", "config", "show"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "当前配置" in result.stdout

    def test_log_level_flag(self):
        """--log-level 标志正常工作"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "--log-level", "DEBUG", "config", "show"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "当前配置" in result.stdout


# ============================================================
# Export 模块单元测试
# ============================================================

class TestExportModule:
    """测试导出模块核心功能"""

    def test_load_srt(self, sample_srt_file):
        """加载 SRT 文件"""
        from video_sub.export import load_srt
        data = load_srt(str(sample_srt_file))
        assert len(data["entries"]) == 3
        assert data["entries"][0]["text"] == "Hello world"
        assert data["entries"][0]["start"] == "00:00:01,000"

    def test_load_vtt(self, sample_vtt_file):
        """加载 VTT 文件"""
        from video_sub.export import load_vtt
        data = load_vtt(str(sample_vtt_file))
        assert len(data["entries"]) == 2
        assert data["entries"][0]["text"] == "Hello world"

    def test_load_ass(self, sample_ass_file):
        """加载 ASS 文件"""
        from video_sub.export import load_ass
        data = load_ass(str(sample_ass_file))
        assert len(data["entries"]) == 2
        assert data["entries"][0]["text"] == "Hello world"

    def test_export_srt(self, sample_srt_file):
        """导出 SRT 格式"""
        from video_sub.export import load_srt, export_subtitle
        data = load_srt(str(sample_srt_file))
        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False, mode="w") as f:
            export_subtitle(data, "srt", f.name)
            content = Path(f.name).read_text(encoding="utf-8")
            assert "00:00:01,000 --> 00:00:04,000" in content
            assert "Hello world" in content

    def test_export_vtt(self, sample_srt_file):
        """导出 VTT 格式"""
        from video_sub.export import load_srt, export_subtitle
        data = load_srt(str(sample_srt_file))
        with tempfile.NamedTemporaryFile(suffix=".vtt", delete=False, mode="w") as f:
            export_subtitle(data, "vtt", f.name)
            content = Path(f.name).read_text(encoding="utf-8")
            assert "WEBVTT" in content
            assert "00:00:01.000 --> 00:00:04.000" in content

    def test_export_ass(self, sample_srt_file):
        """导出 ASS 格式"""
        from video_sub.export import load_srt, export_subtitle
        data = load_srt(str(sample_srt_file))
        with tempfile.NamedTemporaryFile(suffix=".ass", delete=False, mode="w") as f:
            export_subtitle(data, "ass", f.name, font="Arial", font_size=24)
            content = Path(f.name).read_text(encoding="utf-8")
            assert "[Script Info]" in content
            assert "[V4+ Styles]" in content
            assert "Arial" in content

    def test_export_txt(self, sample_srt_file):
        """导出 TXT 格式"""
        from video_sub.export import load_srt, export_subtitle
        data = load_srt(str(sample_srt_file))
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            export_subtitle(data, "txt", f.name)
            content = Path(f.name).read_text(encoding="utf-8")
            assert "Hello world" in content
            assert "This is a test subtitle" in content
            assert "-->" not in content  # 无时间轴

    def test_export_unsupported_format(self, sample_srt_file):
        """不支持的格式抛出异常"""
        from video_sub.export import load_srt, export_subtitle
        from video_sub.exceptions import ExportError
        data = load_srt(str(sample_srt_file))
        with pytest.raises(ExportError):
            export_subtitle(data, "xml", "/tmp/out.xml")

    def test_srt_to_vtt_conversion(self, sample_srt_file):
        """SRT → VTT 完整转换链路"""
        from video_sub.export import load_srt, export_subtitle
        data = load_srt(str(sample_srt_file))
        with tempfile.NamedTemporaryFile(suffix=".vtt", delete=False, mode="w") as f:
            export_subtitle(data, "vtt", f.name)
            # 验证 VTT 可以重新加载
            from video_sub.export import load_vtt
            reloaded = load_vtt(f.name)
            assert len(reloaded["entries"]) == 3

    def test_srt_to_ass_conversion(self, sample_srt_file):
        """SRT → ASS 完整转换链路"""
        from video_sub.export import load_srt, export_subtitle
        data = load_srt(str(sample_srt_file))
        with tempfile.NamedTemporaryFile(suffix=".ass", delete=False, mode="w") as f:
            export_subtitle(data, "ass", f.name)
            # 验证 ASS 可以重新加载
            from video_sub.export import load_ass
            reloaded = load_ass(f.name)
            assert len(reloaded["entries"]) == 3

    def test_export_utf8_encoding(self, temp_dir):
        """导出文件使用 UTF-8 编码"""
        from video_sub.export import export_subtitle
        data = {
            "entries": [
                {"index": 1, "start": "00:00:01,000", "end": "00:00:04,000", "text": "你好世界"},
                {"index": 2, "start": "00:00:05,000", "end": "00:00:08,000", "text": "こんにちは"},
            ]
        }
        output_path = temp_dir / "utf8_test.srt"
        export_subtitle(data, "srt", str(output_path))
        content = output_path.read_text(encoding="utf-8")
        assert "你好世界" in content
        assert "こんにちは" in content


# ============================================================
# Config 模块单元测试
# ============================================================

class TestConfigModule:
    """测试配置管理模块"""

    def test_load_default_config(self):
        """加载默认配置"""
        from video_sub.cli.main import load_config
        config = load_config()
        assert "whisper" in config
        assert "translate" in config
        assert "export" in config

    def test_load_config_from_file(self, mock_config_file):
        """从文件加载配置"""
        from video_sub.cli.main import load_config
        config = load_config(str(mock_config_file))
        assert config["whisper"]["model"] == "base"
        assert config["translate"]["backend"] == "openai"

    def test_env_override(self):
        """环境变量覆盖配置"""
        os.environ["VIDEO_SUB_WHISPER_MODEL"] = "large"
        try:
            from video_sub.cli.main import load_config
            config = load_config()
            assert config["whisper"]["model"] == "large"
        finally:
            del os.environ["VIDEO_SUB_WHISPER_MODEL"]

    def test_env_override_translate_backend(self):
        """环境变量覆盖翻译后端"""
        os.environ["VIDEO_SUB_TRANSLATE_BACKEND"] = "libretranslate"
        try:
            from video_sub.cli.main import load_config
            config = load_config()
            assert config["translate"]["backend"] == "libretranslate"
        finally:
            del os.environ["VIDEO_SUB_TRANSLATE_BACKEND"]

    def test_save_and_reload_config(self, temp_dir):
        """保存并重新加载配置"""
        from video_sub.cli.main import load_config, save_config
        config_path = temp_dir / "test-save.yaml"
        config = load_config()
        config["whisper"]["model"] = "large"
        save_config(config, str(config_path))
        reloaded = load_config(str(config_path))
        assert reloaded["whisper"]["model"] == "large"

    def test_config_sensitive_info_masking(self):
        """敏感信息脱敏"""
        from video_sub.cli.main import load_config, _print_config
        import io
        import sys
        config = load_config()
        config["translate"]["openai_api_key"] = "sk-secret-key-12345"
        # _print_config 输出到 stdout，验证脱敏
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            _print_config(config)
            output = sys.stdout.getvalue()
            assert "sk-secret-key" not in output
            assert "****" in output
        finally:
            sys.stdout = old_stdout


# ============================================================
# Full Pipeline 集成测试（mock 外部依赖）
# ============================================================

class TestFullPipeline:
    """测试完整处理流程（使用 mock）"""

    def test_full_pipeline_mock(self, temp_dir, monkeypatch):
        """完整流程：识别 → 翻译 → 导出"""
        # Mock recognize_video
        mock_subtitle_data = {
            "entries": [
                {"index": 1, "start": "00:00:01,000", "end": "00:00:04,000", "text": "Hello"},
                {"index": 2, "start": "00:00:05,000", "end": "00:00:08,000", "text": "World"},
            ]
        }

        # Mock translate_subtitle
        mock_translated = {
            "entries": [
                {"index": 1, "start": "00:00:01,000", "end": "00:00:04,000", "text": "你好"},
                {"index": 2, "start": "00:00:05,000", "end": "00:00:08,000", "text": "世界"},
            ]
        }

        # Mock the module functions directly (monkeypatch works in same process)
        import video_sub.recognition
        import video_sub.translation
        monkeypatch.setattr(
            video_sub.recognition, "recognize_video",
            lambda path, model: mock_subtitle_data,
        )
        monkeypatch.setattr(
            video_sub.translation, "translate_subtitle",
            lambda data, lang, backend: mock_translated,
        )

        # Create mock video file
        video_path = temp_dir / "test.mp4"
        video_path.touch()

        # Call CLI handler directly (same process, monkeypatch applies)
        from video_sub.cli.main import handle_full
        import argparse
        args = argparse.Namespace(
            video_path=str(video_path),
            lang="zh",
            format="srt",
            output=str(temp_dir / "output.srt"),
            config=None,
        )
        handle_full(args)

        output_path = temp_dir / "output.srt"
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "你好" in content
        assert "世界" in content

    def test_recognize_nonexistent_video(self, temp_dir):
        """识别不存在的视频文件"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "recognize", str(temp_dir / "nonexistent.mp4")],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 1
        assert "不存在" in result.stdout or "不存在" in result.stderr

    def test_translate_nonexistent_subtitle(self, temp_dir):
        """翻译不存在的字幕文件"""
        result = subprocess.run(
            [sys.executable, "-m", "video_sub.cli.main", "translate", str(temp_dir / "nonexistent.srt")],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 1
        assert "不存在" in result.stdout or "不存在" in result.stderr


# ============================================================
# 测试报告生成
# ============================================================

def generate_test_report(results, report_path):
    """生成测试报告"""
    total = results.get("total", 0)
    passed = results.get("passed", 0)
    failed = results.get("failed", 0)
    skipped = results.get("skipped", 0)
    errors = results.get("errors", 0)

    report_lines = [
        "=" * 60,
        "video-sub 集成测试报告",
        "=" * 60,
        "",
        f"总测试数: {total}",
        f"通过: {passed}",
        f"失败: {failed}",
        f"跳过: {skipped}",
        f"错误: {errors}",
        "",
        "-" * 60,
        "测试详情:",
        "-" * 60,
    ]

    for test_name, status in results.get("tests", []):
        icon = "✓" if status == "passed" else "✗" if status == "failed" else "○"
        report_lines.append(f"  {icon} {test_name}: {status}")

    report_lines.extend([
        "",
        "-" * 60,
        f"通过率: {passed}/{total} ({passed/total*100:.1f}%)" if total > 0 else "通过率: N/A",
        "=" * 60,
    ])

    report_content = "\n".join(report_lines) + "\n"
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(report_content, encoding="utf-8")
    return report_content
