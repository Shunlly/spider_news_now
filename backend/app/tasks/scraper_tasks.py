"""Scheduled scraper tasks."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    logger.info(f"Starting scheduled scraper job", extra={"source_key": source_key})

    async with AsyncSessionLocal() as db:
        try:
            run_id = await ScraperService.run_scraper(db, source_key)

            if run_id:
                logger.info(
                    f"Scheduled scraper job completed successfully",
                    extra={"source_key": source_key, "run_id": run_id},
                )
            else:
                logger.error(
                    f"Scheduled scraper job failed",
                    extra={"source_key": source_key},
                )

        except Exception as e:
            logger.error(
                f"Scheduled scraper job exception",
                extra={"source_key": source_key, "error": str(e)},
                exc_info=True,
            )


async def register_scraper_jobs() -> None:
    """
    Register all enabled scrapers as scheduled jobs.

    This is called during application startup to initialize all scraper schedules.
    Reads from database and creates APScheduler jobs for each enabled source.
    """
    from apscheduler.triggers.interval import IntervalTrigger
    from datetime import timedelta

    async with AsyncSessionLocal() as db:
        # Get all enabled sources
        stmt = select(NewsSource).where(NewsSource.enabled == True)  # noqa: E712
        result = await db.execute(stmt)
        sources = result.scalars().all()

        scheduler = await get_scheduler()

        for source in sources:
            job_id = f"scraper_{source.source_key}"

            # Add interval job with IntervalTrigger (APScheduler 4.0)
            await scheduler.add_schedule(
                run_scraper_job,
                IntervalTrigger(seconds=source.schedule_interval),
                id=job_id,
                args=[source.source_key],
            )

            logger.info(
                f"Registered scraper job",
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
    from apscheduler.triggers.interval import IntervalTrigger

    scheduler = await get_scheduler()
    job_id = f"scraper_{source_key}"

    await scheduler.add_schedule(
        run_scraper_job,
        IntervalTrigger(seconds=interval_seconds),
        id=job_id,
        args=[source_key],
    )

    logger.info(
        f"Added/updated scraper job",
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

    logger.info(f"Removed scraper job", extra={"source_key": source_key})


async def trigger_scraper_now(source_key: str) -> None:
    """
    Manually trigger a scraper to run immediately.

    Args:
        source_key: Source identifier
    """
    logger.info(f"Manual trigger for scraper", extra={"source_key": source_key})

    async with AsyncSessionLocal() as db:
        await ScraperService.run_scraper(db, source_key)
