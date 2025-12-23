"""
Cache Infrastructure - Redis 缓存基础设施

提供统一的 Redis 连接管理和常用缓存操作封装。
"""

from app.infrastructure.cache.redis_client import (
    RedisService,
    get_redis,
    get_redis_client,
)

__all__ = [
    "RedisService",
    "get_redis",
    "get_redis_client",
]
