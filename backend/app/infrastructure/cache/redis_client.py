"""
Redis Client - Redis 客户端封装

提供统一的 Redis 连接管理和常用操作封装。
支持连接池、重试和健康检查。
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """
    Redis 服务封装

    提供：
    - 连接池管理
    - 常用操作封装（get/set/delete）
    - JSON 序列化支持
    - 键过期管理
    """

    def __init__(
        self,
        url: str | None = None,
        decode_responses: bool = True,
        max_connections: int = 50,
    ):
        """
        初始化 Redis 服务

        Args:
            url: Redis 连接 URL，默认从配置读取
            decode_responses: 是否自动解码响应
            max_connections: 连接池最大连接数
        """
        self.url = url or settings.REDIS_URL
        self.decode_responses = decode_responses
        self.max_connections = max_connections
        self._client: redis.Redis | None = None
        self._pool: redis.ConnectionPool | None = None

    async def get_client(self) -> redis.Redis:
        """
        获取 Redis 客户端（懒加载）

        使用连接池确保连接复用，避免频繁创建连接。

        Returns:
            redis.Redis: Redis 异步客户端
        """
        if self._client is None:
            self._pool = redis.ConnectionPool.from_url(
                self.url,
                max_connections=self.max_connections,
                decode_responses=self.decode_responses,
            )
            self._client = redis.Redis(connection_pool=self._pool)
        return self._client

    async def close(self) -> None:
        """关闭 Redis 连接"""
        if self._client:
            await self._client.close()
            self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None

    # ==================== 基础操作 ====================

    async def get(self, key: str) -> str | None:
        """获取字符串值"""
        client = await self.get_client()
        return await client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
        px: int | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        设置字符串值

        Args:
            key: 键名
            value: 值
            ex: 过期时间（秒）
            px: 过期时间（毫秒）
            nx: 仅在键不存在时设置
            xx: 仅在键存在时设置

        Returns:
            bool: 是否设置成功
        """
        client = await self.get_client()
        result = await client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
        return result is not None

    async def delete(self, *keys: str) -> int:
        """
        删除键

        Args:
            *keys: 要删除的键名列表

        Returns:
            int: 实际删除的键数量
        """
        if not keys:
            return 0
        client = await self.get_client()
        return await client.delete(*keys)

    async def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        if not keys:
            return 0
        client = await self.get_client()
        return await client.exists(*keys)

    async def expire(self, key: str, seconds: int) -> bool:
        """设置键过期时间"""
        client = await self.get_client()
        return await client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """获取键剩余过期时间（秒）"""
        client = await self.get_client()
        return await client.ttl(key)

    # ==================== JSON 操作 ====================

    async def get_json(self, key: str) -> Any | None:
        """获取 JSON 对象"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode JSON for key: {key}")
                return None
        return None

    async def set_json(
        self,
        key: str,
        value: Any,
        ex: int | None = None,
    ) -> bool:
        """
        存储 JSON 对象

        Args:
            key: 键名
            value: 可 JSON 序列化的对象
            ex: 过期时间（秒）

        Returns:
            bool: 是否设置成功
        """
        json_str = json.dumps(value, ensure_ascii=False, default=str)
        return await self.set(key, json_str, ex=ex)

    # ==================== 集合操作 ====================

    async def sadd(self, key: str, *members: str) -> int:
        """向集合添加成员"""
        if not members:
            return 0
        client = await self.get_client()
        return await client.sadd(key, *members)

    async def sismember(self, key: str, member: str) -> bool:
        """检查成员是否在集合中"""
        client = await self.get_client()
        return await client.sismember(key, member)

    async def smembers(self, key: str) -> set[str]:
        """获取集合所有成员"""
        client = await self.get_client()
        return await client.smembers(key)

    async def srem(self, key: str, *members: str) -> int:
        """从集合移除成员"""
        if not members:
            return 0
        client = await self.get_client()
        return await client.srem(key, *members)

    # ==================== 计数器操作 ====================

    async def incr(self, key: str, amount: int = 1) -> int:
        """增加计数"""
        client = await self.get_client()
        return await client.incrby(key, amount)

    async def decr(self, key: str, amount: int = 1) -> int:
        """减少计数"""
        client = await self.get_client()
        return await client.decrby(key, amount)

    # ==================== 健康检查 ====================

    async def ping(self) -> bool:
        """健康检查"""
        try:
            client = await self.get_client()
            return await client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False


# 全局单例实例
_redis_service: RedisService | None = None


def get_redis() -> RedisService:
    """
    获取 Redis 服务单例实例

    Returns:
        RedisService: Redis 服务实例
    """
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service


async def get_redis_client() -> redis.Redis:
    """
    获取底层 Redis 客户端（用于需要直接操作的场景）

    Returns:
        redis.Redis: Redis 异步客户端
    """
    return await get_redis().get_client()
