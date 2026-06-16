"""video stub provider：configured 取决于 VIDEO_API_KEY。"""

from __future__ import annotations

import os

from capabilities.base import BaseProvider


class VideoStubProvider(BaseProvider):
    is_stub = True

    @property
    def provider_name(self) -> str:
        return os.getenv("VIDEO_API_PROVIDER", "stub")

    def is_configured(self) -> bool:
        return bool(os.getenv("VIDEO_API_KEY"))

    def required_env(self) -> list[str]:
        return ["VIDEO_API_KEY"]

    def execute(self, operation: str, **kwargs) -> dict:
        raise NotImplementedError("video stub provider has no real implementation")
