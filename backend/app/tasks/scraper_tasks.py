"""Scheduled scraper tasks."""

from sqlalchemy import select

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.news_source import NewsSource
from app.services.scraper_service import ScraperService
from app.tasks.scheduler import get_scheduler

logger = get_logger(__name__)


async def run_scraper_job(source_key: str) -> None:
    """
    Job function to run a single scraper.

    This is executed by APScheduler on schedule.

    Args:
        source_key: Source identifier to scrape
    """
    logger.info("Starting scheduled scraper job", extra={"source_key": source_key})

    async with AsyncSessionLocal() as db:
        try:
            run_id = await ScraperService.run_scraper(db, source_key)

            if run_id:
                logger.info(
                    "Scheduled scraper job completed successfully",
                    extra={"source_key": source_key, "run_id": run_id},
                )
            else:
                logger.error(
                    "Scheduled scraper job failed",
                    extra={"source_key": source_key},
                )

        except Exception as e:
            logger.error(
                "Scheduled scraper job exception",
                extra={"source_key": source_key, "error": str(e)},
                exc_info=True,
            )


async def register_scraper_jobs() -> None:
    """
    Register all enabled scrapers as scheduled jobs.

    This is called during application startup to initialize all scraper schedules.
    Reads from database and creates APScheduler jobs for each enabled source.
    """
    from datetime import datetime, timedelta

    from apscheduler import ConflictPolicy
    from apscheduler.triggers.interval import IntervalTrigger

    async with AsyncSessionLocal() as db:
        # Get all enabled sources
        stmt = select(NewsSource).where(NewsSource.enabled == True)  # noqa: E712
        result = await db.execute(stmt)
        sources = result.scalars().all()

        scheduler = await get_scheduler()

        for source in sources:
            job_id = f"scraper_{source.source_key}"

            # 计算首次运行时间：当前时间 + 调度间隔
            # 避免启动时立即运行所有爬虫导致阻塞
            first_run = datetime.now() + timedelta(seconds=source.schedule_interval)

            # Add interval job with IntervalTrigger (APScheduler 4.0)
            await scheduler.add_schedule(
                run_scraper_job,
                IntervalTrigger(seconds=source.schedule_interval, start_time=first_run),
                id=job_id,
                args=[source.source_key],
                conflict_policy=ConflictPolicy.replace,
            )

            logger.info(
                "Registered scraper job",
                extra={
                    "source_key": source.source_key,
                    "interval": source.schedule_interval,
                    "job_id": job_id,
                },
            )

        logger.info(f"Registered {len(sources)} scraper jobs")


async def add_scraper_job(source_key: str, interval_seconds: int) -> None:
    """
    Add or update a scraper job dynamically.

    Args:
        source_key: Source identifier
        interval_seconds: Scrape interval in seconds
    """
    from apscheduler import ConflictPolicy
    from apscheduler.triggers.interval import IntervalTrigger

    scheduler = await get_scheduler()
    job_id = f"scraper_{source_key}"

    await scheduler.add_schedule(
        run_scraper_job,
        IntervalTrigger(seconds=interval_seconds),
        id=job_id,
        args=[source_key],
        conflict_policy=ConflictPolicy.replace,
    )

    logger.info(
        "Added/updated scraper job",
        extra={"source_key": source_key, "interval": interval_seconds},
    )


async def remove_scraper_job(source_key: str) -> None:
    """
    Remove a scraper job.

    Args:
        source_key: Source identifier
    """
    scheduler = await get_scheduler()
    job_id = f"scraper_{source_key}"

    await scheduler.remove_schedule(job_id)

    logger.info("Removed scraper job", extra={"source_key": source_key})


