"""Celery 应用配置。"""

from __future__ import annotations

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "talentmatch",
    broker=settings.redis_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.parse_tasks",
        "app.tasks.match_tasks",
        "app.tasks.search_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 分钟硬限制
    task_soft_time_limit=300,  # 5 分钟软限制
    result_expires=3600 * 24,  # 任务结果保留 24 小时
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=settings.celery_task_always_eager,
    # 默认重试策略：指数退避，最多 3 次
    task_default_retry_delay=10,
    task_max_retries=3,
    broker_connection_retry_on_startup=True,
)
