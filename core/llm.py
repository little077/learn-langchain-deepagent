from __future__ import annotations

from typing import Any

from .config import get_settings
from .reasoning_chat_model import ReasoningChatModel


def build_model() -> ReasoningChatModel:
    """按 .env 的模型配置建模型；没配的项不传，交给服务端默认值。"""
    settings = get_settings()
    kwargs: dict[str, Any] = {
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        "timeout": settings.llm_timeout,
        "max_retries": settings.llm_max_retries,
    }
    extra_body: dict[str, Any] = {}
    if settings.llm_enable_thinking is not None:
        extra_body["enable_thinking"] = settings.llm_enable_thinking
    return ReasoningChatModel(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        extra_body=extra_body or None,
        **{k: v for k, v in kwargs.items() if v is not None},
    )
