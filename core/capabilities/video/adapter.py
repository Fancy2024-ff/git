"""video.process adapter —— 轻视频能力入口（当前 stub）。

仅轻量入口（摘要/封面/元数据），不做重型本地剪辑。
"""

from __future__ import annotations

from capabilities.base import BaseAdapter
from capabilities.video.providers.stub import VideoStubProvider


class VideoAdapter(BaseAdapter):
    capability_name = "video.process"
    display_name = "轻视频处理"
    supported_operations = ["summarize", "cover_generate", "metadata_extract"]

    def __init__(self, provider=None):
        super().__init__(provider or VideoStubProvider())

    def _notes(self) -> str:
        return "仅轻量入口；配置 VIDEO_API_KEY 接入视频 provider 后 runtime_ready。"
