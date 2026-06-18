"""core.qa.compliance_qa — 合规交付质量验证。

职责：
  1. 上架合规材料齐全（隐私政策、用户协议、审核备注）；
  2. 隐私政策关键条款完整；
  3. 上架文案敏感性扫描：过度营销词 + 平台敏感描述（warning 级，不阻塞）。
平台差异的合规细则在 core/platforms；这里做通用合规闸。
规则版 v1。
"""

from __future__ import annotations

import json
from pathlib import Path

# 微信/支付宝/抖音等普遍禁止或慎用的「过度营销 / 绝对化」词
_MARKETING_WORDS = [
    "最佳", "最好", "第一", "唯一", "顶级", "国家级", "世界级", "史上最",
    "100%", "永久免费", "绝对", "包治", "秒杀全网", "独一无二", "全网最低",
]
# 平台敏感 / 易触审词（涉及金融、医疗、博彩、诱导等）
_SENSITIVE_WORDS = [
    "赌博", "博彩", "彩票", "贷款", "炒股", "诊断", "治疗", "处方",
    "整容", "代孕", "翻墙", "VPN", "私彩", "返利提现",
]


def _scan(text: str, words: list[str]) -> list[str]:
    return [w for w in words if w in text]


def run_compliance_qa(miniapp_dir: Path, output_dir: Path) -> dict:
    """检查合规材料完整性 + 上架文案敏感性。"""
    issues: list[str] = []
    warnings: list[str] = []
    checks: dict = {}

    # 1. 必备法务文档
    privacy = miniapp_dir / "docs" / "privacy-policy.md"
    agreement = miniapp_dir / "docs" / "user-agreement.md"
    checks["privacy_policy_exists"] = privacy.exists()
    checks["user_agreement_exists"] = agreement.exists()
    if not privacy.exists():
        issues.append("缺少隐私政策 docs/privacy-policy.md")
    if not agreement.exists():
        issues.append("缺少用户协议 docs/user-agreement.md")

    # 2. 隐私政策关键条款
    privacy_ok = True
    if privacy.exists():
        text = privacy.read_text(encoding="utf-8-sig")
        for kw in ["信息收集", "信息使用", "信息存储"]:
            if kw not in text:
                privacy_ok = False
                issues.append(f"隐私政策缺少条款: {kw}")
    else:
        privacy_ok = False
    checks["privacy_policy_complete"] = privacy_ok

    # 3. 上架审核备注
    review_notes = output_dir / "publish-package" / "review-notes.md"
    checks["review_notes_exists"] = review_notes.exists()
    if not review_notes.exists():
        issues.append("缺少审核备注 publish-package/review-notes.md")

    # 4. 上架文案敏感性扫描（过度营销 + 平台敏感词）。
    #    命中是 warning，不阻塞提交，但必须显式暴露给人工。
    listing = output_dir / "listing-materials.json"
    marketing_hits: list[str] = []
    sensitive_hits: list[str] = []
    if listing.exists():
        try:
            data = json.loads(listing.read_text(encoding="utf-8-sig"))
            blob = json.dumps(data, ensure_ascii=False)
        except Exception:
            blob = listing.read_text(encoding="utf-8-sig", errors="replace")
        marketing_hits = _scan(blob, _MARKETING_WORDS)
        sensitive_hits = _scan(blob, _SENSITIVE_WORDS)
    checks["no_overmarketing_words"] = not marketing_hits
    checks["no_sensitive_words"] = not sensitive_hits
    if marketing_hits:
        warnings.append(f"上架文案含过度营销/绝对化词（平台可能驳回）: {', '.join(marketing_hits)}")
    if sensitive_hits:
        warnings.append(f"上架文案含平台敏感词（需人工确认资质/措辞）: {', '.join(sensitive_hits)}")

    # passed 只取决于硬性合规闸（材料齐全 + 隐私条款）；敏感词为 warning 级。
    hard_checks = {k: v for k, v in checks.items()
                   if k not in ("no_overmarketing_words", "no_sensitive_words")}
    passed = all(hard_checks.values())
    return {"passed": passed, "checks": checks, "issues": issues, "warnings": warnings}

