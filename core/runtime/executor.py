"""统一执行器：capability → runtime 真实执行。

复用 capabilities 层 adapter，不重写能力逻辑。统一 6 动作：
create / poll / result / fail / timeout / cleanup。

设计要点（回应"不准假异步/假完成"）：
- 异步能力（image）：create 走 adapter.create_task，poll 走 adapter.poll_task。
- 同步能力（text/utility）：create 即调 adapter.execute，立即落终态（succeeded/failed），
  不伪造 PROCESSING 等待。
- 未接入 provider：create 直接落 FAILED(provider_missing)，绝不假完成。
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_CORE = Path(__file__).resolve().parent.parent  # core/
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from runtime.task_model import Task, TaskState
from runtime import task_store
from runtime.errors import RuntimeErrorCode

# 异步能力：用 create_task/poll_task 任务接口；其余为同步能力
_ASYNC_CAPABILITIES = {"image.process"}

DEFAULT_TIMEOUT_SECONDS = 120


def _adapter(capability_id: str):
    from capabilities.registry import get_adapter
    return get_adapter(capability_id)


def create(capability_id: str, operation: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
           **kwargs) -> Task:
    """创建并启动任务。返回 Task（同步能力会直接是终态）。"""
    task = Task(capability_id=capability_id, operation=operation,
                deadline=time.time() + timeout_seconds)
    adapter = _adapter(capability_id)
    if adapter is None:
        task.provider = "none"
        task.transition(TaskState.FAILED)
        task.error_code = RuntimeErrorCode.NOT_FOUND
        task.error_message = f"未知能力: {capability_id}"
        task_store.save(task)
        return task

    task.provider = adapter.provider_name
    task.attempts += 1

    # 未接入 provider → 直接 FAILED(provider_missing)，绝不假完成
    if not adapter.configured:
        task.transition(TaskState.FAILED)
        task.error_code = RuntimeErrorCode.PROVIDER_MISSING
        task.error_message = (f"{capability_id} 未接入 provider"
                              f"（缺: {', '.join(adapter.validate_config()) or 'provider'}）")
        task_store.save(task)
        return task

    if capability_id in _ASYNC_CAPABILITIES:
        # 异步：交给 adapter 的任务接口
        created = adapter.create_task(operation, kwargs.get("image_ref", ""), **kwargs.get("params", {}))
        if not created.success:
            task.transition(TaskState.FAILED)
            task.error_code = created.error_code or RuntimeErrorCode.PROVIDER_ERROR
            task.error_message = created.message
        else:
            task.transition(TaskState.PROCESSING)
            task.result = {"provider_task_id": created.data.get("task_id")}
        task_store.save(task)
        return task

    # 同步能力：立即执行，直接落终态
    res = adapter.execute(operation, **kwargs)
    if res.success:
        task.transition(TaskState.SUCCEEDED)
        task.result = res.data
    else:
        task.transition(TaskState.FAILED)
        task.error_code = res.error_code or RuntimeErrorCode.PROVIDER_ERROR
        task.error_message = res.message
    task_store.save(task)
    return task


def poll(task_id: str) -> Task | None:
    """轮询任务。处理超时；异步任务查询 provider 状态。"""
    task = task_store.load(task_id)
    if task is None:
        return None
    if task.state in TaskState.TERMINAL:
        return task
    if task.is_timed_out():
        task.transition(TaskState.TIMEOUT)
        task.error_code = RuntimeErrorCode.TIMEOUT
        task.error_message = "任务超时"
        task_store.save(task)
        return task
    # 异步能力：查询 provider
    if task.capability_id in _ASYNC_CAPABILITIES and task.state == TaskState.PROCESSING:
        adapter = _adapter(task.capability_id)
        provider_task_id = task.result.get("provider_task_id", "")
        polled = adapter.poll_task(provider_task_id)
        if polled.success and polled.data.get("status") == "succeeded":
            task.transition(TaskState.SUCCEEDED)
            # 取完整结果（若 adapter 提供 get_result）
            payload = {"result_url": polled.data.get("result_url", "")}
            if hasattr(adapter, "get_result"):
                got = adapter.get_result(provider_task_id)
                if got.success:
                    payload = {**payload, **got.data}
            task.result = {
                **task.result, **payload,
                "operation": task.operation, "provider": task.provider,
                "finished_at": time.time(),
            }
            task_store.save(task)
        elif polled.success and polled.data.get("status") == "failed":
            # 上游业务状态明确失败：立即落 FAILED，保留真实错误，不要白等到超时
            task.transition(TaskState.FAILED)
            task.error_code = polled.data.get("error_code") or RuntimeErrorCode.PROVIDER_ERROR
            task.error_message = (polled.data.get("error_message")
                                  or polled.message or "provider 处理失败")
            task_store.save(task)
        elif not polled.success:
            task.transition(TaskState.FAILED)
            task.error_code = polled.error_code or RuntimeErrorCode.PROVIDER_ERROR
            task.error_message = polled.message
            task_store.save(task)
    return task


def result(task_id: str) -> dict | None:
    """取已完成任务的结果。未完成/不存在返回 None。"""
    task = task_store.load(task_id)
    if task is None or task.state != TaskState.SUCCEEDED:
        return None
    return task.result


def fail(task_id: str, error_message: str, error_code: str = RuntimeErrorCode.PROVIDER_ERROR) -> Task | None:
    task = task_store.load(task_id)
    if task is None:
        return None
    if task.state not in TaskState.TERMINAL:
        task.transition(TaskState.FAILED)
        task.error_code = error_code
        task.error_message = error_message
        task_store.save(task)
    return task


def timeout(task_id: str) -> Task | None:
    task = task_store.load(task_id)
    if task is None:
        return None
    if task.state not in TaskState.TERMINAL:
        task.transition(TaskState.TIMEOUT)
        task.error_code = RuntimeErrorCode.TIMEOUT
        task.error_message = "任务超时"
        task_store.save(task)
    return task


def cleanup(task_id: str | None = None) -> int:
    """清理任务。给 task_id 清单个，否则清全部临时任务。返回清理数。"""
    if task_id:
        task = task_store.load(task_id)
        if task and task.state in (TaskState.SUCCEEDED, TaskState.FAILED, TaskState.TIMEOUT):
            task.transition(TaskState.CLEANED)
        return 1 if task_store.delete(task_id) else 0
    return task_store.cleanup_all()
