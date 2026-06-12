"""LLM client wrapper for consistent usage across agents."""

from langchain_anthropic import ChatAnthropic
from config.settings import ANTHROPIC_API_KEY, LLM_MODEL, LLM_TEMPERATURE


def get_llm(
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int = 4096,
) -> ChatAnthropic:
    """Get a configured LLM instance."""
    return ChatAnthropic(
        model=model or LLM_MODEL,
        api_key=ANTHROPIC_API_KEY,
        temperature=temperature if temperature is not None else LLM_TEMPERATURE,
        max_tokens=max_tokens,
    )
