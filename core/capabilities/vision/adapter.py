"""vision.ocr adapter —— OCR/文档/表格识别（当前 stub）。"""

from __future__ import annotations

from capabilities.base import BaseAdapter
from capabilities.vision.providers.stub import VisionStubProvider


class VisionAdapter(BaseAdapter):
    capability_name = "vision.ocr"
    display_name = "视觉识别(OCR)"
    supported_operations = ["ocr", "document_extract", "table_extract"]

    def __init__(self, provider=None):
        super().__init__(provider or VisionStubProvider())

    def _notes(self) -> str:
        return "配置 VISION_API_KEY 接入视觉 provider 后 runtime_ready。"
