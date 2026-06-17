"""微信平台授权读取与校验。"""

from __future__ import annotations

import json
from pathlib import Path

REQUIRED_FIELDS = ["appid", "private_key_path"]


def load_auth(platform_auth_dir: Path) -> dict | None:
    """读取 data/platform-auth/wechat.json。不存在返回 None。"""
    f = Path(platform_auth_dir) / "wechat.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def validate_auth(config: dict | None) -> tuple[bool, list[str]]:
    """返回 (configured, missing_fields)。"""
    if not config:
        return False, list(REQUIRED_FIELDS)
    missing = [f for f in REQUIRED_FIELDS if not config.get(f)]
    return len(missing) == 0, missing
