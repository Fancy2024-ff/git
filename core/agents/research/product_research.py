"""产品决策研究总入口（成熟需求分析框架）。

analyze_product 编排 8 维度 + MVP 拆解 + 决策，产出 4 个结构化结果 dict。
规则驱动（USE_LLM=false 也完整）；LLM 可选增强 reasoning（失败不影响）。

注：与历史 agent.py:run_research（LangChain PRD 生成，orchestrator 用）并存、职责不同，互不影响。
"""

from __future__ import annotations

import sys
from pathlib import Path

_CORE = Path(__file__).resolve().parents[2]   # core/agents/research → core
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from research import framework as fw
from research import decision as dec
from research import schemas as sc


def _build_mvp_split_plan(app: dict, app_type: str, scenario: dict,
                          cap_feas: dict, fit: dict) -> dict:
    plan = sc.mvp_split_plan_defaults()
    name_cn = app.get("name_cn") or app.get("name", "")
    features = app.get("features_cn") or app.get("features", []) or []
    plan["original_product_summary"] = f"{name_cn}：{app.get('description_cn') or app.get('description','')}"[:200]
    plan["original_core_users"] = "；".join(app.get("target_users", [])) or "移动端用户"
    plan["original_core_value"] = app.get("description_cn", "")[:120]
    plan["core_feature_breakdown"] = list(features)

    needs_canvas = fit.get("needs_complex_canvas")
    if needs_canvas:
        plan["replicable_features"] = [f for f in features][:2] or ["核心单任务处理"]
        plan["non_replicable_features"] = ["多图层/画布编辑", "时间轴/工程文件", "复杂拖拽交互"]
        plan["substitution_strategies"] = [
            "用预设模板 + 一键处理替代自由编辑",
            "复杂编辑引导到原 App，小程序只做高频单任务",
        ]
    else:
        plan["replicable_features"] = list(features)
        plan["non_replicable_features"] = []
        plan["substitution_strategies"] = []

    mvp_app_type = app_type
    mvp_name = f"{name_cn} · 小程序版"
    if scenario.get("_is_platform") or needs_canvas:
        if app_type == "image_ai":
            mvp_name = "证件照/一键抠图"
        mvp_name = mvp_name + "（垂直 MVP）"
    plan["recommended_mvp"] = {
        "name": mvp_name,
        "app_type": mvp_app_type,
        "capabilities": cap_feas.get("required_capabilities", []),
        "first_version_scope": (plan["replicable_features"][:3] or ["核心单任务"]),
        "reason": ("原产品平台型/复杂，建议拆成垂直单任务上线" if (scenario.get("_is_platform") or needs_canvas)
                   else "工具型，可直接做成单任务小程序"),
    }
    return plan


def analyze_product(app: dict, *, app_type: str, opportunity: dict, gap: dict,
                    cap_snapshot: dict, use_llm: bool = False) -> dict:
    """规则驱动的产品决策分析。返回 {demand, feasibility, split_plan, decision}。永不抛异常。"""
    try:
        market = fw.analyze_market_demand(app, opportunity)
        scenario = fw.analyze_scenario_granularity(app)
        fit = fw.analyze_miniapp_fit(app, scenario)
        cap_feas = fw.analyze_capability_feasibility(app_type, cap_snapshot)
        gen_feas = fw.analyze_generation_feasibility(app_type, cap_feas)
        compliance = fw.analyze_compliance_review_risk(app)
        business = fw.analyze_business_competition(app, market)

        market_score = market.pop("_market_opportunity_score", 0)
        feasibility_score = dec.compute_miniapp_feasibility_score(fit, scenario, cap_feas, gen_feas)
        decision = dec.decide(market_score=market_score, feasibility_score=feasibility_score,
                              compliance=compliance, scenario=scenario)

        demand = sc.demand_analysis_defaults()
        demand.update({
            "app_name": app.get("name", ""), "app_name_cn": app.get("name_cn", ""),
            "market_demand": market, "scenario_granularity": dict(scenario),
            "business_competition": business,
            "target_users": app.get("target_users", []) or [],
            "core_value": app.get("description_cn", "")[:120],
            "market_opportunity_score": round(market_score, 1),
        })
        for k in ("_is_platform", "_is_complex"):
            demand["scenario_granularity"].pop(k, None)

        feas = sc.feasibility_report_defaults()
        feas.update({
            "app_name": app.get("name", ""), "app_type": app_type,
            "miniapp_fit": fit, "capability_feasibility": cap_feas,
            "generation_feasibility": gen_feas, "compliance_review_risk": compliance,
            "miniapp_feasibility_score": feasibility_score,
        })

        split_plan = _build_mvp_split_plan(app, app_type, scenario, cap_feas, fit)

        if use_llm:
            try:
                from research.demand_llm import run_llm_demand_analysis
                ai = run_llm_demand_analysis(app)
                if ai.get("reasoning_summary"):
                    decision["reason"] = decision["reason"] + f"；AI: {ai['reasoning_summary']}"
                    demand["_llm_reasoning"] = ai.get("reasoning_summary", "")
            except Exception:
                pass

        return {"demand": demand, "feasibility": feas,
                "split_plan": split_plan, "decision": decision}
    except Exception as e:
        d = sc.execution_decision_defaults()
        d["reason"] = f"analyze_product error: {type(e).__name__}: {str(e)[:150]}"
        return {"demand": sc.demand_analysis_defaults(),
                "feasibility": sc.feasibility_report_defaults(),
                "split_plan": sc.mvp_split_plan_defaults(), "decision": d}
