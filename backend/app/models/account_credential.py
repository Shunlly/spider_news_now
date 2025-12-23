"""
账号凭证模型 - 社交平台账号管理
Account Credentials Model - Social Platform Account Management

遵循宪法 II.C 安全要求：
- 凭证加密存储
- 支持多账号轮换
- 数据隔离：通过 user_id 关联到创建者
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.social_session import Platform


def generate_uuid() -> str:
    """生成 UUID 字符串"""
    return str(uuid.uuid4())

if TYPE_CHECKING:
    from app.models.user import User


class CredentialStatus(str, Enum):
    """凭证状态枚举"""
    ACTIVE = "active"        # 可用
    RATE_LIMITED = "rate_limited"  # 限流中
    EXPIRED = "expired"      # 已过期
    DISABLED = "disabled"    # 已禁用
    ERROR = "error"          # 错误


class AccountCredential(Base):
    """
    社交平台账号凭证实体

    安全存储 Twitter/Telegram 等平台的 API 凭证。
    支持多账号轮换以应对 API 限流。
    数据隔离：通过 user_id 关联到创建者
    """

    __tablename__ = "account_credentials"

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

    # 凭证标识
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="凭证名称（用于识别）"
    )

    # 平台信息
    platform: Mapped[Platform] = mapped_column(
        SQLEnum(Platform), nullable=False, index=True,
        comment="社交平台类型"
    )

    # 状态
    status: Mapped[CredentialStatus] = mapped_column(
        SQLEnum(CredentialStatus),
        nullable=False,
        default=CredentialStatus.ACTIVE,
        index=True,
        comment="凭证状态"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="是否为默认凭证"
    )

    # 凭证数据（加密存储）
    credentials_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="加密的凭证 JSON 数据"
    )

    # 使用统计
    request_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="请求次数"
    )
    error_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="错误次数"
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
        comment="最后使用时间"
    )
    last_error_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
        comment="最后错误时间"
    )
    last_error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="最后错误信息"
    )

    # 限流信息
    rate_limit_reset_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
        comment="限流重置时间"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # 关联关系
    owner: Mapped["User"] = relationship("User", back_populates="account_credentials")

    # 索引定义
    __table_args__ = (
        Index("idx_cred_platform_status", "platform", "status"),
        Index("idx_cred_platform_default", "platform", "is_default"),
        {"comment": "社交平台账号凭证表"},
    )

    def __repr__(self) -> str:
        return (
            f"<AccountCredential(id={self.id}, "
            f"name='{self.name}', "
            f"platform='{self.platform.value}', "
            f"status='{self.status.value}')>"
        )
