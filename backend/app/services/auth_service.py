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

from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
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
    ) -> tuple[User | None, str]:
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
            locked_until = datetime.now(UTC) + timedelta(
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
            .values(last_login_at=datetime.now(UTC))
        )
        await db.execute(stmt)
        await db.commit()

    # ============== Token 管理 ==============

    def create_tokens(self, user: User) -> tuple[str, str, int]:
        """
        为用户创建访问令牌和刷新令牌

        Args:
            user: 用户对象

        Returns:
            (access_token, refresh_token, expires_in)
        """
        # 创建 Access Token，包含角色信息
        extra_claims = {
            "role_id": user.role_id,
            "tenant_id": user.tenant_id,
        }

        access_token = create_access_token(
            subject=user.id,
            extra_claims=extra_claims
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
    ) -> tuple[str | None, int | None, str]:
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
        extra_claims = {
            "role_id": user.role_id,
            "tenant_id": user.tenant_id,
        }
        access_token = create_access_token(
            subject=user.id,
            extra_claims=extra_claims
        )
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        logger.info("Access token refreshed", extra={"user_id": user.id})

        return access_token, expires_in, ""

    # ============== 账号管理（管理员功能） ==============

    async def unlock_user(self, db: AsyncSession, user_id: int) -> tuple[bool, str]:
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

    # ============== 用户注册 ==============

    async def register_user(
        self,
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
    ) -> tuple[User | None, str]:
        """
        注册新用户

        Args:
            db: 数据库会话
            username: 用户名
            email: 邮箱
            password: 明文密码

        Returns:
            (User 或 None, 错误消息)
        """
        # 检查用户名是否已存在
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is not None:
            return None, "用户名已被使用"

        # 检查邮箱是否已存在
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is not None:
            return None, "邮箱已被注册"

        # 创建新用户
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role_id=3,  # 默认为普通用户
            is_active=True,
            is_verified=False,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info("New user registered", extra={"user_id": user.id, "username": username})

        return user, ""

    # ============== 个人信息更新 ==============

    async def update_profile(
        self,
        db: AsyncSession,
        user: User,
        email: str | None = None,
        current_password: str | None = None,
        new_password: str | None = None,
    ) -> tuple[User | None, str]:
        """
        更新用户个人信息

        Args:
            db: 数据库会话
            user: 当前用户
            email: 新邮箱（可选）
            current_password: 当前密码（修改密码时必填）
            new_password: 新密码（可选）

        Returns:
            (更新后的 User 或 None, 错误消息)
        """
        update_values = {}

        # 更新邮箱
        if email is not None and email != user.email:
            # 检查邮箱是否已被其他用户使用
            stmt = select(User).where(User.email == email, User.id != user.id)
            result = await db.execute(stmt)
            if result.scalar_one_or_none() is not None:
                return None, "邮箱已被其他用户使用"
            update_values["email"] = email

        # 更新密码
        if new_password is not None:
            if current_password is None:
                return None, "修改密码需要提供当前密码"

            # 验证当前密码
            if not verify_password(current_password, user.password_hash):
                return None, "当前密码错误"

            update_values["password_hash"] = hash_password(new_password)

        # 如果没有需要更新的内容
        if not update_values:
            return user, ""

        # 执行更新
        stmt = (
            update(User)
            .where(User.id == user.id)
            .values(**update_values)
        )
        await db.execute(stmt)
        await db.commit()

        # 刷新用户对象
        await db.refresh(user)

        logger.info("User profile updated", extra={"user_id": user.id})

        return user, ""


# 全局服务实例
auth_service = AuthService()
