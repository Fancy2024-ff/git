"""Mock image provider：与 HTTP provider 完全相同的接口与任务生命周期。

用途：CI 测试 + 本地演示 app_runtime.runnable=true，无需真实 vendor。
启用：IMAGE_PROVIDER=mock（无需 IMAGE_API_KEY/BASE）。
注意：这是"真实可执行的确定性 provider"，不是假成功——它走完整 create→poll→succeeded
生命周期并返回确定的 result_url，代码路径与 http_provider 一致。
"""

from __future__ import annotations

import os
import uuid

from integrations.image_providers.base import ImageProvider, ProviderTask
from integrations.image_providers.errors import ImageProviderError, ImageErrorCode

# 进程内任务表（mock 用）
_TASKS: dict[str, dict] = {}


class MockImageProvider(ImageProvider):
    name = "mock"
    supported_operations = ["remove_background"]

    def is_configured(self) -> bool:
        # 显式选 mock 即视为已配置（用于演示/CI）
        return os.getenv("IMAGE_PROVIDER", "").lower() == "mock"

    def required_env(self) -> list[str]:
        return ["IMAGE_PROVIDER=mock"]

    def missing_env(self) -> list[str]:
        return [] if self.is_configured() else ["IMAGE_PROVIDER=mock"]

    def create_task(self, operation: str, image_ref: str, **params) -> ProviderTask:
        if not self.is_configured():
            raise ImageProviderError(ImageErrorCode.PROVIDER_MISSING)
        if operation not in self.supported_operations:
            raise ImageProviderError(ImageErrorCode.UNSUPPORTED, f"mock 暂不支持 {operation}")
        tid = f"mock_{uuid.uuid4().hex[:10]}"
        # mock：一次轮询即完成（确定性），result_url 指向占位结果
        _TASKS[tid] = {"status": "succeeded", "operation": operation,
                       "result_url": f"mock://image-result/{operation}/{tid}.png",
                       "source": image_ref}
        return ProviderTask(provider_task_id=tid, status="processing", raw=_TASKS[tid])

    def poll_task(self, provider_task_id: str) -> ProviderTask:
        t = _TASKS.get(provider_task_id)
        if not t:
            raise ImageProviderError(ImageErrorCode.INVALID_REQUEST, "unknown task")
        return ProviderTask(provider_task_id=provider_task_id, status=t["status"],
                            result_url=t["result_url"], raw=t)

    def get_result(self, provider_task_id: str) -> dict:
        t = _TASKS.get(provider_task_id)
        if not t:
            raise ImageProviderError(ImageErrorCode.INVALID_REQUEST, "unknown task")
        if t["status"] != "succeeded":
            raise ImageProviderError(ImageErrorCode.RESULT_NOT_READY)
        return {"result_url": t["result_url"], "raw": t}
