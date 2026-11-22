from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

from agent.contact_schema import ContactInfo
from core.llm import build_model
from tools.ask_user import ask_user

SYSTEM_PROMPT = """你是一个联系方式收集助手。

规则：
1. 只负责收集姓名、电话、地址三项信息。
2. 缺少哪一项，就调用 ask_user 问哪一项；一次只问一个问题。
3. 不要编造用户没有提供的信息。
4. 三项信息齐全后，调用结构化输出工具返回 ContactInfo。
5. 如果用户一次给了多项，先确认缺失项，再输出结构化结果。
"""


def build_contact_agent(*, model: Any | None = None, checkpointer: Any | None = None):
    return create_agent(
        model=model if model is not None else build_model(),
        tools=[ask_user],
        system_prompt=SYSTEM_PROMPT,
        response_format=ToolStrategy(ContactInfo, handle_errors=True),
        checkpointer=checkpointer,
    )


# langgraph.json 指向这个变量。langgraph dev 会自己管理持久化。
contact_agent = build_contact_agent()
