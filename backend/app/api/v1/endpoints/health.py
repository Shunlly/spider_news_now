"""
健康检查 API 端点 - Health Check API Endpoints
System Health and Status Monitoring

提供系统健康检查接口：
- GET /health - 基本健康检查
- GET /health/ready - 就绪检查（包含数据库、Redis等）
- GET /health/live - 存活检查

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["健康检查"])


class HealthStatus(BaseModel):
    """健康状态响应"""
    status: str = Field(..., description="状态: healthy, degraded, unhealthy")
    timestamp: str = Field(..., description="检查时间")
    version: str = Field(..., description="API版本")


class ComponentStatus(BaseModel):
    """组件状态"""
    name: str = Field(..., description="组件名称")
    status: str = Field(..., description="状态: ok, error")
    latency_ms: float | None = Field(None, description="响应延迟（毫秒）")
    message: str | None = Field(None, description="状态消息")


class ReadinessStatus(BaseModel):
    """就绪检查响应"""
    status: str = Field(..., description="状态: ready, not_ready")
    timestamp: str = Field(..., description="检查时间")
    version: str = Field(..., description="API版本")
    components: list[ComponentStatus] = Field(..., description="组件状态列表")


@router.get(
    "",
    response_model=HealthStatus,
    summary="基本健康检查",
    description="返回服务基本健康状态"
)
async def health_check() -> HealthStatus:
    """
    基本健康检查

    用于负载均衡器或 Kubernetes 探针检测服务是否存活。
    仅检查服务进程是否运行，不检查依赖组件。
    """
    return HealthStatus(
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
        version=settings.VERSION,
    )


@router.get(
    "/live",
    response_model=HealthStatus,
    summary="存活检查",
    description="Kubernetes liveness probe"
)
async def liveness_check() -> HealthStatus:
    """
    存活检查（Liveness Probe）

    用于 Kubernetes 判断容器是否需要重启。
    应该只检查服务进程是否正常运行。
    """
    return HealthStatus(
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
        version=settings.VERSION,
    )


@router.get(
    "/ready",
    response_model=ReadinessStatus,
    summary="就绪检查",
    description="检查所有依赖组件是否就绪"
)
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> ReadinessStatus:
    """
    就绪检查（Readiness Probe）

    检查服务是否可以接收流量。
    包括数据库、Redis、Meilisearch 等依赖组件的健康状态。
    """
    components: list[ComponentStatus] = []
    overall_status = "ready"

    # 检查数据库
    db_status = await _check_database(db)
    components.append(db_status)
    if db_status.status != "ok":
        overall_status = "not_ready"

    # 检查 Redis
    redis_status = await _check_redis()
    components.append(redis_status)
    if redis_status.status != "ok":
        overall_status = "not_ready"

    # 检查 Meilisearch（可选）
    if settings.MEILISEARCH_URL:
        search_status = await _check_meilisearch()
        components.append(search_status)
        # Meilisearch 不影响整体就绪状态

    return ReadinessStatus(
        status=overall_status,
        timestamp=datetime.now(UTC).isoformat(),
        version=settings.VERSION,
        components=components,
    )


async def _check_database(db: AsyncSession) -> ComponentStatus:
    """检查数据库连接"""
    start_time = datetime.now(UTC)
    try:
        await db.execute(text("SELECT 1"))
        latency = (datetime.now(UTC) - start_time).total_seconds() * 1000
        return ComponentStatus(
            name="database",
            status="ok",
            latency_ms=round(latency, 2),
            message="MySQL connection healthy",
        )
    except Exception as e:
        logger.error("Database health check failed", extra={"error": str(e)})
        return ComponentStatus(
            name="database",
            status="error",
            message=f"MySQL connection failed: {str(e)[:100]}",
        )


async def _check_redis() -> ComponentStatus:
    """检查 Redis 连接"""
    start_time = datetime.now(UTC)
    try:
        import redis.asyncio as redis

        client = redis.from_url(settings.REDIS_URL)
        await client.ping()
        await client.close()

        latency = (datetime.now(UTC) - start_time).total_seconds() * 1000
        return ComponentStatus(
            name="redis",
            status="ok",
            latency_ms=round(latency, 2),
            message="Redis connection healthy",
        )
    except Exception as e:
        logger.error("Redis health check failed", extra={"error": str(e)})
        return ComponentStatus(
            name="redis",
            status="error",
            message=f"Redis connection failed: {str(e)[:100]}",
        )


async def _check_meilisearch() -> ComponentStatus:
    """检查 Meilisearch 连接"""
    start_time = datetime.now(UTC)
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.MEILISEARCH_URL}/health",
                timeout=5.0,
            )

        latency = (datetime.now(UTC) - start_time).total_seconds() * 1000

        if response.status_code == 200:
            return ComponentStatus(
                name="meilisearch",
                status="ok",
                latency_ms=round(latency, 2),
                message="Meilisearch connection healthy",
            )
        else:
            return ComponentStatus(
                name="meilisearch",
                status="error",
                latency_ms=round(latency, 2),
                message=f"Meilisearch returned status {response.status_code}",
            )
    except Exception as e:
        logger.warning("Meilisearch health check failed", extra={"error": str(e)})
        return ComponentStatus(
            name="meilisearch",
            status="error",
            message=f"Meilisearch connection failed: {str(e)[:100]}",
        )
