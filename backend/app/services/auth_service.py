"""
认证服务 - Auth Service
User Authentication and Session Management

提供用户认证功能：
1. 用户登录验证
2. 登录尝试追踪
3. 账号锁定管理
4. Token 刷新

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
)
from app.models.user import User

logger = get_logger(__name__)


class AuthService:
    """
    认证服务

    处理用户认证相关的业务逻辑：
    - 凭证验证
    - 登录尝试追踪
    - 账号锁定/解锁
    - Token 管理
    """

    # ============== 用户验证 ==============

    async def authenticate_user(
        self,
        db: AsyncSession,
        username: str,
        password: str,
    ) -> Tuple[Optional[User], str]:
        """
        验证用户凭证

        Args:
            db: 数据库会话
            username: 用户名
            password: 明文密码

        Returns:
            (User 或 None, 错误消息)
        """
        # 查找用户
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            logger.warning("Login attempt for non-existent user", extra={"username": username})
            return None, "用户名或密码错误"

        # 检查账号是否激活
        if not user.is_active:
            logger.warning("Login attempt for inactive user", extra={"user_id": user.id})
            return None, "账号已被禁用"

        # 检查账号是否被锁定
        if user.is_locked():
            remaining = user.get_lock_remaining_seconds()
            logger.warning("Login attempt for locked user", extra={"user_id": user.id, "remaining": remaining})
            return None, f"账号已被锁定，请 {remaining // 60 + 1} 分钟后再试"

        # 验证密码
        if not verify_password(password, user.password_hash):
            # 增加登录失败计数
            await self._increment_login_attempts(db, user)
            logger.warning(
                "Invalid password",
                extra={"user_id": user.id, "attempts": user.login_attempts + 1}
            )

            # 检查是否需要锁定账号
            if user.login_attempts + 1 >= settings.MAX_LOGIN_ATTEMPTS:
                return None, f"密码错误次数过多，账号已被锁定 {settings.ACCOUNT_LOCKOUT_MINUTES} 分钟"

            remaining = settings.MAX_LOGIN_ATTEMPTS - user.login_attempts - 1
            return None, f"用户名或密码错误，还剩 {remaining} 次机会"

        # 验证成功，重置登录尝试计数
        await self._reset_login_attempts(db, user)
        await self._update_last_login(db, user)

        logger.info("User authenticated successfully", extra={"user_id": user.id})
        return user, ""

    async def _increment_login_attempts(self, db: AsyncSession, user: User) -> None:
        """
        增加登录失败计数

        如果达到最大尝试次数，自动锁定账号
        """
        new_attempts = user.login_attempts + 1
        locked_until = None

        # 达到最大尝试次数，锁定账号
        if new_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCOUNT_LOCKOUT_MINUTES
            )
            logger.warning(
                "Account locked due to too many failed attempts",
                extra={"user_id": user.id, "locked_until": locked_until}
            )

        stmt = (
            update(User)
            .where(User.id == user.id)
            .values(
                login_attempts=new_attempts,
                locked_until=locked_until
            )
        )
        await db.execute(stmt)
        await db.commit()

    async def _reset_login_attempts(self, db: AsyncSession, user: User) -> None:
        """重置登录尝试计数（登录成功后调用）"""
        stmt = (
            update(User)
            .where(User.id == user.id)
            .values(
                login_attempts=0,
                locked_until=None
            )
        )
        await db.execute(stmt)
        await db.commit()

    async def _update_last_login(self, db: AsyncSession, user: User) -> None:
        """更新最后登录时间"""
        stmt = (
            update(User)
            .where(User.id == user.id)
            .values(last_login_at=datetime.now(timezone.utc))
        )
        await db.execute(stmt)
        await db.commit()

    # ============== Token 管理 ==============

    def create_tokens(self, user: User) -> Tuple[str, str, int]:
        """
        为用户创建访问令牌和刷新令牌

        Args:
            user: 用户对象

        Returns:
            (access_token, refresh_token, expires_in)
        """
        # 创建 Access Token
        access_token = create_access_token(
            subject=user.id,
            extra_claims={"role": user.role.value}
        )

        # 创建 Refresh Token
        refresh_token = create_refresh_token(subject=user.id)

        # 计算过期时间（秒）
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        logger.debug("Tokens created", extra={"user_id": user.id})

        return access_token, refresh_token, expires_in

    async def refresh_access_token(
        self,
        db: AsyncSession,
        refresh_token: str,
    ) -> Tuple[Optional[str], Optional[int], str]:
        """
        使用 Refresh Token 获取新的 Access Token

        Args:
            db: 数据库会话
            refresh_token: 刷新令牌

        Returns:
            (新的 access_token 或 None, expires_in 或 None, 错误消息)
        """
        # 验证 Refresh Token
        user_id = verify_token(refresh_token, token_type="refresh")
        if user_id is None:
            logger.warning("Invalid refresh token")
            return None, None, "无效的刷新令牌"

        # 查找用户
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            logger.warning("User not found for refresh token", extra={"user_id": user_id})
            return None, None, "用户不存在"

        # 检查账号状态
        if not user.is_active:
            logger.warning("Refresh attempt for inactive user", extra={"user_id": user.id})
            return None, None, "账号已被禁用"

        if user.is_locked():
            logger.warning("Refresh attempt for locked user", extra={"user_id": user.id})
            return None, None, "账号已被锁定"

        # 创建新的 Access Token
        access_token = create_access_token(
            subject=user.id,
            extra_claims={"role": user.role.value}
        )
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        logger.info("Access token refreshed", extra={"user_id": user.id})

        return access_token, expires_in, ""

    # ============== 账号管理（管理员功能） ==============

    async def unlock_user(self, db: AsyncSession, user_id: int) -> Tuple[bool, str]:
        """
        解锁用户账号（管理员功能）

        Args:
            db: 数据库会话
            user_id: 要解锁的用户 ID

        Returns:
            (是否成功, 消息)
        """
        # 查找用户
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            return False, "用户不存在"

        if not user.is_locked():
            return False, "账号未被锁定"

        # 重置锁定状态
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                login_attempts=0,
                locked_until=None
            )
        )
        await db.execute(stmt)
        await db.commit()

        logger.info("User account unlocked", extra={"user_id": user_id})

        return True, "账号已解锁"


# 全局服务实例
auth_service = AuthService()
