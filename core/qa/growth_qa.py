"""core.qa.growth_qa — 增长/裂变交付质量验证。

职责：
  1. 增长产物齐全（growth-plan.md / share-strategy.md / viral-score.json）；
  2. growth/share 文档含必要裂变要素（分享钩子、激励、裂变回环、去水印）；
  3. 生成的小程序代码本身含传播链路：分享 CTA、解锁/裂变机制、品牌露出位。
规则版 v1。
"""

from __future__ import annotations

from pathlib import Path

# 生成代码中传播链路信号（命中即视为该传播位已预留）
_SHARE_CTA = ["分享", "share", "转发", "晒"]
_UNLOCK_HOOK = ["解锁", "unlock", "邀请", "invite", "去水印", "watermark", "高清"]
_RESULT_PAGE = ["result", "gallery", "pack", "clip", "greeting", "preview", "结果", "作品"]


def _scan_generated(miniapp_dir: Path, words: list[str]) -> bool:
    """扫描生成项目的页面（目录名 + 源码），命中任一关键词即返回 True。"""
    pages = miniapp_dir / "src" / "pages"
    if not pages.exists():
        return False
    lowered = [w.lower() for w in words]
    for vue in pages.rglob("*.vue"):
        # 页面路由名本身也是信号（如 pages/result/result.vue 即结果页）
        haystack = vue.parent.name.lower()
        try:
            haystack += " " + vue.read_text(encoding="utf-8-sig").lower()
        except Exception:
            pass
        if any(w in haystack for w in lowered):
            return True
    return False


def run_growth_qa(output_dir: Path, miniapp_dir: Path | None = None) -> dict:
    """检查 growth 产物完整性、关键要素，以及生成代码的传播链路。"""
    issues: list[str] = []
    checks: dict = {}

    growth_plan = output_dir / "growth-plan.md"
    share_strategy = output_dir / "share-strategy.md"
    viral_score = output_dir / "viral-score.json"

    # 1. 产物存在性
    checks["growth_plan_exists"] = growth_plan.exists()
    checks["share_strategy_exists"] = share_strategy.exists()
    checks["viral_score_exists"] = viral_score.exists()
    if not growth_plan.exists():
        issues.append("growth-plan.md 不存在")
    if not share_strategy.exists():
        issues.append("share-strategy.md 不存在")
    if not viral_score.exists():
        issues.append("viral-score.json 不存在")

    # 2. growth-plan 关键要素
    growth_keywords_ok = True
    if growth_plan.exists():
        text = growth_plan.read_text(encoding="utf-8-sig")
        for kw in ["增长重心", "渠道", "裂变", "指标"]:
            if kw not in text:
                growth_keywords_ok = False
                issues.append(f"growth-plan.md 缺少要素: {kw}")
    else:
        growth_keywords_ok = False
    checks["growth_plan_complete"] = growth_keywords_ok

    # 3. share-strategy 关键要素（分享钩子 + 激励 + 裂变路径）
    share_keywords_ok = True
    if share_strategy.exists():
        text = share_strategy.read_text(encoding="utf-8-sig")
        for kw in ["分享钩子", "激励", "裂变", "水印"]:
            if kw not in text:
                share_keywords_ok = False
                issues.append(f"share-strategy.md 缺少要素: {kw}")
    else:
        share_keywords_ok = False
    checks["share_strategy_complete"] = share_keywords_ok

    # 4. 生成小程序代码的传播链路（分享 CTA / 解锁裂变钩子 / 可传播结果页）
    if miniapp_dir is not None:
        has_share = _scan_generated(miniapp_dir, _SHARE_CTA)
        has_unlock = _scan_generated(miniapp_dir, _UNLOCK_HOOK)
        has_result = _scan_generated(miniapp_dir, _RESULT_PAGE)
        checks["code_has_share_cta"] = has_share
        checks["code_has_unlock_hook"] = has_unlock
        checks["code_has_result_page"] = has_result
        if not has_share:
            issues.append("生成代码未发现分享 CTA（传播入口缺失）")
        if not has_unlock:
            issues.append("生成代码未发现解锁/裂变机制预留")
        if not has_result:
            issues.append("生成代码未发现可传播结果页")

    passed = all(checks.values())
    return {"passed": passed, "checks": checks, "issues": issues}

