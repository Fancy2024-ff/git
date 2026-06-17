"""微信上传链路测试：miniprogram_ci CLI 封装 + platform service + API + artifact 联动。

无微信真实环境，用 mock subprocess/which 走真实代码路径（与真实 miniprogram-ci 路径一致）。
"""

import json
import sys
import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
for p in (REPO_ROOT / "core", REPO_ROOT / "core" / "agents"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


# ── miniprogram_ci CLI 封装 ──

def test_ci_cli_missing_when_no_npx():
    from integrations.platform_clis import miniprogram_ci
    r = miniprogram_ci.upload_project(
        appid="wx", private_key_path="/k", project_path="/p",
        which=lambda name: None,   # npx 不存在
    )
    assert r.success is False
    assert r.error_code == miniprogram_ci.CIErrorCode.CLI_MISSING


def test_ci_parse_success():
    from integrations.platform_clis import miniprogram_ci
    r = miniprogram_ci.parse_upload_result(0, "upload complete", "")
    assert r.success is True


def test_ci_parse_auth_failed():
    from integrations.platform_clis import miniprogram_ci
    r = miniprogram_ci.parse_upload_result(1, "", "invalid private key")
    assert r.success is False
    assert r.error_code == miniprogram_ci.CIErrorCode.AUTH_FAILED


def test_ci_timeout(monkeypatch):
    from integrations.platform_clis import miniprogram_ci
    def boom(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, kw.get("timeout", 1))
    r = miniprogram_ci.upload_project(
        appid="wx", private_key_path="/k", project_path="/p",
        runner=boom, which=lambda n: "/usr/bin/" + n,
    )
    assert r.error_code == miniprogram_ci.CIErrorCode.TIMEOUT


def test_ci_command_uses_npx_miniprogram_ci():
    from integrations.platform_clis import miniprogram_ci
    captured = {}
    def runner(cmd, **kw):
        captured["cmd"] = cmd
        class P: returncode = 0; stdout = "ok"; stderr = ""
        return P()
    miniprogram_ci.upload_project(appid="wx1", private_key_path="/k/p.pem",
                                  project_path="/proj", runner=runner,
                                  which=lambda n: "/usr/bin/" + n)
    cmd = captured["cmd"]
    assert cmd[:3] == ["npx", "miniprogram-ci", "upload"]
    assert "--appid" in cmd and "wx1" in cmd
    assert "--pp" in cmd and "/proj" in cmd


# ── platform service ──

def _setup_job(tmp_path, *, configured=True, with_dist=True, upload_enabled=True):
    job = tmp_path / "job"; job.mkdir()
    auth = tmp_path / "auth"; auth.mkdir()
    if configured:
        cfg = {"appid": "wx123", "private_key_path": "/k/key.pem", "version": "1.0.0"}
        if upload_enabled:
            cfg["upload_enabled"] = True
        (auth / "wechat.json").write_text(json.dumps(cfg), encoding="utf-8")
    if with_dist:
        dist = job / "generated" / "miniapp" / "dist" / "build" / "mp-weixin"
        dist.mkdir(parents=True)
        (dist / "app.json").write_text("{}", encoding="utf-8")
        (job / "qa-report.json").write_text(json.dumps({"checks": {"dist_path": str(dist)}}), encoding="utf-8")
    (job / "submit-status.json").write_text(json.dumps({
        "job_id": "t", "platforms": [{"platform_id": "wechat", "upload_status": "not_started",
                                       "review_status": "not_submitted"}]}), encoding="utf-8")
    # readiness 报告（用于联动测试）
    (job / "submission-readiness-report.json").write_text(json.dumps({
        "job_id": "t", "ready_to_submit": False, "is_ready_to_submit": False,
        "blocking_issues": ["缺少真机测试截图，需人工准备"], "warning_issues": [],
        "platform_readiness": [
            {"platform": "wechat", "name_cn": "微信小程序", "ready": False,
             "configured": True, "can_upload": True, "next_action": "可上传"}
        ],
        "next_action": "解决阻塞后提交",
    }), encoding="utf-8")
    return job, auth


def test_upload_config_missing(tmp_path):
    from platforms.wechat.upload import upload_dev_version
    job, auth = _setup_job(tmp_path, configured=False)
    r = upload_dev_version(job_dir=job, platform_auth_dir=auth)
    assert r["error_code"] == "config_missing"
    assert r["upload_passed"] is False


def test_upload_disabled(tmp_path):
    from platforms.wechat.upload import upload_dev_version
    job, auth = _setup_job(tmp_path, upload_enabled=False)
    r = upload_dev_version(job_dir=job, platform_auth_dir=auth)
    assert r["error_code"] == "upload_disabled"


def test_upload_dist_missing(tmp_path):
    from platforms.wechat.upload import upload_dev_version
    job, auth = _setup_job(tmp_path, with_dist=False)
    r = upload_dev_version(job_dir=job, platform_auth_dir=auth)
    assert r["error_code"] == "dist_missing"


def test_upload_cli_missing(tmp_path):
    from platforms.wechat.upload import upload_dev_version
    job, auth = _setup_job(tmp_path)
    r = upload_dev_version(job_dir=job, platform_auth_dir=auth, which=lambda n: None)
    assert r["error_code"] == "cli_missing"


def test_upload_success_with_mock_subprocess(tmp_path):
    from platforms.wechat.upload import upload_dev_version, update_submit_status
    job, auth = _setup_job(tmp_path)
    class P: returncode = 0; stdout = "upload done v1.0.0"; stderr = ""
    r = upload_dev_version(job_dir=job, platform_auth_dir=auth,
                           runner=lambda cmd, **kw: P(), which=lambda n: "/usr/bin/" + n)
    assert r["upload_passed"] is True
    assert r["status"] == "uploaded"
    assert r["provider"] == "miniprogram-ci"
    assert "mp.weixin.qq.com" in r["next_action"]
    # artifact 联动
    update_submit_status(job, r)
    ss = json.loads((job / "submit-status.json").read_text(encoding="utf-8"))
    w = ss["platforms"][0]
    assert w["upload_status"] == "uploaded"
    assert w["last_action_by"] == "agent"
    assert "提交审核" in w["next_action"]


def test_upload_failure_maps_error(tmp_path):
    from platforms.wechat.upload import upload_dev_version, update_submit_status
    job, auth = _setup_job(tmp_path)
    class P: returncode = 1; stdout = ""; stderr = "invalid private key"
    r = upload_dev_version(job_dir=job, platform_auth_dir=auth,
                           runner=lambda cmd, **kw: P(), which=lambda n: "/usr/bin/" + n)
    assert r["upload_passed"] is False
    assert r["error_code"] == "auth_failed"
    update_submit_status(job, r)
    ss = json.loads((job / "submit-status.json").read_text(encoding="utf-8"))
    assert ss["platforms"][0]["upload_status"] == "failed"


# ── API ──

def _load_api(monkeypatch, tmp_path):
    monkeypatch.setenv("DASHBOARD_API_KEY", "t")
    spec = importlib.util.spec_from_file_location("api_wx", REPO_ROOT / "apps" / "api" / "main.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    from fastapi.testclient import TestClient
    return m, TestClient(m.app)


def test_api_wechat_upload_requires_auth(monkeypatch, tmp_path):
    _, client = _load_api(monkeypatch, tmp_path)
    r = client.post("/api/platforms/wechat/upload", json={"job_id": "x"})
    assert r.status_code == 401


def test_api_wechat_upload_missing_job_id(monkeypatch, tmp_path):
    _, client = _load_api(monkeypatch, tmp_path)
    r = client.post("/api/platforms/wechat/upload", json={}, headers={"X-API-Key": "t"})
    assert r.status_code == 400


def test_api_wechat_upload_job_not_found(monkeypatch, tmp_path):
    _, client = _load_api(monkeypatch, tmp_path)
    r = client.post("/api/platforms/wechat/upload",
                    json={"job_id": "no-such-job"}, headers={"X-API-Key": "t"})
    assert r.status_code == 404


# ── readiness 真联动 ──

def test_readiness_synced_on_upload_success(tmp_path):
    from platforms.wechat.upload import upload_dev_version, update_submit_status, update_submission_readiness
    import json as _j
    job, auth = _setup_job(tmp_path)
    class P: returncode = 0; stdout = "upload done"; stderr = ""
    r = upload_dev_version(job_dir=job, platform_auth_dir=auth,
                           runner=lambda c, **k: P(), which=lambda n: "/usr/bin/" + n)
    update_submit_status(job, r)
    update_submission_readiness(job, r)

    ss = _j.loads((job / "submit-status.json").read_text(encoding="utf-8"))
    rd = _j.loads((job / "submission-readiness-report.json").read_text(encoding="utf-8"))
    w_ss = ss["platforms"][0]
    w_rd = next(p for p in rd["platform_readiness"] if p["platform"] == "wechat")
    # 两个 artifact 不矛盾：都体现已上传
    assert w_ss["upload_status"] == "uploaded"
    assert w_rd["uploaded"] is True and w_rd["upload_status"] == "uploaded"
    assert rd["upload_ready"] is True          # 具备上传条件
    assert rd["upload_completed"] is True       # 已上传成功
    # 上传成功 ≠ review_ready
    assert rd["review_ready"] is False
    assert "提交审核" in w_rd["next_action"]


def test_readiness_synced_on_upload_failure(tmp_path):
    from platforms.wechat.upload import upload_dev_version, update_submit_status, update_submission_readiness
    import json as _j
    job, auth = _setup_job(tmp_path)
    class P: returncode = 1; stdout = ""; stderr = "invalid private key"
    r = upload_dev_version(job_dir=job, platform_auth_dir=auth,
                           runner=lambda c, **k: P(), which=lambda n: "/usr/bin/" + n)
    update_submit_status(job, r)
    update_submission_readiness(job, r)

    ss = _j.loads((job / "submit-status.json").read_text(encoding="utf-8"))
    rd = _j.loads((job / "submission-readiness-report.json").read_text(encoding="utf-8"))
    assert ss["platforms"][0]["upload_status"] == "failed"
    w_rd = next(p for p in rd["platform_readiness"] if p["platform"] == "wechat")
    assert w_rd["upload_status"] == "upload_failed"
    assert w_rd["uploaded"] is False
    # 失败不改"可上传"语义：平台仍具备上传条件（configured+dist），upload_ready 不漂移
    assert rd["upload_ready"] is True
    # 已上传成功为 false
    assert rd["upload_completed"] is False
    assert any("微信上传失败" in b for b in rd["blocking_issues"])


# ── 平台公共骨架 ──

def test_platform_registry_lists_wechat():
    from platforms import registry
    assert "wechat" in registry.list_platforms()
    assert registry.supports_action("wechat", registry.ACTION_UPLOAD) is True
    assert registry.supports_action("wechat", registry.ACTION_REVIEW) is False  # 自动提审未做
    assert registry.is_upload_automatable("wechat") is True
    assert registry.is_upload_automatable("alipay") is False   # manual
    assert registry.get_submit_url("wechat").startswith("http")
    snap = registry.build_platform_snapshot()
    assert "wechat" in snap["implemented_upload"]


def test_platform_common_models_and_status():
    from platforms.common.models import PlatformUploadResult, PlatformNextAction
    from platforms.common.status import UploadStatus
    r = PlatformUploadResult(
        platform_id="wechat", upload_passed=True, upload_status=UploadStatus.UPLOADED,
        provider="miniprogram-ci", next_action=PlatformNextAction(owner="human", text="去提审"),
    )
    d = r.to_dict()
    assert d["status"] == "uploaded"          # 兼容历史前端字段
    assert d["next_action"] == "去提审"
    assert d["next_action_owner"] == "human"
    assert d["tool"] == "miniprogram-ci"


def test_wechat_upload_result_maps_to_common_structure(tmp_path):
    # wechat upload 结果带公共结构字段（platform_id / upload_status / status 兼容）
    from platforms.wechat.upload import upload_dev_version
    job, auth = _setup_job(tmp_path, configured=False)
    r = upload_dev_version(job_dir=job, platform_auth_dir=auth)
    assert r["platform_id"] == "wechat"
    assert r["upload_status"] == "not_uploaded"
    assert r["status"] == "not_started"       # 历史兼容
