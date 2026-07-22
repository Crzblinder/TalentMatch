"""Redis 客户端封装，支持 Redis 不可用时降级到内存缓存。"""

from __future__ import annotations

import json
import logging
import threading
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


class _MemoryCache:
    """线程安全的内存缓存，作为 Redis 不可用时的兜底。"""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._ttls: dict[str, float] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Any:
        with self._lock:
            import time

            expire_at = self._ttls.get(key)
            if expire_at is not None and time.time() > expire_at:
                self._store.pop(key, None)
                self._ttls.pop(key, None)
                return None
            return self._store.get(key)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        with self._lock:
            self._store[key] = value
            if ttl is not None and ttl > 0:
                import time

                self._ttls[key] = time.time() + ttl
            else:
                self._ttls.pop(key, None)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)
            self._ttls.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._ttls.clear()


class CacheClient:
    """缓存客户端：优先 Redis，失败时降级到内存缓存。"""

    def __init__(self) -> None:
        self._redis: Any | None = None
        self._memory = _MemoryCache()
        self._redis_available: bool | None = None
        self._lock = threading.RLock()
        self._connect()

    def _connect(self) -> None:
        settings = get_settings()
        try:
            import redis as redis_lib

            self._redis = redis_lib.Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                health_check_interval=30,
            )
            self._redis.ping()
            self._redis_available = True
            logger.info("Redis 缓存已连接: %s", settings.redis_url)
        except Exception as exc:
            self._redis = None
            self._redis_available = False
            logger.warning("Redis 连接失败，降级到内存缓存: %s", exc)

    def _ensure_redis(self) -> Any | None:
        if self._redis_available is False:
            return None
        if self._redis is None:
            return None
        try:
            self._redis.ping()
            return self._redis
        except Exception as exc:
            logger.warning("Redis 不可用，降级到内存缓存: %s", exc)
            with self._lock:
                self._redis_available = False
                self._redis = None
            return None

    def get(self, key: str) -> Any:
        redis = self._ensure_redis()
        if redis is not None:
            try:
                raw = redis.get(key)
                if raw is not None:
                    return json.loads(raw)
            except Exception as exc:
                logger.warning("Redis get 失败: %s", exc)
        return self._memory.get(key)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        redis = self._ensure_redis()
        if redis is not None:
            try:
                raw = json.dumps(value, ensure_ascii=False, default=str)
                if ttl is not None and ttl > 0:
                    redis.setex(key, ttl, raw)
                else:
                    redis.set(key, raw)
                return
            except Exception as exc:
                logger.warning("Redis set 失败: %s", exc)
        self._memory.set(key, value, ttl=ttl)

    def delete(self, key: str) -> None:
        redis = self._ensure_redis()
        if redis is not None:
            try:
                redis.delete(key)
            except Exception as exc:
                logger.warning("Redis delete 失败: %s", exc)
        self._memory.delete(key)

    def clear(self) -> None:
        redis = self._ensure_redis()
        if redis is not None:
            try:
                redis.flushdb()
            except Exception as exc:
                logger.warning("Redis clear 失败: %s", exc)
        self._memory.clear()

    def is_redis_available(self) -> bool:
        return self._ensure_redis() is not None


# 模块级单例
_cache_client: CacheClient | None = None


def get_cache_client() -> CacheClient:
    global _cache_client
    if _cache_client is None:
        _cache_client = CacheClient()
    return _cache_client