async def trigger_scraper_now(
    source_key: str,
    user_id: str | None = None,
    tenant_id: int | None = None,
) -> None:
    """
    Manually trigger a scraper to run immediately.

    Args:
        source_key: Source identifier
        user_id: User ID for quota management (optional)
        tenant_id: Tenant ID for multi-tenant isolation
    """
    logger.info(
        "Manual trigger for scraper",
        extra={"source_key": source_key, "user_id": user_id, "tenant_id": tenant_id}
    )

    async with AsyncSessionLocal() as db:
        try:
            run_id = await ScraperService.run_scraper(
                db, source_key, user_id=user_id, tenant_id=tenant_id
            )

            # 如果有用户 ID，处理配额消耗
            # If user_id provided, handle quota consumption
            if user_id:
                from app.models.scraper_run import ScraperRun
                from app.services.quota_service import quota_service

                # 获取本次运行的文章数量用于配额消耗
                # Get the number of new articles for quota consumption
                if run_id:
                    stmt = select(ScraperRun).where(ScraperRun.id == run_id)
                    result = await db.execute(stmt)
                    run_record = result.scalar_one_or_none()

                    if run_record and run_record.articles_new > 0:
                        # 消耗配额（按新增文章数）
                        await quota_service.consume_daily_quota(
                            db, user_id, run_record.articles_new
                        )
                        logger.info(
                            "Quota consumed for scraper run",
                            extra={
                                "source_key": source_key,
                                "user_id": user_id,
                                "articles_new": run_record.articles_new,
                            }
                        )

                # 释放并发槽位
                # Release concurrent slot
                await quota_service.release_concurrent_slot(db, user_id)
                logger.debug(
                    "Concurrent slot released after scraper",
                    extra={"source_key": source_key, "user_id": user_id}
                )

        except Exception as e:
            # 发生异常也要释放并发槽位
            # Release concurrent slot even on exception
            if user_id:
                try:
                    from app.services.quota_service import quota_service
                    await quota_service.release_concurrent_slot(db, user_id)
                except Exception:
                    pass  # Ignore release errors

            logger.error(
                "Manual trigger failed",
                extra={"source_key": source_key, "user_id": user_id, "error": str(e)},
                exc_info=True,
            )


# ============== 正文解析任务 ==============


async def run_content_parser_job(batch_size: int = 20) -> None:
    """
    Job function to parse article content in background.

    This is executed by APScheduler on schedule.

    Args:
        batch_size: Number of articles to process per batch
    """
    from app.services.content_parser_service import run_content_parser

    logger.info("Starting content parser job", extra={"batch_size": batch_size})

    async with AsyncSessionLocal() as db:
        try:
            result = await run_content_parser(db, batch_size)

            logger.info(
                "Content parser job completed",
                extra={
                    "total": result["total"],
                    "success": result["success"],
                    "failed": result["failed"],
                },
            )

        except Exception as e:
            logger.error(
                "Content parser job exception",
                extra={"error": str(e)},
                exc_info=True,
            )


async def register_content_parser_job(interval_seconds: int = 300) -> None:
    """
    Register content parser as a scheduled job.

    Args:
        interval_seconds: Parse interval in seconds (default 5 minutes)
    """
    from datetime import datetime, timedelta

    from apscheduler import ConflictPolicy
    from apscheduler.triggers.interval import IntervalTrigger

    scheduler = await get_scheduler()
    job_id = "content_parser"

    # 延迟首次运行，避免启动时阻塞
    first_run = datetime.now() + timedelta(seconds=interval_seconds)

    await scheduler.add_schedule(
        run_content_parser_job,
        IntervalTrigger(seconds=interval_seconds, start_time=first_run),
        id=job_id,
        args=[20],  # batch size
        conflict_policy=ConflictPolicy.replace,
    )

    logger.info(
        "Registered content parser job",
        extra={"interval": interval_seconds, "job_id": job_id},
    )


async def trigger_content_parser_now(batch_size: int = 50) -> dict:
    """
    Manually trigger content parser to run immediately.

    Args:
        batch_size: Number of articles to process

    Returns:
        Processing result statistics
    """
    from app.services.content_parser_service import run_content_parser

    logger.info("Manual trigger for content parser", extra={"batch_size": batch_size})

    async with AsyncSessionLocal() as db:
        return await run_content_parser(db, batch_size)
