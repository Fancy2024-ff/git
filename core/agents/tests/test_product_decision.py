"""产品决策框架测试：8 维度 / 双总分 / 决策门槛 / MVP 拆解 / capability 联动 / schema。"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
for p in (REPO_ROOT / "core", REPO_ROOT / "core" / "agents"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def _text_app():
    return {"name": "AI Writer", "name_cn": "AI写作助手",
            "description": "writing grammar translate summarize", "features": ["write", "translate"],
            "downloads": 5_000_000, "rating": 4.6, "monetization": "freemium", "category": "Productivity"}


def _canva_app():
    return {"name": "Canva", "name_cn": "Canva设计",
            "description": "all-in-one design platform canvas editor layers timeline drag video edit",
            "features": ["design", "canvas", "layers", "timeline", "video edit", "templates", "brand kit"],
            "downloads": 50_000_000, "rating": 4.8, "monetization": "subscription", "category": "Design"}


def _cap(required, configured, missing, level):
    return {"required_capabilities": required, "configured_capabilities": configured,
            "missing_capabilities": missing, "runnable_level": level}


# ── 决策：文本类 immediate / Canva split ──

def test_text_app_immediate_execute():
    from research.product_research import analyze_product
    r = analyze_product(_text_app(), app_type="text_ai",
                        opportunity={"demand_score": 88, "miniapp_gap_score": 85},
                        gap={}, cap_snapshot=_cap(["text.generate"], ["text.generate"], [], "runtime_ready"))
    assert r["decision"]["recommendation"] == "immediate_execute"
    assert r["decision"]["miniapp_feasibility_score"] >= 50


def test_canva_split_then_execute_not_immediate():
    from research.product_research import analyze_product
    r = analyze_product(_canva_app(), app_type="image_ai",
                        opportunity={"demand_score": 95, "miniapp_gap_score": 60},
                        gap={}, cap_snapshot=_cap(["image.process"], [], ["image.process"], "buildable"))
    dec = r["decision"]
    assert dec["recommendation"] == "split_then_execute"
    assert dec["recommendation"] != "immediate_execute"
    # 市场高但落地性低
    assert dec["market_opportunity_score"] >= 70
    assert dec["miniapp_feasibility_score"] < 50


def test_platform_product_downgraded():
    from research.product_research import analyze_product
    app = {"name": "Mega Suite", "name_cn": "全能套件", "description": "all-in-one platform suite",
           "features": ["a", "b", "c", "d", "e", "f", "g"], "downloads": 3_000_000, "category": "Productivity"}
    r = analyze_product(app, app_type="text_ai",
                        opportunity={"demand_score": 85, "miniapp_gap_score": 80},
                        gap={}, cap_snapshot=_cap(["text.generate"], ["text.generate"], [], "runtime_ready"))
    # 平台型 → 不应 immediate（应降级为 split/research）
    assert r["decision"]["recommendation"] != "immediate_execute"
    assert r["demand"]["scenario_granularity"]["product_type"] == "platform"


def test_high_brand_risk_blocks_immediate():
    from research.product_research import analyze_product
    app = {"name": "Photoshop Mini", "name_cn": "PS小程序", "description": "photoshop photo editor",
           "features": ["edit"], "downloads": 4_000_000, "category": "Photography"}
    r = analyze_product(app, app_type="image_ai",
                        opportunity={"demand_score": 90, "miniapp_gap_score": 85},
                        gap={}, cap_snapshot=_cap(["image.process"], ["image.process"], [], "runtime_ready"))
    assert r["decision"]["brand_risk_score"] >= 70
    assert r["decision"]["recommendation"] != "immediate_execute"


# ── MVP 拆解 ──

def test_mvp_split_plan_for_complex_product():
    from research.product_research import analyze_product
    r = analyze_product(_canva_app(), app_type="image_ai",
                        opportunity={"demand_score": 95, "miniapp_gap_score": 60},
                        gap={}, cap_snapshot=_cap(["image.process"], [], ["image.process"], "buildable"))
    plan = r["split_plan"]
    assert plan["recommended_mvp"]["name"]
    assert plan["non_replicable_features"]          # 复杂产品有不可迁移功能
    assert plan["substitution_strategies"]
    assert "垂直" in plan["recommended_mvp"]["reason"] or plan["recommended_mvp"]["app_type"] == "image_ai"


# ── capability 联动 ──

def test_capability_feasibility_reflects_missing_provider():
    from research.product_research import analyze_product
    r = analyze_product(_text_app(), app_type="image_ai",
                        opportunity={"demand_score": 80, "miniapp_gap_score": 70},
                        gap={}, cap_snapshot=_cap(["image.process"], [], ["image.process"], "buildable"))
    feas = r["feasibility"]["capability_feasibility"]
    assert feas["supported"] is False
    assert "image.process" in feas["missing_capabilities"]
    # 缺 provider → 不给虚高 runtime_ready
    assert r["feasibility"]["generation_feasibility"]["likely_shell_only"] is True


def test_video_missing_provider_in_feasibility():
    from research.product_research import analyze_product
    app = {"name": "Vid Tool", "name_cn": "视频工具", "description": "video summarize",
           "features": ["summarize"], "downloads": 1_000_000, "category": "Video"}
    r = analyze_product(app, app_type="video_light",
                        opportunity={"demand_score": 70, "miniapp_gap_score": 60},
                        gap={}, cap_snapshot=_cap(["video.process"], [], ["video.process"], "buildable"))
    assert "video.process" in r["feasibility"]["capability_feasibility"]["missing_capabilities"]
    assert r["decision"]["recommendation"] != "immediate_execute"


# ── schema 完整性 ──

def test_schema_complete_and_valid():
    from research.product_research import analyze_product
    from research.schemas import is_valid_recommendation, DIMENSIONS
    r = analyze_product(_text_app(), app_type="text_ai",
                        opportunity={"demand_score": 88, "miniapp_gap_score": 85},
                        gap={}, cap_snapshot=_cap(["text.generate"], ["text.generate"], [], "runtime_ready"))
    dec = r["decision"]
    assert is_valid_recommendation(dec["recommendation"])
    assert 0 <= dec["market_opportunity_score"] <= 100
    assert 0 <= dec["miniapp_feasibility_score"] <= 100
    assert 0.0 <= dec["confidence"] <= 1.0
    assert dec["next_action"]
    # demand/feasibility 维度字段齐备
    assert "market_demand" in r["demand"] and "scenario_granularity" in r["demand"]
    assert "miniapp_fit" in r["feasibility"] and "capability_feasibility" in r["feasibility"]


def test_low_market_rejected():
    from research.product_research import analyze_product
    app = {"name": "Niche", "name_cn": "冷门", "description": "tiny tool",
           "features": ["x"], "downloads": 1000, "rating": 3.0, "category": "Utilities"}
    r = analyze_product(app, app_type="utility_tool",
                        opportunity={"demand_score": 20, "miniapp_gap_score": 15},
                        gap={}, cap_snapshot=_cap(["utility.execute"], ["utility.execute"], [], "runtime_ready"))
    assert r["decision"]["recommendation"] in ("reject", "research_only")
