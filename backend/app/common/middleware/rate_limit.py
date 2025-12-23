"""
限流中间件 - Rate Limiting Middleware
Rate Limiting for API Protection

提供 API 速率限制功能：
- 基于 IP 地址的限流
- 不同端点不同限制
- 支持 Redis 存储（可扩展到多实例）
- 带有限流头信息响应
"""

import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitExceeded(Exception):
    """限流异常"""
    pass


class InMemoryRateLimiter:
    """
    内存限流器

    使用滑动窗口算法实现限流
    """

    def __init__(self):
        # 格式: {key: [(timestamp, count), ...]}
        self._requests: dict[str, list[tuple[float, int]]] = defaultdict(list)

    def is_allowed(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """
        检查请求是否被允许

        Args:
            key: 限流键（通常是 IP + 端点）
            limit: 窗口内最大请求数
            window_seconds: 时间窗口（秒）

        Returns:
            (是否允许, 剩余请求数, 重置时间戳)
        """
        now = time.time()
        window_start = now - window_seconds

        # 清理过期的请求记录
        self._requests[key] = [
            (ts, count) for ts, count in self._requests[key]
            if ts > window_start
        ]

        # 统计当前窗口内的请求数
        total_requests = sum(count for _, count in self._requests[key])

        if total_requests >= limit:
            # 计算重置时间
            if self._requests[key]:
                reset_time = int(self._requests[key][0][0] + window_seconds)
            else:
                reset_time = int(now + window_seconds)
            return False, 0, reset_time

        # 记录本次请求
        self._requests[key].append((now, 1))

        remaining = limit - total_requests - 1
        reset_time = int(now + window_seconds)

        return True, remaining, reset_time


# 全局限流器实例
_rate_limiter = InMemoryRateLimiter()


# 不同端点的限流规则
RATE_LIMIT_RULES = {
    # 认证相关 - 严格限制防止暴力破解
    "/api/v1/auth/login": (5, 60),       # 5次/分钟
    "/api/v1/auth/register": (3, 60),    # 3次/分钟
    "/api/v1/auth/refresh": (10, 60),    # 10次/分钟
    "/api/v1/auth/captcha": (10, 60),    # 10次/分钟

    # 搜索 - 中等限制
    "/api/v1/search": (30, 60),          # 30次/分钟

    # 默认规则
    "default": (60, 60),                 # 60次/分钟
}

# 白名单路径（不做限流）
RATE_LIMIT_WHITELIST = {
    "/api/v1/health",
    "/api/v1/docs",
    "/api/v1/openapi.json",
    "/api/v1/redoc",
    "/",
}


def get_client_ip(request: Request) -> str:
    """获取客户端真实 IP"""
    # 优先从 X-Forwarded-For 获取（反向代理场景）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 取第一个 IP（最初的客户端 IP）
        return forwarded_for.split(",")[0].strip()

    # 从 X-Real-IP 获取（Nginx 常用）
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # 直接从连接获取
    if request.client:
        return request.client.host

    return "unknown"


def get_rate_limit_for_path(path: str) -> tuple[int, int]:
    """获取路径对应的限流规则"""
    # 精确匹配
    if path in RATE_LIMIT_RULES:
        return RATE_LIMIT_RULES[path]

    # 前缀匹配
    for rule_path, limits in RATE_LIMIT_RULES.items():
        if rule_path != "default" and path.startswith(rule_path):
            return limits

    return RATE_LIMIT_RULES["default"]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    限流中间件

    在请求处理前检查限流，超出限制返回 429 状态码。
    响应头包含限流信息：
    - X-RateLimit-Limit: 最大请求数
    - X-RateLimit-Remaining: 剩余请求数
    - X-RateLimit-Reset: 重置时间戳
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        path = request.url.path

        # 白名单跳过（精确匹配）
        if path in RATE_LIMIT_WHITELIST:
            return await call_next(request)

        # 获取客户端 IP
        client_ip = get_client_ip(request)

        # 获取限流规则
        limit, window = get_rate_limit_for_path(path)

        # 构建限流键
        rate_limit_key = f"{client_ip}:{path}"

        # 检查是否允许
        allowed, remaining, reset_time = _rate_limiter.is_allowed(
            rate_limit_key, limit, window
        )

        if not allowed:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "client_ip": client_ip,
                    "path": path,
                    "limit": limit,
                    "window": window,
                }
            )
            return Response(
                content='{"detail": "请求过于频繁，请稍后再试"}',
                status_code=429,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time - int(time.time())),
                },
            )

        # 处理请求
        response = await call_next(request)

        # 添加限流头信息
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response
