"""需求分析决策框架的结构化 schema（单一事实源）。

定义 4 类 artifact 的字段与默认值。framework/decision 产出的 dict 以此为契约，
artifacts.py 据此写盘。所有字段缺失时补默认，保证下游稳定。
"""

from __future__ import annotations

# 合法的执行建议
RECOMMENDATIONS = ("immediate_execute", "split_then_execute", "research_only", "reject")

# 8 个分析维度 key（每个维度结构化输出）
DIMENSIONS = (
    "market_demand",
    "scenario_granularity",
    "miniapp_fit",
    "capability_feasibility",
    "generation_feasibility",
    "compliance_review_risk",
    "business_competition",
    "execution_recommendation",
)


def demand_analysis_defaults() -> dict:
    """demand-analysis.json 默认结构。"""
    return {
        "app_name": "",
        "app_name_cn": "",
        "market_demand": {
            "pain_point_frequency": "",      # high/medium/low
            "long_term": False,
            "trend_sustainable": "",
            "competition_level": "",         # high/medium/low
            "evidence": [],
        },
        "scenario_granularity": {
            "product_type": "",              # platform / tool / vertical
            "splittable_to_mvp": False,
            "steps_to_core_task": 0,
            "notes": "",
        },
        "business_competition": {
            "monetization_fit": [],          # subscription/credits/one_time/lead_gen
            "miniapp_differentiation": "",
            "worth_grabbing_gap": False,
        },
        "target_users": [],
        "core_value": "",
        "market_opportunity_score": 0,
    }


def feasibility_report_defaults() -> dict:
    """miniapp-feasibility-report.json 默认结构。"""
    return {
        "app_name": "",
        "app_type": "",
        "miniapp_fit": {
            "light_interaction": False,
            "short_flow": False,
            "needs_complex_canvas": False,   # 画布/时间轴/拖拽/多图层
            "closed_loop_in_miniapp": False,
            "score": 0,
        },
        "capability_feasibility": {
            "required_capabilities": [],
            "configured_capabilities": [],
            "missing_capabilities": [],
            "runnable_level_estimate": "buildable",
            "supported": False,
            "notes": "",
        },
        "generation_feasibility": {
            "template_available": False,
            "runtime_supported": False,
            "likely_shell_only": True,
            "risks": [],
        },
        "compliance_review_risk": {
            "brand_risk_score": 0,           # 0-100，高=风险大
            "review_risk_score": 0,
            "naming_brand_risk": "",
            "content_risk": "",
            "privacy_risk": "",
            "wechat_review_friendly": "",
        },
        "miniapp_feasibility_score": 0,
    }


def mvp_split_plan_defaults() -> dict:
    """mvp-split-plan.json 默认结构。"""
    return {
        "original_product_summary": "",
        "original_core_users": "",
        "original_core_value": "",
        "core_feature_breakdown": [],
        "replicable_features": [],
        "non_replicable_features": [],
        "substitution_strategies": [],
        "recommended_mvp": {
            "name": "",
            "app_type": "",
            "capabilities": [],
            "first_version_scope": [],
            "reason": "",
        },
    }


def execution_decision_defaults() -> dict:
    """execution-decision.json 默认结构。"""
    return {
        "recommendation": "research_only",   # RECOMMENDATIONS 之一
        "confidence": 0.0,                    # 0-1
        "market_opportunity_score": 0,
        "miniapp_feasibility_score": 0,
        "brand_risk_score": 0,
        "review_risk_score": 0,
        "execution_confidence": 0.0,
        "blocking_reasons": [],
        "next_action": "",
        "reason": "",
    }


def is_valid_recommendation(rec: str) -> bool:
    return rec in RECOMMENDATIONS
