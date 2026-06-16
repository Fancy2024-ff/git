"""image provider 统一接口。

vendor 各异（同步/异步），但都在此包装成统一的 create_task / poll_task / get_result，
对 runtime 暴露一致的任务生命周期。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class ProviderTask:
    """provider 侧任务句柄。"""
    provider_task_id: str
    status: str                       # processing / succeeded / failed
    result_url: str = ""
    error_code: str = ""
    error_message: str = ""
    raw: dict = field(default_factory=dict)


class ImageProvider:
    """image provider 基类。子类实现真实/mock 逻辑。

    本轮真接通的 operation：remove_background。
    其余 operation 由 adapter 标记 not_implemented / provider_unsupported。
    """
    name = "base"
    # provider 真实支持的 operation（adapter 据此判断 truly_connected）
    supported_operations: list[str] = []

    def is_configured(self) -> bool:
        return False

    def required_env(self) -> list[str]:
        return ["IMAGE_API_BASE", "IMAGE_API_KEY"]

    def missing_env(self) -> list[str]:
        return [k for k in self.required_env() if not os.getenv(k)]

    def create_task(self, operation: str, image_ref: str, **params) -> ProviderTask:
        raise NotImplementedError

    def poll_task(self, provider_task_id: str) -> ProviderTask:
        raise NotImplementedError

    def get_result(self, provider_task_id: str) -> dict:
        raise NotImplementedError
