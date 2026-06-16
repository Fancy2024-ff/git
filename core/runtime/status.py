"""Runtime 执行报告：把能力执行就绪状态写成 artifact 可消费结构。

核心诚实区分（回应追问 2/4）：
- capability_runtime：工厂侧能否执行该能力（text=是, utility.calculate=是, image=否/缺provider）
- app_runtime：生成出来的小程序自身能否真跑（当前全部 false——生成的页面仍调用未实现的 /api/*）
不把"工厂能调 LLM"冒充"text_ai 小程序能跑"；不把单个 calculate 当整个 utility 品类成熟。
"""

from __future__ import annotations

import sys
from pathlib import Path

_CORE = Path(__file__).resolve().parent.parent
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from runtime.task_model import TaskState


# 每个能力当前在工厂侧真正能执行的 operation（精确到 operation，不夸大品类）
_CAPABILITY_RUNTIME_OPS = {
    "text.generate": ["generate", "chat", "summarize", "translate"],   # LLM 已接
    "utility.execute": ["calculate"],                                   # 仅 calculate 本地实现；convert/query 占位
    # image/vision/speech/video：未接 provider，运行就绪 op 为空
}


def _capability_runtime(capability_id: str, configured: bool) -> dict:
    """工厂侧该能力可执行的 operation。未配置 → 空 + 诚实标注。"""
    if not configured:
        return {"executable_operations": [], "note": "provider 未接入，工厂侧无法执行"}
    # image：可执行 operation 由 provider 真接通的决定（本轮 remove_background）
    if capability_id == "image.process":
        try:
            from capabilities.registry import get_adapter
            adapter = get_adapter("image.process")
            ops = adapter.truly_connected_operations() if hasattr(adapter, "truly_connected_operations") else []
        except Exception:
            ops = []
        return {"executable_operations": ops,
                "note": f"provider 已接入，真接通 operation: {ops}" if ops else "provider 已接入但无真接通 operation"}
    ops = _CAPABILITY_RUNTIME_OPS.get(capability_id, [])
    note = "已可执行" if ops else "provider 已配置但未声明可执行 operation"
    if capability_id == "utility.execute":
        note = "仅 calculate 为本地真实实现；convert/query 为占位，未实现"
    return {"executable_operations": ops, "note": note}


def build_execution_report(app_type: str) -> dict:
    """产出 runtime-execution-report.json 的内容。永不抛异常。"""
    try:
        from capabilities.registry import build_capability_snapshot, get_adapter
        snap = build_capability_snapshot(app_type)
        required = snap.get("required_capabilities", [])
        configured = snap.get("configured_capabilities", [])
        missing = snap.get("missing_capabilities", [])
        runnable_level = snap.get("runnable_level", "buildable")

        cap_runtime = {}
        for cap in required:
            adapter = get_adapter(cap)
            is_conf = bool(adapter and adapter.configured)
            cap_runtime[cap] = _capability_runtime(cap, is_conf)
    except Exception as e:
        return {
            "app_type": app_type, "error": f"{type(e).__name__}: {str(e)[:200]}",
            "required_capabilities": [], "configured_capabilities": [],
            "missing_capabilities": [], "runnable_level": "buildable",
            "capability_runtime": {}, "app_runtime": {"runnable": False, "reason": "report 构建异常"},
            "task_model": _task_model_spec(),
        }

    return {
        "app_type": app_type,
        "required_capabilities": required,
        "configured_capabilities": configured,
        "missing_capabilities": missing,
        "runnable_level": runnable_level,
        # 工厂侧能力执行就绪（精确到 operation）
        "capability_runtime": cap_runtime,
        # 生成的小程序自身运行就绪（按 app_type + provider 真实判断）
        "app_runtime": _app_runtime(app_type, cap_runtime, missing),
        # runtime 任务模型声明（供 image/OCR/speech/video 复用同一模式）
        "task_model": _task_model_spec(),
    }


def _app_runtime(app_type: str, cap_runtime: dict, missing: list[str]) -> dict:
    """生成的小程序自身是否能真跑。

    image_ai：当 image.process 已接入且有真接通 operation（remove_background）时 = true，
    因为生成的小程序前端已真实调用 runtime image API（create/poll/result）。
    其余 app_type：前端尚未真实接 runtime，保持 false 并说明。
    """
    if app_type == "image_ai":
        img = cap_runtime.get("image.process", {})
        if "image.process" not in missing and img.get("executable_operations"):
            return {
                "runnable": True,
                "operations": img.get("executable_operations", []),
                "reason": ("image provider 已接入，生成的小程序前端通过 /api/runtime/image/tasks "
                           "真实调用 create→poll→result，可真跑 remove_background。"),
            }
        return {
            "runnable": False,
            "reason": ("image 能力未接入 provider（配置 IMAGE_API_BASE+IMAGE_API_KEY 或 IMAGE_PROVIDER=mock）；"
                       "未接入前生成的小程序可上架但不能真跑。"),
        }
    return {
        "runnable": False,
        "reason": ("生成的小程序为可构建/可上架骨架，其前端调用的能力接口尚未真实接 runtime；"
                   "本轮仅打通 image_ai。"),
    }


def _task_model_spec() -> dict:
    """声明 runtime 任务模型，证明 OCR/speech/video 可复用同一套。"""
    return {
        "states": list(TaskState.ALL),
        "actions": ["create", "poll", "result", "fail", "timeout", "cleanup"],
        "async_capabilities": ["image.process"],
        "note": "异步能力走 create→poll→result；同步能力 create 即落终态。新增慢能力复用此模型。",
    }
