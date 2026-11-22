from __future__ import annotations

import sys
from uuid import uuid4

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from agent.graph import build_agent


def _reasoning_text(message) -> str:
    parts = []
    for block in getattr(message, "content_blocks", None) or []:
        if block.get("type") == "reasoning" and block.get("reasoning"):
            parts.append(str(block["reasoning"]))
    return "".join(parts)


def _print_answer(result) -> None:
    for message in reversed(result.get("messages", [])):
        if message.type != "ai":
            continue
        text = getattr(message, "text", "") or ""
        if not text:
            continue
        reasoning = _reasoning_text(message)
        if reasoning:
            print(f"\n[思考] {reasoning}")
        print(f"\n助手：{text}")
        return
    print("\n助手：（本轮没有文本回复）")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    graph = build_agent(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": str(uuid4())}}

    print("LangChain 最小示例已启动。输入 exit 退出。")
    while True:
        text = input("\n你：").strip()
        if text.lower() in {"exit", "quit", "q"}:
            print("再见。")
            return
        if not text:
            continue

        result = graph.invoke({"messages": [HumanMessage(content=text)]}, config)

        while "__interrupt__" in result:
            payload = result["__interrupt__"][0].value
            question = (
                payload.get("question", "请补充信息")
                if isinstance(payload, dict)
                else str(payload)
            )
            answer = input(f"\n[需要你回答] {question}\n你：").strip()
            result = graph.invoke(Command(resume=answer), config)

        _print_answer(result)


if __name__ == "__main__":
    main()
