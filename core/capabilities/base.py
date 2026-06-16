"""能力适配统一接口。

把"文本/图像/OCR/语音/视频/工具"抽象成统一 adapter，供应商可替换。
没有真实 provider 时，adapter 返回 configured=False 的诚实状态，绝不假成功。
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class CapabilityResult:
    """能力调用结果。ok=False 且 configured=False 表示"未接入"，不是"失败"。"""
    capability_id: str
    operation: str
    ok: bool
    configured: bool
    data: dict = field(default_factory=dict)
    error: str = ""
    provider: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CapabilitySpec:
    """能力在注册表里的元信息。"""
    capability_id: str          # e.g. "text.generate", "image.process"
    name_cn: str
    provider: str               # 当前供应商名；"stub" = 未接真实
    configured: bool            # 是否已配置可真实调用
    supported_operations: list[str]
    automation_level: str       # full_automatic / semi_automatic / manual
    config_requirements: list[str]   # 缺哪些 env/配置
    status: str                 # ready / provider_missing / not_implemented

    def to_dict(self) -> dict:
        return asdict(self)


class BaseAdapter:
    """所有能力 adapter 的基类。"""
    capability_id: str = ""
    name_cn: str = ""
    supported_operations: list[str] = []
    automation_level: str = "manual"

    def spec(self) -> CapabilitySpec:
        configured = self.is_configured()
        return CapabilitySpec(
            capability_id=self.capability_id,
            name_cn=self.name_cn,
            provider=self.provider_name(),
            configured=configured,
            supported_operations=list(self.supported_operations),
            automation_level=self.automation_level,
            config_requirements=self.config_requirements(),
            status="ready" if configured else self.unconfigured_status(),
        )

    # —— 子类按需覆盖 ——
    def provider_name(self) -> str:
        return "stub"

    def is_configured(self) -> bool:
        return False

    def config_requirements(self) -> list[str]:
        return []

    def unconfigured_status(self) -> str:
        return "provider_missing"

    def run(self, operation: str, **kwargs) -> CapabilityResult:
        """执行能力操作。未配置时返回 configured=False 的诚实结果。"""
        if not self.is_configured():
            return CapabilityResult(
                capability_id=self.capability_id,
                operation=operation,
                ok=False,
                configured=False,
                provider=self.provider_name(),
                error=f"{self.capability_id} 未接入 provider（缺: {', '.join(self.config_requirements()) or 'provider'}）",
            )
        return self._run(operation, **kwargs)

    def _run(self, operation: str, **kwargs) -> CapabilityResult:
        raise NotImplementedError
