"""vision stub provider：configured 取决于 VISION_API_KEY。"""

from __future__ import annotations

import os

from capabilities.base import BaseProvider


class VisionStubProvider(BaseProvider):
    is_stub = True

    @property
    def provider_name(self) -> str:
        return os.getenv("VISION_API_PROVIDER", "stub")

    def is_configured(self) -> bool:
        return bool(os.getenv("VISION_API_KEY"))

    def required_env(self) -> list[str]:
        return ["VISION_API_KEY"]

    def execute(self, operation: str, **kwargs) -> dict:
        raise NotImplementedError("vision stub provider has no real implementation")
