"""LLM 需求分析（路线 B）测试。

覆盖：
1. USE_LLM=false → 不调 LLM，analysis 标记 llm_used=false，pipeline 字段稳定
2. USE_LLM=true + LLM 成功（mock）→ 生成 ai-demand-analysis.json，analysis.llm_used=true
3. USE_LLM=true + LLM 抛异常（mock）→ 不崩，llm_fallback=true，保留 demand_score
4. schema 校验：缺字段补默认、非 JSON 抠取/兜底
5. prompt 文档存在且含关键字段名
"""

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = REPO_ROOT / "core" / "pipeline" / "runner.py"


@pytest.fixture()
def runner():
    spec = importlib.util.spec_from_file_location("pipeline_runner_llm", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _app():
    return {
        "name": "AI Writing Assistant", "name_cn": "AI 写作助手", "source": "Google Play",
        "category": "Productivity", "description": "writing", "description_cn": "写作",
        "downloads": 5_500_000, "rating": 4.6, "review_count": 12000,
        "features": ["grammar"], "features_cn": ["语法"], "monetization": "freemium",
    }


# ---- demand_llm 纯逻辑 -------------------------------------------------------

def test_schema_fills_missing_fields():
    from research import demand_llm
    norm = demand_llm._normalize({"reasoning_summary": "值得做"})
    # 缺的字段补默认
    assert norm["reasoning_summary"] == "值得做"
    assert norm["target_users"] == []
    assert norm["miniapp_mvp_scope"] == []
    assert norm["confidence"] == 0.0


def test_extract_json_from_fenced_text():
    from research import demand_llm
    raw = '```json\n{"reasoning_summary": "ok", "confidence": 0.8}\n```'
    got = demand_llm._extract_json(raw)
    assert got["reasoning_summary"] == "ok"


def test_extract_json_non_json_raises():
    from research import demand_llm
    with pytest.raises(Exception):
        demand_llm._extract_json("这不是 JSON，完全是一段话")


# ---- _apply_llm_demand_analysis 行为 ----------------------------------------

def test_use_llm_false_marks_not_used(runner, tmp_path, monkeypatch):
    import config.settings as settings
    monkeypatch.setattr(settings, "USE_LLM", False)
    analysis = {"demand_score": 88, "score_breakdown": {}, "reasons": ["r1"]}
    runner._apply_llm_demand_analysis(_app(), analysis, tmp_path)

    assert analysis["llm_used"] is False
    assert analysis["llm_fallback"] is False
    assert analysis["ai_summary"] == ""
    assert analysis["ai_analysis_path"] is None
    assert analysis["demand_score"] == 88  # 规则分不动
    marker = json.loads((tmp_path / "ai-demand-analysis.json").read_text(encoding="utf-8"))
    assert marker["llm_used"] is False


def test_use_llm_success_writes_ai_file(runner, tmp_path, monkeypatch):
    import config.settings as settings
    monkeypatch.setattr(settings, "USE_LLM", True)

    # mock LLM 调用，返回结构化结果
    from research import demand_llm
    def fake(app):
        out = dict(demand_llm.SCHEMA_DEFAULTS)
        out.update({
            "llm_used": True, "model": "claude-test", "app_name": app["name"],
            "reasoning_summary": "需求成立，适合做小程序",
            "user_pain_points": ["原生 App 要下载"],
            "replicable_features": ["语法纠正"],
        })
        return out
    monkeypatch.setattr(demand_llm, "run_llm_demand_analysis", fake)

    analysis = {"demand_score": 88, "reasons": ["r1"]}
    runner._apply_llm_demand_analysis(_app(), analysis, tmp_path)

    assert analysis["llm_used"] is True
    assert analysis["llm_fallback"] is False
    assert analysis["ai_summary"] == "需求成立，适合做小程序"
    assert analysis["ai_analysis_path"] == "ai-demand-analysis.json"
    assert analysis["demand_score"] == 88  # 仍不改分
    assert any("AI:" in r for r in analysis["reasons"])  # reasons 被增强

    ai = json.loads((tmp_path / "ai-demand-analysis.json").read_text(encoding="utf-8"))
    assert ai["reasoning_summary"] == "需求成立，适合做小程序"
    assert ai["user_pain_points"] == ["原生 App 要下载"]


def test_use_llm_failure_falls_back(runner, tmp_path, monkeypatch):
    import config.settings as settings
    monkeypatch.setattr(settings, "USE_LLM", True)

    from research import demand_llm
    def boom(app):
        raise RuntimeError("proxy 503")
    monkeypatch.setattr(demand_llm, "run_llm_demand_analysis", boom)

    analysis = {"demand_score": 88, "reasons": ["r1"]}
    # 不能抛异常
    runner._apply_llm_demand_analysis(_app(), analysis, tmp_path)

    assert analysis["llm_used"] is False
    assert analysis["llm_fallback"] is True
    assert analysis["demand_score"] == 88  # 规则分保留
    assert "fallback" in analysis["ai_summary"].lower() or "fallback" in analysis["ai_summary"]
    rec = json.loads((tmp_path / "ai-demand-analysis.json").read_text(encoding="utf-8"))
    assert rec["llm_fallback"] is True
    assert "503" in rec["error"]


def test_prompt_doc_exists_with_key_fields():
    doc = REPO_ROOT / "docs" / "product" / "LLM_DEMAND_ANALYSIS_PROMPT.md"
    assert doc.exists()
    text = doc.read_text(encoding="utf-8-sig")
    for field in ("user_pain_points", "miniapp_mvp_scope", "non_replicable_features"):
        assert field in text, f"prompt doc missing {field}"
