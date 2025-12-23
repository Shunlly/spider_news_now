"""
用户模型 - User SQLAlchemy Model
User Model for Authentication and RBAC

遵循宪法要求：
- 类型提示完整
- 中文注释说明核心逻辑

支持多租户 SaaS 系统，用户可属于租户或为超级管理员（无租户）。
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.account_credential import AccountCredential
    from app.models.audit import AuditLog
    from app.models.export_task import ExportTask
    from app.models.news_article import NewsArticle
    from app.models.news_source import NewsSource
    from app.models.proxy_config import ProxyConfig
    from app.models.quota import Quota
    from app.models.role import Role
    from app.models.scraper_run import ScraperRun
    from app.models.social_session import SocialSession
    from app.models.tenant import Tenant


class UserRole(str, Enum):
    """
    用户角色枚举 (向后兼容)
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
    支持多租户：普通用户属于某个租户，超级管理员可不属于租户。
    所有业务数据表通过 user_id 外键关联到此表。

    使用 UUID 作为主键，便于分布式扩展和安全性。
    """

    __tablename__ = "users"

    # 主键 - 使用 UUID (CHAR(36))
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid,
        comment="用户UUID"
    )

    # 租户外键 - 超级管理员可为空
    tenant_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True, index=True,
        comment="所属租户ID（超级管理员可为空）"
    )

    # 角色外键 - 关联 Role 表
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id"),
        nullable=False, default=3,  # 默认为普通用户
        comment="角色ID"
    )

    # 用户名 - 唯一标识，用于登录
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False,
        comment="用户名（唯一）"
    )

    # 邮箱 - 用于登录、通知和找回密码
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        comment="邮箱（唯一）"
    )

    # 密码哈希 - 使用 bcrypt 加密存储
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="密码哈希（bcrypt）"
    )

    # 配额等级 - free, basic, pro
    quota_tier: Mapped[str] = mapped_column(
        String(20), nullable=False, default="free",
        comment="配额等级: free, basic, pro"
    )

    # 邮箱是否已验证
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="邮箱是否已验证"
    )

    # 账号状态 - 是否激活
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="是否激活"
    )

    # 邮箱验证 Token
    verification_token: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="邮箱验证Token"
    )

    # 验证 Token 过期时间
    verification_expires: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
        comment="验证Token过期时间"
    )

    # 最后登录时间 - 用于审计
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
        comment="最后登录时间"
    )

    # 登录尝试次数 - 用于防暴力破解
    login_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
        comment="连续登录失败次数"
    )

    # 账号锁定截止时间 - 超过最大尝试次数后锁定
    locked_until: Mapped[datetime | None] = mapped_column(
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

    # 关联关系 - 多租户
    tenant: Mapped[Optional["Tenant"]] = relationship(
        "Tenant", back_populates="users"
    )
    role: Mapped["Role"] = relationship(
        "Role", back_populates="users"
    )
    quota: Mapped[Optional["Quota"]] = relationship(
        "Quota", back_populates="user", uselist=False
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )

    # 关联关系（数据隔离 - 原有）
    news_sources: Mapped[list["NewsSource"]] = relationship(
        "NewsSource", back_populates="owner", cascade="all, delete-orphan"
    )
    news_articles: Mapped[list["NewsArticle"]] = relationship(
        "NewsArticle", back_populates="owner", cascade="all, delete-orphan"
    )
    scraper_runs: Mapped[list["ScraperRun"]] = relationship(
        "ScraperRun", back_populates="owner", cascade="all, delete-orphan"
    )
    social_sessions: Mapped[list["SocialSession"]] = relationship(
        "SocialSession", back_populates="owner", cascade="all, delete-orphan"
    )
    account_credentials: Mapped[list["AccountCredential"]] = relationship(
        "AccountCredential", back_populates="owner", cascade="all, delete-orphan"
    )
    proxy_configs: Mapped[list["ProxyConfig"]] = relationship(
        "ProxyConfig", back_populates="owner", cascade="all, delete-orphan"
    )
    export_tasks: Mapped[list["ExportTask"]] = relationship(
        "ExportTask", back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role_id={self.role_id})>"

    @property
    def is_admin(self) -> bool:
        """检查用户是否为管理员（向后兼容）"""
        # 角色ID 1 = super_admin, 2 = tenant_admin
        return self.role_id in (1, 2)

    @property
    def is_super_admin(self) -> bool:
        """检查用户是否为超级管理员"""
        return self.role_id == 1

    @property
    def is_tenant_admin(self) -> bool:
        """检查用户是否为租户管理员"""
        return self.role_id == 2

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

    def has_permission(self, permission: str) -> bool:
        """
        检查用户是否拥有指定权限

        Args:
            permission: 权限点字符串，如 "user:create"

        Returns:
            True if 用户拥有该权限
        """
        if self.role:
            return self.role.has_permission(permission)
        return False
