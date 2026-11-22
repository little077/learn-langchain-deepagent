from __future__ import annotations

from ddgs import DDGS
from langchain_core.tools import tool


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """用网页搜索引擎查找资料。

    query 是搜索关键词；max_results 是最多返回几条（1-10）。
    返回每条结果的标题、链接和摘要。
    """
    limit = max(1, min(int(max_results), 10))
    try:
        results = DDGS().text(
            query,
            region="cn-zh",
            safesearch="moderate",
            max_results=limit,
            backend="bing",
        )
    except Exception as exc:
        raise RuntimeError(
            f"网页搜索失败：{exc}。如果是国内网络问题，可在 .env 里设置 HTTPS_PROXY 后重试。"
        ) from exc

    if not results:
        return f"没有找到与「{query}」相关的结果。"

    lines = []
    for index, item in enumerate(results, start=1):
        title = item.get("title", "").strip()
        href = item.get("href", "").strip()
        body = item.get("body", "").strip()
        lines.append(f"{index}. {title}\n   {href}\n   {body}")
    return "\n".join(lines)
