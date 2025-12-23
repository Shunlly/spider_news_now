"""
FastAPI 依赖注入模块 - Dependencies
Authentication and Authorization Dependencies

提供路由保护所需的依赖函数：
1. get_current_user - 获取当前登录用户
2. get_current_active_user - 获取当前激活用户
3. require_permission - 权限检查
4. require_role - 角色检查

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import verify_token
from app.db.session import get_db
from app.models.role import Permission, RoleType
from app.models.user import User

logger = get_logger(__name__)

# OAuth2 密码流 Bearer Token 提取器
# tokenUrl 是获取 Token 的端点路径（用于 Swagger UI）
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False  # 不自动抛出错误，允许可选认证
)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    从 JWT Token 获取当前登录用户

    这是核心认证依赖，用于保护需要登录的路由。
    从 Authorization Header 提取 Bearer Token，
    验证后从数据库查询用户。

    Args:
        token: JWT Access Token（从 Authorization Header 提取）
        db: 数据库会话

    Returns:
        当前登录的 User 对象

    Raises:
        HTTPException 401: Token 无效或用户不存在
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 检查 Token 是否存在
    if not token:
        logger.debug("No token provided")
        raise credentials_exception

    # 验证 Token 并获取用户 ID
    user_id = verify_token(token, token_type="access")
    if user_id is None:
        logger.debug("Token verification failed")
        raise credentials_exception

    # 从数据库查询用户
    try:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    except Exception as e:
        logger.error("Database query failed", extra={"error": str(e)})
        raise credentials_exception from None

    if user is None:
        logger.warning("User not found", extra={"user_id": user_id})
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    获取当前激活用户

    在 get_current_user 基础上，额外检查用户是否激活且未被锁定。

    Args:
        current_user: 通过 get_current_user 获取的用户

    Returns:
        当前激活的 User 对象

    Raises:
        HTTPException 403: 用户未激活或被锁定
    """
    # 检查账号是否激活
    if not current_user.is_active:
        logger.warning("Inactive user attempted access", extra={"user_id": current_user.id})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )

    # 检查账号是否被锁定
    if current_user.is_locked():
        logger.warning("Locked user attempted access", extra={"user_id": current_user.id})
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="账号已被锁定，请稍后再试"
        )

    return current_user


