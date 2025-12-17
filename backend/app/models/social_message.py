"""
社交消息模型 - Twitter/Telegram 消息数据
Social Message Model - Twitter/Telegram Message Data

遵循宪法 II.B 异构数据建模：
- 消息属于某个 Session，支持时间线展示
- 存储原始消息内容和媒体附件
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
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
    from app.models.social_session import SocialSession


class SocialMessage(Base):
    """
    社交消息实体

    存储 Twitter 推文或 Telegram 消息的详细信息。
    通过 session_id 关联到对应的采集会话。
    """

    __tablename__ = "social_messages"

    # 主键 (UUID)
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid,
        comment="主键UUID"
    )

    # 关联会话（逻辑外键）
    # ForeignKey 用于 ORM 关系映射，但数据库层面不创建约束
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("social_sessions.id"),
        nullable=False,
        index=True,
        comment="所属会话UUID"
    )

    # 消息标识（用于去重）
    message_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="平台消息 ID"
    )
    message_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False,
        comment="消息哈希（用于去重）"
    )

    # 发送者信息
    author_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="发送者 ID"
    )
    author_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="发送者显示名"
    )
    author_username: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="发送者用户名"
    )

    # 消息内容
    content: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="消息文本内容"
    )
    content_html: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="消息 HTML 格式（保留格式化）"
    )

    # SimHash 指纹（用于相似内容检测）
    simhash: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, index=True,
        comment="内容 SimHash 指纹"
    )

    # 媒体附件（JSON 格式存储）
    media_urls: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="媒体 URL 列表（JSON 数组）"
    )
    media_local_paths: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="本地存储路径列表（JSON 数组）"
    )

    # 交互数据
    reply_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="回复数"
    )
    repost_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="转发数"
    )
    like_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="点赞数"
    )
    view_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="浏览数"
    )

    # 引用/回复关系
    reply_to_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="回复的消息 ID"
    )
    repost_of_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="转发的原消息 ID"
    )

    # 原始数据（用于调试和数据恢复）
    raw_data: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="原始 JSON 数据"
    )

    # 时间戳
    posted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True,
        comment="消息发布时间"
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(),
        comment="消息采集时间"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # 关联关系
    session: Mapped["SocialSession"] = relationship(
        "SocialSession",
        back_populates="messages",
    )

    # 索引定义
    __table_args__ = (
        Index("idx_session_posted", "session_id", "posted_at"),
        Index("idx_author_posted", "author_id", "posted_at"),
        Index("idx_session_message", "session_id", "message_id", unique=True),
        {"comment": "社交消息表"},
    )

    def __repr__(self) -> str:
        content_preview = (self.content[:30] + "...") if self.content and len(self.content) > 30 else self.content
        return (
            f"<SocialMessage(id={self.id}, "
            f"author='{self.author_name}', "
            f"content='{content_preview}')>"
        )
