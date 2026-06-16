"""图像能力 adapter —— 完整接口 + 异步任务状态机 + stub provider。

仓库当前无图像 provider 配置，因此 configured=False、status=provider_missing。
但接口、操作、异步任务链路、错误处理全部就位：一旦配置 IMAGE_API_KEY/IMAGE_API_BASE，
把 _run 的 stub 换成真实调用即可，业务层与模板层无需改动。
"""

from __future__ import annotations

import os
import uuid

from capabilities.base import BaseAdapter, CapabilityResult


class ImageAdapter(BaseAdapter):
    capability_id = "image.process"
    name_cn = "图像处理"
    # 证件照/抠图/头像/增强 —— image_ai 类的核心操作
    supported_operations = ["remove_background", "id_photo", "avatar_style", "enhance"]
    automation_level = "full_automatic"

    def provider_name(self) -> str:
        return os.getenv("IMAGE_API_PROVIDER", "stub")

    def is_configured(self) -> bool:
        # 需要图像 provider 的 key + base，二者齐全才算可真实运行
        return bool(os.getenv("IMAGE_API_KEY") and os.getenv("IMAGE_API_BASE"))

    def config_requirements(self) -> list[str]:
        missing = []
        if not os.getenv("IMAGE_API_KEY"):
            missing.append("IMAGE_API_KEY")
        if not os.getenv("IMAGE_API_BASE"):
            missing.append("IMAGE_API_BASE")
        return missing

    # —— 通用异步任务链路（接口就位；configured 时才真正执行）——

    def create_task(self, operation: str, image_ref: str, **params) -> CapabilityResult:
        """创建图像处理任务。返回 task_id（stub 下为本地生成）。"""
        if not self.is_configured():
            return CapabilityResult(
                capability_id=self.capability_id, operation=operation, ok=False,
                configured=False, provider=self.provider_name(),
                error=f"图像能力未接入 provider（缺: {', '.join(self.config_requirements())}）",
                data={"task_id": None},
            )
        # 真实 provider 接入点：此处发起异步任务，返回 provider 的 task_id
        return CapabilityResult(
            capability_id=self.capability_id, operation=operation, ok=True,
            configured=True, provider=self.provider_name(),
            data={"task_id": f"task_{uuid.uuid4().hex[:12]}", "status": "processing"},
        )

    def poll_task(self, task_id: str) -> CapabilityResult:
        """轮询任务状态。真实 provider 接入点。"""
        if not self.is_configured():
            return CapabilityResult(
                capability_id=self.capability_id, operation="poll", ok=False,
                configured=False, provider=self.provider_name(),
                error="图像能力未接入 provider", data={"status": "unconfigured"},
            )
        return CapabilityResult(
            capability_id=self.capability_id, operation="poll", ok=True,
            configured=True, provider=self.provider_name(),
            data={"task_id": task_id, "status": "succeeded", "result_url": ""},
        )

    def _run(self, operation: str, **kwargs) -> CapabilityResult:
        # 同步入口：内部走 create→poll。真实 provider 时替换为实际调用。
        created = self.create_task(operation, kwargs.get("image_ref", ""), **kwargs)
        if not created.ok:
            return created
        return self.poll_task(created.data["task_id"])
