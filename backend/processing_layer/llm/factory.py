import os

from .base import LLMProvider


def get_provider(name: str | None = None) -> LLMProvider:
    provider_name = name or os.environ.get("LLM_PROVIDER", "gemini")
    if provider_name == "gemini":
        from .gemini import GeminiProvider
        return GeminiProvider()
    if provider_name == "claude":
        from .claude import ClaudeProvider
        return ClaudeProvider()
    raise ValueError(f"Unknown provider: {provider_name!r}")
