"""能力注册表：集中管理所有 capability adapter，提供查询与快照。"""

from __future__ import annotations

from capabilities.text_adapter import TextAdapter
from capabilities.image_adapter import ImageAdapter
from capabilities.stub_adapters import (
    VisionAdapter, SpeechAdapter, VideoAdapter, UtilityAdapter,
)

# capability_id → adapter 实例
_ADAPTERS = {
    "text.generate": TextAdapter(),
    "image.process": ImageAdapter(),
    "vision.ocr": VisionAdapter(),
    "speech.tts": SpeechAdapter(),
    "video.process": VideoAdapter(),
    "utility.execute": UtilityAdapter(),
}


def get_adapter(capability_id: str):
    return _ADAPTERS.get(capability_id)


def is_configured(capability_id: str) -> bool:
    a = _ADAPTERS.get(capability_id)
    return bool(a and a.is_configured())


def capability_status(capability_id: str) -> dict:
    """单个能力的状态（给前端/artifact 用）。未知 id 返回 not_implemented。"""
    a = _ADAPTERS.get(capability_id)
    if not a:
        return {
            "capability_id": capability_id, "name_cn": capability_id,
            "provider": "none", "configured": False,
            "supported_operations": [], "automation_level": "manual",
            "config_requirements": [], "status": "not_implemented",
        }
    return a.spec().to_dict()


def snapshot() -> dict:
    """全量能力快照 → capability-registry-snapshot.json。"""
    caps = [a.spec().to_dict() for a in _ADAPTERS.values()]
    return {
        "capabilities": caps,
        "configured_count": sum(1 for c in caps if c["configured"]),
        "total_count": len(caps),
    }


def split_configured(required: list[str]) -> tuple[list[str], list[str]]:
    """把所需能力分成 (已配置, 未配置)。"""
    configured, missing = [], []
    for cap in required:
        (configured if is_configured(cap) else missing).append(cap)
    return configured, missing
