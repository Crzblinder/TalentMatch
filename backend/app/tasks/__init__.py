"""后台异步任务包。"""

from app.tasks.celery_app import celery_app
from app.tasks.match_tasks import match_profile_to_job_task
from app.tasks.parse_tasks import (
    parse_jd_file_task,
    parse_jd_text_task,
    parse_resume_file_task,
    parse_resume_text_task,
)
from app.tasks.search_tasks import web_search_task

__all__ = [
    "celery_app",
    "parse_resume_text_task",
    "parse_resume_file_task",
    "parse_jd_text_task",
    "parse_jd_file_task",
    "match_profile_to_job_task",
    "web_search_task",
]
