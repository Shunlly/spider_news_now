"""
Dashboard API 端点 - Dashboard API Endpoints
T135: /dashboard/stats endpoint
T136: WebSocket endpoint for real-time updates

提供 Dashboard 统计数据和实时更新功能。
"""

import asyncio
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.schemas.websocket import (
    WSConnectedMessage,
    WSError,
    WSStatsUpdate,
)
from app.services.dashboard_service import dashboard_service

logger = get_logger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# =============================================================
# 响应模型
# =============================================================


class DashboardStatsResponse(BaseModel):
    """Dashboard 统计响应"""
    total_articles: int = Field(..., description="文章总数")
    articles_today: int = Field(..., description="今日文章数")
    active_scrapers: int = Field(..., description="活跃爬虫数")
    total_scrapers: int = Field(..., description="爬虫总数")
    active_social_sessions: int = Field(..., description="活跃社交会话数")
    total_social_messages: int = Field(..., description="社交消息总数")
    quota_used: int = Field(..., description="已用配额")
    quota_limit: int = Field(..., description="配额限制")
    timestamp: str = Field(..., description="数据时间戳")


class ActivityItem(BaseModel):
    """活动项"""
    type: str
    icon: str
    message: str
    timestamp: str | None
    status: str | None = None


class RecentActivityResponse(BaseModel):
    """最近活动响应"""
    activities: list[ActivityItem]


class ScraperStatusItem(BaseModel):
    """爬虫状态项"""
    source_key: str
    display_name: str
    enabled: bool
    status: str
    last_run: str | None
    articles_scraped: int
    error_message: str | None = None


class ScraperStatusListResponse(BaseModel):
    """爬虫状态列表响应"""
    scrapers: list[ScraperStatusItem]


