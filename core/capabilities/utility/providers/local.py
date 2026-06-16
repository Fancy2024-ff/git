"""utility 本地 provider：无需外部 API，runtime_ready 样板。

提供最小可用的本地实现（计算/转换/查询）。这类能力不依赖任何 provider key。
"""

from __future__ import annotations

from capabilities.base import BaseProvider


class LocalUtilityProvider(BaseProvider):
    is_stub = False
    provider_name = "local"

    def is_configured(self) -> bool:
        return True  # 本地能力，永远可用

    def required_env(self) -> list[str]:
        return []

    def execute(self, operation: str, **kwargs) -> dict:
        args = kwargs.get("args", {}) or {}
        if operation == "calculate":
            a = float(args.get("a", 0) or 0)
            b = float(args.get("b", 0) or 0)
            op = args.get("op", "add")
            result = {"add": a + b, "sub": a - b, "mul": a * b,
                      "div": (a / b if b else None)}.get(op, a + b)
            return {"result": result}
        if operation == "convert":
            # 占位：单位换算示例（真实换算表按需扩展）
            return {"result": args.get("value"), "note": "convert 本地逻辑按需扩展"}
        if operation == "query":
            return {"result": None, "note": "query 本地逻辑按需扩展"}
        return {"result": None}
