"""简历与 JD 解析后台任务。"""

from __future__ import annotations

import base64
import logging
import os
from typing import Any

from app.api.metrics import record_parse_task
from app.services.jd_service import JDService
from app.services.resume_service import ResumeService, should_use_fuzzy_parsing
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _retry_countdown(retry_count: int) -> int:
    """指数退避：第 n 次重试等待 10 * 2^n 秒。"""
    return 10 * (2 ** retry_count)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def parse_resume_text_task(
    self,
    resume_text: str,
    fuzzy: bool | None = None,
    prompt_variant: str | None = None,
    detect_obstacles: bool = True,
) -> dict[str, Any]:
    """异步解析简历文本。"""
    try:
        service = ResumeService()
        actual_fuzzy = (
            fuzzy if fuzzy is not None else should_use_fuzzy_parsing(resume_text, "resume")
        )
        result = service.parse_resume_text(
            resume_text,
            fuzzy=actual_fuzzy,
            prompt_variant=prompt_variant,
        )
        result["fuzzy"] = actual_fuzzy
        if actual_fuzzy and detect_obstacles:
            from app.agents.obstacle_detector import ObstacleDetector

            detector = ObstacleDetector()
            result["obstacles"] = detector.detect_from_resume(result)
        record_parse_task("resume_text", success=True)
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.exception("简历文本解析任务失败")
        record_parse_task("resume_text", success=False)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=_retry_countdown(self.request.retries))
        return {"status": "failed", "error": str(exc)}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def parse_resume_file_task(
    self,
    file_b64: str,
    filename: str,
    fuzzy: bool | None = None,
    prompt_variant: str | None = None,
) -> dict[str, Any]:
    """异步解析简历文件（PDF/DOCX）。"""
    file_bytes = base64.b64decode(file_b64)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".pdf", ".docx"):
        record_parse_task("resume_file", success=False)
        return {"status": "failed", "error": f"不支持的文件格式: {ext}"}

    try:
        service = ResumeService()
        if ext == ".pdf":
            raw_text = service.extract_text_from_pdf(file_bytes)
        else:
            raw_text = service.extract_text_from_docx(file_bytes)

        actual_fuzzy = fuzzy if fuzzy is not None else should_use_fuzzy_parsing(raw_text, "resume")
        result = service.parse_resume_text(
            raw_text,
            fuzzy=actual_fuzzy,
            prompt_variant=prompt_variant,
        )
        result["fuzzy"] = actual_fuzzy
        result["filename"] = filename
        if actual_fuzzy:
            from app.agents.obstacle_detector import ObstacleDetector

            detector = ObstacleDetector()
            result["obstacles"] = detector.detect_from_resume(result)
        record_parse_task("resume_file", success=True)
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.exception("简历文件解析任务失败")
        record_parse_task("resume_file", success=False)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=_retry_countdown(self.request.retries))
        return {"status": "failed", "error": str(exc)}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def parse_jd_text_task(
    self,
    jd_text: str,
    fuzzy: bool | None = None,
    prompt_variant: str | None = None,
) -> dict[str, Any]:
    """异步解析 JD 文本。"""
    try:
        service = JDService()
        actual_fuzzy = fuzzy if fuzzy is not None else should_use_fuzzy_parsing(jd_text, "jd")
        result = service.parse_jd_text(
            jd_text,
            fuzzy=actual_fuzzy,
            prompt_variant=prompt_variant,
        )
        result["fuzzy"] = actual_fuzzy
        record_parse_task("jd_text", success=True)
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.exception("JD 文本解析任务失败")
        record_parse_task("jd_text", success=False)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=_retry_countdown(self.request.retries))
        return {"status": "failed", "error": str(exc)}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def parse_jd_file_task(
    self,
    file_b64: str,
    filename: str,
    fuzzy: bool | None = None,
) -> dict[str, Any]:
    """异步解析 JD 文件（PDF/DOCX/图片）。"""
    file_bytes = base64.b64decode(file_b64)
    ext = filename.split(".")[-1].lower() if "." in filename else ""

    try:
        raw_text = ""
        if ext in ("pdf", "docx", "doc"):
            service = ResumeService()
            raw_text = service._extract_text(file_bytes, filename)
        elif ext in ("png", "jpg", "jpeg", "webp", "gif"):
            from app.config import get_settings

            service = JDService()
            raw_text = service.extract_text_from_image(file_bytes, ext, get_settings())
        else:
            raw_text = file_bytes.decode("utf-8", errors="ignore")

        actual_fuzzy = fuzzy if fuzzy is not None else should_use_fuzzy_parsing(raw_text, "jd")
        service = JDService()
        result = service.parse_jd_text(raw_text, fuzzy=actual_fuzzy)
        result["fuzzy"] = actual_fuzzy
        result["filename"] = filename
        record_parse_task("jd_file", success=True)
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.exception("JD 文件解析任务失败")
        record_parse_task("jd_file", success=False)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=_retry_countdown(self.request.retries))
        return {"status": "failed", "error": str(exc)}
