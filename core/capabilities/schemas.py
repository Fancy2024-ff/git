"""能力层统一数据结构（单一事实源）。

所有 adapter 返回 CapabilityResult；registry/快照用 CapabilitySpec。
不允许任何 adapter 自造返回格式。
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class CapabilityResult:
    """一次能力调用的统一结果。

    success=False 且 status=provider_missing/stub 表示"未接入"，不是"运行失败"。
    retryable 供上层决定是否重试（如临时网络错误）。
    """
    capability_id: str
    operation: str
    success: bool
    status: str               # CapabilityStatus.*
    provider: str
    message: str = ""
    data: dict = field(default_factory=dict)
    error_code: str = ""
    retryable: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CapabilitySpec:
    """能力在注册表/快照里的统一描述。"""
    capability_id: str            # e.g. "text.generate" / "image.process"
    display_name: str
    configured: bool
    runtime_ready: bool
    status: str                   # CapabilityStatus.*
    provider_name: str
    supported_operations: list[str]
    required_env: list[str]
    missing_requirements: list[str]
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
