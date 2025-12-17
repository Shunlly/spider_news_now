"""
社交会话模型 - Twitter/Telegram 会话数据
Social Session Model - Twitter/Telegram Session Data

遵循宪法 II.B 异构数据建模：
- 社交数据采用 Session 模式，与新闻 Article 模式区分
- Session 包含多个 Message，支持时间线展示
- 数据隔离：通过 user_id 关联到创建者
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def generate_uuid() -> str:
    """生成 UUID 字符串"""
    return str(uuid.uuid4())

if TYPE_CHECKING:
    from app.models.social_message import SocialMessage
    from app.models.user import User


class Platform(str, Enum):
    """社交平台枚举"""
    TWITTER = "twitter"
    TELEGRAM = "telegram"


class SessionStatus(str, Enum):
    """会话状态枚举"""
    ACTIVE = "active"      # 活跃采集中
    PAUSED = "paused"      # 暂停采集
    COMPLETED = "completed"  # 采集完成
    ERROR = "error"        # 采集出错


class TargetType(str, Enum):
    """目标类型枚举"""
    USER = "user"          # 用户时间线
    CHANNEL = "channel"    # 频道
    GROUP = "group"        # 群组
    HASHTAG = "hashtag"    # 话题标签


class SocialSession(Base):
    """
    社交数据会话实体

    代表一个社交媒体数据采集会话，如：
    - Twitter 用户时间线
    - Telegram 频道/群组

    每个 Session 包含多条 Message。
    数据隔离：通过 user_id 关联到创建者
    """

    __tablename__ = "social_sessions"

    # 主键 (UUID)
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid,
        comment="主键UUID"
    )

    # 用户关联（逻辑外键，数据隔离）
    # ForeignKey 用于 ORM 关系映射，但数据库层面不创建约束
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="所属用户UUID"
    )

    # 会话标识
    session_key: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False,
        comment="会话唯一标识，如 twitter:@username 或 telegram:channel_id"
    )

    # 平台信息
    platform: Mapped[Platform] = mapped_column(
        SQLEnum(Platform, values_callable=lambda x: [e.value for e in x]),
        nullable=False, index=True,
        comment="社交平台类型"
    )

    # 目标账号/频道信息
    target_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="目标账号 ID 或频道 ID"
    )
    target_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="目标显示名称"
    )
    target_username: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="目标用户名（如 @username）"
    )
    target_type: Mapped[TargetType] = mapped_column(
        SQLEnum(TargetType, values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=TargetType.USER,
        comment="目标类型：用户、频道、群组、话题"
    )

    # 会话配置
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="会话描述/备注"
    )

    # 状态信息
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=SessionStatus.ACTIVE,
        index=True,
        comment="会话状态"
    )

    # 统计信息
    message_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="消息总数"
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="最后一条消息时间"
    )

    # 采集配置
    fetch_interval: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3600,
        comment="采集间隔（秒）"
    )
    last_fetch_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="最后采集时间"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # 关联关系
    owner: Mapped["User"] = relationship("User", back_populates="social_sessions")
    messages: Mapped[List["SocialMessage"]] = relationship(
        "SocialMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # 索引定义
    __table_args__ = (
        Index("idx_platform_status", "platform", "status"),
        Index("idx_platform_target", "platform", "target_id"),
        Index("idx_session_user_platform", "user_id", "platform"),
        {"comment": "社交数据会话表"},
    )

    def __repr__(self) -> str:
        return (
            f"<SocialSession(id={self.id}, "
            f"platform='{self.platform.value}', "
            f"target='{self.target_name}')>"
        )
