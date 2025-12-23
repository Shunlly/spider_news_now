"""
角色模型 - Role SQLAlchemy Model
Role Model for RBAC Permission System

遵循宪法要求：
- 类型提示完整
- 中文注释说明核心逻辑

角色定义了用户的权限范围，支持三级权限：
- super_admin: 超级管理员，全局权限
- tenant_admin: 租户管理员，租户内管理权限
- user: 普通用户，基础操作权限
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class RoleType(str, Enum):
    """
    角色类型枚举

    - SUPER_ADMIN: 超级管理员，拥有全局权限，可管理所有租户
    - TENANT_ADMIN: 租户管理员，可管理所属租户的用户和数据
    - USER: 普通用户，只能访问自己的数据
    """
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    USER = "user"


# 预定义权限列表
class Permission(str, Enum):
    """
    权限枚举 - 定义系统中的所有权限点

    命名规则: {资源}_{操作}
    """
    # 用户管理
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # 租户管理
    TENANT_CREATE = "tenant:create"
    TENANT_READ = "tenant:read"
    TENANT_UPDATE = "tenant:update"
    TENANT_DELETE = "tenant:delete"

    # 任务管理
    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"
    TASK_RUN = "task:run"
    TASK_CANCEL = "task:cancel"

    # 数据访问
    NEWS_READ = "news:read"
    NEWS_EXPORT = "news:export"
    SOCIAL_READ = "social:read"
    SOCIAL_EXPORT = "social:export"

    # 搜索
    SEARCH_READ = "search:read"

    # 仪表盘
    DASHBOARD_READ = "dashboard:read"

    # 审计日志
    AUDIT_READ = "audit:read"

    # 系统管理
    SYSTEM_CONFIG = "system:config"


# 角色-权限映射
ROLE_PERMISSIONS = {
    RoleType.SUPER_ADMIN: [p.value for p in Permission],  # 超级管理员拥有所有权限
    RoleType.TENANT_ADMIN: [
        Permission.USER_CREATE.value,
        Permission.USER_READ.value,
        Permission.USER_UPDATE.value,
        Permission.USER_DELETE.value,
        Permission.TASK_CREATE.value,
        Permission.TASK_READ.value,
        Permission.TASK_UPDATE.value,
        Permission.TASK_DELETE.value,
        Permission.TASK_RUN.value,
        Permission.TASK_CANCEL.value,
        Permission.NEWS_READ.value,
        Permission.NEWS_EXPORT.value,
        Permission.SOCIAL_READ.value,
        Permission.SOCIAL_EXPORT.value,
        Permission.SEARCH_READ.value,
        Permission.DASHBOARD_READ.value,
        Permission.AUDIT_READ.value,
    ],
    RoleType.USER: [
        Permission.TASK_CREATE.value,
        Permission.TASK_READ.value,
        Permission.TASK_RUN.value,
        Permission.TASK_CANCEL.value,
        Permission.NEWS_READ.value,
        Permission.NEWS_EXPORT.value,
        Permission.SOCIAL_READ.value,
        Permission.SOCIAL_EXPORT.value,
        Permission.SEARCH_READ.value,
        Permission.DASHBOARD_READ.value,
    ],
}


class Role(Base):
    """
    角色实体 - RBAC 权限模型的角色定义

    支持自定义角色和权限列表。
    预定义角色：super_admin, tenant_admin, user
    """

    __tablename__ = "roles"

    # 主键 - 自增整数
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
        comment="角色ID"
    )

    # 角色名称 - 唯一标识
    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True,
        comment="角色名称（唯一）"
    )

    # 显示名称 - 用于UI展示
    display_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="显示名称"
    )

    # 角色描述
    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        comment="角色描述"
    )

    # 权限列表 - JSON数组格式存储权限点
    permissions: Mapped[list] = mapped_column(
        JSON, nullable=False, default=[],
        comment="权限列表"
    )

    # 是否为系统预定义角色 - 预定义角色不可删除
    is_system: Mapped[bool] = mapped_column(
        default=False, nullable=False,
        comment="是否为系统预定义角色"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(),
        comment="创建时间"
    )

    # 关联关系
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="role"
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"

    def has_permission(self, permission: str) -> bool:
        """
        检查角色是否拥有指定权限

        Args:
            permission: 权限点字符串，如 "user:create"

        Returns:
            True if 角色拥有该权限
        """
        return permission in self.permissions

    def get_all_permissions(self) -> list:
        """获取角色的所有权限列表"""
        return self.permissions.copy()


# 预定义角色数据（用于数据库初始化）
PREDEFINED_ROLES = [
    {
        "id": 1,
        "name": RoleType.SUPER_ADMIN.value,
        "display_name": "超级管理员",
        "description": "系统超级管理员，拥有全局权限",
        "permissions": ROLE_PERMISSIONS[RoleType.SUPER_ADMIN],
        "is_system": True,
    },
    {
        "id": 2,
        "name": RoleType.TENANT_ADMIN.value,
        "display_name": "租户管理员",
        "description": "租户管理员，可管理所属租户的用户和数据",
        "permissions": ROLE_PERMISSIONS[RoleType.TENANT_ADMIN],
        "is_system": True,
    },
    {
        "id": 3,
        "name": RoleType.USER.value,
        "display_name": "普通用户",
        "description": "普通用户，基础操作权限",
        "permissions": ROLE_PERMISSIONS[RoleType.USER],
        "is_system": True,
    },
]
