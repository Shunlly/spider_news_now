"""
User Data Relation Models - 用户数据关系模型

管理用户对数据的个人化操作：收藏、标签、笔记。
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import CHAR, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.infrastructure.database import Base


class UserDataRelation(Base):
    """
    用户数据关系

    存储用户对 DataPointer 的个人化操作：
    - 收藏/书签
    - 自定义标签
    - 个人笔记
    - 阅读状态
    """
    __tablename__ = "user_data_relations"

    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # 关联的用户和数据指针
    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID"
    )
    pointer_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("data_pointers.id", ondelete="CASCADE"),
        nullable=False,
        comment="数据指针ID"
    )

    # 收藏状态
    is_favorited: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否收藏"
    )
    is_bookmarked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否书签"
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已读"
    )

    # 用户标签（JSON 数组）
    user_tags: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="用户自定义标签列表"
    )

    # 用户笔记
    user_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="用户笔记"
    )

    # 评分（可选）
    rating: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="用户评分 1-5"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="阅读时间"
    )

    __table_args__ = (
        # 每个用户对每个数据只有一条关系记录
        UniqueConstraint("user_id", "pointer_id", name="uq_user_data_relation"),
        # 常用查询索引
        Index("ix_user_data_user", "user_id"),
        Index("ix_user_data_pointer", "pointer_id"),
        Index("ix_user_data_favorited", "user_id", "is_favorited"),
        Index("ix_user_data_bookmarked", "user_id", "is_bookmarked"),
    )

    def __repr__(self) -> str:
        return f"<UserDataRelation user={self.user_id} pointer={self.pointer_id}>"
