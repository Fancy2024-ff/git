"""image.process adapter —— 第一条真实接入的复杂能力。

桥接 core/integrations/image_providers（真实 vendor 逻辑在那里，不在此）。
异步任务接口：create_task / poll_task / get_result，供 runtime 驱动。
本轮真接通 operation：remove_background；其余 operation 接口保留但诚实标注未接通。
未配置 provider → provider_missing，绝不假完成。
"""

from __future__ import annotations

import sys
from pathlib import Path

from capabilities.base import BaseAdapter
from capabilities.schemas import CapabilityResult
from capabilities.status import CapabilityStatus

# 让 integrations 可导入（core/ 在 path）
_CORE = Path(__file__).resolve().parents[2]
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))


def _provider():
    from integrations.image_providers import get_image_provider
    return get_image_provider()


class ImageAdapter(BaseAdapter):
    capability_name = "image.process"
    display_name = "图像处理"
    supported_operations = ["remove_background", "id_photo", "avatar_style", "enhance"]

    def __init__(self, provider=None):
        # provider 延迟解析：injected 优先，否则每次按 env 实时选择（便于测试/运行时切换）
        self._injected = provider
        super().__init__(_AdapterProviderBridge(self._get_provider))

    @property
    def _provider(self):
        return self._injected or _provider()

    def _get_provider(self):
        return self._provider

    # 本轮真接通的 operation（由 integrations provider 声明）
    def truly_connected_operations(self) -> list[str]:
        return [op for op in self.supported_operations
                if op in getattr(self._provider, "supported_operations", [])]

    def _notes(self) -> str:
        if not self.configured:
            return "图像能力未接入 provider：配置 IMAGE_API_BASE+IMAGE_API_KEY 或 IMAGE_PROVIDER=mock。"
        return f"已接入 provider={self._provider.name}；真接通 operation: {self.truly_connected_operations()}"

    # —— 异步任务接口（runtime 调用）——

    def create_task(self, operation: str, image_ref: str, **params) -> CapabilityResult:
        if operation not in self.supported_operations:
            return self._fail(operation, "unsupported_operation", f"不支持的操作: {operation}")
        if not self.configured:
            return self._fail(operation, "provider_missing",
                              f"图像能力未接入 provider（缺: {', '.join(self.validate_config()) or 'provider'}）",
                              data={"task_id": None})
        if operation not in self.truly_connected_operations():
            return self._fail(operation, "provider_unsupported",
                              f"operation {operation} 接口已就位但当前 provider 未接通（本轮仅 remove_background）",
                              data={"task_id": None})
        from integrations.image_providers import ImageProviderError
        try:
            t = self._provider.create_task(operation, image_ref, **params)
        except ImageProviderError as e:
            return self._fail(operation, e.code, e.message, data={"task_id": None})
        return CapabilityResult(
            capability_id=self.capability_name, operation=operation, success=True,
            status=CapabilityStatus.CONFIGURED, provider=self._provider.name,
            data={"task_id": t.provider_task_id, "status": t.status},
        )

    def poll_task(self, provider_task_id: str) -> CapabilityResult:
        if not self.configured:
            return self._fail("poll", "provider_missing", "图像能力未接入 provider",
                              data={"task_id": provider_task_id, "status": "unconfigured"})
        from integrations.image_providers import ImageProviderError
        try:
            t = self._provider.poll_task(provider_task_id)
        except ImageProviderError as e:
            return self._fail("poll", e.code, e.message, data={"task_id": provider_task_id})
        return CapabilityResult(
            capability_id=self.capability_name, operation="poll", success=True,
            status=CapabilityStatus.CONFIGURED, provider=self._provider.name,
            data={"task_id": provider_task_id, "status": t.status, "result_url": t.result_url},
        )

    def get_result(self, provider_task_id: str) -> CapabilityResult:
        if not self.configured:
            return self._fail("result", "provider_missing", "图像能力未接入 provider")
        from integrations.image_providers import ImageProviderError
        try:
            data = self._provider.get_result(provider_task_id)
        except ImageProviderError as e:
            return self._fail("result", e.code, e.message)
        return CapabilityResult(
            capability_id=self.capability_name, operation="result", success=True,
            status=CapabilityStatus.CONFIGURED, provider=self._provider.name,
            data={"task_id": provider_task_id, **data},
        )

    def execute(self, operation: str, **kwargs) -> CapabilityResult:
        created = self.create_task(operation, kwargs.get("image_ref", ""), **kwargs.get("params", {}))
        if not created.success:
            return created
        polled = self.poll_task(created.data["task_id"])
        if polled.success and polled.data.get("status") == "succeeded":
            return self.get_result(created.data["task_id"])
        return polled

    def _fail(self, operation: str, code: str, msg: str, data: dict | None = None) -> CapabilityResult:
        return CapabilityResult(
            capability_id=self.capability_name, operation=operation, success=False,
            status=self.status(), provider=getattr(self._provider, "name", "none"),
            message=msg, error_code=code, data=data or {},
        )


class _AdapterProviderBridge:
    """把 integrations ImageProvider 适配成 BaseAdapter 需要的 provider 协议。
    持有一个返回 live provider 的 getter，使 env 变化实时生效。"""
    is_stub = False

    def __init__(self, getter):
        self._getter = getter

    @property
    def provider_name(self) -> str:
        return self._getter().name

    def is_configured(self) -> bool:
        return self._getter().is_configured()

    def required_env(self) -> list[str]:
        return self._getter().required_env()

    def missing_requirements(self) -> list[str]:
        return self._getter().missing_env()

    def execute(self, operation: str, **kwargs):
        raise NotImplementedError  # image 走 create/poll/result，不走同步 execute
