"""定时任务调度器。

提供基于 APScheduler BackgroundScheduler 的岗位定时采集任务，
支持启动、关闭以及手动触发单次采集。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.crawler.scraper import JobScraper, save_jobs

logger = logging.getLogger(__name__)

# 全局调度器实例（懒加载）
_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    """获取或创建全局调度器实例。"""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


def fetch_jobs_job() -> dict[str, Any]:
    """定时采集岗位任务。

    实例化 JobScraper 遍历所有 RSS 源，去重后保存到 raw_jobs.json。
    单个源失败已被 scraper 内部捕获，本函数再做最后一层保护，
    确保任何异常都不会导致调度器线程中断。
    """
    # 配置校验可在需要时从 get_settings() 读取；当前任务不依赖动态配置
    logger.info("开始执行定时岗位采集任务...")

    try:
        # BackgroundScheduler 在独立线程中运行，需要新建事件循环执行异步爬虫
        jobs = asyncio.run(_run_scraper())
        save_jobs(jobs)
        logger.info("定时岗位采集完成，共 %d 条岗位已保存", len(jobs))
        return {
            "success": True,
            "fetched": len(jobs),
        }
    except Exception as exc:
        # 失败时记录 warning，不影响其他源或下一次调度
        logger.warning("定时岗位采集任务执行失败: %s", exc, exc_info=True)
        return {
            "success": False,
            "error": str(exc),
        }


async def _run_scraper() -> list[dict[str, Any]]:
    """异步运行 JobScraper 并返回采集结果。"""
    scraper = JobScraper()
    return await scraper.fetch_all()


def start_scheduler() -> BackgroundScheduler | None:
    """启动定时采集调度器。

    仅当 scheduler_enabled 为 true 时才会真正启动，避免开发环境意外运行。
    """
    settings = get_settings()
    if not settings.scheduler_enabled:
        logger.info("scheduler_enabled 为 false，跳过启动定时任务")
        return None

    scheduler = get_scheduler()
    if scheduler.running:
        logger.info("调度器已在运行中")
        return scheduler

    # 按配置的小时间隔添加岗位采集任务
    scheduler.add_job(
        fetch_jobs_job,
        trigger=IntervalTrigger(hours=settings.fetch_interval_hours),
        id="fetch_jobs_job",
        name="定时岗位采集",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "定时岗位采集调度器已启动，每 %d 小时执行一次",
        settings.fetch_interval_hours,
    )
    return scheduler


def shutdown_scheduler() -> None:
    """关闭调度器并释放资源。"""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("定时岗位采集调度器已关闭")
    _scheduler = None


def trigger_fetch_jobs() -> dict[str, Any]:
    """手动触发一次岗位采集任务。"""
    return fetch_jobs_job()
