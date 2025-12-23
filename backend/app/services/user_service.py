"""
用户服务 - User Service
User CRUD Operations

提供用户管理功能：
1. 列出用户
2. 创建用户
3. 更新用户
4. 删除用户
5. 解锁用户

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
"""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.logging import get_logger
from app.core.security import hash_password
from app.models.user import User

logger = get_logger(__name__)


class UserService:
    """
    用户服务

    处理用户 CRUD 操作的业务逻辑
    """

    # ============== 查询操作 ==============

    async def get_users(
        self,
        db: AsyncSession,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        """
        获取用户列表

        Args:
            db: 数据库会话
            current_user: 当前用户（用于权限过滤）
            page: 页码
            page_size: 每页数量
            search: 搜索关键词（用户名或邮箱）

        Returns:
            (用户列表, 总数)
        """
        # 基础查询
        stmt = select(User).options(joinedload(User.role))

        # 权限过滤
        if current_user.is_super_admin:
            # 超级管理员可查看所有用户
            pass
        elif current_user.is_tenant_admin:
            # 租户管理员只能查看本租户用户
            stmt = stmt.where(User.tenant_id == current_user.tenant_id)
        else:
            # 普通用户只能查看自己
            stmt = stmt.where(User.id == current_user.id)

        # 搜索过滤
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                (User.username.ilike(search_pattern)) |
                (User.email.ilike(search_pattern))
            )

        # 统计总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        # 分页
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size).order_by(User.created_at.desc())

        result = await db.execute(stmt)
        users = list(result.scalars().unique().all())

        return users, total

    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> User | None:
        """
        根据 ID 获取用户

        Args:
            db: 数据库会话
            user_id: 用户 ID

        Returns:
            用户对象或 None
        """
        stmt = select(User).options(joinedload(User.role)).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username(
        self,
        db: AsyncSession,
        username: str,
    ) -> User | None:
        """
        根据用户名获取用户

        Args:
            db: 数据库会话
            username: 用户名

        Returns:
            用户对象或 None
        """
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(
        self,
        db: AsyncSession,
        email: str,
    ) -> User | None:
        """
        根据邮箱获取用户

        Args:
            db: 数据库会话
            email: 邮箱

        Returns:
            用户对象或 None
        """
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    # ============== 创建操作 ==============

    async def create_user(
        self,
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        role_id: int = 3,
        tenant_id: int | None = None,
    ) -> tuple[User | None, str]:
        """
        创建新用户

        Args:
            db: 数据库会话
            username: 用户名
            email: 邮箱
            password: 明文密码
            role_id: 角色 ID（默认 3 = 普通用户）
            tenant_id: 租户 ID

        Returns:
            (User 或 None, 错误消息)
        """
        # 检查用户名是否已存在
        existing = await self.get_user_by_username(db, username)
        if existing:
            return None, "用户名已被使用"

        # 检查邮箱是否已存在
        existing = await self.get_user_by_email(db, email)
        if existing:
            return None, "邮箱已被注册"

        # 创建用户
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role_id=role_id,
            tenant_id=tenant_id,
            is_active=True,
            is_verified=False,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info("User created", extra={"user_id": user.id, "username": username})

        return user, ""

    # ============== 更新操作 ==============

    async def update_user(
        self,
        db: AsyncSession,
        user: User,
        email: str | None = None,
        role_id: int | None = None,
        is_active: bool | None = None,
        tenant_id: int | None = None,
    ) -> tuple[User | None, str]:
        """
        更新用户信息

        Args:
            db: 数据库会话
            user: 要更新的用户
            email: 新邮箱
            role_id: 新角色 ID
            is_active: 是否激活
            tenant_id: 租户 ID

        Returns:
            (更新后的 User 或 None, 错误消息)
        """
        update_data = {}

        # 更新邮箱
        if email is not None and email != user.email:
            # 检查邮箱是否被其他用户使用
            existing = await self.get_user_by_email(db, email)
            if existing and existing.id != user.id:
                return None, "邮箱已被其他用户使用"
            update_data["email"] = email

        # 更新角色
        if role_id is not None and role_id != user.role_id:
            update_data["role_id"] = role_id

        # 更新激活状态
        if is_active is not None and is_active != user.is_active:
            update_data["is_active"] = is_active

        # 更新租户
        if tenant_id is not None and tenant_id != user.tenant_id:
            update_data["tenant_id"] = tenant_id

        if not update_data:
            return user, ""

        # 执行更新
        stmt = (
            update(User)
            .where(User.id == user.id)
            .values(**update_data)
        )
        await db.execute(stmt)
        await db.commit()
        await db.refresh(user)

        logger.info("User updated", extra={"user_id": user.id, "updates": list(update_data.keys())})

        return user, ""

    async def reset_password(
        self,
        db: AsyncSession,
        user: User,
        new_password: str,
    ) -> tuple[bool, str]:
        """
        重置用户密码（管理员操作）

        Args:
            db: 数据库会话
            user: 目标用户
            new_password: 新密码

        Returns:
            (是否成功, 消息)
        """
        stmt = (
            update(User)
            .where(User.id == user.id)
            .values(password_hash=hash_password(new_password))
        )
        await db.execute(stmt)
        await db.commit()

        logger.info("User password reset by admin", extra={"user_id": user.id})

        return True, "密码已重置"

    # ============== 删除操作 ==============

    async def delete_user(
        self,
        db: AsyncSession,
        user: User,
    ) -> tuple[bool, str]:
        """
        删除用户

        Args:
            db: 数据库会话
            user: 要删除的用户

        Returns:
            (是否成功, 消息)
        """
        await db.delete(user)
        await db.commit()

        logger.info("User deleted", extra={"user_id": user.id, "username": user.username})

        return True, "用户已删除"

    # ============== 账号管理 ==============

    async def unlock_user(
        self,
        db: AsyncSession,
        user: User,
    ) -> tuple[bool, str]:
        """
        解锁用户账号

        Args:
            db: 数据库会话
            user: 要解锁的用户

        Returns:
            (是否成功, 消息)
        """
        if not user.is_locked():
            return False, "账号未被锁定"

        stmt = (
            update(User)
            .where(User.id == user.id)
            .values(login_attempts=0, locked_until=None)
        )
        await db.execute(stmt)
        await db.commit()

        logger.info("User unlocked", extra={"user_id": user.id})

        return True, "账号已解锁"

    async def toggle_user_active(
        self,
        db: AsyncSession,
        user: User,
    ) -> tuple[bool, str]:
        """
        切换用户激活状态

        Args:
            db: 数据库会话
            user: 目标用户

        Returns:
            (新的激活状态, 消息)
        """
        new_status = not user.is_active

        stmt = (
            update(User)
            .where(User.id == user.id)
            .values(is_active=new_status)
        )
        await db.execute(stmt)
        await db.commit()

        status_text = "已激活" if new_status else "已禁用"
        logger.info(f"User {status_text}", extra={"user_id": user.id})

        return new_status, f"账号{status_text}"


# 全局服务实例
user_service = UserService()
