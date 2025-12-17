"""
FastAPI 依赖注入模块 - Dependencies
Authentication and Authorization Dependencies

提供路由保护所需的依赖函数：
1. get_current_user - 获取当前登录用户
2. get_current_active_user - 获取当前激活用户

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
"""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import verify_token
from app.db.session import get_db
from app.models.user import User

logger = get_logger(__name__)

# OAuth2 密码流 Bearer Token 提取器
# tokenUrl 是获取 Token 的端点路径（用于 Swagger UI）
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False  # 不自动抛出错误，允许可选认证
)


async def get_current_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
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
        raise credentials_exception

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
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
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
