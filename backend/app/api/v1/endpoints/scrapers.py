"""Scraper management API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_db
from app.models.news_source import NewsSource
from app.models.scraper_run import ScraperRun
from app.schemas.scraper import (
    ScraperTriggerResponse,
    ScraperStatusResponse,
    ScraperStatusListResponse,
    ScraperRunResponse,
    ScraperRunListResponse,
)
from app.tasks.scraper_tasks import trigger_scraper_now

logger = get_logger(__name__)

router = APIRouter(prefix="/scrapers", tags=["scrapers"])


@router.post("/{source_key}/trigger", response_model=ScraperTriggerResponse, status_code=202)
async def trigger_scraper(
    source_key: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger a scraper to run immediately.

    This endpoint is useful for:
    - Testing scrapers
    - Manually collecting news on demand
    - Recovering from scraper failures

    Args:
        source_key: Source identifier (sina, qq, wangyi, yicai, huanqiu, ifeng)
        db: Database session

    Returns:
        202 Accepted with scraper trigger confirmation

    Raises:
        404: Source not found
        409: Scraper already running
    """
    # Verify source exists
    stmt = select(NewsSource).where(NewsSource.source_key == source_key)
    result = await db.execute(stmt)
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{source_key}' not found")

    if not source.enabled:
        raise HTTPException(status_code=400, detail=f"Source '{source_key}' is disabled")

    # Check if scraper is already running
    if source.status == "running":
        raise HTTPException(
            status_code=409,
            detail=f"Scraper for '{source_key}' is already running"
        )

    # Trigger scraper asynchronously (fire and forget)
    import asyncio
    asyncio.create_task(trigger_scraper_now(source_key))

    logger.info(f"Manual trigger initiated", extra={"source_key": source_key})

    from datetime import datetime
    return ScraperTriggerResponse(
        message="Scraper triggered successfully",
        run_id=0,  # Will be assigned when job starts
        source_key=source_key,
        started_at=datetime.now(),
        status="queued",
    )


@router.get("/status", response_model=ScraperStatusListResponse)
async def get_scrapers_status(
    db: AsyncSession = Depends(get_db),
):
    """
    Get status of all scrapers.

    Returns comprehensive status information including:
    - Last run time and status
    - Next scheduled run time
    - Success/failure statistics
    - Health status indicators

    This endpoint is useful for:
    - Monitoring dashboard
    - Health checks
    - Operational visibility
    """
    stmt = select(NewsSource).order_by(NewsSource.source_key)
    result = await db.execute(stmt)
    sources = result.scalars().all()

    statuses = []
    active_runs = 0

    for source in sources:
        # Get last completed run
        run_stmt = (
            select(ScraperRun)
            .where(
                ScraperRun.source_key == source.source_key,
                ScraperRun.status.in_(["success", "failed", "timeout"])
            )
            .order_by(desc(ScraperRun.started_at))
            .limit(1)
        )
        run_result = await db.execute(run_stmt)
        last_run_record = run_result.scalar_one_or_none()

        # Get current running job
        current_stmt = (
            select(ScraperRun)
            .where(
                ScraperRun.source_key == source.source_key,
                ScraperRun.status == "running"
            )
            .order_by(desc(ScraperRun.started_at))
            .limit(1)
        )
        current_result = await db.execute(current_stmt)
        current_run_record = current_result.scalar_one_or_none()

        if current_run_record:
            active_runs += 1

        # Convert to RunSummary schemas
        from app.schemas.scraper import RunSummary

        last_run = None
        if last_run_record:
            last_run = RunSummary(
                started_at=last_run_record.started_at,
                completed_at=last_run_record.completed_at,
                status=last_run_record.status,
                articles_scraped=last_run_record.articles_scraped,
                articles_new=last_run_record.articles_new,
                articles_duplicate=last_run_record.articles_duplicate,
                duration_seconds=last_run_record.duration_seconds,
            )

        current_run = None
        if current_run_record:
            current_run = RunSummary(
                started_at=current_run_record.started_at,
                completed_at=current_run_record.completed_at,
                status=current_run_record.status,
                articles_scraped=current_run_record.articles_scraped,
                articles_new=current_run_record.articles_new,
                articles_duplicate=current_run_record.articles_duplicate,
                duration_seconds=current_run_record.duration_seconds,
            )

        # Calculate next run time (approximate - based on schedule interval)
        from datetime import datetime, timedelta
        next_run_at = None
        if source.enabled and source.last_run_at:
            next_run_at = source.last_run_at + timedelta(seconds=source.schedule_interval)

        status = ScraperStatusResponse(
            source_key=source.source_key,
            source_name=source.display_name,
            enabled=source.enabled,
            status=source.status,
            last_run=last_run,
            current_run=current_run,
            next_run_at=next_run_at,
            failure_count=source.failure_count,
        )
        statuses.append(status)

    return ScraperStatusListResponse(
        scrapers=statuses,
        total_scrapers=len(statuses),
        active_runs=active_runs
    )


@router.get("/{source_key}/runs", response_model=ScraperRunListResponse)
async def get_scraper_runs(
    source_key: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get execution history for a specific scraper.

    Returns paginated list of scraper runs with:
    - Start/end times
    - Success/failure status
    - Articles scraped (total and new)
    - Error messages if failed

    Args:
        source_key: Source identifier
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)

    Returns:
        Paginated list of scraper run records
    """
    # Verify source exists
    stmt = select(NewsSource).where(NewsSource.source_key == source_key)
    result = await db.execute(stmt)
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{source_key}' not found")

    # Get total count
    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(ScraperRun).where(
        ScraperRun.source_key == source_key
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Get paginated runs
    offset = (page - 1) * page_size
    runs_stmt = (
        select(ScraperRun)
        .where(ScraperRun.source_key == source_key)
        .order_by(desc(ScraperRun.started_at))
        .offset(offset)
        .limit(page_size)
    )
    runs_result = await db.execute(runs_stmt)
    runs = runs_result.scalars().all()

    return ScraperRunListResponse(
        runs=[ScraperRunResponse.model_validate(run) for run in runs],
        total=total,
        page=page,
        page_size=page_size,
    )
