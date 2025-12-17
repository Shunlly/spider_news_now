"""
社交数据 API 端点
Social Data API Endpoints

提供社交会话和消息的 CRUD 操作。
遵循宪法 II.B 异构数据建模规范。
数据隔离：用户只能访问自己的数据，管理员可访问所有数据。
"""

import json
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.models.social_session import Platform, SessionStatus, SocialSession
from app.models.social_message import SocialMessage
from app.schemas.social import (
    SocialMessageListResponse,
    SocialMessageResponse,
    SocialSessionActionResponse,
    SocialSessionCreate,
    SocialSessionDetailResponse,
    SocialSessionListResponse,
    SocialSessionResponse,
    SocialSessionUpdate,
    SocialStatisticsResponse,
    PlatformStats,
)
from app.services.permission_service import apply_user_filter

logger = get_logger(__name__)

router = APIRouter(prefix="/social", tags=["social"])


# =============================================================
# 会话管理端点
# =============================================================

@router.get("/sessions", response_model=SocialSessionListResponse)
async def list_sessions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    platform: Optional[Platform] = Query(None, description="按平台过滤"),
    status: Optional[SessionStatus] = Query(None, description="按状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取社交会话列表

    支持按平台和状态过滤，返回分页结果。
    Note: 管理员可查看所有会话，普通用户只能查看自己的会话。
    """
    # 构建查询（应用用户过滤）
    stmt = select(SocialSession)
    stmt = apply_user_filter(stmt, current_user, SocialSession)

    if platform:
        stmt = stmt.where(SocialSession.platform == platform)
    if status:
        stmt = stmt.where(SocialSession.status == status)

    # 计算总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # 分页查询
    stmt = stmt.order_by(SocialSession.updated_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    sessions = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return SocialSessionListResponse(
        data=[SocialSessionResponse.model_validate(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/sessions", response_model=SocialSessionActionResponse)
async def create_session(
    session_data: SocialSessionCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的社交会话

    自动生成 session_key：{platform}:{target_id}
    """
    # 生成 session_key
    session_key = f"{session_data.platform.value}:{session_data.target_id}"

    # 检查是否已存在（只检查当前用户的会话）
    existing_stmt = select(SocialSession).where(SocialSession.session_key == session_key)
    existing_stmt = apply_user_filter(existing_stmt, current_user, SocialSession)
    existing = await db.execute(existing_stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"会话已存在: {session_key}"
        )

    # 创建会话（设置 user_id）
    session = SocialSession(
        user_id=current_user.id,
        session_key=session_key,
        platform=session_data.platform,
        target_id=session_data.target_id,
        target_name=session_data.target_name,
        target_username=session_data.target_username,
        description=session_data.description,
        fetch_interval=session_data.fetch_interval,
        status=SessionStatus.ACTIVE,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    logger.info(f"创建社交会话: {session_key}")

    return SocialSessionActionResponse(
        success=True,
        message="会话创建成功",
        session_id=session.id,
        session=SocialSessionResponse.model_validate(session),
    )


@router.get("/sessions/{session_id}", response_model=SocialSessionDetailResponse)
async def get_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    include_messages: bool = Query(True, description="是否包含最近消息"),
    message_limit: int = Query(10, ge=1, le=50, description="消息数量限制"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取会话详情

    可选择是否包含最近的消息列表。
    Note: 管理员可查看所有会话，普通用户只能查看自己的会话。
    """
    stmt = select(SocialSession).where(SocialSession.id == session_id)
    stmt = apply_user_filter(stmt, current_user, SocialSession)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")

    response = SocialSessionDetailResponse.model_validate(session)

    # 获取最近消息
    if include_messages:
        msg_stmt = (
            select(SocialMessage)
            .where(SocialMessage.session_id == session_id)
            .order_by(SocialMessage.posted_at.desc())
            .limit(message_limit)
        )
        msg_result = await db.execute(msg_stmt)
        messages = msg_result.scalars().all()

        response.recent_messages = [
            _convert_message(m) for m in messages
        ]

    return response


@router.put("/sessions/{session_id}", response_model=SocialSessionActionResponse)
async def update_session(
    session_id: int,
    update_data: SocialSessionUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    更新会话信息

    支持更新名称、描述、采集间隔和状态。
    Note: 管理员可更新所有会话，普通用户只能更新自己的会话。
    """
    stmt = select(SocialSession).where(SocialSession.id == session_id)
    stmt = apply_user_filter(stmt, current_user, SocialSession)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")

    # 更新字段
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(session, field, value)

    await db.commit()
    await db.refresh(session)

    logger.info(f"更新社交会话: {session.session_key}")

    return SocialSessionActionResponse(
        success=True,
        message="会话更新成功",
        session_id=session.id,
        session=SocialSessionResponse.model_validate(session),
    )


@router.delete("/sessions/{session_id}", response_model=SocialSessionActionResponse)
async def delete_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    删除会话

    会同时删除该会话下的所有消息（级联删除）。
    Note: 管理员可删除所有会话，普通用户只能删除自己的会话。
    """
    stmt = select(SocialSession).where(SocialSession.id == session_id)
    stmt = apply_user_filter(stmt, current_user, SocialSession)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")

    session_key = session.session_key
    await db.delete(session)
    await db.commit()

    logger.info(f"删除社交会话: {session_key}")

    return SocialSessionActionResponse(
        success=True,
        message="会话删除成功",
        session_id=session_id,
    )


@router.post("/sessions/{session_id}/pause", response_model=SocialSessionActionResponse)
async def pause_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """暂停会话采集"""
    return await _update_session_status(db, session_id, SessionStatus.PAUSED, "会话已暂停", current_user)


@router.post("/sessions/{session_id}/resume", response_model=SocialSessionActionResponse)
async def resume_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """恢复会话采集"""
    return await _update_session_status(db, session_id, SessionStatus.ACTIVE, "会话已恢复", current_user)


async def _update_session_status(
    db: AsyncSession,
    session_id: int,
    new_status: SessionStatus,
    message: str,
    current_user: User,
) -> SocialSessionActionResponse:
    """更新会话状态的内部方法"""
    stmt = select(SocialSession).where(SocialSession.id == session_id)
    stmt = apply_user_filter(stmt, current_user, SocialSession)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")

    session.status = new_status
    await db.commit()
    await db.refresh(session)

    logger.info(f"会话状态变更: {session.session_key} -> {new_status.value}")

    return SocialSessionActionResponse(
        success=True,
        message=message,
        session_id=session.id,
        session=SocialSessionResponse.model_validate(session),
    )


# =============================================================
# 消息查询端点
# =============================================================

@router.get("/sessions/{session_id}/messages", response_model=SocialMessageListResponse)
async def list_messages(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取会话下的消息列表

    按发布时间倒序返回分页结果。
    Note: 管理员可查看所有会话消息，普通用户只能查看自己会话的消息。
    """
    # 验证会话存在且用户有权限
    session_stmt = select(SocialSession).where(SocialSession.id == session_id)
    session_stmt = apply_user_filter(session_stmt, current_user, SocialSession)
    session_result = await db.execute(session_stmt)
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")

    # 构建查询
    stmt = select(SocialMessage).where(SocialMessage.session_id == session_id)

    # 计算总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # 分页查询
    stmt = stmt.order_by(SocialMessage.posted_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    messages = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return SocialMessageListResponse(
        data=[_convert_message(m) for m in messages],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        session=SocialSessionResponse.model_validate(session),
    )


@router.get("/messages/{message_id}", response_model=SocialMessageResponse)
async def get_message(
    message_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    获取单条消息详情

    Note: 管理员可查看所有消息，普通用户只能查看自己会话的消息。
    """
    # 需要通过 session 来过滤权限
    stmt = (
        select(SocialMessage)
        .join(SocialSession)
        .where(SocialMessage.id == message_id)
    )
    if not current_user.is_admin:
        stmt = stmt.where(SocialSession.user_id == current_user.id)

    result = await db.execute(stmt)
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail=f"消息不存在: {message_id}")

    return _convert_message(message)


# =============================================================
# 统计端点
# =============================================================

@router.get("/statistics", response_model=SocialStatisticsResponse)
async def get_statistics(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    获取社交数据统计

    返回会话和消息的汇总统计信息。
    Note: 管理员可查看所有统计，普通用户只能查看自己的数据统计。
    """
    # 构建用户过滤条件
    session_filter = []
    if not current_user.is_admin:
        session_filter.append(SocialSession.user_id == current_user.id)

    # 总会话数
    total_sessions_stmt = select(func.count()).select_from(SocialSession)
    if session_filter:
        total_sessions_stmt = total_sessions_stmt.where(*session_filter)
    total_sessions_result = await db.execute(total_sessions_stmt)
    total_sessions = total_sessions_result.scalar() or 0

    # 总消息数（通过 join 过滤）
    total_messages_stmt = select(func.count()).select_from(SocialMessage).join(SocialSession)
    if session_filter:
        total_messages_stmt = total_messages_stmt.where(*session_filter)
    total_messages_result = await db.execute(total_messages_stmt)
    total_messages = total_messages_result.scalar() or 0

    # 活跃会话数
    active_sessions_stmt = (
        select(func.count())
        .select_from(SocialSession)
        .where(SocialSession.status == SessionStatus.ACTIVE)
    )
    if session_filter:
        active_sessions_stmt = active_sessions_stmt.where(*session_filter)
    active_sessions_result = await db.execute(active_sessions_stmt)
    active_sessions = active_sessions_result.scalar() or 0

    # 按平台统计
    platform_stats = []
    for platform in Platform:
        # 会话数
        session_count_stmt = (
            select(func.count())
            .select_from(SocialSession)
            .where(SocialSession.platform == platform)
        )
        if session_filter:
            session_count_stmt = session_count_stmt.where(*session_filter)
        session_count_result = await db.execute(session_count_stmt)
        session_count = session_count_result.scalar() or 0

        # 消息数（通过 join）
        message_count_stmt = (
            select(func.count())
            .select_from(SocialMessage)
            .join(SocialSession)
            .where(SocialSession.platform == platform)
        )
        if session_filter:
            message_count_stmt = message_count_stmt.where(*session_filter)
        message_count_result = await db.execute(message_count_stmt)
        message_count = message_count_result.scalar() or 0

        # 活跃会话数
        active_count_stmt = (
            select(func.count())
            .select_from(SocialSession)
            .where(
                SocialSession.platform == platform,
                SocialSession.status == SessionStatus.ACTIVE
            )
        )
        if session_filter:
            active_count_stmt = active_count_stmt.where(*session_filter)
        active_count_result = await db.execute(active_count_stmt)
        active_count = active_count_result.scalar() or 0

        if session_count > 0:
            platform_stats.append(PlatformStats(
                platform=platform,
                session_count=session_count,
                message_count=message_count,
                active_sessions=active_count,
            ))

    return SocialStatisticsResponse(
        total_sessions=total_sessions,
        total_messages=total_messages,
        active_sessions=active_sessions,
        by_platform=platform_stats,
    )


# =============================================================
# 数据采集端点
# =============================================================

@router.post("/subscribe/twitter")
async def subscribe_twitter_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_id: str = Query(..., description="Twitter 用户 ID"),
    screen_name: str = Query(..., description="用户名"),
    name: str = Query(..., description="显示名称"),
    description: Optional[str] = Query(None, description="订阅描述"),
    fetch_interval: int = Query(3600, description="采集间隔（秒）"),
    db: AsyncSession = Depends(get_db),
):
    """
    添加 Twitter 用户订阅

    从 Twitter 页面搜索用户后，使用此接口添加订阅
    """
    from app.services.social_service import SocialService

    result = await SocialService.add_twitter_subscription(
        db=db,
        user_id=user_id,
        screen_name=screen_name,
        name=name,
        description=description,
        fetch_interval=fetch_interval,
        owner_user_id=current_user.id,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.post("/subscribe/telegram")
async def subscribe_telegram_channel(
    current_user: Annotated[User, Depends(get_current_active_user)],
    channel_id: int = Query(..., description="频道/群组 ID"),
    title: str = Query(..., description="标题"),
    username: Optional[str] = Query(None, description="用户名"),
    target_type: str = Query("channel", description="类型：channel/group"),
    description: Optional[str] = Query(None, description="订阅描述"),
    fetch_interval: int = Query(1800, description="采集间隔（秒）"),
    db: AsyncSession = Depends(get_db),
):
    """
    添加 Telegram 频道/群组订阅

    从 Telegram 页面搜索频道后，使用此接口添加订阅
    """
    from app.services.social_service import SocialService

    result = await SocialService.add_telegram_subscription(
        db=db,
        channel_id=channel_id,
        title=title,
        username=username,
        target_type=target_type,
        description=description,
        fetch_interval=fetch_interval,
        owner_user_id=current_user.id,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.post("/sessions/{session_id}/fetch")
async def fetch_session_messages(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    手动触发单个订阅的数据采集

    Note: 管理员可触发所有会话，普通用户只能触发自己的会话。
    """
    # 验证会话存在且用户有权限
    session_stmt = select(SocialSession).where(SocialSession.id == session_id)
    session_stmt = apply_user_filter(session_stmt, current_user, SocialSession)
    session_result = await db.execute(session_stmt)
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")

    from app.tasks.social_tasks import trigger_subscription_fetch

    result = await trigger_subscription_fetch(session_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.post("/fetch-all")
async def fetch_all_active_subscriptions(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    手动触发所有活跃订阅的数据采集

    Note: 需要登录认证。
    """
    from app.tasks.social_tasks import trigger_social_fetch_now

    result = await trigger_social_fetch_now()

    return result


@router.get("/messages")
async def search_all_messages(
    current_user: Annotated[User, Depends(get_current_active_user)],
    platform: Optional[str] = Query(None, description="平台过滤：twitter/telegram"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    subscription_id: Optional[int] = Query(None, description="订阅 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    """
    搜索所有消息

    支持按平台、关键词、订阅 ID 过滤
    Note: 管理员可搜索所有消息，普通用户只能搜索自己会话的消息。
    """
    from app.services.social_service import SocialService

    platform_enum = None
    if platform:
        platform_enum = Platform(platform)

    # 传递用户信息用于数据过滤
    user_id = None if current_user.is_admin else current_user.id

    result = await SocialService.get_messages(
        db=db,
        subscription_id=subscription_id,
        platform=platform_enum,
        keyword=keyword,
        limit=page_size,
        offset=(page - 1) * page_size,
        user_id=user_id,
    )

    total = result.get("total", 0)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "data": result.get("messages", []),
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# =============================================================
# 辅助函数
# =============================================================

def _convert_message(message: SocialMessage) -> SocialMessageResponse:
    """
    将 SocialMessage 模型转换为响应模型

    处理 JSON 字段的解析。
    """
    data = {
        "id": message.id,
        "session_id": message.session_id,
        "message_id": message.message_id,
        "author_id": message.author_id,
        "author_name": message.author_name,
        "author_username": message.author_username,
        "content": message.content,
        "content_html": message.content_html,
        "reply_count": message.reply_count,
        "repost_count": message.repost_count,
        "like_count": message.like_count,
        "view_count": message.view_count,
        "reply_to_id": message.reply_to_id,
        "repost_of_id": message.repost_of_id,
        "posted_at": message.posted_at,
        "fetched_at": message.fetched_at,
    }

    # 解析 JSON 字段
    if message.media_urls:
        try:
            data["media_urls"] = json.loads(message.media_urls)
        except json.JSONDecodeError:
            data["media_urls"] = None

    if message.media_local_paths:
        try:
            data["media_local_paths"] = json.loads(message.media_local_paths)
        except json.JSONDecodeError:
            data["media_local_paths"] = None

    return SocialMessageResponse(**data)
