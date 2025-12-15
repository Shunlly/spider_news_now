"""
Telegram API 端点
Telegram API Endpoints

提供 Telegram 用户认证、频道管理和消息获取功能。
基于 Telethon MTProto API 实现。
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.logging import get_logger
from app.services.telegram_service import get_telegram_service
from app.schemas.telegram import (
    TelegramInitRequest,
    TelegramInitResponse,
    TelegramSendCodeRequest,
    TelegramSendCodeResponse,
    TelegramSignInRequest,
    TelegramSignInResponse,
    TelegramConnectRequest,
    TelegramConnectResponse,
    TelegramDialogsResponse,
    TelegramDialogResponse,
    TelegramSearchRequest,
    TelegramSearchResponse,
    TelegramEntityResponse,
    TelegramJoinRequest,
    TelegramLeaveRequest,
    TelegramBaseResponse,
    TelegramMessagesRequest,
    TelegramMessagesResponse,
    TelegramMessageResponse,
    TelegramStatusResponse,
    TelegramUserInfo,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


# =============================================================
# 认证端点
# =============================================================

@router.post("/init", response_model=TelegramInitResponse)
async def init_client(request: TelegramInitRequest):
    """
    初始化 Telegram 客户端

    使用 API ID 和 API Hash 初始化客户端。
    可选提供 StringSession 恢复之前的会话。
    """
    service = get_telegram_service()

    result = await service.init_client(
        api_id=request.api_id,
        api_hash=request.api_hash,
        string_session=request.string_session or "",
        proxy=request.proxy,
    )

    if result:
        logger.info("Telegram client initialized successfully")
        return TelegramInitResponse(success=True, message="客户端初始化成功")
    else:
        return TelegramInitResponse(success=False, message="客户端初始化失败")


@router.post("/send-code", response_model=TelegramSendCodeResponse)
async def send_code(request: TelegramSendCodeRequest):
    """
    发送登录验证码

    向指定手机号发送登录验证码。
    """
    service = get_telegram_service()

    if not service.client:
        raise HTTPException(status_code=400, detail="请先初始化客户端")

    result = await service.send_code(request.phone)

    return TelegramSendCodeResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
        phone_code_hash=result.get("phone_code_hash"),
    )


@router.post("/sign-in", response_model=TelegramSignInResponse)
async def sign_in(request: TelegramSignInRequest):
    """
    验证登录

    使用验证码完成登录，成功后返回 StringSession。
    """
    service = get_telegram_service()

    if not service.client:
        raise HTTPException(status_code=400, detail="请先初始化客户端")

    result = await service.sign_in(
        phone=request.phone,
        code=request.code,
        phone_code_hash=request.phone_code_hash,
        password=request.password,
    )

    user_info = None
    if result.get("user_info"):
        user_info = TelegramUserInfo(**result["user_info"])

    return TelegramSignInResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
        string_session=result.get("string_session"),
        user_info=user_info,
        need_password=result.get("need_password", False),
    )


@router.post("/connect", response_model=TelegramConnectResponse)
async def connect_with_session(request: TelegramConnectRequest):
    """
    使用 StringSession 连接

    使用之前保存的 StringSession 恢复会话。
    """
    service = get_telegram_service()

    # 先初始化客户端
    init_result = await service.init_client(
        api_id=request.api_id,
        api_hash=request.api_hash,
        string_session=request.string_session,
        proxy=request.proxy,
    )

    if not init_result:
        return TelegramConnectResponse(success=False, message="客户端初始化失败")

    # 验证 session
    result = await service.connect_with_session(request.string_session)

    user_info = None
    if result.get("user_info"):
        user_info = TelegramUserInfo(**result["user_info"])

    return TelegramConnectResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
        user_info=user_info,
    )


@router.get("/status", response_model=TelegramStatusResponse)
async def get_status():
    """
    获取连接状态

    返回当前客户端的连接状态和用户信息。
    """
    service = get_telegram_service()

    user_info = None
    if service.user_info:
        user_info = TelegramUserInfo(**service.user_info)

    return TelegramStatusResponse(
        connected=service.is_connected,
        user_info=user_info,
    )


@router.post("/disconnect", response_model=TelegramBaseResponse)
async def disconnect():
    """
    断开连接

    断开 Telegram 客户端连接。
    """
    service = get_telegram_service()
    await service.disconnect()

    return TelegramBaseResponse(success=True, message="已断开连接")


# =============================================================
# 频道/对话管理端点
# =============================================================

@router.get("/dialogs", response_model=TelegramDialogsResponse)
async def get_dialogs(
    limit: int = Query(100, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    filter_type: Optional[str] = Query(None, description="过滤类型: channel/group/user"),
):
    """
    获取已加入的对话列表

    返回用户已加入的频道、群组和私聊列表。
    """
    service = get_telegram_service()

    if not service.is_connected:
        raise HTTPException(status_code=400, detail="未连接，请先登录")

    dialogs = await service.get_dialogs(
        limit=limit,
        offset=offset,
        filter_type=filter_type,
    )

    return TelegramDialogsResponse(
        success=True,
        message="获取成功",
        dialogs=[TelegramDialogResponse(**d) for d in dialogs],
        total=len(dialogs),
    )


@router.post("/search", response_model=TelegramSearchResponse)
async def search_channel(request: TelegramSearchRequest):
    """
    搜索频道/用户

    通过用户名搜索频道或用户。
    """
    service = get_telegram_service()

    if not service.is_connected:
        raise HTTPException(status_code=400, detail="未连接，请先登录")

    result = await service.search_channel(request.username)

    entity = None
    if result.get("entity"):
        entity = TelegramEntityResponse(**result["entity"])

    return TelegramSearchResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
        entity=entity,
    )


@router.post("/join", response_model=TelegramBaseResponse)
async def join_channel(request: TelegramJoinRequest):
    """
    加入频道

    加入指定的公开频道或群组。
    """
    service = get_telegram_service()

    if not service.is_connected:
        raise HTTPException(status_code=400, detail="未连接，请先登录")

    result = await service.join_channel(request.channel)

    return TelegramBaseResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
    )


@router.post("/leave", response_model=TelegramBaseResponse)
async def leave_channel(request: TelegramLeaveRequest):
    """
    退出频道

    退出指定的频道或群组。
    """
    service = get_telegram_service()

    if not service.is_connected:
        raise HTTPException(status_code=400, detail="未连接，请先登录")

    result = await service.leave_channel(request.channel_id)

    return TelegramBaseResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
    )


# =============================================================
# 消息获取端点
# =============================================================

@router.get("/messages/{channel_id}", response_model=TelegramMessagesResponse)
async def get_messages(
    channel_id: int,
    limit: int = Query(100, ge=1, le=1000, description="消息数量限制"),
    offset_id: int = Query(0, description="从指定消息 ID 开始获取"),
    min_date: Optional[datetime] = Query(None, description="最早日期"),
    max_date: Optional[datetime] = Query(None, description="最晚日期"),
):
    """
    获取频道历史消息

    获取指定频道的历史消息。
    """
    service = get_telegram_service()

    if not service.is_connected:
        raise HTTPException(status_code=400, detail="未连接，请先登录")

    messages = await service.get_messages(
        channel_id=channel_id,
        limit=limit,
        offset_id=offset_id,
        min_date=min_date,
        max_date=max_date,
    )

    return TelegramMessagesResponse(
        success=True,
        message="获取成功",
        messages=[TelegramMessageResponse(**m) for m in messages],
        total=len(messages),
    )


@router.post("/messages", response_model=TelegramMessagesResponse)
async def get_messages_post(request: TelegramMessagesRequest):
    """
    获取频道历史消息（POST 方式）

    支持更复杂的查询参数。
    """
    service = get_telegram_service()

    if not service.is_connected:
        raise HTTPException(status_code=400, detail="未连接，请先登录")

    messages = await service.get_messages(
        channel_id=request.channel_id,
        limit=request.limit,
        offset_id=request.offset_id,
        min_date=request.min_date,
        max_date=request.max_date,
    )

    return TelegramMessagesResponse(
        success=True,
        message="获取成功",
        messages=[TelegramMessageResponse(**m) for m in messages],
        total=len(messages),
    )
