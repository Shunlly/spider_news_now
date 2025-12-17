"""
用户模型 - User SQLAlchemy Model
User Model for Authentication and RBAC

遵循宪法要求：
- 类型提示完整
- 中文注释说明核心逻辑
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.news_source import NewsSource
    from app.models.news_article import NewsArticle
    from app.models.scraper_run import ScraperRun
    from app.models.social_session import SocialSession
    from app.models.account_credential import AccountCredential
    from app.models.proxy_config import ProxyConfig
    from app.models.export_task import ExportTask


class UserRole(str, Enum):
    """
    用户角色枚举
    - ADMIN: 管理员，拥有上帝视角，可查看所有数据
    - USER: 普通用户，只能查看自己的数据
    """
    ADMIN = "admin"
    USER = "user"


# 系统用户 UUID（用于后台任务）
SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000001"


def generate_uuid() -> str:
    """生成 UUID 字符串"""
    return str(uuid.uuid4())


class User(Base):
    """
    用户实体 - 系统核心认证模型

    用于用户认证、角色权限控制和数据隔离。
    所有业务数据表通过 user_id 外键关联到此表。

    使用 UUID 作为主键，便于分布式扩展和安全性。
    """

    __tablename__ = "users"

    # 主键 - 使用 UUID (CHAR(36))
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid,
        comment="用户UUID"
    )

    # 用户名 - 唯一标识，用于登录
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False,
        comment="用户名（唯一）"
    )

    # 邮箱 - 可选，用于通知和找回密码
    email: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True,
        comment="邮箱（可选）"
    )

    # 密码哈希 - 使用 bcrypt 加密存储
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="密码哈希（bcrypt）"
    )

    # 用户角色 - admin 或 user
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=UserRole.USER, index=True,
        comment="用户角色"
    )

    # 账号状态 - 是否激活
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="是否激活"
    )

    # 最后登录时间 - 用于审计
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="最后登录时间"
    )

    # 登录尝试次数 - 用于防暴力破解
    login_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
        comment="连续登录失败次数"
    )

    # 账号锁定截止时间 - 超过最大尝试次数后锁定
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="账号锁定截止时间"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(),
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now(),
        comment="更新时间"
    )

    # 关联关系（数据隔离）
    news_sources: Mapped[List["NewsSource"]] = relationship(
        "NewsSource", back_populates="owner", cascade="all, delete-orphan"
    )
    news_articles: Mapped[List["NewsArticle"]] = relationship(
        "NewsArticle", back_populates="owner", cascade="all, delete-orphan"
    )
    scraper_runs: Mapped[List["ScraperRun"]] = relationship(
        "ScraperRun", back_populates="owner", cascade="all, delete-orphan"
    )
    social_sessions: Mapped[List["SocialSession"]] = relationship(
        "SocialSession", back_populates="owner", cascade="all, delete-orphan"
    )
    account_credentials: Mapped[List["AccountCredential"]] = relationship(
        "AccountCredential", back_populates="owner", cascade="all, delete-orphan"
    )
    proxy_configs: Mapped[List["ProxyConfig"]] = relationship(
        "ProxyConfig", back_populates="owner", cascade="all, delete-orphan"
    )
    export_tasks: Mapped[List["ExportTask"]] = relationship(
        "ExportTask", back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"

    @property
    def is_admin(self) -> bool:
        """检查用户是否为管理员"""
        return self.role == UserRole.ADMIN

    def is_locked(self) -> bool:
        """
        检查账号是否被锁定

        Returns:
            True if 账号当前处于锁定状态
        """
        if self.locked_until is None:
            return False
        return datetime.now() < self.locked_until

    def get_lock_remaining_seconds(self) -> int:
        """获取锁定剩余时间（秒）"""
        if self.locked_until is None:
            return 0
        remaining = (self.locked_until - datetime.now()).total_seconds()
        return max(0, int(remaining))
