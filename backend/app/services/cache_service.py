"""缓存服务：提供 Redis 优先、内存兜底的缓存装饰器与失效接口。"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
from typing import Any, Callable

from app.core.cache import get_cache_client

logger = logging.getLogger(__name__)

CACHE_KEYS = {
    "skill_statistics": "skill:statistics",
    "job_statistics": "job:statistics",
    "trends": "trends:summary",
    "job_list": "job:list",
    "skill_graph": "skill:graph",
}

DEFAULT_TTLS = {
    "skill_statistics": 3600,
    "job_statistics": 3600,
    "trends": 3600,
    "job_list": 300,
    "skill_graph": 3600,
}


def _serialize_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """根据参数生成稳定的缓存 key。"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, ensure_ascii=False)
    suffix = hashlib.md5(key_data.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:{suffix}"


def cached(prefix: str, ttl: int = 300) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """方法级缓存装饰器。

    被装饰方法的第一个参数通常为 self，会被忽略；其余位置参数和关键字参数参与 key 计算。
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache = get_cache_client()
            cache_args = args[1:] if args else args
            key = _serialize_key(prefix, *cache_args, **kwargs)

            cached_value = cache.get(key)
            if cached_value is not None:
                logger.debug("缓存命中: %s", key)
                return cached_value

            result = func(*args, **kwargs)
            cache.set(key, result, ttl=ttl)
            logger.debug("缓存写入: %s", key)
            return result

        return wrapper

    return decorator


def invalidate_cache(prefix: str) -> None:
    """按前缀删除缓存（简单实现：仅支持精确 key 或全量清除）。"""
    cache = get_cache_client()
    if prefix == "all":
        cache.clear()
        logger.info("全部缓存已清空")
        return
    cache.delete(prefix)
    logger.info("缓存已失效: %s", prefix)


def invalidate_job_cache() -> None:
    """岗位相关数据变更时调用，清除岗位统计与列表缓存。"""
    cache = get_cache_client()
    cache.delete(CACHE_KEYS["job_statistics"])
    cache.delete(CACHE_KEYS["job_list"])
    cache.delete(CACHE_KEYS["trends"])
    logger.info("岗位相关缓存已失效")


def invalidate_skill_cache() -> None:
    """技能相关数据变更时调用，清除技能统计与图谱缓存。"""
    cache = get_cache_client()
    cache.delete(CACHE_KEYS["skill_statistics"])
    cache.delete(CACHE_KEYS["skill_graph"])
    logger.info("技能相关缓存已失效")


def get_cache_stats() -> dict[str, Any]:
    """返回缓存客户端状态。"""
    cache = get_cache_client()
    return {
        "redis_available": cache.is_redis_available(),
        "backend": "redis" if cache.is_redis_available() else "memory",
    }
