"""文本能力 adapter —— 真实可用（复用 shared/llm.py，中转站已通）。"""

from __future__ import annotations

import os

from capabilities.base import BaseAdapter, CapabilityResult


class TextAdapter(BaseAdapter):
    capability_id = "text.generate"
    name_cn = "文本生成"
    supported_operations = ["generate", "chat", "summarize", "translate"]
    automation_level = "full_automatic"

    def provider_name(self) -> str:
        # 有 base_url 视为中转站，否则官方 anthropic
        return "anthropic_proxy" if os.getenv("ANTHROPIC_BASE_URL") else "anthropic"

    def is_configured(self) -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY"))

    def config_requirements(self) -> list[str]:
        return [] if self.is_configured() else ["ANTHROPIC_API_KEY"]

    def _run(self, operation: str, **kwargs) -> CapabilityResult:
        prompt = kwargs.get("prompt", "")
        try:
            import sys
            from pathlib import Path
            agents_dir = Path(__file__).resolve().parent.parent.parent / "core" / "agents"
            if str(agents_dir) not in sys.path:
                sys.path.insert(0, str(agents_dir))
            from shared.llm import get_llm
            llm = get_llm(max_tokens=kwargs.get("max_tokens", 1024))
            resp = llm.invoke(prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)
            if isinstance(content, list):
                content = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
            return CapabilityResult(
                capability_id=self.capability_id, operation=operation, ok=True,
                configured=True, provider=self.provider_name(), data={"text": content},
            )
        except Exception as e:
            return CapabilityResult(
                capability_id=self.capability_id, operation=operation, ok=False,
                configured=True, provider=self.provider_name(),
                error=f"{type(e).__name__}: {str(e)[:200]}",
            )
