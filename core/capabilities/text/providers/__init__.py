"""text providers 包。当前 provider：复用现有 LLM（中转站/Anthropic）。"""
from capabilities.text.providers.local_or_existing_llm import ExistingLLMProvider

__all__ = ["ExistingLLMProvider"]
