"""core.opportunity.scoring — Opportunity Score（机会评分）。

单一事实源：机会评分规则只在这里。runner 调用 compute_opportunity_score，
不再内嵌评分公式。规则版 v1（可解释），后续可替换为 LLM 重算维度。
"""

from __future__ import annotations


_WEIGHTS = {"viral": 0.25, "demand": 0.22, "gap": 0.20, "fit": 0.15, "impl": 0.10, "risk": 0.08}
_COMPLEX_KW = ["camera", "ar", "video", "real-time", "3d", "hardware"]
_RISK_KW = ["health", "medical", "finance", "gambling", "dating", "children"]


def compute_opportunity_score(app: dict, analysis: dict, gap: dict, viral: dict | None = None) -> dict:
    """机会评分：Viral Score 是核心维度，综合 demand/gap/fit/impl/risk。"""
    features = app.get("features", [])
    features_cn = app.get("features_cn", [])

    # 1. 需求强度 demand_score (from analysis)
    demand_score = analysis["demand_score"]

    # 2. 小程序缺口 miniapp_gap_score (from gap check)
    miniapp_gap_score = gap["gap_score"]

    # 3. 小程序适配度 miniapp_fit_score
    fit_score = 0
    is_complex = any(kw in " ".join(features).lower() for kw in _COMPLEX_KW)
    fit_score += 0 if is_complex else 25       # 不依赖复杂原生能力
    fit_score += 25 if len(features) <= 5 else 15  # 短流程
    fit_score += 25                            # 轻工具（默认 AI 工具适合）
    fit_score += 25 if app.get("category") in ("Productivity", "Education", "Utilities") else 15  # 适合分享
    miniapp_fit_score = min(100, fit_score)

    # 4. 实现难度 implementation_score (高分=容易实现)
    page_count = min(6, len(features_cn) + 1)
    needs_payment = app.get("monetization") in ("freemium", "subscription")
    impl_score = 100
    impl_score -= page_count * 8
    impl_score -= 15 if needs_payment else 0
    impl_score -= 20 if is_complex else 0
    implementation_score = max(20, impl_score)

    # 5. 风险 risk_score (高分=低风险=好)
    risk_score = 85
    if any(kw in app.get("category", "").lower() or kw in app.get("description", "").lower() for kw in _RISK_KW):
        risk_score = 45
    if "Health" in app.get("category", ""):
        risk_score = 50

    # 6. 传播力 viral_score。正式链路从 core.opportunity.viral_score 注入；
    # 测试/兼容调用未传时，使用 analysis 中的预选传播分或中性分。
    viral_score = (
        (viral or {}).get("viral_score")
        or analysis.get("viral_score")
        or 50
    )

    total_score = round(
        viral_score * _WEIGHTS["viral"]
        + demand_score * _WEIGHTS["demand"]
        + miniapp_gap_score * _WEIGHTS["gap"]
        + miniapp_fit_score * _WEIGHTS["fit"]
        + implementation_score * _WEIGHTS["impl"]
        + risk_score * _WEIGHTS["risk"],
        1,
    )

    if total_score >= 70:
        recommendation = "立即执行"
        next_action = "进入 PRD 生成阶段"
    elif total_score >= 50:
        recommendation = "值得尝试"
        next_action = "建议进一步人工确认后执行"
    else:
        recommendation = "暂缓"
        next_action = "风险或难度过高，建议换目标"

    reasons = []
    if demand_score >= 70: reasons.append(f"需求强度高（{demand_score}）")
    if viral_score >= 72: reasons.append(f"传播力强（Viral Score {viral_score}）")
    if miniapp_gap_score >= 70: reasons.append(f"小程序缺口大（{miniapp_gap_score}）")
    if miniapp_fit_score >= 70: reasons.append(f"适配度高（{miniapp_fit_score}）")
    if implementation_score >= 60: reasons.append(f"实现难度可控（{implementation_score}）")

    reject_reasons = []
    if risk_score < 60: reject_reasons.append(f"风险偏高（{risk_score}）")
    if implementation_score < 40: reject_reasons.append(f"实现难度过大（{implementation_score}）")
    if miniapp_fit_score < 50: reject_reasons.append(f"小程序适配度低（{miniapp_fit_score}）")

    return {
        "app_name": app["name"],
        "app_name_cn": app["name_cn"],
        "viral_score": viral_score,
        "viral_weight": _WEIGHTS["viral"],
        "demand_score": demand_score,
        "demand_evidence": [
            f"下载量 {app.get('downloads', 0):,}",
            f"评分 {app.get('rating', 0)}/5",
            f"变现模式: {app.get('monetization', 'unknown')}",
        ],
        "miniapp_gap_score": miniapp_gap_score,
        "gap_evidence": [
            f"检查 {len(gap.get('platforms_checked', []))} 个平台",
            f"缺失/薄弱: {', '.join(gap.get('missing_platforms', []))}",
        ],
        "miniapp_fit_score": miniapp_fit_score,
        "fit_evidence": [
            "轻工具类" if not is_complex else "含复杂原生能力",
            f"功能数: {len(features)}",
            f"品类: {app.get('category', '')}",
        ],
        "implementation_score": implementation_score,
        "impl_evidence": [
            f"预计 {page_count} 个页面",
            "需要支付能力" if needs_payment else "无支付依赖",
        ],
        "risk_score": risk_score,
        "risk_evidence": [
            "无高风险品类" if risk_score >= 70 else "涉及敏感品类",
        ],
        "total_score": total_score,
        "opportunity_score": total_score,
        "recommendation": recommendation,
        "reasons": reasons,
        "reject_reasons": reject_reasons,
        "next_action": next_action,
        "target_platforms": gap["recommended_platforms"],
        "estimated_dev_days": max(3, page_count * 2),
        "data_source": "demo_rule_based",
    }
