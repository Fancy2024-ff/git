"""Architecture regression tests (collab refactor follow-up).

Guards the path-unification fixes so the DATA_DIR / outputs-location class of
bugs cannot silently come back:
  1. settings.DATA_DIR points at the REPO-ROOT data dir, not core/data.
  2. API OUTPUTS_DIR == Pipeline OUTPUTS_DIR (same physical directory).
  3. API can list a job that exists under data/outputs.
  4. POST /api/real-inputs/apps writes to data/inputs/real/apps.json.
"""

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
AGENTS_DIR = REPO_ROOT / "core" / "agents"
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_settings_data_dir_is_repo_root():
    """settings.PROJECT_ROOT must be the repo root, DATA_DIR = repo_root/data."""
    from config import settings
    assert settings.PROJECT_ROOT == REPO_ROOT, (
        f"PROJECT_ROOT={settings.PROJECT_ROOT}, expected {REPO_ROOT}"
    )
    assert settings.DATA_DIR == REPO_ROOT / "data"
    # Regression guard: the old bug pointed DATA_DIR at core/data.
    assert settings.DATA_DIR != REPO_ROOT / "core" / "data"


def test_api_and_pipeline_outputs_dir_match():
    """The directory the API reads from must equal the one the pipeline writes to."""
    runner = _load_module("pipeline_runner", REPO_ROOT / "core" / "pipeline" / "runner.py")
    api = _load_module("api_main_arch", REPO_ROOT / "apps" / "api" / "main.py")

    assert runner.OUTPUTS_DIR == api.OUTPUTS_DIR == REPO_ROOT / "data" / "outputs"
    assert api.REAL_INPUTS_DIR == REPO_ROOT / "data" / "inputs" / "real"


def test_api_lists_existing_job(server_client, auth_headers):
    """A job directory present under OUTPUTS_DIR must appear in GET /api/jobs."""
    client, server = server_client
    job_dir = server.OUTPUTS_DIR / "arch-regression-job"
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "candidate.json").write_text(
        json.dumps({"name": "Test App", "name_cn": "测试"}), encoding="utf-8"
    )

    res = client.get("/api/jobs", headers=auth_headers)
    assert res.status_code == 200
    ids = [j["id"] for j in res.json()["jobs"]]
    assert "arch-regression-job" in ids


def test_real_inputs_post_writes_to_inputs_real(server_client, auth_headers):
    """POST /api/real-inputs/apps must persist to REAL_INPUTS_DIR/apps.json."""
    client, server = server_client
    payload = [{
        "name": "Translator", "name_cn": "翻译",
        "source": "app_store",
        "category": "Productivity",
        "description": "translate", "description_cn": "翻译工具",
        "features": ["translate"], "features_cn": ["翻译"],
        "downloads": 100000, "rating": 4.6, "review_count": 500,
        "monetization": "freemium",
    }]
    res = client.post("/api/real-inputs/apps", json=payload, headers=auth_headers)
    assert res.status_code == 200

    written = server.REAL_INPUTS_DIR / "apps.json"
    assert written.exists(), f"expected file at {written}"
    data = json.loads(written.read_text(encoding="utf-8"))
    assert isinstance(data, list) and data[0]["name"] == "Translator"
