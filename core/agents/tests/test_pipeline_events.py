"""Pipeline step-event regression tests.

Guards the live-Timeline contract: step_start / step_end must emit structured
events carrying the fields the dashboard needs — especially `name` (the Chinese
step label) so the UI never has to fall back to the technical step id.
"""

import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = REPO_ROOT / "core" / "pipeline" / "runner.py"


@pytest.fixture()
def runner():
    spec = importlib.util.spec_from_file_location("pipeline_runner_events", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Isolate module-level pipeline state for a clean event capture.
    mod._pipeline_steps = []
    mod._pipeline_job_id = "evt-test-job"
    mod._report_meta = dict(mod._report_meta)
    mod._report_meta["started_at"] = None
    return mod


def _events(text: str, event_name: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{") and '"event"' in line:
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue
            if evt.get("event") == event_name:
                out.append(evt)
    return out


def test_step_started_event_has_required_fields(runner, tmp_path):
    runner._pipeline_output_dir = tmp_path
    buf = io.StringIO()
    with redirect_stdout(buf):
        runner.step_start("market_input", "读取市场数据", "MarketInputAgent")

    events = _events(buf.getvalue(), "step_started")
    assert len(events) == 1
    evt = events[0]
    for field in ("step", "name", "agent", "job_id", "status"):
        assert field in evt, f"step_started missing {field}"
    assert evt["step"] == "market_input"
    assert evt["name"] == "读取市场数据"  # Chinese label, not the id
    assert evt["agent"] == "MarketInputAgent"
    assert evt["status"] == "running"
    assert evt["job_id"] == "evt-test-job"


def test_step_finished_event_carries_name(runner, tmp_path):
    runner._pipeline_output_dir = tmp_path
    buf = io.StringIO()
    with redirect_stdout(buf):
        runner.step_start("gap_check", "覆盖检查", "GapCheckAgent")
        runner.step_end(artifact="gap-check.json")

    events = _events(buf.getvalue(), "step_finished")
    assert len(events) == 1
    evt = events[0]
    assert evt["step"] == "gap_check"
    assert evt["name"] == "覆盖检查"
    assert evt["agent"] == "GapCheckAgent"
    assert evt["status"] == "passed"
