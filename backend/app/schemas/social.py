"""
社交数据 Pydantic Schema
Social Data Pydantic Schemas

定义社交会话和消息的请求/响应模型。
遵循宪法 II.B 异构数据建模规范。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.social_session import Platform, SessionStatus


# =============================================================
# 基础模型
# =============================================================

class SocialMessageBase(BaseModel):
    """社交消息基础模型"""
    content: Optional[str] = Field(None, description="消息文本内容")
    media_urls: Optional[List[str]] = Field(None, description="媒体 URL 列表")


class SocialSessionBase(BaseModel):
    """社交会话基础模型"""
    platform: Platform = Field(..., description="社交平台类型")
    target_id: str = Field(..., description="目标账号/频道 ID")
    target_name: str = Field(..., description="目标显示名称")
    target_username: Optional[str] = Field(None, description="目标用户名")
    description: Optional[str] = Field(None, description="会话描述")
    fetch_interval: int = Field(3600, ge=60, le=86400, description="采集间隔（秒）")


# =============================================================
# 请求模型
# =============================================================

class SocialSessionCreate(SocialSessionBase):
    """创建社交会话请求"""
    pass


class SocialSessionUpdate(BaseModel):
    """更新社交会话请求"""
    target_name: Optional[str] = Field(None, description="目标显示名称")
    description: Optional[str] = Field(None, description="会话描述")
    fetch_interval: Optional[int] = Field(None, ge=60, le=86400, description="采集间隔（秒）")
    status: Optional[SessionStatus] = Field(None, description="会话状态")


# =============================================================
# 响应模型
# =============================================================

class SocialMessageResponse(BaseModel):
    """社交消息响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    message_id: str = Field(..., description="平台消息 ID")

    # 发送者信息
    author_id: str
    author_name: str
    author_username: Optional[str] = None

    # 消息内容
    content: Optional[str] = None
    content_html: Optional[str] = None

    # 媒体附件（从 JSON 字符串转换为列表）
    media_urls: Optional[List[str]] = None
    media_local_paths: Optional[List[str]] = None

    # 交互数据
    reply_count: int = 0
    repost_count: int = 0
    like_count: int = 0
    view_count: int = 0

    # 引用关系
    reply_to_id: Optional[str] = None
    repost_of_id: Optional[str] = None

    # 时间戳
    posted_at: datetime
    fetched_at: datetime


class SocialSessionResponse(BaseModel):
    """社交会话响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_key: str
    platform: Platform
    target_id: str
    target_name: str
    target_username: Optional[str] = None
    description: Optional[str] = None
    status: SessionStatus
    message_count: int
    last_message_at: Optional[datetime] = None
    fetch_interval: int
    last_fetch_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SocialSessionDetailResponse(SocialSessionResponse):
    """社交会话详情响应（包含最近消息）"""
    recent_messages: List[SocialMessageResponse] = Field(
        default_factory=list,
        description="最近的消息列表"
    )


class SocialSessionListResponse(BaseModel):
    """社交会话列表响应"""
    data: List[SocialSessionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SocialMessageListResponse(BaseModel):
    """社交消息列表响应"""
    data: List[SocialMessageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    session: Optional[SocialSessionResponse] = Field(
        None, description="所属会话信息"
    )


# =============================================================
# 统计和汇总模型
# =============================================================

class PlatformStats(BaseModel):
    """平台统计"""
    platform: Platform
    session_count: int
    message_count: int
    active_sessions: int


class SocialStatisticsResponse(BaseModel):
    """社交数据统计响应"""
    total_sessions: int
    total_messages: int
    active_sessions: int
    by_platform: List[PlatformStats]
    recent_activity: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="最近活动记录"
    )


# =============================================================
# 操作响应模型
# =============================================================

class SocialSessionActionResponse(BaseModel):
    """会话操作响应"""
    success: bool
    message: str
    session_id: Optional[int] = None
    session: Optional[SocialSessionResponse] = None
