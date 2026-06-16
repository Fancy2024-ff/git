"""真实 image 能力接入 + runtime 链路测试。

provider / adapter / executor / API / 模板代码 / 端到端，覆盖真实接入路径
（用 mock provider 跑 CI，但代码路径与 http provider 一致）。
"""

import os
import sys
import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
for p in (REPO_ROOT / "core", REPO_ROOT / "core" / "agents"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    from runtime import task_store
    task_store.cleanup_all()
    for k in ("IMAGE_PROVIDER", "IMAGE_API_KEY", "IMAGE_API_BASE"):
        monkeypatch.delenv(k, raising=False)
    yield
    task_store.cleanup_all()


# ── provider 配置 ──

def test_http_provider_unconfigured_is_provider_missing():
    from integrations.image_providers import get_image_provider
    p = get_image_provider()   # 默认 http，无 env
    assert p.is_configured() is False
    assert "IMAGE_API_BASE" in p.missing_env()


def test_http_provider_configured_with_env(monkeypatch):
    monkeypatch.setenv("IMAGE_API_BASE", "https://img.example.com")
    monkeypatch.setenv("IMAGE_API_KEY", "k")
    from integrations.image_providers import get_image_provider
    p = get_image_provider()
    assert p.name == "http"
    assert p.is_configured() is True


def test_http_provider_non_json_response_maps_to_upstream_error(monkeypatch):
    """上游返回 200 但 body 非 JSON（网关 HTML/空体）：必须映射成 ImageProviderError，不得击穿成 ValueError。"""
    import httpx
    monkeypatch.setenv("IMAGE_API_BASE", "https://img.example.com")
    monkeypatch.setenv("IMAGE_API_KEY", "k")
    from integrations.image_providers.http_provider import HttpImageProvider
    from integrations.image_providers.errors import ImageProviderError, ImageErrorCode

    class _Resp:
        status_code = 200
        def json(self):
            raise ValueError("not json")  # 模拟 HTML/空体

    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Resp())
    p = HttpImageProvider()
    with pytest.raises(ImageProviderError) as ei:
        p.create_task("remove_background", "photo.jpg")
    assert ei.value.code == ImageErrorCode.UPSTREAM_ERROR


def test_http_provider_poll_id_is_url_encoded(monkeypatch):
    """上游返回的 task_id 含特殊字符时，poll URL 必须编码，不能改变请求路径。"""
    import httpx
    monkeypatch.setenv("IMAGE_API_BASE", "https://img.example.com")
    monkeypatch.setenv("IMAGE_API_KEY", "k")
    from integrations.image_providers.http_provider import HttpImageProvider

    captured = {}

    class _Resp:
        status_code = 200
        def json(self):
            return {"status": "processing"}

    def _get(url, *a, **k):
        captured["url"] = url
        return _Resp()

    monkeypatch.setattr(httpx, "get", _get)
    p = HttpImageProvider()
    p.poll_task("../../etc/passwd")
    assert "../../etc/passwd" not in captured["url"]
    assert "%2F" in captured["url"] or "%2E" in captured["url"]


def test_mock_provider_full_lifecycle(monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "mock")
    from integrations.image_providers import get_image_provider
    p = get_image_provider()
    assert p.is_configured() is True
    t = p.create_task("remove_background", "photo.jpg")
    assert t.provider_task_id
    res = p.get_result(t.provider_task_id)
    assert res["result_url"].startswith("mock://")


# ── adapter ──

def test_image_adapter_operations_and_truly_connected(monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "mock")
    from capabilities.image import ImageAdapter
    a = ImageAdapter()
    assert a.supported_operations == ["remove_background", "id_photo", "avatar_style", "enhance"]
    assert a.truly_connected_operations() == ["remove_background"]
    assert a.configured is True


def test_image_adapter_unsupported_operation_honest(monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "mock")
    from capabilities.image import ImageAdapter
    a = ImageAdapter()
    # id_photo 接口在，但本轮 provider 未接通 → provider_unsupported（诚实）
    r = a.create_task("id_photo", "x.jpg")
    assert r.success is False
    assert r.error_code == "provider_unsupported"


def test_image_adapter_unconfigured_provider_missing():
    from capabilities.image import ImageAdapter
    a = ImageAdapter()
    assert a.configured is False
    r = a.create_task("remove_background", "x.jpg")
    assert r.success is False
    assert r.error_code == "provider_missing"


# ── executor 真实执行 ──

def test_executor_image_real_lifecycle_with_mock(monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "mock")
    from runtime import executor
    from runtime.task_model import TaskState
    t = executor.create("image.process", "remove_background", image_ref="photo.jpg")
    assert t.state == TaskState.PROCESSING
    polled = executor.poll(t.task_id)
    assert polled.state == TaskState.SUCCEEDED
    res = executor.result(t.task_id)
    assert res["result_url"].startswith("mock://")
    assert res["operation"] == "remove_background"
    assert res["provider"] == "mock"
    assert "finished_at" in res


# ── API ──

