"""能力注册表：全项目能力的单一事实源。

聚合 6 类 adapter，提供稳定的查询与快照，供 pipeline / API / artifact / 前端消费。
换 provider 不影响这里；新增能力类型才在此登记。
"""

from __future__ import annotations

from capabilities.text import TextAdapter
from capabilities.image import ImageAdapter
from capabilities.vision import VisionAdapter
from capabilities.speech import SpeechAdapter
from capabilities.video import VideoAdapter
from capabilities.utility import UtilityAdapter
from capabilities.status import CapabilityStatus, derive_runnable_level, is_usable
from capabilities import app_types as _app_types

# capability_id → adapter 实例（单例）
_ADAPTERS = {
    TextAdapter.capability_name: TextAdapter(),
    ImageAdapter.capability_name: ImageAdapter(),
    VisionAdapter.capability_name: VisionAdapter(),
    SpeechAdapter.capability_name: SpeechAdapter(),
    VideoAdapter.capability_name: VideoAdapter(),
    UtilityAdapter.capability_name: UtilityAdapter(),
}

# 别名：app_type 声明的 capability_id 可能与 adapter 主标识不同
#（如 speech.asr 复用 speech.tts adapter）
_ALIASES = {
    "speech.asr": "speech.tts",
}


def _resolve(capability_id: str):
    return _ADAPTERS.get(capability_id) or _ADAPTERS.get(_ALIASES.get(capability_id, ""))


# ── 核心查询 ──

def get_capability_registry() -> dict:
    """全部 capability_id → adapter。"""
    return dict(_ADAPTERS)


def get_adapter(capability_name: str):
    """按能力名取 adapter（兼容别名）。未知返回 None。"""
    return _resolve(capability_name)


def required_capabilities_for_app_type(app_type: str) -> list[str]:
    """由 app_type 推导所需能力（来自 app_types 单一事实源）。"""
    return _app_types.capabilities_for(app_type)


def is_configured(capability_id: str) -> bool:
    a = _resolve(capability_id)
    return bool(a and a.configured)


def capability_status(capability_id: str) -> dict:
    """单个能力状态（含别名解析）。未知 → not_implemented。"""
    a = _resolve(capability_id)
    if not a:
        return {
            "capability_id": capability_id, "display_name": capability_id,
            "provider": "none", "configured": False, "runtime_ready": False,
            "supported_operations": [], "required_env": [],
            "missing_requirements": [], "status": "not_implemented",
        }
    return a.get_spec().to_dict()


# ── 快照（给 pipeline / API / artifact / 前端）──

def build_capability_snapshot(app_type: str | None = None) -> dict:
    """构建能力快照。给定 app_type 时附带该类型的 required/configured/missing 分流。"""
    caps = [a.get_spec().to_dict() for a in _ADAPTERS.values()]
    snap = {
        "capabilities": caps,
        "configured_count": sum(1 for c in caps if c["configured"]),
        "runtime_ready_count": sum(1 for c in caps if c["runtime_ready"]),
        "total_count": len(caps),
    }
    if app_type:
        required = required_capabilities_for_app_type(app_type)
        configured, missing = split_required(required)
        snap["app_type"] = app_type
        snap["required_capabilities"] = required
        snap["configured_capabilities"] = configured
        snap["missing_capabilities"] = missing
        snap["runnable_level"] = derive_runnable_level(required, configured, missing)
    return snap


def split_required(required: list[str]) -> tuple[list[str], list[str]]:
    """把所需能力分成 (已可用, 缺失)。"""
    configured, missing = [], []
    for cap in required:
        (configured if is_configured(cap) else missing).append(cap)
    return configured, missing


# ── 向后兼容（旧消费方：runner.py / 旧测试）──

def snapshot() -> dict:
    """旧接口：全量能力快照（无 app_type）。"""
    return build_capability_snapshot()


def split_configured(required: list[str]) -> tuple[list[str], list[str]]:
    """旧接口别名。"""
    return split_required(required)


def configured_capabilities() -> list[str]:
    return [cid for cid, a in _ADAPTERS.items() if a.configured]


def missing_capabilities() -> list[str]:
    return [cid for cid, a in _ADAPTERS.items() if not a.configured]


def runtime_ready_capabilities() -> list[str]:
    return [cid for cid, a in _ADAPTERS.items() if a.runtime_ready()]


def stub_capabilities() -> list[str]:
    return [cid for cid, a in _ADAPTERS.items() if a.status() == CapabilityStatus.STUB]
