"""
租户模型 - Tenant SQLAlchemy Model
Tenant Model for Multi-tenancy Support

遵循宪法要求：
- 类型提示完整
- 中文注释说明核心逻辑

租户是多租户 SaaS 系统的核心实体，用于数据隔离。
所有业务数据表通过 tenant_id 外键关联到此表实现数据隔离。
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Tenant(Base):
    """
    租户/组织实体 - 多租户数据隔离的核心

    用于多租户数据隔离，所有业务数据都归属于特定租户。
    每个租户可以有多个用户，数据完全隔离。
    """

    __tablename__ = "tenants"

    # 主键 - 自增整数
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
        comment="租户ID"
    )

    # 租户名称 - 唯一标识
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        comment="租户名称（唯一）"
    )

    # 显示名称 - 用于UI展示
    display_name: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        comment="显示名称"
    )

    # 配额配置 - JSON格式存储租户级配额设置
    # 示例: {"daily_limit": 1000, "concurrent_limit": 5}
    quota_config: Mapped[dict] = mapped_column(
        JSON, nullable=False,
        default={"daily_limit": 1000, "concurrent_limit": 5},
        comment="租户级配额配置"
    )

    # 租户设置 - JSON格式存储租户自定义设置
    settings: Mapped[dict] = mapped_column(
        JSON, nullable=False, default={},
        comment="租户自定义设置"
    )

    # 是否激活 - 用于软禁用租户
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="是否激活"
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

    # 关联关系 - 租户拥有的用户
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="tenant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name='{self.name}', is_active={self.is_active})>"

    def get_daily_limit(self) -> int:
        """获取每日采集配额限制"""
        return self.quota_config.get("daily_limit", 1000)

    def get_concurrent_limit(self) -> int:
        """获取并发任务配额限制"""
        return self.quota_config.get("concurrent_limit", 5)
