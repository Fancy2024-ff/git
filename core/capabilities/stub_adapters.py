"""OCR/语音/视频/工具能力 adapter —— 接口就位 + stub provider。

均为 stub：configured=False、status=provider_missing（或 utility 的 ready）。
架构到位，等待真实 provider 接入即可，无需改业务/模板层。
"""

from __future__ import annotations

import os

from capabilities.base import BaseAdapter, CapabilityResult


class VisionAdapter(BaseAdapter):
    capability_id = "vision.ocr"
    name_cn = "视觉识别(OCR)"
    supported_operations = ["ocr", "recognize", "extract_table"]
    automation_level = "full_automatic"

    def provider_name(self) -> str:
        return os.getenv("VISION_API_PROVIDER", "stub")

    def is_configured(self) -> bool:
        return bool(os.getenv("VISION_API_KEY"))

    def config_requirements(self) -> list[str]:
        return [] if self.is_configured() else ["VISION_API_KEY"]


class SpeechAdapter(BaseAdapter):
    capability_id = "speech.tts"
    name_cn = "语音(TTS/ASR)"
    supported_operations = ["tts", "asr"]
    automation_level = "full_automatic"

    def provider_name(self) -> str:
        return os.getenv("SPEECH_API_PROVIDER", "stub")

    def is_configured(self) -> bool:
        return bool(os.getenv("SPEECH_API_KEY"))

    def config_requirements(self) -> list[str]:
        return [] if self.is_configured() else ["SPEECH_API_KEY"]


class VideoAdapter(BaseAdapter):
    capability_id = "video.process"
    name_cn = "轻视频处理"
    supported_operations = ["summarize", "cover", "script"]
    automation_level = "semi_automatic"

    def provider_name(self) -> str:
        return os.getenv("VIDEO_API_PROVIDER", "stub")

    def is_configured(self) -> bool:
        return bool(os.getenv("VIDEO_API_KEY"))

    def config_requirements(self) -> list[str]:
        return [] if self.is_configured() else ["VIDEO_API_KEY"]


class UtilityAdapter(BaseAdapter):
    """工具类：纯本地逻辑，无需外部 provider，默认 ready。"""
    capability_id = "utility.execute"
    name_cn = "实用工具"
    supported_operations = ["calculate", "convert", "query"]
    automation_level = "full_automatic"

    def provider_name(self) -> str:
        return "local"

    def is_configured(self) -> bool:
        return True  # 本地能力，无外部依赖

    def config_requirements(self) -> list[str]:
        return []

    def _run(self, operation: str, **kwargs) -> CapabilityResult:
        # 本地工具示例：真实实现按需扩展
        return CapabilityResult(
            capability_id=self.capability_id, operation=operation, ok=True,
            configured=True, provider="local", data={"note": "本地工具逻辑，按需扩展"},
        )
