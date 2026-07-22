"""联网搜索后台任务。"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.search_agent import SearchAgent
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _retry_countdown(retry_count: int) -> int:
    """指数退避：第 n 次重试等待 10 * 2^n 秒。"""
    return 10 * (2 ** retry_count)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def web_search_task(
    self,
    query: str,
    intent: str = "general",
    location: str | None = None,
    top_n: int = 5,
    summarize: bool = True,
) -> dict[str, Any]:
    """异步执行联网搜索。"""
    try:
        agent = SearchAgent()
        result = agent.search(
            query=query,
            intent=intent,
            location=location,
            top_n=top_n,
            summarize=summarize,
        )
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.exception("联网搜索任务失败")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=_retry_countdown(self.request.retries))
        return {"status": "failed", "error": str(exc)}
