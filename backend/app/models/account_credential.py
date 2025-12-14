"""
账号凭证模型 - 社交平台账号管理
Account Credentials Model - Social Platform Account Management

遵循宪法 II.C 安全要求：
- 凭证加密存储
- 支持多账号轮换
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.social_session import Platform


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
    """

    __tablename__ = "account_credentials"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

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
    # 不同平台存储不同字段，使用 JSON 格式
    # Twitter: api_key, api_secret, access_token, access_secret, bearer_token
    # Telegram: api_id, api_hash, phone_number, session_string
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
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="最后使用时间"
    )
    last_error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="最后错误时间"
    )
    last_error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="最后错误信息"
    )

    # 限流信息
    rate_limit_reset_at: Mapped[Optional[datetime]] = mapped_column(
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

    # 索引定义
    __table_args__ = (
        Index("idx_platform_status", "platform", "status"),
        Index("idx_platform_default", "platform", "is_default"),
        {"comment": "社交平台账号凭证表"},
    )

    def __repr__(self) -> str:
        return (
            f"<AccountCredential(id={self.id}, "
            f"name='{self.name}', "
            f"platform='{self.platform.value}', "
            f"status='{self.status.value}')>"
        )
