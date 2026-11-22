from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.tools import tool


@tool
def get_current_time() -> str:
    """获取当前日期和时间（Asia/Shanghai 时区）。"""
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    weekday = "一二三四五六日"[now.weekday()]
    return f"{now:%Y-%m-%d %H:%M:%S} {now.tzname()} 星期{weekday}"