async def get_optional_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    可选的用户获取依赖

    与 get_current_user 类似，但在未提供 Token 时返回 None 而不是抛出异常。
    用于某些页面需要根据是否登录显示不同内容的场景。

    Args:
        token: JWT Access Token（可选）
        db: 数据库会话

    Returns:
        User 对象或 None
    """
    if not token:
        return None

    user_id = verify_token(token, token_type="access")
    if user_id is None:
        return None

    try:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        return user
    except Exception:
        return None


# ============== 权限检查依赖 ==============


def require_permission(permission: Permission | str) -> Callable:
    """
    创建权限检查依赖

    用于保护需要特定权限的路由。

    Args:
        permission: 所需权限（Permission 枚举或字符串）

    Returns:
        FastAPI 依赖函数

    Example:
        @router.post("/users", dependencies=[Depends(require_permission(Permission.USER_CREATE))])
        async def create_user(...):
            ...
    """
    permission_value = permission.value if isinstance(permission, Permission) else permission

    async def permission_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        """检查用户是否拥有指定权限"""
        if not current_user.has_permission(permission_value):
            logger.warning(
                "Permission denied",
                extra={
                    "user_id": current_user.id,
                    "required_permission": permission_value,
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要权限: {permission_value}"
            )
        return current_user

    return permission_checker


def require_role(*roles: RoleType | int) -> Callable:
    """
    创建角色检查依赖

    用于保护需要特定角色的路由。

    Args:
        roles: 允许的角色列表（RoleType 枚举或 role_id）

    Returns:
        FastAPI 依赖函数

    Example:
        @router.delete("/users/{id}", dependencies=[Depends(require_role(RoleType.SUPER_ADMIN))])
        async def delete_user(...):
            ...
    """
    # 将 RoleType 转换为 role_id
    role_ids = set()
    for role in roles:
        if isinstance(role, RoleType):
            # super_admin=1, tenant_admin=2, user=3
            role_map = {
                RoleType.SUPER_ADMIN: 1,
                RoleType.TENANT_ADMIN: 2,
                RoleType.USER: 3,
            }
            role_ids.add(role_map.get(role, 3))
        else:
            role_ids.add(role)

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        """检查用户是否拥有指定角色"""
        if current_user.role_id not in role_ids:
            logger.warning(
                "Role check failed",
                extra={
                    "user_id": current_user.id,
                    "user_role_id": current_user.role_id,
                    "required_roles": list(role_ids),
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        return current_user

    return role_checker


def require_admin() -> Callable:
    """
    创建管理员检查依赖

    快捷方式，要求用户是超级管理员或租户管理员。

    Returns:
        FastAPI 依赖函数
    """
    return require_role(RoleType.SUPER_ADMIN, RoleType.TENANT_ADMIN)


def require_super_admin() -> Callable:
    """
    创建超级管理员检查依赖

    Returns:
        FastAPI 依赖函数
    """
    return require_role(RoleType.SUPER_ADMIN)


# ============== 配额检查依赖 (T128) ==============


class QuotaChecker:
    """
    配额检查依赖类 (T128)

    用于在创建任务前检查用户配额是否足够。
    支持检查每日配额和并发配额。

    Usage:
        @router.post("/trigger")
        async def trigger_task(
            quota: Annotated[dict, Depends(QuotaChecker())],
            ...
        ):
            # quota 包含 {"daily_remaining": int, "concurrent_used": int}
            ...

        # 或者只检查不获取槽位
        @router.post("/trigger")
        async def trigger_task(
            quota: Annotated[dict, Depends(QuotaChecker(acquire_slot=False))],
            ...
        ):
            ...
    """

    def __init__(
        self,
        check_daily: bool = True,
        check_concurrent: bool = True,
        acquire_slot: bool = True,
        daily_amount: int = 1,
    ):
        """
        初始化配额检查器

        Args:
            check_daily: 是否检查每日配额
            check_concurrent: 是否检查并发配额
            acquire_slot: 是否获取并发槽位（需要在任务完成后释放）
            daily_amount: 每次检查消耗的每日配额数量
        """
        self.check_daily = check_daily
        self.check_concurrent = check_concurrent
        self.acquire_slot = acquire_slot
        self.daily_amount = daily_amount

    async def __call__(
        self,
        current_user: Annotated[User, Depends(get_current_active_user)],
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        """
        执行配额检查

        Returns:
            配额信息字典: {"daily_remaining": int, "concurrent_used": int, "slot_acquired": bool}

        Raises:
            HTTPException 429: 配额不足
        """
        from app.services.quota_service import quota_service

        result = {
            "daily_remaining": -1,
            "concurrent_used": -1,
            "slot_acquired": False,
            "user_id": str(current_user.id),
        }

        # 检查每日配额
        if self.check_daily:
            has_quota, msg, remaining = await quota_service.check_daily_quota(
                db, str(current_user.id), self.daily_amount
            )
            result["daily_remaining"] = remaining

            if not has_quota:
                logger.warning(
                    "Daily quota exceeded",
                    extra={"user_id": current_user.id, "remaining": remaining}
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"每日配额已用尽: {msg}",
                    headers={"X-Quota-Remaining": str(remaining)},
                )

        # 检查并发配额
        if self.check_concurrent:
            has_quota, msg, used = await quota_service.check_concurrent_quota(
                db, str(current_user.id)
            )
            result["concurrent_used"] = used

            if not has_quota:
                logger.warning(
                    "Concurrent quota exceeded",
                    extra={"user_id": current_user.id, "concurrent_used": used}
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"并发任务数已达上限: {msg}",
                    headers={"X-Concurrent-Used": str(used)},
                )

            # 获取并发槽位
            if self.acquire_slot:
                acquired, acquire_msg = await quota_service.acquire_concurrent_slot(
                    db, str(current_user.id)
                )
                if not acquired:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"无法获取并发槽位: {acquire_msg}",
                    )
                result["slot_acquired"] = True
                result["concurrent_used"] = used + 1

        logger.debug(
            "Quota check passed",
            extra={
                "user_id": current_user.id,
                "daily_remaining": result["daily_remaining"],
                "concurrent_used": result["concurrent_used"],
            }
        )

        return result


def require_quota(
    check_daily: bool = True,
    check_concurrent: bool = True,
    acquire_slot: bool = True,
) -> QuotaChecker:
    """
    创建配额检查依赖的快捷函数

    Args:
        check_daily: 是否检查每日配额
        check_concurrent: 是否检查并发配额
        acquire_slot: 是否获取并发槽位

    Returns:
        QuotaChecker 实例

    Example:
        @router.post("/trigger", dependencies=[Depends(require_quota())])
        async def trigger_task(...):
            ...

        # 或者获取配额信息
        @router.post("/trigger")
        async def trigger_task(
            quota: Annotated[dict, Depends(require_quota())],
            ...
        ):
            print(f"剩余配额: {quota['daily_remaining']}")
    """
    return QuotaChecker(
        check_daily=check_daily,
        check_concurrent=check_concurrent,
        acquire_slot=acquire_slot,
    )
