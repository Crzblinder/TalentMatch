"""岗位匹配后台任务。"""

from __future__ import annotations

import logging
from typing import Any

from app.models.base import SessionLocal
from app.services.matching_service import MatchingService
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _retry_countdown(retry_count: int) -> int:
    """指数退避：第 n 次重试等待 10 * 2^n 秒。"""
    return 10 * (2 ** retry_count)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def match_profile_to_job_task(
    self,
    profile_id: int,
    job_id: int,
    profile_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """异步执行画像与岗位的匹配分析。"""
    db = SessionLocal()
    try:
        service = MatchingService(db)
        match_result = service.match_profile_to_job(
            profile_id=profile_id,
            job_id=job_id,
            profile_override=profile_override,
        )
        return {"status": "success", "data": match_result}
    except Exception as exc:
        logger.exception("匹配任务失败")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=_retry_countdown(self.request.retries))
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def recommend_jobs_task(
    self,
    profile_id: int,
    top_n: int = 20,
) -> dict[str, Any]:
    """异步为画像推荐岗位。"""
    db = SessionLocal()
    try:
        service = MatchingService(db)
        recommendations = service.recommend_jobs(profile_id=profile_id, top_n=top_n)
        return {"status": "success", "data": recommendations}
    except Exception as exc:
        logger.exception("岗位推荐任务失败")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=_retry_countdown(self.request.retries))
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()
