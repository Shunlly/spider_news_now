"""
Twitter API 端点
Twitter API Endpoints

提供 Twitter Cookie 认证、用户信息和推文获取功能。
需要登录认证才能访问。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.schemas.twitter import (
    TwitterBaseResponse,
    TwitterConnectRequest,
    TwitterConnectResponse,
    TwitterGetTweetsRequest,
    TwitterGetUserRequest,
    TwitterMediaItem,
    TwitterSearchRequest,
    TwitterStatusResponse,
    TwitterTweet,
    TwitterTweetsResponse,
    TwitterTweetUser,
    TwitterUserInfo,
    TwitterUserResponse,
)
from app.services.quota_service import quota_service
from app.services.twitter_service import get_twitter_service

logger = get_logger(__name__)

router = APIRouter(prefix="/twitter", tags=["twitter"])


# =============================================================
# 认证端点
# =============================================================

@router.post("/connect", response_model=TwitterConnectResponse)
async def connect(
    request: TwitterConnectRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    使用 Cookie 连接 Twitter

    需要提供从浏览器获取的 auth_token 和 ct0 cookie。
    """
    service = get_twitter_service()

    result = await service.connect(
        auth_token=request.auth_token,
        ct0=request.ct0,
        proxy=request.proxy,
    )

    user_info = None
    if result.get("user_info"):
        user_info = TwitterUserInfo(**result["user_info"])

    return TwitterConnectResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
        user_info=user_info,
    )


