"""Scraper management API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, require_quota
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.news_source import NewsSource
from app.models.scraper_run import ScraperRun
from app.models.user import User
from app.schemas.scraper import (
    NewsSourceCreate,
    NewsSourceResponse,
    ScraperConfigUpdate,
    ScraperEnableResponse,
    ScraperRunListResponse,
    ScraperRunResponse,
    ScraperStatusListResponse,
    ScraperStatusResponse,
    ScraperTriggerResponse,
)
from app.services.permission_service import apply_user_filter
from app.tasks.scraper_tasks import trigger_content_parser_now, trigger_scraper_now

logger = get_logger(__name__)

router = APIRouter(prefix="/scrapers", tags=["scrapers"])


@router.post("/{source_key}/trigger", response_model=ScraperTriggerResponse, status_code=202)
async def trigger_scraper(
    source_key: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    quota_info: Annotated[dict, Depends(require_quota())],
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
        429: Quota exceeded
    """
    # Verify source exists and user has permission
    stmt = select(NewsSource).where(NewsSource.source_key == source_key)
    stmt = apply_user_filter(stmt, current_user, NewsSource)
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

    # 配额已由 require_quota() 依赖检查，并发槽位已获取
    # Quota already checked by require_quota() dependency, concurrent slot acquired

    # Trigger scraper asynchronously (fire and forget)
    # Note: The scraper task will release concurrent slot and consume daily quota on completion
    import asyncio
    asyncio.create_task(trigger_scraper_now(
        source_key,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    ))

    logger.info(
        "Manual trigger initiated",
        extra={
            "source_key": source_key,
            "user_id": current_user.id,
            "daily_remaining": quota_info["daily_remaining"],
            "concurrent_used": quota_info["concurrent_used"],
        }
    )

    from datetime import datetime
    return ScraperTriggerResponse(
        message="Scraper triggered successfully",
        run_id="pending",  # Will be assigned when job starts
        source_key=source_key,
        started_at=datetime.now(),
        status="queued",
    )


@router.get("/status", response_model=ScraperStatusListResponse)
async def get_scrapers_status(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Get status of all scrapers.

    Returns comprehensive status information including:
    - Last run time and status
    - Next scheduled run time
    - Success/failure statistics
    - Health status indicators

    Note: Admin sees all scrapers, regular users see only their own.
    """
    # 应用用户过滤：管理员看所有，普通用户看自己的
    stmt = select(NewsSource).order_by(NewsSource.source_key)
    stmt = apply_user_filter(stmt, current_user, NewsSource)
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
        from datetime import timedelta
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


@router.post("", response_model=NewsSourceResponse, status_code=201)
async def create_scraper(
    source_data: NewsSourceCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new news source/scraper.

    This endpoint allows adding new scrapers to the system without
    modifying core code.

    Args:
        source_data: New source configuration including scraper module path

    Returns:
        201 Created with the new source details

    Raises:
        409: Source with same key already exists
        400: Invalid scraper module path
    """
    # Check if source already exists
    stmt = select(NewsSource).where(NewsSource.source_key == source_data.source_key)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Source '{source_data.source_key}' already exists"
        )

    # Validate scraper module can be loaded
    try:
        import importlib
        module = importlib.import_module(source_data.scraper_module)
        class_name = f"{source_data.source_key.capitalize()}Scraper"
        if not hasattr(module, class_name):
            raise HTTPException(
                status_code=400,
                detail=f"Scraper class '{class_name}' not found in module '{source_data.scraper_module}'"
            )
    except ImportError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot import scraper module '{source_data.scraper_module}': {str(e)}"
        ) from None

    # Create new source with user_id
    new_source = NewsSource(
        user_id=current_user.id,  # 设置所有者
        source_key=source_data.source_key,
        display_name=source_data.display_name,
        enabled=source_data.enabled,
        scraper_module=source_data.scraper_module,
        schedule_interval=source_data.schedule_interval,
        status="idle",
        failure_count=0,
    )
    db.add(new_source)
    await db.commit()
    await db.refresh(new_source)

    logger.info("Created new source", extra={"source_key": source_data.source_key, "user_id": current_user.id})

    return NewsSourceResponse.model_validate(new_source)


