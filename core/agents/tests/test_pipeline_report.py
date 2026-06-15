"""Pipeline tests: gap-check coverage scoring, report failure state, readiness, manifest.

Loads the standalone scripts/run_demo_pipeline.py (stdlib-only, no LLM deps).
"""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "run_demo_pipeline.py"


@pytest.fixture(scope="module")
def pipe():
    spec = importlib.util.spec_from_file_location("run_demo_pipeline", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _app(downloads):
    return {
        "name": "Demo", "name_cn": "演示", "category": "Productivity",
        "description": "d", "description_cn": "d",
        "features": ["a"], "features_cn": ["甲"],
        "downloads": downloads, "rating": 4.5, "review_count": 100,
        "monetization": "freemium",
    }


# --- P2-9: gap-check coverage ordering --------------------------------------

@pytest.mark.parametrize("downloads,expect_wechat", [
    (4_000_000, "missing"),
    (6_000_000, "weak"),
    (12_000_000, "strong"),
])
def test_coverage_level_thresholds(pipe, downloads, expect_wechat):
    gap = pipe.gap_check_agent(_app(downloads))
    wechat = next(p for p in gap["platforms_checked"] if p["platform"] == "wechat")
    assert wechat["coverage_level"] == expect_wechat


# --- P1-5: pipeline-report never stays 'running' on failure -----------------

def test_report_failure_state(pipe, tmp_path):
    pipe._pipeline_output_dir = tmp_path
    pipe._pipeline_job_id = "jobX"
    pipe._pipeline_steps = []
    pipe._report_meta.update({
        "started_at": None, "finished_at": None, "total_passed": None,
        "error": None, "mode": "demo", "data_source": "demo_rule_based",
    })

    pipe.step_start("s1", "Step 1", "AgentA")  # left running on purpose
    pipe.finalize_pipeline_report(total_passed=False, error="boom")

    report = json.loads((tmp_path / "pipeline-report.json").read_text(encoding="utf-8"))
    assert report["total_passed"] is False
    assert report["error"] == "boom"
    assert report["finished_at"] is not None
    assert all(s["status"] != "running" for s in report["steps"])
    assert report["steps"][0]["status"] == "failed"


def test_step_end_records_structured_error(pipe, tmp_path):
    pipe._pipeline_output_dir = tmp_path
    pipe._pipeline_steps = []
    pipe._report_meta["started_at"] = None
    pipe.step_start("s2", "Step 2", "AgentB")
    pipe.step_end(error="kaboom", error_code="my_code",
                  user_message="用户可读", developer_message="dev detail")
    entry = pipe._pipeline_steps[-1]
    assert entry["status"] == "failed"
    assert entry["error_code"] == "my_code"
    assert entry["user_message"] == "用户可读"


# --- P1-7: honest submission readiness --------------------------------------

def test_readiness_blocked_without_auth_or_qa(pipe, tmp_path):
    pipe._pipeline_job_id = "jobR"
    opportunity = {"target_platforms": ["wechat"]}
    qa = {"passed": False, "checks": {"dist_exists": False}}
    readiness = pipe.build_submission_readiness(
        {"name_cn": "演示"}, opportunity, qa, tmp_path, "demo"
    )
    assert readiness["ready_to_submit"] is False
    assert readiness["blocking_issues"]  # non-empty
    assert any("QA" in b for b in readiness["blocking_issues"])


# --- P1-8: artifact manifest -------------------------------------------------

def test_artifact_manifest_marks_blocked(pipe, tmp_path):
    qa = {"passed": False, "checks": {"dist_exists": False}}
    readiness = {"ready_to_submit": False}
    manifest = pipe.build_artifact_manifest(tmp_path, qa, readiness)
    items = {i["path"]: i for i in manifest["items"]}
    assert items["generated/miniapp"]["status"] == "blocked"
    assert items["publish-package"]["status"] == "blocked"
    assert items["prd.md"]["status"] == "needs_review"


def test_artifact_manifest_ready_when_passing(pipe, tmp_path):
    qa = {"passed": True, "checks": {"dist_exists": True}}
    readiness = {"ready_to_submit": True}
    manifest = pipe.build_artifact_manifest(tmp_path, qa, readiness)
    items = {i["path"]: i for i in manifest["items"]}
    assert items["generated/miniapp"]["status"] == "ready"


# --- P0-3: app normalization is KeyError-safe -------------------------------

def test_normalize_app_fills_defaults(pipe):
    app = pipe._normalize_app({"name": "X", "source": "App Store", "category": "Tools",
                               "description": "d", "features": ["f"]})
    assert app["name_cn"] == "X"
    assert app["features_cn"] == ["f"]
    assert app["downloads"] == 0
    # guaranteed non-empty features_cn so features_cn[0] is always safe
    empty = pipe._normalize_app({"name": "Y"})
    assert empty["features_cn"]
