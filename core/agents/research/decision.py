"""执行决策：把 8 维度结果归纳为 market/feasibility 双总分 + recommendation。

门槛（回应"热门≠适合直接小程序化"）：
- feasibility<50 → 禁 immediate_execute
- market 高 + feasibility 中 → split_then_execute / research_only
- market & feasibility 都高 + 无高风险 → immediate_execute
- market 低 → reject / research_only
"""

from __future__ import annotations

HIGH = 70
MID = 50


def compute_miniapp_feasibility_score(fit: dict, scenario: dict, cap_feas: dict,
                                      gen_feas: dict) -> int:
    """落地性总分：miniapp_fit + 场景颗粒度 + 能力可实现性 + 生成可行性。"""
    fit_score = fit.get("score", 0)
    cap_bonus = 20 if cap_feas.get("supported") else 0
    gen_penalty = 20 if gen_feas.get("likely_shell_only") else 0
    granularity_bonus = 10 if scenario.get("steps_to_core_task", 9) <= 2 else 0
    score = fit_score * 0.6 + cap_bonus + granularity_bonus - gen_penalty
    return int(max(0, min(100, round(score))))


def decide(*, market_score: float, feasibility_score: int, compliance: dict,
           scenario: dict) -> dict:
    """综合决策。返回 execution-decision 内容（不含默认补全）。"""
    brand_risk = compliance.get("brand_risk_score", 0)
    review_risk = compliance.get("review_risk_score", 0)
    high_risk = brand_risk >= 70 or review_risk >= 70
    splittable = scenario.get("splittable_to_mvp", False)

    blockers: list[str] = []
    if feasibility_score < MID:
        blockers.append(f"小程序落地性低（{feasibility_score}）")
    if high_risk:
        if brand_risk >= 70:
            blockers.append("品牌/商标风险高")
        if review_risk >= 70:
            blockers.append("内容审核风险高")

    # 决策门槛
    if market_score < MID:
        rec = "reject" if feasibility_score < MID else "research_only"
    elif feasibility_score < MID:
        # 市场可以但落地性低：可拆则拆，否则只研究
        rec = "split_then_execute" if splittable else "research_only"
    elif feasibility_score < HIGH or market_score < HIGH:
        # 市场高 + 落地中 → 拆分或研究
        rec = "split_then_execute" if splittable else "research_only"
    else:
        # 两者都高
        rec = "immediate_execute"

    # 高风险一律不得 immediate_execute
    if rec == "immediate_execute" and high_risk:
        rec = "split_then_execute" if splittable else "research_only"

    # confidence：双分越高、风险越低越高
    execution_confidence = round(
        max(0.0, min(1.0,
            (market_score + feasibility_score) / 200 - (brand_risk + review_risk) / 400)), 2)

    next_action = {
        "immediate_execute": "进入 PRD 生成与代码生成",
        "split_then_execute": "先按 mvp-split-plan 拆成垂直子场景，再执行",
        "research_only": "暂缓执行，补充调研与能力/合规确认",
        "reject": "不建议做成小程序，换目标",
    }[rec]

    reason_bits = [f"市场机会 {market_score}", f"落地性 {feasibility_score}"]
    if high_risk:
        reason_bits.append("存在高风险阻塞")
    if rec == "split_then_execute":
        reason_bits.append("原产品宜拆成垂直 MVP 而非原样小程序化")

    return {
        "recommendation": rec,
        "confidence": execution_confidence,
        "market_opportunity_score": round(market_score, 1),
        "miniapp_feasibility_score": feasibility_score,
        "brand_risk_score": brand_risk,
        "review_risk_score": review_risk,
        "execution_confidence": execution_confidence,
        "blocking_reasons": blockers,
        "next_action": next_action,
        "reason": "；".join(reason_bits),
    }
