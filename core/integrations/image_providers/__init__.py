"""image provider 选择器：按 env 选 http / mock，否则未配置。

IMAGE_PROVIDER=http（默认，需 IMAGE_API_BASE+IMAGE_API_KEY）
IMAGE_PROVIDER=mock（CI/演示，确定性 provider）
"""

from __future__ import annotations

import os

from integrations.image_providers.base import ImageProvider, ProviderTask
from integrations.image_providers.errors import ImageProviderError, ImageErrorCode
from integrations.image_providers.http_provider import HttpImageProvider
from integrations.image_providers.mock_provider import MockImageProvider

__all__ = ["ImageProvider", "ProviderTask", "ImageProviderError", "ImageErrorCode",
           "get_image_provider"]


def get_image_provider() -> ImageProvider:
    """按 env 返回当前 image provider 实例。"""
    kind = os.getenv("IMAGE_PROVIDER", "http").lower()
    if kind == "mock":
        return MockImageProvider()
    return HttpImageProvider()
