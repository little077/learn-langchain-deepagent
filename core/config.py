from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    llm_temperature: float | None
    llm_max_tokens: int | None
    llm_timeout: int | None
    llm_max_retries: int | None
    llm_enable_thinking: bool | None


_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


def _raw(name: str) -> str:
    return os.getenv(name, "").strip()


def _require(name: str) -> str:
    value = _raw(name)
    if not value:
        raise RuntimeError(f"{name} 还没填。打开项目根目录的 .env，配置好后再运行。")
    return value


def _get_float(name: str) -> float | None:
    value = _raw(name)
    if not value:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} 需要是数字，当前是 {value!r}") from exc


def _get_int(name: str) -> int | None:
    value = _raw(name)
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} 需要是整数，当前是 {value!r}") from exc


def _get_bool(name: str) -> bool | None:
    value = _raw(name).lower()
    if not value:
        return None
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    raise RuntimeError(f"{name} 只能是 true/false，当前是 {value!r}")


def get_settings() -> Settings:
    return Settings(
        llm_api_key=_require("LLM_API_KEY"),
        llm_base_url=_require("LLM_BASE_URL"),
        llm_model=_require("LLM_MODEL"),
        llm_temperature=_get_float("LLM_TEMPERATURE"),
        llm_max_tokens=_get_int("LLM_MAX_TOKENS"),
        llm_timeout=_get_int("LLM_TIMEOUT"),
        llm_max_retries=_get_int("LLM_MAX_RETRIES"),
        llm_enable_thinking=_get_bool("LLM_ENABLE_THINKING"),
    )
