"""能力 adapter 统一基类（单一事实源）。

设计：adapter = 稳定接口 + 状态表达；provider = 可替换的真实/stub 实现。
业务层只认 adapter 接口；换 provider 不改业务层。
"""

from __future__ import annotations

from capabilities.schemas import CapabilityResult, CapabilitySpec
from capabilities.status import CapabilityStatus, is_usable


class BaseProvider:
    """provider 真实实现的基类。stub provider 继承它但 configured=False。"""
    provider_name: str = "stub"

    def is_configured(self) -> bool:
        return False

    def required_env(self) -> list[str]:
        return []

    def missing_requirements(self) -> list[str]:
        """默认：未配置时整组 required_env 都算缺。"""
        if self.is_configured():
            return []
        return list(self.required_env())

    def execute(self, operation: str, **kwargs) -> dict:
        """真实 provider 覆盖此方法返回结果 data。stub 不应被调到（adapter 会拦截）。"""
        raise NotImplementedError


class BaseAdapter:
    """所有能力 adapter 的统一基类。

    子类需定义 capability_name / display_name / supported_operations，
    并在 __init__ 里绑定一个 provider 实例。
    """
    capability_name: str = ""        # e.g. "text.generate"
    display_name: str = ""
    supported_operations: list[str] = []
    # 本地能力（无需外部 provider）置 True，例如 utility
    local_capability: bool = False

    def __init__(self, provider: BaseProvider):
        self.provider = provider

    # —— 状态 ——
    @property
    def configured(self) -> bool:
        return self.local_capability or self.provider.is_configured()

    @property
    def provider_name(self) -> str:
        return self.provider.provider_name

    def runtime_ready(self) -> bool:
        return self.configured

    def status(self) -> str:
        if self.local_capability:
            return CapabilityStatus.RUNTIME_READY
        if self.provider.is_configured():
            return CapabilityStatus.CONFIGURED
        # 未配置：若 provider 声明了 required_env，说明它"可以变真实"，
        # 表达为 provider_missing（缺 key）；只有完全无 env 路径的占位才算 stub。
        if self.provider.required_env():
            return CapabilityStatus.PROVIDER_MISSING
        return CapabilityStatus.STUB

    def validate_config(self) -> list[str]:
        """返回缺失的配置项；空表示配置完整。"""
        return [] if self.local_capability else self.provider.missing_requirements()

    # —— 描述 ——
    def get_spec(self) -> CapabilitySpec:
        return CapabilitySpec(
            capability_id=self.capability_name,
            display_name=self.display_name or self.capability_name,
            configured=self.configured,
            runtime_ready=self.runtime_ready(),
            status=self.status(),
            provider_name=self.provider_name,
            supported_operations=list(self.supported_operations),
            required_env=list(self.provider.required_env()),
            missing_requirements=self.validate_config(),
            notes=self._notes(),
        )

    def get_status(self) -> dict:
        spec = self.get_spec()
        return {
            "capability_id": spec.capability_id,
            "status": spec.status,
            "configured": spec.configured,
            "runtime_ready": spec.runtime_ready,
            "provider": spec.provider_name,
            "missing_requirements": spec.missing_requirements,
        }

    def _notes(self) -> str:
        return ""

    # —— 执行入口 ——
    def execute(self, operation: str, **kwargs) -> CapabilityResult:
        """统一执行入口。未配置→provider_missing 诚实结果；操作非法→error。"""
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
                message=f"{self.capability_name} 未接入 provider（缺: {', '.join(self.validate_config()) or 'provider'}）",
                error_code="provider_missing", retryable=False,
            )
        try:
            data = self.provider.execute(operation, **kwargs)
            return CapabilityResult(
                capability_id=self.capability_name, operation=operation, success=True,
                status=CapabilityStatus.RUNTIME_READY if self.local_capability else CapabilityStatus.CONFIGURED,
                provider=self.provider_name, data=data or {},
            )
        except Exception as e:
            return CapabilityResult(
                capability_id=self.capability_name, operation=operation, success=False,
                status=CapabilityStatus.DEGRADED, provider=self.provider_name,
                message=f"{type(e).__name__}: {str(e)[:200]}", error_code="provider_error", retryable=True,
            )
