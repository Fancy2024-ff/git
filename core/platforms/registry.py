"""平台层注册表：平台元数据的**唯一访问入口**（单一事实源）。

设计：
- 平台"实现状态"（哪些 action 真接了代码）是硬编码真相，在本文件维护。
- 平台"业务元数据"（名称/status/automation_level/submit_url/upload_target/类目…）以
  data/platforms/platform-registry.json 为 backing data（legacy 富数据），但**只能经本文件函数访问**。
- 业务层（runner/API/前端经 API）一律调本文件函数，不再直接读 data 文件 → 消灭两套真相。

后续 alipay/douyin/telegram 接入时，把 _ACTION_IMPL 对应项改为 implemented 即可。
"""

from __future__ import annotations

import json
from pathlib import Path

# core/platforms/registry.py → core → repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]
_LEGACY_REGISTRY = _REPO_ROOT / "data" / "platforms" / "platform-registry.json"

# 平台动作
ACTION_UPLOAD = "upload"
ACTION_REVIEW = "review"
ACTION_MATERIALS = "materials"

# 实现状态
IMPL_IMPLEMENTED = "implemented"
IMPL_PARTIAL = "partial"
IMPL_NOT_IMPLEMENTED = "not_implemented"

# 各平台「已接了哪些代码」—— 硬编码真相（与仓库实现一致）
_ACTION_IMPL: dict[str, dict[str, str]] = {
    "wechat": {ACTION_UPLOAD: IMPL_IMPLEMENTED, ACTION_REVIEW: IMPL_NOT_IMPLEMENTED, ACTION_MATERIALS: IMPL_PARTIAL},
    "alipay": {ACTION_UPLOAD: IMPL_NOT_IMPLEMENTED, ACTION_REVIEW: IMPL_NOT_IMPLEMENTED, ACTION_MATERIALS: IMPL_NOT_IMPLEMENTED},
    "douyin": {ACTION_UPLOAD: IMPL_NOT_IMPLEMENTED, ACTION_REVIEW: IMPL_NOT_IMPLEMENTED, ACTION_MATERIALS: IMPL_NOT_IMPLEMENTED},
    "telegram": {ACTION_UPLOAD: IMPL_NOT_IMPLEMENTED, ACTION_REVIEW: IMPL_NOT_IMPLEMENTED, ACTION_MATERIALS: IMPL_NOT_IMPLEMENTED},
}

# backing data 缓存
_BACKING: dict[str, dict] | None = None


def _load_backing() -> dict[str, dict]:
    """加载 legacy 富元数据（按 id 索引）。失败返回空 dict（不崩）。"""
    global _BACKING
    if _BACKING is not None:
        return _BACKING
    data: dict[str, dict] = {}
    if _LEGACY_REGISTRY.exists():
        try:
            for p in json.loads(_LEGACY_REGISTRY.read_text(encoding="utf-8-sig")):
                if p.get("id"):
                    data[p["id"]] = p
        except Exception:
            data = {}
    _BACKING = data
    return data


def reset_cache() -> None:
    """测试用：清缓存以便重新加载 backing。"""
    global _BACKING
    _BACKING = None


# ── 访问函数（业务层只用这些）──

def list_platforms() -> list[str]:
    """已知平台 id（backing ∪ 实现表）。"""
    ids = set(_load_backing().keys()) | set(_ACTION_IMPL.keys())
    return sorted(ids)


def get_platform(platform_id: str) -> dict:
    """平台完整元数据（backing 富字段 + 实现状态 actions）。未知返回最小占位。"""
    base = dict(_load_backing().get(platform_id, {}))
    base.setdefault("id", platform_id)
    base["actions"] = _ACTION_IMPL.get(platform_id, {
        ACTION_UPLOAD: IMPL_NOT_IMPLEMENTED, ACTION_REVIEW: IMPL_NOT_IMPLEMENTED,
        ACTION_MATERIALS: IMPL_NOT_IMPLEMENTED})
    return base


def supports_action(platform_id: str, action: str) -> bool:
    """该平台是否**已真实实现**某动作（implemented 才算）。"""
    return _ACTION_IMPL.get(platform_id, {}).get(action) == IMPL_IMPLEMENTED


def is_upload_automatable(platform_id: str) -> bool:
    """该平台能否自动上传：实现了 upload 动作 且 automation_level 非 manual。"""
    if not supports_action(platform_id, ACTION_UPLOAD):
        return False
    lvl = get_platform(platform_id).get("automation_level", "manual")
    return lvl != "manual"


def get_submit_url(platform_id: str) -> str:
    p = get_platform(platform_id)
    return p.get("submit_url") or p.get("developer_url") or ""


def get_upload_target(platform_id: str) -> str:
    return get_platform(platform_id).get("upload_target", "") or "dist/build/mp-weixin"


def get_status(platform_id: str) -> str:
    """平台支持状态：active / research_needed / not_supported / unknown。"""
    return get_platform(platform_id).get("status", "unknown")


def get_automation_level(platform_id: str) -> str:
    return get_platform(platform_id).get("automation_level", "manual")


def get_platform_display(platform_id: str) -> dict:
    """前端/报告展示用：名称等。"""
    p = get_platform(platform_id)
    return {
        "platform_id": platform_id,
        "name_cn": p.get("name_cn", platform_id),
        "name_en": p.get("name_en", platform_id),
    }


def build_platform_snapshot() -> dict:
    """平台层快照（清单 + 实现状态 + 自动化能力），供 API/前端/文档/测试消费。"""
    out = []
    for pid in list_platforms():
        p = get_platform(pid)
        out.append({
            "platform_id": pid,
            "name_cn": p.get("name_cn", pid),
            "status": p.get("status", "unknown"),
            "automation_level": p.get("automation_level", "manual"),
            "actions": p.get("actions", {}),
            "submit_url": get_submit_url(pid),
            "upload_automatable": is_upload_automatable(pid),
        })
    return {
        "platforms": out,
        "implemented_upload": [pid for pid in list_platforms() if supports_action(pid, ACTION_UPLOAD)],
        "source": "core/platforms/registry.py (backing: data/platforms/platform-registry.json legacy fallback)",
    }
