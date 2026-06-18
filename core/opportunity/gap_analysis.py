"""core.opportunity.gap_analysis — 小程序平台覆盖缺口检查。

单一事实源：缺口规则只在这里。runner 调用 check_gap（从 platform-registry 读 active 平台）。
"""

from __future__ import annotations

import json

from core.runtime.config import DATA_DIR


def check_gap(app: dict) -> dict:
    """覆盖检查：从 platform-registry 动态获取 active 平台，评估覆盖情况。"""
    downloads = app.get("downloads", 0)
    category = app.get("category", "").lower()

    # Load active platforms from registry
    registry_file = DATA_DIR / "platforms" / "platform-registry.json"
    active_platforms = []
    research_platforms = []
    if registry_file.exists():
        reg_list = json.loads(registry_file.read_text(encoding="utf-8-sig"))
        for p in reg_list:
            if p["status"] == "active":
                active_platforms.append(p)
            elif p["status"] == "research_needed":
                research_platforms.append(p)
    else:
        # Fallback if registry doesn't exist
        active_platforms = [{"id": "wechat"}, {"id": "alipay"}, {"id": "douyin"}, {"id": "telegram"}]

    # Coverage rule (local heuristic). Order matters: check the higher
    # threshold first so the 'strong' branch is reachable.
    def _coverage_level(plat_id: str) -> str:
        if plat_id == "wechat" and downloads > 10_000_000:
            return "strong"
        if plat_id == "wechat" and downloads > 5_000_000:
            return "weak"
        return "missing"

    # Product type matching
    def _fits_product(plat: dict) -> bool:
        fit_types = [t.lower() for t in plat.get("fit_product_types", [])]
        not_fit = [t.lower() for t in plat.get("not_fit_product_types", [])]
        # Check if category matches fit types
        if not fit_types:
            return True  # No restriction
        cat_map = {"productivity": "工具", "photography": "图片", "education": "教育", "utilities": "工具", "health & fitness": "本地生活"}
        mapped = cat_map.get(category, category)
        if any(mapped in t or t in mapped for t in not_fit):
            return False
        return True

    platforms_checked = []
    missing_platforms = []
    recommended = []

    for plat in active_platforms:
        plat_id = plat["id"]
        level = _coverage_level(plat_id)
        fits = _fits_product(plat)

        platforms_checked.append({
            "platform": plat_id,
            "name_cn": plat.get("name_cn", plat_id),
            "coverage_level": level,
            "product_fit": fits,
            "competitors": [],
            "evidence": [],
            "notes": "" if level == "missing" else "本地规则推断，待接入真实搜索",
        })

        if level in ("missing", "weak") and fits:
            missing_platforms.append(plat_id)
            recommended.append(plat_id)

    # Gap score
    gap_score = len(missing_platforms) / max(len(active_platforms), 1) * 100

    return {
        "app_name": app["name"],
        "platforms_checked": platforms_checked,
        "missing_platforms": missing_platforms,
        "research_platforms": [p["id"] for p in research_platforms],
        "gap_score": round(gap_score, 1),
        "gap_summary": f"{len(missing_platforms)} 个 active 平台缺失或覆盖薄弱（共检查 {len(active_platforms)} 个）",
        "recommended_platforms": recommended[:5],  # Top 5
        "opportunity_level": "高" if len(missing_platforms) >= 4 else "中" if len(missing_platforms) >= 2 else "低",
    }
