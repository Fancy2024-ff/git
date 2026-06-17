"""微信上架材料读取（复用 pipeline 产出的 listing-materials）。

平台层薄封装：从 job 产物读取微信所需的上架材料结构，供上传/提审参考。
"""

from __future__ import annotations

import json
from pathlib import Path


def load_listing_materials(job_dir: Path) -> dict | None:
    """读取 job 的 listing-materials.json（上架文案/类目/关键词等）。"""
    f = Path(job_dir) / "listing-materials.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None
