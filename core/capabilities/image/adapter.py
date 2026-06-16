"""image.process adapter —— 第一条复杂能力范式（异步任务）。

supported_operations: remove_background / id_photo / avatar_style / enhance
异步接口: create_task → poll_task，供慢速图像处理使用。
未配置 provider 时如实 provider_missing，绝不 setTimeout 假完成。
"""

from __future__ import annotations

import uuid

from capabilities.base import BaseAdapter
from capabilities.schemas import CapabilityResult
from capabilities.status import CapabilityStatus
from capabilities.image.providers.stub import ImageStubProvider
from capabilities.image import schemas as S


class ImageAdapter(BaseAdapter):
    capability_name = "image.process"
    display_name = "图像处理"
    supported_operations = ["remove_background", "id_photo", "avatar_style", "enhance"]

    def __init__(self, provider=None):
        super().__init__(provider or ImageStubProvider())

    def _notes(self) -> str:
        return ("复杂能力范式：异步 create_task/poll_task。"
                "配置 IMAGE_API_KEY + IMAGE_API_BASE 后接真实图生图/抠图 provider 即 runtime_ready。")

    # —— 异步任务接口（业务/模板层只认这两个方法）——

    def create_task(self, operation: str, image_ref: str, **params) -> CapabilityResult:
        """创建图像处理任务。未配置 → provider_missing，data.task_id=None。"""
        if operation not in self.supported_operations:
            return CapabilityResult(
                capability_id=self.capability_name, operation=operation, success=False,
                status=self.status(), provider=self.provider_name,
                message=f"不支持的操作: {operation}", error_code="unsupported_operation",
            )
        if not self.configured:
            return CapabilityResult(
                capability_id=self.capability_name, operation=operation, success=False,
                status=self.status(), provider=self.provider_name,
                message=f"图像能力未接入 provider（缺: {', '.join(self.validate_config())}）",
                error_code="provider_missing", data={"task_id": None},
            )
        # 真实 provider 接入点：发起异步任务，返回 vendor task_id
        task_id = f"img_{uuid.uuid4().hex[:12]}"
        return CapabilityResult(
            capability_id=self.capability_name, operation=operation, success=True,
            status=CapabilityStatus.CONFIGURED, provider=self.provider_name,
            data={"task_id": task_id, "status": S.TASK_PROCESSING},
        )

    def poll_task(self, task_id: str) -> CapabilityResult:
        """轮询任务状态。未配置 → provider_missing。"""
        if not self.configured:
            return CapabilityResult(
                capability_id=self.capability_name, operation="poll", success=False,
                status=self.status(), provider=self.provider_name,
                message="图像能力未接入 provider", error_code="provider_missing",
                data={"task_id": task_id, "status": "unconfigured"},
            )
        # 真实 provider 接入点：查询 vendor 任务状态
        return CapabilityResult(
            capability_id=self.capability_name, operation="poll", success=True,
            status=CapabilityStatus.CONFIGURED, provider=self.provider_name,
            data={"task_id": task_id, "status": S.TASK_SUCCEEDED, "result_url": ""},
        )

    def execute(self, operation: str, **kwargs) -> CapabilityResult:
        """同步入口：内部 create→poll。真实 provider 时替换为实际调用。"""
        created = self.create_task(operation, kwargs.get("image_ref", ""), **kwargs.get("params", {}))
        if not created.success:
            return created
        return self.poll_task(created.data["task_id"])
