"""能力状态统一表达（单一事实源）。

所有 adapter / registry / snapshot 都用这里的常量，不允许各自造一套字符串。
上层（pipeline/readiness）再把 capability 级状态映射到全局 runnable_level。
"""

from __future__ import annotations


class CapabilityStatus:
    """单个能力（adapter/provider）的状态。"""
    CONFIGURED = "configured"            # 已配置且可真实调用
    PROVIDER_MISSING = "provider_missing"  # 需要外部 provider，但未配置
    STUB = "stub"                        # 仅占位实现（接口就位，无真实逻辑）
    RUNTIME_READY = "runtime_ready"      # 可真实运行（本地能力或已配置 provider）
    DEGRADED = "degraded"                # 部分可用 / 降级运行

    ALL = (CONFIGURED, PROVIDER_MISSING, STUB, RUNTIME_READY, DEGRADED)


class RunnableLevel:
    """全局运行等级（上层依据 capability 状态汇总得到）。

    capabilities 层不直接负责 upload/review，但提供 runtime 基础，
    供 pipeline/readiness 映射到这五档。
    """
    SHELL_ONLY = "shell_only"
    BUILDABLE = "buildable"
    RUNTIME_READY = "runtime_ready"
    UPLOAD_READY = "upload_ready"
    REVIEW_READY = "review_ready"

    ALL = (SHELL_ONLY, BUILDABLE, RUNTIME_READY, UPLOAD_READY, REVIEW_READY)


def is_usable(status: str) -> bool:
    """该状态是否表示能力当前可真实使用。"""
    return status in (CapabilityStatus.CONFIGURED, CapabilityStatus.RUNTIME_READY)


def derive_runnable_level(required: list[str], configured: list[str], missing: list[str]) -> str:
    """由所需/已配置/缺失能力，推导基础 runnable_level。

    - 无所需能力：buildable（骨架可构建）
    - 全部就位：runtime_ready
    - 部分就位：degraded → 仍属 buildable（运行能力不完整，但可构建可提交）
    - 全部缺失：buildable（空壳可上架，能力未接入）
    上层若再叠加平台授权/审核，可继续升到 upload_ready / review_ready。
    """
    if not required:
        return RunnableLevel.BUILDABLE
    if not missing:
        return RunnableLevel.RUNTIME_READY
    return RunnableLevel.BUILDABLE
