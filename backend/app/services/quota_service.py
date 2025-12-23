"""
配额服务 - Quota Service
Usage Quota Management

提供配额管理功能：
1. 配额检查和消耗
2. 并发控制
3. 配额重置

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.quota import Quota, QuotaTier

logger = get_logger(__name__)


class QuotaService:
    """
    配额服务

    管理用户的配额使用情况：
    - 每日采集配额
    - 并发任务配额
    - 配额警告和重置
    """

    async def get_or_create_quota(
        self,
        db: AsyncSession,
        user_id: str,
        tier: QuotaTier = QuotaTier.FREE,
    ) -> Quota:
        """
        获取或创建用户配额记录

        Args:
            db: 数据库会话
            user_id: 用户 ID
            tier: 配额等级

        Returns:
            Quota 实例
        """
        stmt = select(Quota).where(Quota.user_id == user_id)
        result = await db.execute(stmt)
        quota = result.scalar_one_or_none()

        if quota is None:
            quota = Quota.create_for_tier(user_id=user_id, tier=tier)
            db.add(quota)
            await db.commit()
            await db.refresh(quota)
            logger.info("Created quota for user", extra={"user_id": user_id, "tier": tier.value})

        return quota

    async def check_daily_quota(
        self,
        db: AsyncSession,
        user_id: str,
        amount: int = 1,
    ) -> tuple[bool, str, int]:
        """
        检查每日配额是否足够

        Args:
            db: 数据库会话
            user_id: 用户 ID
            amount: 需要消耗的数量

        Returns:
            (是否足够, 消息, 剩余配额)
        """
        quota = await self.get_or_create_quota(db, user_id)

        # 检查是否需要重置配额
        await self._check_and_reset(db, quota)

        if quota.daily_used + amount > quota.daily_limit:
            return False, f"每日配额已用尽，剩余 {quota.daily_remaining}", quota.daily_remaining

        # 检查是否应该显示警告
        if quota.should_warn and not quota.warning_shown:
            quota.warning_shown = True
            await db.commit()
            return True, f"配额即将用尽，剩余 {quota.daily_remaining}", quota.daily_remaining

        return True, "", quota.daily_remaining

    async def consume_daily_quota(
        self,
        db: AsyncSession,
        user_id: str,
        amount: int = 1,
    ) -> tuple[bool, str]:
        """
        消耗每日配额

        Args:
            db: 数据库会话
            user_id: 用户 ID
            amount: 消耗数量

        Returns:
            (是否成功, 消息)
        """
        quota = await self.get_or_create_quota(db, user_id)

        # 检查是否需要重置
        await self._check_and_reset(db, quota)

        if not quota.consume_daily(amount):
            return False, "配额不足"

        await db.commit()
        logger.debug(
            "Daily quota consumed",
            extra={"user_id": user_id, "amount": amount, "remaining": quota.daily_remaining}
        )

        return True, ""

    async def check_concurrent_quota(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> tuple[bool, str, int]:
        """
        检查并发配额是否足够

        Args:
            db: 数据库会话
            user_id: 用户 ID

        Returns:
            (是否足够, 消息, 当前使用数)
        """
        quota = await self.get_or_create_quota(db, user_id)

        if quota.is_concurrent_exhausted:
            return (
                False,
                f"并发任务数已达上限 ({quota.concurrent_limit})",
                quota.concurrent_used,
            )

        return True, "", quota.concurrent_used

    async def acquire_concurrent_slot(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> tuple[bool, str]:
        """
        获取一个并发槽位

        Args:
            db: 数据库会话
            user_id: 用户 ID

        Returns:
            (是否成功, 消息)
        """
        quota = await self.get_or_create_quota(db, user_id)

        if not quota.acquire_concurrent():
            return False, f"并发任务数已达上限 ({quota.concurrent_limit})"

        await db.commit()
        logger.debug(
            "Concurrent slot acquired",
            extra={"user_id": user_id, "concurrent_used": quota.concurrent_used}
        )

        return True, ""

    async def release_concurrent_slot(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> None:
        """
        释放一个并发槽位

        Args:
            db: 数据库会话
            user_id: 用户 ID
        """
        quota = await self.get_or_create_quota(db, user_id)
        quota.release_concurrent()
        await db.commit()

        logger.debug(
            "Concurrent slot released",
            extra={"user_id": user_id, "concurrent_used": quota.concurrent_used}
        )

    async def get_quota_info(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> dict:
        """
        获取用户配额信息

        Args:
            db: 数据库会话
            user_id: 用户 ID

        Returns:
            配额信息字典
        """
        quota = await self.get_or_create_quota(db, user_id)

        # 检查是否需要重置
        await self._check_and_reset(db, quota)

        return {
            "tier": quota.tier,
            "daily_limit": quota.daily_limit,
            "daily_used": quota.daily_used,
            "daily_remaining": quota.daily_remaining,
            "concurrent_limit": quota.concurrent_limit,
            "concurrent_used": quota.concurrent_used,
            "concurrent_remaining": quota.concurrent_remaining,
            "reset_at": quota.reset_at.isoformat() if quota.reset_at else None,
            "warning": quota.should_warn,
        }

    async def update_tier(
        self,
        db: AsyncSession,
        user_id: str,
        tier: QuotaTier,
    ) -> Quota:
        """
        更新用户配额等级

        Args:
            db: 数据库会话
            user_id: 用户 ID
            tier: 新的配额等级

        Returns:
            更新后的 Quota 实例
        """
        quota = await self.get_or_create_quota(db, user_id)
        quota.update_tier(tier)
        await db.commit()

        logger.info(
            "User quota tier updated",
            extra={"user_id": user_id, "new_tier": tier.value}
        )

        return quota

    async def _check_and_reset(self, db: AsyncSession, quota: Quota) -> None:
        """
        检查并重置过期的配额

        如果当前时间已超过重置时间，自动重置配额。
        """
        if quota.reset_at and datetime.utcnow() >= quota.reset_at:
            quota.reset_daily()
            await db.commit()
            logger.info("Quota auto-reset", extra={"user_id": quota.user_id})


# 全局服务实例
quota_service = QuotaService()