@router.get("/status", response_model=TwitterStatusResponse)
async def get_status(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    获取连接状态

    返回当前的连接状态和用户信息。
    """
    service = get_twitter_service()

    user_info = None
    if service.user_info:
        user_info = TwitterUserInfo(**service.user_info)

    return TwitterStatusResponse(
        connected=service.is_connected,
        user_info=user_info,
    )


@router.post("/disconnect", response_model=TwitterBaseResponse)
async def disconnect(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    断开连接

    清除 Cookie 信息并断开连接。
    """
    service = get_twitter_service()
    await service.disconnect()

    return TwitterBaseResponse(success=True, message="已断开连接")


# =============================================================
# 用户端点
# =============================================================

@router.post("/user", response_model=TwitterUserResponse)
async def get_user(
    request: TwitterGetUserRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    获取用户信息

    通过用户名获取 Twitter 用户的详细信息。
    """
    service = get_twitter_service()

    if not service.is_connected:
        raise HTTPException(status_code=400, detail="未连接，请先登录")

    result = await service.get_user_by_screen_name(request.screen_name)

    user = None
    if result.get("user"):
        user = TwitterUserInfo(**result["user"])

    return TwitterUserResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
        user=user,
    )


# =============================================================
# 推文端点
# =============================================================

@router.post("/tweets", response_model=TwitterTweetsResponse)
async def get_tweets(
    request: TwitterGetTweetsRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户推文列表

    获取指定用户的推文，支持分页和是否包含转推。
    配额控制：每获取的推文计入每日配额。
    """
    service = get_twitter_service()

    if not service.is_connected:
        raise HTTPException(status_code=400, detail="未连接，请先登录")

    # 配额检查 - Check daily quota
    has_daily_quota, daily_msg, _ = await quota_service.check_daily_quota(
        db, current_user.id
    )
    if not has_daily_quota:
        raise HTTPException(
            status_code=429,
            detail=f"每日配额已用尽: {daily_msg}"
        )

    # 配额检查 - Check concurrent quota
    has_concurrent_quota, concurrent_msg, _ = await quota_service.check_concurrent_quota(
        db, current_user.id
    )
    if not has_concurrent_quota:
        raise HTTPException(
            status_code=429,
            detail=f"并发任务数已达上限: {concurrent_msg}"
        )

    # 获取并发槽位
    acquired, acquire_msg = await quota_service.acquire_concurrent_slot(db, current_user.id)
    if not acquired:
        raise HTTPException(
            status_code=429,
            detail=f"无法获取并发槽位: {acquire_msg}"
        )

    try:
        result = await service.get_user_tweets(
            user_id=request.user_id,
            count=request.count,
            cursor=request.cursor,
            include_retweets=request.include_retweets,
        )

        tweets = []
        for t in result.get("tweets", []):
            # 解析用户信息
            user = None
            if t.get("user"):
                user = TwitterTweetUser(**t["user"])

            # 解析媒体
            media = [TwitterMediaItem(**m) for m in t.get("media", [])]

            tweets.append(TwitterTweet(
                id=t["id"],
                conversation_id=t.get("conversation_id"),
                text=t.get("text"),
                created_at=t.get("created_at"),
                user=user,
                favorite_count=t.get("favorite_count", 0),
                retweet_count=t.get("retweet_count", 0),
                reply_count=t.get("reply_count", 0),
                views_count=t.get("views_count"),
                media=media,
                is_retweet=t.get("is_retweet", False),
                urls=t.get("urls", []),
            ))

        # 消耗配额（按推文数量）
        if tweets:
            await quota_service.consume_daily_quota(db, current_user.id, len(tweets))

        return TwitterTweetsResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            tweets=tweets,
            next_cursor=result.get("next_cursor"),
            total=len(tweets),
        )
    finally:
        # 释放并发槽位
        await quota_service.release_concurrent_slot(db, current_user.id)


@router.post("/search", response_model=TwitterTweetsResponse)
async def search_tweets(
    request: TwitterSearchRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    搜索推文

    使用关键词搜索推文，支持分页。
    配额控制：每获取的推文计入每日配额。
    """
    service = get_twitter_service()

    if not service.is_connected:
        raise HTTPException(status_code=400, detail="未连接，请先登录")

    # 配额检查 - Check daily quota
    has_daily_quota, daily_msg, _ = await quota_service.check_daily_quota(
        db, current_user.id
    )
    if not has_daily_quota:
        raise HTTPException(
            status_code=429,
            detail=f"每日配额已用尽: {daily_msg}"
        )

    # 配额检查 - Check concurrent quota
    has_concurrent_quota, concurrent_msg, _ = await quota_service.check_concurrent_quota(
        db, current_user.id
    )
    if not has_concurrent_quota:
        raise HTTPException(
            status_code=429,
            detail=f"并发任务数已达上限: {concurrent_msg}"
        )

    # 获取并发槽位
    acquired, acquire_msg = await quota_service.acquire_concurrent_slot(db, current_user.id)
    if not acquired:
        raise HTTPException(
            status_code=429,
            detail=f"无法获取并发槽位: {acquire_msg}"
        )

    try:
        result = await service.search_tweets(
            query=request.query,
            count=request.count,
            cursor=request.cursor,
        )

        tweets = []
        for t in result.get("tweets", []):
            user = None
            if t.get("user"):
                user = TwitterTweetUser(**t["user"])

            media = [TwitterMediaItem(**m) for m in t.get("media", [])]

            tweets.append(TwitterTweet(
                id=t["id"],
                conversation_id=t.get("conversation_id"),
                text=t.get("text"),
                created_at=t.get("created_at"),
                user=user,
                favorite_count=t.get("favorite_count", 0),
                retweet_count=t.get("retweet_count", 0),
                reply_count=t.get("reply_count", 0),
                views_count=t.get("views_count"),
                media=media,
                is_retweet=t.get("is_retweet", False),
                urls=t.get("urls", []),
            ))

        # 消耗配额（按推文数量）
        if tweets:
            await quota_service.consume_daily_quota(db, current_user.id, len(tweets))

        return TwitterTweetsResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            tweets=tweets,
            next_cursor=result.get("next_cursor"),
            total=len(tweets),
        )
    finally:
        # 释放并发槽位
        await quota_service.release_concurrent_slot(db, current_user.id)
