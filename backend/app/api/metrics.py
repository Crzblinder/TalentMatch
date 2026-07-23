"""Prometheus 指标暴露。

提供 TalentMatch 核心运行指标：RSS 采集、LLM 调用、解析任务、缓存命中率等。
"""

from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

# ---------------------------------------------------------------------------
# Registry & metrics
# ---------------------------------------------------------------------------
registry = CollectorRegistry()

# RSS 采集结果统计
rss_fetch_total = Counter(
    "talentmatch_rss_fetch_total",
    "Total number of RSS source fetches",
    ["source", "status"],
    registry=registry,
)

# LLM 调用延迟
llm_call_duration_ms = Histogram(
    "talentmatch_llm_call_duration_milliseconds",
    "LLM call latency in milliseconds",
    ["agent"],
    buckets=[50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000],
    registry=registry,
)

# LLM 调用结果统计
llm_call_total = Counter(
    "talentmatch_llm_call_total",
    "Total number of LLM calls",
    ["agent", "status"],
    registry=registry,
)

# 解析任务统计
parse_task_total = Counter(
    "talentmatch_parse_task_total",
    "Total number of parse tasks",
    ["kind", "status"],
    registry=registry,
)

# 缓存命中统计
cache_access_total = Counter(
    "talentmatch_cache_access_total",
    "Total number of cache accesses",
    ["prefix", "status"],
    registry=registry,
)

# 健康检查统计
health_check_total = Counter(
    "talentmatch_health_check_total",
    "Total number of health checks",
    ["endpoint", "status"],
    registry=registry,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def record_rss_fetch(source: str, success: bool) -> None:
    """记录一次 RSS 源采集结果。"""
    status = "success" if success else "failure"
    rss_fetch_total.labels(source=source, status=status).inc()


def record_llm_call(agent: str, duration_ms: float, success: bool) -> None:
    """记录一次 LLM 调用结果与延迟。"""
    llm_call_duration_ms.labels(agent=agent).observe(duration_ms)
    status = "success" if success else "failure"
    llm_call_total.labels(agent=agent, status=status).inc()


def record_parse_task(kind: str, success: bool) -> None:
    """记录一次解析任务结果。"""
    status = "success" if success else "failure"
    parse_task_total.labels(kind=kind, status=status).inc()


def record_cache_access(prefix: str, hit: bool) -> None:
    """记录一次缓存访问结果。"""
    status = "hit" if hit else "miss"
    cache_access_total.labels(prefix=prefix, status=status).inc()


def record_health_check(endpoint: str, healthy: bool) -> None:
    """记录一次健康检查结果。"""
    status = "healthy" if healthy else "unhealthy"
    health_check_total.labels(endpoint=endpoint, status=status).inc()


def generate_metrics() -> tuple[bytes, str]:
    """生成 Prometheus 抓取用的指标数据。"""
    return generate_latest(registry), CONTENT_TYPE_LATEST
