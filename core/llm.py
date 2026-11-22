from __future__ import annotations

from .config import get_settings
from .reasoning_chat_model import ReasoningChatModel


def build_model() -> ReasoningChatModel:
    settings = get_settings()
    return ReasoningChatModel(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0,
        timeout=60,
        max_retries=2,
    )
