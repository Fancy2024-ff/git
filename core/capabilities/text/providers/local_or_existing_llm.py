"""text provider：复用项目现有 LLM 封装（core/agents/shared/llm.py）。

configured 取决于 ANTHROPIC_API_KEY；base_url 存在则走中转站。真实可用，非 stub。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from capabilities.base import BaseProvider


class ExistingLLMProvider(BaseProvider):
    is_stub = False

    @property
    def provider_name(self) -> str:
        return "anthropic_proxy" if os.getenv("ANTHROPIC_BASE_URL") else "anthropic"

    def is_configured(self) -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY"))

    def required_env(self) -> list[str]:
        return ["ANTHROPIC_API_KEY"]

    def execute(self, operation: str, **kwargs) -> dict:
        # 延迟导入：USE_LLM=false / 不调用时不引入 langchain
        agents_dir = Path(__file__).resolve().parents[4] / "core" / "agents"
        if str(agents_dir) not in sys.path:
            sys.path.insert(0, str(agents_dir))
        from shared.llm import get_llm

        prompt = kwargs.get("prompt")
        if prompt is None and kwargs.get("messages"):
            prompt = kwargs["messages"]
        llm = get_llm(max_tokens=kwargs.get("max_tokens", 1024))
        resp = llm.invoke(prompt)
        content = resp.content if hasattr(resp, "content") else str(resp)
        if isinstance(content, list):
            content = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
        return {"text": content}
