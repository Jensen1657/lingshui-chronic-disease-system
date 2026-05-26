"""Redis 缓存工具"""
import os
import json
import redis
from typing import Optional, Any
from functools import wraps
import logging

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None
_is_initialized = False


def get_redis() -> Optional[redis.Redis]:
    """获取 Redis 连接（单例，连接失败返回 None）"""
    global _redis_client, _is_initialized
    if _is_initialized:
        return _redis_client
    _is_initialized = True
    
    redis_url = os.getenv('REDIS_URL', '')
    if not redis_url:
        logger.info("REDIS_URL 未配置，使用无缓存模式")
        _redis_client = None
        return None
    
    try:
        # Render 提供的 REDIS_URL 格式: redis://host:port
        _redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        _redis_client.ping()
        logger.info("Redis 连接成功")
    except Exception as e:
        logger.warning(f"Redis 连接失败: {e}，使用无缓存模式")
        _redis_client = None
    return _redis_client


def get(key: str) -> Optional[Any]:
    """读取缓存"""
    r = get_redis()
    if r is None:
        return None
    try:
        val = r.get(key)
        if val:
            return json.loads(val)
    except Exception as e:
        logger.warning(f"Redis GET 失败: {e}")
    return None


def set(key: str, value: Any, ttl: int = 60) -> bool:
    """写入缓存，TTL 秒"""
    r = get_redis()
    if r is None:
        return False
    try:
        r.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
        return True
    except Exception as e:
        logger.warning(f"Redis SET 失败: {e}")
    return False


def invalidate(key: str) -> bool:
    """删除缓存"""
    r = get_redis()
    if r is None:
        return False
    try:
        r.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Redis DELETE 失败: {e}")
    return False


def invalidate_pattern(pattern: str) -> bool:
    """删除匹配模式的所有 key"""
    r = get_redis()
    if r is None:
        return False
    try:
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
        return True
    except Exception as e:
        logger.warning(f"Redis DELETE pattern 失败: {e}")
    return False


# 仪表盘缓存 key
DASHBOARD_STATS_KEY = "dashboard:stats"
DASHBOARD_KPI_KEY = "dashboard:kpi"
DASHBOARD_TTL = 60  # 60秒缓存


def cached(key: str, ttl: int = 60):
    """装饰器：为 async 函数添加缓存"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = key
            cached_val = get(cache_key)
            if cached_val is not None:
                return cached_val
            result = await func(*args, **kwargs)
            if result is not None:
                set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
