"""text.generate adapter —— 真实能力（复用现有 LLM）。"""

from __future__ import annotations

from capabilities.base import BaseAdapter
from capabilities.text.providers.local_or_existing_llm import ExistingLLMProvider


class TextAdapter(BaseAdapter):
    capability_name = "text.generate"
    display_name = "文本生成"
    supported_operations = ["generate", "chat", "summarize", "translate"]

    def __init__(self, provider=None):
        super().__init__(provider or ExistingLLMProvider())

    def _notes(self) -> str:
        return "最成熟能力，复用现有 LLM（中转站/Anthropic），配置 ANTHROPIC_API_KEY 即 runtime_ready。"
