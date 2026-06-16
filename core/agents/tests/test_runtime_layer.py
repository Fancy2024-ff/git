"""Runtime 执行层测试：任务模型 + 执行器 + 执行报告 + 消费链。"""

import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
for p in (REPO_ROOT / "core", REPO_ROOT / "core" / "agents"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


@pytest.fixture(autouse=True)
def _clean_tasks():
    from runtime import task_store
    task_store.cleanup_all()
    yield
    task_store.cleanup_all()


# ── 任务模型 ──

def test_task_state_machine_legal_and_illegal():
    from runtime.task_model import Task, TaskState, can_transition
    assert can_transition(TaskState.CREATED, TaskState.PROCESSING)
    assert can_transition(TaskState.PROCESSING, TaskState.SUCCEEDED)
    assert can_transition(TaskState.SUCCEEDED, TaskState.CLEANED)
    assert not can_transition(TaskState.SUCCEEDED, TaskState.PROCESSING)
    assert not can_transition(TaskState.CLEANED, TaskState.SUCCEEDED)
    t = Task(capability_id="x", operation="y")
    t.transition(TaskState.PROCESSING)
    with pytest.raises(ValueError):
        t.transition(TaskState.CREATED)  # 非法回退


def test_task_timeout_detection():
    from runtime.task_model import Task, TaskState
    t = Task(capability_id="x", operation="y", deadline=time.time() - 1)
    assert t.is_timed_out() is True
    t.transition(TaskState.SUCCEEDED)
    assert t.is_timed_out() is False  # 终态不再超时


# ── 执行器：同步能力（utility 本地，不依赖网络）──

def test_executor_utility_calculate_succeeds():
    from runtime import executor
    from runtime.task_model import TaskState
    t = executor.create("utility.execute", "calculate", args={"a": 2, "b": 3, "op": "add"})
    assert t.state == TaskState.SUCCEEDED
    assert t.result["result"] == 5
    assert executor.result(t.task_id) == t.result


def test_executor_unknown_capability_fails():
    from runtime import executor
    from runtime.task_model import TaskState
    from runtime.errors import RuntimeErrorCode
    t = executor.create("nope.nope", "x")
    assert t.state == TaskState.FAILED
    assert t.error_code == RuntimeErrorCode.NOT_FOUND


# ── 执行器：image 未配置 → 绝不假完成 ──

def test_executor_image_unconfigured_fails_honestly(monkeypatch):
    monkeypatch.delenv("IMAGE_API_KEY", raising=False)
    monkeypatch.delenv("IMAGE_API_BASE", raising=False)
    from runtime import executor
    from runtime.task_model import TaskState
    from runtime.errors import RuntimeErrorCode
    t = executor.create("image.process", "id_photo", image_ref="x.jpg")
    assert t.state == TaskState.FAILED           # 不是 processing/succeeded
    assert t.error_code == RuntimeErrorCode.PROVIDER_MISSING
    assert executor.result(t.task_id) is None     # 无假结果


# ── 执行器：image 配置后走真实任务模型（mock env）──

def test_executor_image_configured_runs_task_model(monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "mock")
    from runtime import executor
    from runtime.task_model import TaskState
    t = executor.create("image.process", "remove_background", image_ref="x.jpg")
    assert t.state == TaskState.PROCESSING
    assert t.result.get("provider_task_id")
    polled = executor.poll(t.task_id)
    assert polled.state == TaskState.SUCCEEDED
    assert executor.result(t.task_id) is not None


# ── 执行器：超时 + 清理 ──

def test_executor_timeout_and_cleanup(monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "mock")
    from runtime import executor, task_store
    from runtime.task_model import TaskState
    t = executor.create("image.process", "remove_background", image_ref="x.jpg", timeout_seconds=0)
    # deadline 已过 → poll 判定 timeout
    time.sleep(0.01)
    polled = executor.poll(t.task_id)
    assert polled.state == TaskState.TIMEOUT
    assert executor.cleanup(t.task_id) == 1
    assert task_store.load(t.task_id) is None


# ── 执行报告：capability_runtime vs app_runtime 诚实区分 ──

def test_execution_report_distinguishes_factory_vs_app_runtime(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    from runtime.status import build_execution_report
    r = build_execution_report("text_ai")
    # 工厂侧 text 可执行
    assert r["capability_runtime"]["text.generate"]["executable_operations"]
    # 但生成的小程序自身不能真跑（不偷换概念）
    assert r["app_runtime"]["runnable"] is False
    assert "task_model" in r


def test_execution_report_utility_operation_precision(monkeypatch):
    from runtime.status import build_execution_report
    r = build_execution_report("utility_tool")
    cr = r["capability_runtime"]["utility.execute"]
    # 仅 calculate 算真实实现，不把整品类标成熟
    assert cr["executable_operations"] == ["calculate"]
    assert "calculate" in cr["note"]


def test_execution_report_image_not_runtime(monkeypatch):
    monkeypatch.delenv("IMAGE_API_KEY", raising=False)
    monkeypatch.delenv("IMAGE_API_BASE", raising=False)
    from runtime.status import build_execution_report
    r = build_execution_report("image_ai")
    assert r["runnable_level"] == "buildable"
    assert r["missing_capabilities"] == ["image.process"]
    # 接口范式成立，但工厂侧无可执行 operation（诚实）
    assert r["capability_runtime"]["image.process"]["executable_operations"] == []


# ── 消费链：report → 可序列化为 artifact 结构 ──

def test_execution_report_is_artifact_serializable():
    import json
    from runtime.status import build_execution_report
    r = build_execution_report("text_ai")
    s = json.dumps(r, ensure_ascii=False)  # 必须可序列化（落 artifact / API 返回）
    back = json.loads(s)
    assert set(["app_type", "required_capabilities", "configured_capabilities",
                "missing_capabilities", "runnable_level", "capability_runtime",
                "app_runtime", "task_model"]).issubset(back.keys())
