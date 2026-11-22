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


def get_settings() -> Settings:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "LLM_API_KEY 还没填。打开项目根目录的 .env，填上大模型 API Key 后再运行。"
        )
    return Settings(
        llm_api_key=api_key,
        llm_base_url=os.getenv(
            "LLM_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ).strip(),
        llm_model=os.getenv("LLM_MODEL", "qwen3.7-plus").strip(),
    )
