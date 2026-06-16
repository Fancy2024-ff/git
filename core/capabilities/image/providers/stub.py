"""image stub provider：接口就位，无真实图像 API。

configured 取决于 IMAGE_API_KEY + IMAGE_API_BASE。两者齐全才视为可真实运行；
否则 is_stub=True，状态 provider_missing。绝不假装处理成功。
"""

from __future__ import annotations

import os

from capabilities.base import BaseProvider


class ImageStubProvider(BaseProvider):
    is_stub = True

    @property
    def provider_name(self) -> str:
        return os.getenv("IMAGE_API_PROVIDER", "stub")

    def is_configured(self) -> bool:
        return bool(os.getenv("IMAGE_API_KEY") and os.getenv("IMAGE_API_BASE"))

    def required_env(self) -> list[str]:
        return ["IMAGE_API_KEY", "IMAGE_API_BASE"]

    def execute(self, operation: str, **kwargs) -> dict:
        # 真实 provider 接入点：发起同步处理并返回 result_url。
        # stub 永远不会被 adapter 调到（未配置时 adapter 在 execute 前拦截）。
        raise NotImplementedError("image stub provider has no real implementation")
