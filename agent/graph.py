from __future__ import annotations

from typing import Any

from langchain.agents import create_agent

from core.llm import build_model
from tools import ALL_TOOLS

SYSTEM_PROMPT = """你是一个简洁、可靠的中文助手。

规则：
1. 需要用户本人提供信息时，调用 ask_user，不要替用户猜。
2. 涉及“现在几点/今天几号”时，调用 get_current_time。
3. 涉及最新消息、你不确定或需要外部资料时，调用 web_search。
4. 工具返回结果后，用中文直接回答；引用网页时保留链接。
5. 不要编造工具没有返回的事实。
"""


def build_agent(*, model: Any | None = None, checkpointer: Any | None = None):
    return create_agent(
        model=model if model is not None else build_model(),
        tools=ALL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )


# langgraph.json 指向这个变量。langgraph dev 会自己管理持久化，所以这里不传 checkpointer。
graph = build_agent()