# =============================================================
# REST API 端点
# =============================================================


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="获取 Dashboard 统计数据",
    description="获取当前用户的 Dashboard 统计数据"
)
async def get_dashboard_stats(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> DashboardStatsResponse:
    """
    获取 Dashboard 统计数据

    返回：
    - total_articles: 文章总数
    - articles_today: 今日文章数
    - active_scrapers: 活跃爬虫数
    - total_scrapers: 爬虫总数
    - active_social_sessions: 活跃社交会话数
    - total_social_messages: 社交消息总数
    - quota_used: 已用配额
    - quota_limit: 配额限制
    """
    stats = await dashboard_service.get_stats(
        db=db,
        user_id=current_user.id,
        is_admin=current_user.is_admin,
    )

    return DashboardStatsResponse(**stats)


@router.get(
    "/activity",
    response_model=RecentActivityResponse,
    summary="获取最近活动",
    description="获取最近的系统活动"
)
async def get_recent_activity(
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
) -> RecentActivityResponse:
    """
    获取最近活动

    返回最近的爬虫运行、数据导出等活动。
    """
    activities = await dashboard_service.get_recent_activity(
        db=db,
        user_id=current_user.id,
        is_admin=current_user.is_admin,
        limit=limit,
    )

    return RecentActivityResponse(
        activities=[ActivityItem(**a) for a in activities]
    )


@router.get(
    "/scrapers",
    response_model=ScraperStatusListResponse,
    summary="获取爬虫状态列表",
    description="获取所有爬虫的当前状态"
)
async def get_scraper_status_list(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> ScraperStatusListResponse:
    """
    获取爬虫状态列表

    返回所有爬虫的运行状态、最后运行时间等信息。
    """
    scrapers = await dashboard_service.get_scraper_status_list(
        db=db,
        user_id=current_user.id,
        is_admin=current_user.is_admin,
    )

    return ScraperStatusListResponse(
        scrapers=[ScraperStatusItem(**s) for s in scrapers]
    )


# =============================================================
# WebSocket 连接管理
# =============================================================


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 活跃连接: client_id -> WebSocket
        self.active_connections: dict[str, WebSocket] = {}
        # 用户连接映射: user_id -> set of client_ids
        self.user_connections: dict[str, set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """
        接受 WebSocket 连接

        Args:
            websocket: WebSocket 连接
            user_id: 用户 ID

        Returns:
            client_id: 客户端唯一标识
        """
        await websocket.accept()

        client_id = str(uuid.uuid4())
        self.active_connections[client_id] = websocket

        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(client_id)

        logger.info(f"WebSocket 连接: client_id={client_id}, user_id={user_id}")

        return client_id

    def disconnect(self, client_id: str, user_id: str):
        """断开连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        if user_id in self.user_connections:
            self.user_connections[user_id].discard(client_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        logger.info(f"WebSocket 断开: client_id={client_id}")

    async def send_to_client(self, client_id: str, message: dict):
        """发送消息给指定客户端"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def send_to_user(self, user_id: str, message: dict):
        """发送消息给用户的所有连接"""
        if user_id in self.user_connections:
            for client_id in self.user_connections[user_id]:
                await self.send_to_client(client_id, message)

    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        for client_id in self.active_connections:
            await self.send_to_client(client_id, message)

    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.active_connections)


# 全局连接管理器
manager = ConnectionManager()


# =============================================================
# WebSocket 端点
# =============================================================


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = None,
):
    """
    Dashboard WebSocket 端点

    提供实时数据更新推送。

    连接参数：
    - token: JWT access token（查询参数）

    消息类型：
    - stats_update: 统计数据更新
    - scraper_status: 爬虫状态更新
    - task_progress: 任务进度更新
    - alert: 告警消息
    - quota_warning: 配额警告

    示例连接：ws://localhost:8000/api/v1/dashboard/ws?token=xxx
    """
    from app.core.security import verify_token
    from app.db.session import async_session_maker

    # 验证 token
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    user_id = verify_token(token, token_type="access")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # 建立连接
    client_id = await manager.connect(websocket, user_id)

    try:
        # 发送连接成功消息
        connected_msg = WSConnectedMessage(
            client_id=client_id,
            message="WebSocket 连接成功"
        )
        await websocket.send_json(connected_msg.model_dump(mode="json"))

        # 发送初始统计数据
        async with async_session_maker() as db:
            stats = await dashboard_service.get_stats(
                db=db,
                user_id=user_id,
                is_admin=False,  # WebSocket 不方便查用户角色，默认非管理员
            )

            stats_msg = WSStatsUpdate(
                total_articles=stats["total_articles"],
                articles_today=stats["articles_today"],
                active_scrapers=stats["active_scrapers"],
                total_scrapers=stats["total_scrapers"],
                active_social_sessions=stats["active_social_sessions"],
                total_social_messages=stats["total_social_messages"],
                quota_used=stats["quota_used"],
                quota_limit=stats["quota_limit"],
            )
            await websocket.send_json(stats_msg.model_dump(mode="json"))

        # 保持连接并处理心跳
        while True:
            try:
                # 等待客户端消息（主要是 ping）
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=60.0  # 60 秒超时
                )

                # 处理 ping 消息
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    })

            except TimeoutError:
                # 发送心跳保持连接
                await websocket.send_json({
                    "type": "ping",
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket 客户端断开: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        try:
            error_msg = WSError(
                code="INTERNAL_ERROR",
                message=str(e)
            )
            await websocket.send_json(error_msg.model_dump(mode="json"))
        except Exception:
            pass
    finally:
        manager.disconnect(client_id, user_id)


# =============================================================
# 辅助函数：用于其他模块推送更新
# =============================================================


async def push_stats_update(user_id: str, stats: dict):
    """推送统计更新给指定用户"""
    msg = WSStatsUpdate(
        total_articles=stats.get("total_articles", 0),
        articles_today=stats.get("articles_today", 0),
        active_scrapers=stats.get("active_scrapers", 0),
        total_scrapers=stats.get("total_scrapers", 0),
        active_social_sessions=stats.get("active_social_sessions", 0),
        total_social_messages=stats.get("total_social_messages", 0),
        quota_used=stats.get("quota_used", 0),
        quota_limit=stats.get("quota_limit", 0),
    )
    await manager.send_to_user(user_id, msg.model_dump(mode="json"))


async def push_alert(user_id: str, level: str, title: str, message: str):
    """推送告警给指定用户"""
    from app.schemas.websocket import AlertLevel, WSAlert

    alert = WSAlert(
        level=AlertLevel(level),
        title=title,
        message=message,
    )
    await manager.send_to_user(user_id, alert.model_dump(mode="json"))


async def broadcast_scraper_status(source_key: str, status: str, articles: int = 0):
    """广播爬虫状态更新"""
    from app.schemas.websocket import WSScraperStatus

    msg = WSScraperStatus(
        source_key=source_key,
        status=status,
        articles_scraped=articles,
    )
    await manager.broadcast(msg.model_dump(mode="json"))
