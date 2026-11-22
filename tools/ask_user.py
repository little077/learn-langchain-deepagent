from langchain_core.tools import tool
from langgraph.types import interrupt


@tool
def ask_user(question: str) -> str:
    """向用户提一个必须由本人回答的问题，并暂停等待回答。

    缺少关键信息（例如姓名、偏好、是否确认）时使用。一次只问一个问题。
    """
    answer = interrupt({"type": "question", "question": question})
    return str(answer)
