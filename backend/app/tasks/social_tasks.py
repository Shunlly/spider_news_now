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
from app.models.social_session import Platform, SocialSession
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
    from datetime import datetime, timedelta

    from apscheduler import ConflictPolicy
    from apscheduler.triggers.interval import IntervalTrigger

    scheduler = await get_scheduler()
    job_id = "social_data_fetch"

    # 延迟首次运行，避免启动时阻塞
    first_run = datetime.now() + timedelta(seconds=interval_seconds)

    await scheduler.add_schedule(
        run_social_fetch_job,
        IntervalTrigger(seconds=interval_seconds, start_time=first_run),
        id=job_id,
        conflict_policy=ConflictPolicy.replace,
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


async def run_thread_fetch_job(session_id: int, tweet_id: str) -> dict:
    """
    采集 Twitter Thread (T098)

    Args:
        session_id: 关联的订阅 ID
        tweet_id: Thread 起始推文 ID

    Returns:
        采集结果
    """
    logger.info(
        "Starting Twitter Thread fetch",
        extra={"session_id": session_id, "tweet_id": tweet_id},
    )

    async with AsyncSessionLocal() as db:
        try:
            # 获取订阅
            result = await db.execute(
                select(SocialSession).where(SocialSession.id == session_id)
            )
            session = result.scalar_one_or_none()

            if not session:
                return {"success": False, "message": "订阅不存在"}

            if session.platform != Platform.TWITTER:
                return {"success": False, "message": "仅支持 Twitter 平台"}

            # 采集 Thread
            fetch_result = await SocialService.fetch_twitter_thread(
                db=db,
                session=session,
                tweet_id=tweet_id,
            )

            logger.info(
                "Thread fetch completed",
                extra={
                    "session_id": session_id,
                    "tweet_id": tweet_id,
                    "new_count": fetch_result.get("new_count", 0),
                    "total_count": fetch_result.get("total_count", 0),
                },
            )

            return fetch_result

        except Exception as e:
            logger.error(
                "Thread fetch exception",
                extra={"session_id": session_id, "tweet_id": tweet_id, "error": str(e)},
                exc_info=True,
            )
            return {"success": False, "message": str(e)}


async def trigger_thread_fetch(session_id: int, tweet_id: str) -> dict:
    """
    手动触发 Twitter Thread 采集

    Args:
        session_id: 关联的订阅 ID
        tweet_id: Thread 起始推文 ID（可以是 Thread 中任意一条推文）

    Returns:
        采集结果
    """
    return await run_thread_fetch_job(session_id, tweet_id)


async def run_telegram_history_job(
    session_id: int,
    limit: int = 100,
    min_id: int = 0,
) -> dict:
    """
    采集 Telegram 频道历史消息 (T099)

    Args:
        session_id: 订阅 ID
        limit: 获取消息数量
        min_id: 从此 ID 之后获取（增量采集）

    Returns:
        采集结果
    """
    logger.info(
        "Starting Telegram history fetch",
        extra={"session_id": session_id, "limit": limit, "min_id": min_id},
    )

    async with AsyncSessionLocal() as db:
        try:
            # 获取订阅
            result = await db.execute(
                select(SocialSession).where(SocialSession.id == session_id)
            )
            session = result.scalar_one_or_none()

            if not session:
                return {"success": False, "message": "订阅不存在"}

            if session.platform != Platform.TELEGRAM:
                return {"success": False, "message": "仅支持 Telegram 平台"}

            # 采集历史消息
            fetch_result = await SocialService.fetch_telegram_history(
                db=db,
                session=session,
                limit=limit,
                min_id=min_id,
            )

            logger.info(
                "Telegram history fetch completed",
                extra={
                    "session_id": session_id,
                    "new_count": fetch_result.get("new_count", 0),
                    "total_count": fetch_result.get("total_count", 0),
                },
            )

            return fetch_result

        except Exception as e:
            logger.error(
                "Telegram history fetch exception",
                extra={"session_id": session_id, "error": str(e)},
                exc_info=True,
            )
            return {"success": False, "message": str(e)}


async def trigger_telegram_history_fetch(
    session_id: int,
    limit: int = 100,
    min_id: int = 0,
) -> dict:
    """
    手动触发 Telegram 历史消息采集

    Args:
        session_id: 订阅 ID
        limit: 获取消息数量
        min_id: 增量采集起始 ID

    Returns:
        采集结果
    """
    return await run_telegram_history_job(session_id, limit, min_id)
