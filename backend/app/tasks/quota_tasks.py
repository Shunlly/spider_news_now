"""
配额重置任务 - Quota Reset Celery Task
每日 UTC 00:00 自动重置用户配额

遵循宪法要求：
- 类型提示完整
- 中文注释说明核心逻辑
"""

from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.core.logging import get_logger
from app.db.session import async_session_factory
from app.models.quota import Quota
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.quota_tasks.reset_daily_quotas")
def reset_daily_quotas() -> dict[str, Any]:
    """
    重置所有用户的每日配额

    该任务由 Celery Beat 在每日 UTC 00:00 自动触发。
    重置内容：
    - daily_used -> 0
    - warning_shown -> False
    - reset_at -> 明天 UTC 00:00

    Returns:
        包含重置结果的字典
    """
    import asyncio

    # 在同步任务中运行异步代码
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_reset_quotas_async())
        return result
    finally:
        loop.close()


async def _reset_quotas_async() -> dict[str, Any]:
    """
    异步执行配额重置

    Returns:
        重置结果统计
    """
    reset_count = 0
    error_count = 0
    start_time = datetime.utcnow()

    logger.info("开始执行每日配额重置任务...")

    async with async_session_factory() as session:
        try:
            # 查询所有配额记录
            stmt = select(Quota)
            result = await session.execute(stmt)
            quotas = result.scalars().all()

            for quota in quotas:
                try:
                    quota.reset_daily()
                    reset_count += 1
                except Exception as e:
                    logger.error(f"重置配额失败: user_id={quota.user_id}, error={e}")
                    error_count += 1

            # 提交事务
            await session.commit()

            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"配额重置完成: 成功={reset_count}, 失败={error_count}, "
                f"耗时={elapsed:.2f}秒"
            )

            return {
                "status": "completed",
                "reset_count": reset_count,
                "error_count": error_count,
                "elapsed_seconds": elapsed,
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"配额重置任务执行失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "reset_count": reset_count,
                "error_count": error_count,
            }


@celery_app.task(name="app.tasks.quota_tasks.reset_user_quota")
def reset_user_quota(user_id: str) -> dict[str, Any]:
    """
    重置单个用户的配额

    管理员可以手动触发此任务来重置特定用户的配额。

    Args:
        user_id: 用户ID

    Returns:
        重置结果
    """
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_reset_user_quota_async(user_id))
        return result
    finally:
        loop.close()


async def _reset_user_quota_async(user_id: str) -> dict[str, Any]:
    """
    异步重置单个用户配额

    Args:
        user_id: 用户ID

    Returns:
        重置结果
    """
    async with async_session_factory() as session:
        try:
            stmt = select(Quota).where(Quota.user_id == user_id)
            result = await session.execute(stmt)
            quota = result.scalar_one_or_none()

            if quota is None:
                return {
                    "status": "not_found",
                    "user_id": user_id,
                }

            quota.reset_daily()
            await session.commit()

            logger.info(f"用户配额已重置: user_id={user_id}")
            return {
                "status": "reset",
                "user_id": user_id,
                "new_daily_limit": quota.daily_limit,
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"重置用户配额失败: user_id={user_id}, error={e}")
            return {
                "status": "failed",
                "user_id": user_id,
                "error": str(e),
            }
