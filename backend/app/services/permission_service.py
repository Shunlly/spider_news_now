"""
权限服务 - Permission Service
Role-based Data Access Control

提供基于角色的数据访问控制：
1. get_user_filter - 根据用户角色返回查询过滤条件
2. require_admin - 要求管理员权限的依赖

遵循宪法要求：
- Admin 可查看所有数据
- User 仅能查看自己的数据
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import Select

from app.core.deps import get_current_active_user
from app.core.logging import get_logger
from app.models.user import User, UserRole

logger = get_logger(__name__)


def apply_user_filter(
    stmt: Select,
    user: User,
    model_class,
    user_id_column: str = "user_id",
) -> Select:
    """
    根据用户角色应用数据过滤

    管理员可查看所有数据，普通用户仅能查看自己的数据。

    Args:
        stmt: SQLAlchemy Select 语句
        user: 当前用户
        model_class: 模型类（如 NewsSource, NewsArticle）
        user_id_column: user_id 列名（默认 "user_id"）

    Returns:
        应用过滤后的 Select 语句

    Usage:
        stmt = select(NewsSource)
        stmt = apply_user_filter(stmt, current_user, NewsSource)
    """
    # 管理员不添加过滤条件
    if user.is_admin:
        logger.debug("Admin user, no filter applied", extra={"user_id": user.id})
        return stmt

    # 普通用户添加 user_id 过滤
    user_id_attr = getattr(model_class, user_id_column, None)
    if user_id_attr is None:
        logger.warning(
            f"Model {model_class.__name__} does not have {user_id_column} column"
        )
        return stmt

    logger.debug(
        "User filter applied",
        extra={"user_id": user.id, "model": model_class.__name__}
    )
    return stmt.where(user_id_attr == user.id)


def get_owner_id(user: User) -> int:
    """
    获取资源所有者 ID

    用于创建新资源时设置 user_id。

    Args:
        user: 当前用户

    Returns:
        用户 ID
    """
    return user.id


async def require_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    要求管理员权限的依赖

    用于保护仅限管理员访问的路由。

    Args:
        current_user: 当前登录用户

    Returns:
        当前用户（如果是管理员）

    Raises:
        HTTPException 403: 如果用户不是管理员

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            admin: Annotated[User, Depends(require_admin)]
        ):
            ...
    """
    if not current_user.is_admin:
        logger.warning(
            "Non-admin user attempted to access admin-only resource",
            extra={"user_id": current_user.id, "username": current_user.username}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def require_owner_or_admin(
    resource_user_id: int,
    current_user: User,
) -> bool:
    """
    检查用户是否是资源所有者或管理员

    用于更新/删除操作的权限检查。

    Args:
        resource_user_id: 资源的 user_id
        current_user: 当前用户

    Returns:
        True if 有权限

    Raises:
        HTTPException 403: 如果没有权限
    """
    if current_user.is_admin:
        return True

    if current_user.id == resource_user_id:
        return True

    logger.warning(
        "User attempted to access resource owned by another user",
        extra={
            "user_id": current_user.id,
            "resource_owner_id": resource_user_id
        }
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="无权访问此资源"
    )


class PermissionChecker:
    """
    权限检查器类

    提供更灵活的权限检查，支持依赖注入。

    Usage:
        permission_checker = PermissionChecker(required_role=UserRole.ADMIN)

        @router.get("/")
        async def endpoint(
            _: Annotated[User, Depends(permission_checker)]
        ):
            ...
    """

    def __init__(self, required_role: UserRole | None = None):
        """
        初始化权限检查器

        Args:
            required_role: 所需的最低角色级别
        """
        self.required_role = required_role

    async def __call__(
        self,
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        """执行权限检查"""
        if self.required_role == UserRole.ADMIN and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限"
            )
        return current_user
