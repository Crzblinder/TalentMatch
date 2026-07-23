"""健康检查实现。

聚合数据库、Redis、向量库、LLM、搜索等外部依赖状态，
支持 /health/live、/health/ready 与详细 /health 端点。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.api.metrics import record_health_check
from app.config import Settings, get_settings
from app.services.cache_service import get_cache_stats
from app.utils.config_tester import ConfigTestResult, run_config_tests

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """单个依赖项健康状态。"""

    name: str
    status: str  # ok | fail | skip
    message: str
    response_time_ms: float = 0.0
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthReport:
    """完整健康报告。"""

    status: str
    checked_at: str
    checks: list[HealthStatus]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_redis_check() -> HealthStatus:
    """检查 Redis / 缓存后端是否可用。"""
    start = time.perf_counter()
    try:
        stats = get_cache_stats()
        elapsed = (time.perf_counter() - start) * 1000
        backend = stats.get("backend", "unknown")
        redis_available = stats.get("redis_available", False)
        message = f"缓存后端 {backend} 可用"
        if not redis_available:
            message = "Redis 不可用，已降级到内存缓存"
        return HealthStatus(
            name="redis",
            status="ok",
            message=message,
            response_time_ms=round(elapsed, 2),
            detail=stats,
        )
    except Exception as exc:  # noqa: BLE001
        elapsed = (time.perf_counter() - start) * 1000
        return HealthStatus(
            name="redis",
            status="fail",
            message=f"Redis 检查失败: {exc}",
            response_time_ms=round(elapsed, 2),
        )


def _config_result_to_health(result: ConfigTestResult) -> HealthStatus:
    """将 ConfigTestResult 转换为 HealthStatus。"""
    return HealthStatus(
        name=result.name,
        status=result.status,
        message=result.message,
        response_time_ms=result.response_time_ms,
        detail=result.detail,
    )


def run_health_checks(settings: Settings | None = None) -> HealthReport:
    """运行完整健康检查并返回聚合报告。"""
    if settings is None:
        settings = get_settings()

    checks: list[HealthStatus] = []

    # 复用 config_tester 检测数据库、向量库、LLM、搜索
    config_report = run_config_tests(settings)

    # 数据库
    db_results = [r for r in config_report.results if r.category == "database"]
    checks.extend(_config_result_to_health(r) for r in db_results)

    # 向量库
    vector_results = [r for r in config_report.results if r.category == "vector"]
    checks.extend(_config_result_to_health(r) for r in vector_results)

    # Redis
    checks.append(_run_redis_check())

    # LLM：取第一个配置为 ok 的结果作为可用 LLM；全部未配置或失败则标记失败
    llm_results = [r for r in config_report.results if r.category == "llm"]
    configured_llm = [r for r in llm_results if r.configured]
    ok_llm = [r for r in configured_llm if r.status == "ok"]

    # Ollama 是无需 API Key 的本地 LLM 兜底；如果用户没有配置任何云端 LLM Key，
    # 其失败不应导致整体健康状态为 fail（系统会降级到规则引擎）。
    no_cloud_llm_configured = not any(
        [
            settings.openai_api_key,
            settings.dashscope_api_key,
            settings.zhipu_api_key,
        ]
    )
    only_fallback_ollama = (
        len(configured_llm) == 1
        and configured_llm[0].name == "Ollama 本地 LLM"
    )

    if ok_llm:
        checks.append(
            HealthStatus(
                name="llm",
                status="ok",
                message=f"可用 LLM: {ok_llm[0].name}",
                detail={"available": [r.name for r in ok_llm]},
            )
        )
    elif configured_llm:
        if only_fallback_ollama and no_cloud_llm_configured:
            checks.append(
                HealthStatus(
                    name="llm",
                    status="skip",
                    message="未配置云端 LLM，Ollama 本地兜底暂不可用",
                    detail={
                        "results": [
                            {"name": r.name, "status": r.status, "message": r.message}
                            for r in configured_llm
                        ],
                    },
                )
            )
        else:
            checks.append(
                HealthStatus(
                    name="llm",
                    status="fail",
                    message="已配置 LLM 均不可用",
                    detail={
                        "results": [
                            {"name": r.name, "status": r.status, "message": r.message}
                            for r in configured_llm
                        ],
                    },
                )
            )
    else:
        checks.append(
            HealthStatus(
                name="llm",
                status="skip",
                message="未配置 LLM（使用规则引擎兜底）",
            )
        )

    # 搜索：取第一个配置为 ok 的结果作为可用搜索
    search_results = [r for r in config_report.results if r.category == "search"]
    configured_search = [r for r in search_results if r.configured]
    ok_search = [r for r in configured_search if r.status == "ok"]

    # 兜底搜索：DuckDuckGo 无需配置；SearXNG 默认指向本地 localhost:8080，
    # 未实际部署时不应导致健康状态 fail。只有配置了付费/外部搜索 Key 时，
    # 才将搜索失败视为关键依赖故障。
    fallback_search_names = {"DuckDuckGo 搜索", "SearXNG 本地搜索"}
    has_paid_search_configured = any(
        [
            settings.bocha_api_key,
            settings.zhipu_api_key,
            settings.tavily_api_key,
        ]
    )
    only_fallback_search = configured_search and all(
        r.name in fallback_search_names for r in configured_search
    )

    if ok_search:
        checks.append(
            HealthStatus(
                name="search",
                status="ok",
                message=f"可用搜索: {ok_search[0].name}",
                detail={"available": [r.name for r in ok_search]},
            )
        )
    elif configured_search:
        if only_fallback_search and not has_paid_search_configured:
            checks.append(
                HealthStatus(
                    name="search",
                    status="skip",
                    message="未配置付费/外部搜索 API，本地兜底搜索暂不可用",
                    detail={
                        "results": [
                            {"name": r.name, "status": r.status, "message": r.message}
                            for r in configured_search
                        ],
                    },
                )
            )
        else:
            checks.append(
                HealthStatus(
                    name="search",
                    status="fail",
                    message="已配置搜索均不可用",
                    detail={
                        "results": [
                            {"name": r.name, "status": r.status, "message": r.message}
                            for r in configured_search
                        ],
                    },
                )
            )
    else:
        checks.append(
            HealthStatus(
                name="search",
                status="skip",
                message="未配置搜索（DuckDuckGo 无需配置，将在调用时检测）",
            )
        )

    overall = "ok" if all(c.status in ("ok", "skip") for c in checks) else "degraded"
    if any(c.status == "fail" for c in checks):
        overall = "fail"

    return HealthReport(
        status=overall,
        checked_at=_now_iso(),
        checks=checks,
    )


def run_liveness_check() -> HealthReport:
    """存活探针：仅确认服务仍在运行。"""
    return HealthReport(
        status="ok",
        checked_at=_now_iso(),
        checks=[HealthStatus(name="app", status="ok", message="服务存活")],
    )


def run_readiness_check(settings: Settings | None = None) -> HealthReport:
    """就绪探针：关键依赖必须可用。"""
    report = run_health_checks(settings)
    # 就绪检查将 skip 视为 ok（未配置外部服务仍可启动）
    critical_fail = any(c.status == "fail" for c in report.checks)
    report.status = "ok" if not critical_fail else "fail"
    record_health_check("ready", healthy=not critical_fail)
    return report