def _load_api(monkeypatch):
    monkeypatch.setenv("DASHBOARD_API_KEY", "t")
    spec = importlib.util.spec_from_file_location("api_img", REPO_ROOT / "apps" / "api" / "main.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    from fastapi.testclient import TestClient
    return TestClient(m.app)


def test_api_image_task_lifecycle_mock(monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "mock")
    client = _load_api(monkeypatch)
    h = {"X-API-Key": "t"}
    r = client.post("/api/runtime/image/tasks",
                    json={"operation": "remove_background", "source": "photo.jpg"}, headers=h)
    assert r.status_code == 200
    tid = r.json()["task_id"]
    assert tid
    poll = client.get(f"/api/runtime/image/tasks/{tid}", headers=h)
    assert poll.json()["status"] == "succeeded"
    res = client.get(f"/api/runtime/image/tasks/{tid}/result", headers=h)
    assert res.json()["result"]["result_url"].startswith("mock://")


def test_api_image_provider_missing(monkeypatch):
    client = _load_api(monkeypatch)   # 无 IMAGE_PROVIDER → http 未配置
    h = {"X-API-Key": "t"}
    r = client.post("/api/runtime/image/tasks",
                    json={"operation": "remove_background", "source": "x.jpg"}, headers=h)
    assert r.status_code == 200
    assert r.json()["error_code"] == "provider_missing"


def test_api_image_requires_auth(monkeypatch):
    client = _load_api(monkeypatch)
    r = client.post("/api/runtime/image/tasks", json={"operation": "remove_background"})
    assert r.status_code == 401


def test_api_image_rejects_unsafe_source(monkeypatch):
    """恶意 source（file:// / 云元数据）应被入口校验挡成 400，不进入 executor/provider。"""
    monkeypatch.setenv("IMAGE_PROVIDER", "mock")
    client = _load_api(monkeypatch)
    h = {"X-API-Key": "t"}
    for bad in ("file:///etc/passwd", "https://169.254.169.254/meta", "http://10.0.0.1/x"):
        r = client.post("/api/runtime/image/tasks",
                        json={"operation": "remove_background", "source": bad}, headers=h)
        assert r.status_code == 400, f"{bad} 应被拒"


# ── execution report 双层 ──

def test_execution_report_image_app_runtime_true_with_mock(monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "mock")
    from runtime.status import build_execution_report
    r = build_execution_report("image_ai")
    assert r["runnable_level"] == "runtime_ready"
    assert r["capability_runtime"]["image.process"]["executable_operations"] == ["remove_background"]
    assert r["app_runtime"]["runnable"] is True


def test_execution_report_image_false_without_provider():
    from runtime.status import build_execution_report
    r = build_execution_report("image_ai")
    assert r["app_runtime"]["runnable"] is False
    assert r["missing_capabilities"] == ["image.process"]


# ── 回归：上游 poll 返回 "failed" 应立即落 FAILED，不白等到超时 ──

def test_executor_poll_provider_failed_transitions_to_failed(monkeypatch):
    """provider HTTP 通但业务状态 failed：任务应立即 FAILED（携带真实错误），而非卡到 timeout。"""
    monkeypatch.setenv("IMAGE_PROVIDER", "mock")
    from runtime import executor
    from runtime.task_model import TaskState
    from capabilities.schemas import CapabilityResult
    from capabilities.status import CapabilityStatus

    t = executor.create("image.process", "remove_background", image_ref="photo.jpg")
    assert t.state == TaskState.PROCESSING

    # 让 adapter.poll_task 返回 success=True 但 status=failed（模拟上游处理失败）
    adapter = executor._adapter("image.process")

    def _poll_failed(provider_task_id):
        return CapabilityResult(
            capability_id="image.process", operation="poll", success=True,
            status=CapabilityStatus.CONFIGURED, provider="mock",
            data={"task_id": provider_task_id, "status": "failed",
                  "error_code": "upstream_error", "error_message": "上游处理失败"},
        )

    monkeypatch.setattr(adapter, "poll_task", _poll_failed)
    polled = executor.poll(t.task_id)
    assert polled.state == TaskState.FAILED
    assert polled.error_code == "upstream_error"
    assert "上游处理失败" in polled.error_message


# ── 回归：task_store 对损坏/未知字段文件容错，不抛 500 ──

def test_task_store_load_corrupt_file_returns_none(monkeypatch):
    from runtime import task_store
    from runtime.task_model import Task
    t = Task(capability_id="image.process", operation="remove_background")
    task_store.save(t)
    # 写入半截/损坏内容
    p = task_store._task_path(t.task_id)
    p.write_text("{ not valid json", encoding="utf-8")
    assert task_store.load(t.task_id) is None  # 不抛异常


def test_task_store_load_ignores_unknown_fields(monkeypatch):
    """旧 schema 写入的多余字段不应导致 Task(**data) 崩溃。"""
    import json
    from runtime import task_store
    from runtime.task_model import Task
    t = Task(capability_id="image.process", operation="remove_background")
    task_store.save(t)
    p = task_store._task_path(t.task_id)
    data = json.loads(p.read_text(encoding="utf-8"))
    data["legacy_field_removed_in_new_schema"] = "x"  # 模拟 schema 演进
    p.write_text(json.dumps(data), encoding="utf-8")
    loaded = task_store.load(t.task_id)
    assert loaded is not None
    assert loaded.task_id == t.task_id
    assert not hasattr(loaded, "legacy_field_removed_in_new_schema")