@router.put("/{source_key}/enable", response_model=ScraperEnableResponse)
async def enable_scraper(
    source_key: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Enable a scraper to run on schedule.

    Args:
        source_key: Source identifier

    Returns:
        Confirmation with next scheduled run time

    Raises:
        404: Source not found
    """
    # Verify source exists and user has permission
    stmt = select(NewsSource).where(NewsSource.source_key == source_key)
    stmt = apply_user_filter(stmt, current_user, NewsSource)
    result = await db.execute(stmt)
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{source_key}' not found")

    if source.enabled:
        from datetime import timedelta
        next_run = None
        if source.last_run_at:
            next_run = source.last_run_at + timedelta(seconds=source.schedule_interval)
        return ScraperEnableResponse(
            message=f"Scraper '{source_key}' is already enabled",
            source_key=source_key,
            enabled=True,
            next_run_at=next_run,
        )

    # Enable the source (only if user has permission - already verified above)
    from datetime import datetime, timedelta
    await db.execute(
        update(NewsSource)
        .where(NewsSource.source_key == source_key)
        .values(enabled=True, status="idle")
    )
    await db.commit()

    # Calculate next run time
    next_run = datetime.now() + timedelta(seconds=source.schedule_interval)

    logger.info("Enabled scraper", extra={"source_key": source_key, "user_id": current_user.id})

    return ScraperEnableResponse(
        message=f"Scraper '{source_key}' enabled successfully",
        source_key=source_key,
        enabled=True,
        next_run_at=next_run,
    )


@router.put("/{source_key}/disable", response_model=ScraperEnableResponse)
async def disable_scraper(
    source_key: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Disable a scraper from running on schedule.

    Args:
        source_key: Source identifier

    Returns:
        Confirmation of disabled status

    Raises:
        404: Source not found
    """
    # Verify source exists and user has permission
    stmt = select(NewsSource).where(NewsSource.source_key == source_key)
    stmt = apply_user_filter(stmt, current_user, NewsSource)
    result = await db.execute(stmt)
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{source_key}' not found")

    if not source.enabled:
        return ScraperEnableResponse(
            message=f"Scraper '{source_key}' is already disabled",
            source_key=source_key,
            enabled=False,
            next_run_at=None,
        )

    # Disable the source (only if user has permission - already verified above)
    await db.execute(
        update(NewsSource)
        .where(NewsSource.source_key == source_key)
        .values(enabled=False, status="disabled")
    )
    await db.commit()

    logger.info("Disabled scraper", extra={"source_key": source_key, "user_id": current_user.id})

    return ScraperEnableResponse(
        message=f"Scraper '{source_key}' disabled successfully",
        source_key=source_key,
        enabled=False,
        next_run_at=None,
    )


@router.put("/{source_key}/config", response_model=NewsSourceResponse)
async def update_scraper_config(
    source_key: str,
    config: ScraperConfigUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Update scraper configuration.

    Currently supports updating:
    - schedule_interval: How often the scraper runs (in seconds)

    Args:
        source_key: Source identifier
        config: New configuration values

    Returns:
        Updated source details

    Raises:
        404: Source not found
    """
    # Verify source exists and user has permission
    stmt = select(NewsSource).where(NewsSource.source_key == source_key)
    stmt = apply_user_filter(stmt, current_user, NewsSource)
    result = await db.execute(stmt)
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{source_key}' not found")

    # Update configuration (only if user has permission - already verified above)
    await db.execute(
        update(NewsSource)
        .where(NewsSource.source_key == source_key)
        .values(schedule_interval=config.schedule_interval)
    )
    await db.commit()
    await db.refresh(source)

    logger.info(
        "Updated scraper config",
        extra={"source_key": source_key, "schedule_interval": config.schedule_interval, "user_id": current_user.id}
    )

    return NewsSourceResponse.model_validate(source)


@router.get("/{source_key}/runs", response_model=ScraperRunListResponse)
async def get_scraper_runs(
    source_key: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
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
    # Verify source exists and user has permission
    stmt = select(NewsSource).where(NewsSource.source_key == source_key)
    stmt = apply_user_filter(stmt, current_user, NewsSource)
    result = await db.execute(stmt)
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{source_key}' not found")

    # Get total count
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


# ============== 正文解析接口 ==============


@router.post("/content-parser/trigger", status_code=202)
async def trigger_content_parser(
    current_user: Annotated[User, Depends(get_current_active_user)],
    quota_info: Annotated[dict, Depends(require_quota())],
    batch_size: int = Query(50, ge=1, le=200, description="Number of articles to process"),
    db: AsyncSession = Depends(get_db),
):
    """
    手动触发正文解析任务。

    用于后台异步解析文章正文内容。

    Args:
        batch_size: 每批处理的文章数量 (默认 50, 最大 200)

    Returns:
        202 Accepted with task status

    Raises:
        429: Quota exceeded
    """
    import asyncio

    # 配额已由 require_quota() 依赖检查
    # 异步执行，不阻塞
    asyncio.create_task(trigger_content_parser_now(batch_size))

    logger.info(
        "Content parser triggered",
        extra={
            "batch_size": batch_size,
            "user_id": current_user.id,
            "daily_remaining": quota_info["daily_remaining"],
        }
    )

    return {
        "message": "Content parser triggered successfully",
        "batch_size": batch_size,
        "status": "queued",
    }


@router.get("/content-parser/status")
async def get_content_parser_status(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    获取正文解析状态统计。

    返回待解析、解析中、已完成、失败的文章数量。

    Returns:
        各状态的文章数量统计
    """
    from app.models.news_article import NewsArticle

    # 统计各状态数量
    stats = {}
    for status in ["pending", "parsing", "completed", "failed"]:
        count_stmt = select(func.count()).select_from(NewsArticle).where(
            NewsArticle.content_status == status
        )
        result = await db.execute(count_stmt)
        stats[status] = result.scalar()

    # 统计超过重试次数的文章
    from app.services.content_parser_service import MAX_RETRY_COUNT
    max_retry_stmt = select(func.count()).select_from(NewsArticle).where(
        NewsArticle.content_status == "failed",
        NewsArticle.content_retry_count >= MAX_RETRY_COUNT,
    )
    max_retry_result = await db.execute(max_retry_stmt)
    stats["permanently_failed"] = max_retry_result.scalar()

    return {
        "status": stats,
        "total_pending": stats["pending"] + stats.get("failed", 0) - stats.get("permanently_failed", 0),
        "message": "Content parser status retrieved successfully",
    }
