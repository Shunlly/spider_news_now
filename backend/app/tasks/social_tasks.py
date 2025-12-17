"""
社交数据定时采集任务 - Social Data Scheduled Tasks

功能：
1. 定时采集所有活跃订阅的数据
2. 支持手动触发采集
3. 支持单个订阅采集
"""

from sqlalchemy import select

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.social_session import SocialSession, Platform
from app.services.social_service import SocialService
from app.tasks.scheduler import get_scheduler

logger = get_logger(__name__)


async def run_social_fetch_job() -> None:
    """
    定时采集任务 - 采集所有活跃订阅的数据

    由 APScheduler 定时执行
    """
    logger.info("Starting social data fetch job")

    async with AsyncSessionLocal() as db:
        try:
            result = await SocialService.fetch_all_active(db)

            logger.info(
                f"Social fetch job completed: {result.get('message', '')}",
                extra={
                    "success": result.get("success"),
                    "results_count": len(result.get("results", [])),
                },
            )

        except Exception as e:
            logger.error(
                "Social fetch job exception",
                extra={"error": str(e)},
                exc_info=True,
            )


async def run_single_fetch_job(session_id: int) -> dict:
    """
    采集单个订阅的数据

    Args:
        session_id: 订阅 ID

    Returns:
        采集结果
    """
    logger.info("Starting single subscription fetch", extra={"session_id": session_id})

    async with AsyncSessionLocal() as db:
        try:
            # 获取订阅
            result = await db.execute(
                select(SocialSession).where(SocialSession.id == session_id)
            )
            session = result.scalar_one_or_none()

            if not session:
                return {"success": False, "message": "订阅不存在"}

            # 根据平台采集
            if session.platform == Platform.TWITTER:
                fetch_result = await SocialService.fetch_twitter_messages(db, session)
            elif session.platform == Platform.TELEGRAM:
                fetch_result = await SocialService.fetch_telegram_messages(db, session)
            else:
                return {"success": False, "message": "不支持的平台"}

            logger.info(
                "Single fetch completed",
                extra={
                    "session_id": session_id,
                    "platform": session.platform.value,
                    "new_count": fetch_result.get("new_count", 0),
                },
            )

            return fetch_result

        except Exception as e:
            logger.error(
                "Single fetch exception",
                extra={"session_id": session_id, "error": str(e)},
                exc_info=True,
            )
            return {"success": False, "message": str(e)}


async def register_social_fetch_job(interval_seconds: int = 600) -> None:
    """
    注册社交数据定时采集任务

    Args:
        interval_seconds: 采集间隔（秒），默认 10 分钟
    """
    from apscheduler.triggers.interval import IntervalTrigger

    scheduler = await get_scheduler()
    job_id = "social_data_fetch"

    await scheduler.add_schedule(
        run_social_fetch_job,
        IntervalTrigger(seconds=interval_seconds),
        id=job_id,
    )

    logger.info(
        "Registered social fetch job",
        extra={"interval": interval_seconds, "job_id": job_id},
    )


async def trigger_social_fetch_now() -> dict:
    """
    手动触发社交数据采集

    Returns:
        采集结果
    """
    logger.info("Manual trigger for social data fetch")

    async with AsyncSessionLocal() as db:
        return await SocialService.fetch_all_active(db)


async def trigger_subscription_fetch(session_id: int) -> dict:
    """
    手动触发单个订阅采集

    Args:
        session_id: 订阅 ID

    Returns:
        采集结果
    """
    return await run_single_fetch_job(session_id)
