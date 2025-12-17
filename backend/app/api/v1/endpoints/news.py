"""News article API endpoints."""

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.schemas.news import (
    NewsArticleResponse,
    NewsArticleListResponse,
    NewsArticleDetailResponse,
    NewsArticleGroupedResponse,
    NewsStatisticsResponse,
)
from app.schemas.scraper import NewsSourceListResponse
from app.services.news_service import NewsService
from app.services.permission_service import apply_user_filter
from app.models.news_source import NewsSource
from sqlalchemy import select

logger = get_logger(__name__)

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/articles", response_model=NewsArticleListResponse)
async def get_articles(
    current_user: Annotated[User, Depends(get_current_active_user)],
    source: Optional[str] = Query(None, description="Filter by source key"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    sort_by: str = Query("published_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve paginated news articles with optional filtering.

    Supports filtering by:
    - source: Filter by news source
    - category: Filter by article category
    - search: Search in article title
    - start_date/end_date: Filter by publication date range
    - sort_by: Sort by field (published_at, scraped_at, title)
    - sort_order: Sort order (asc, desc)

    Returns paginated results with total count.
    Note: Admin sees all articles, regular users see only their own.
    """
    # 传递用户信息用于数据过滤
    user_id = None if current_user.is_admin else current_user.id

    articles, total = await NewsService.get_articles(
        db,
        source=source,
        category=category,
        search=search,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        user_id=user_id,
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return NewsArticleListResponse(
        data=[NewsArticleResponse.model_validate(a) for a in articles],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# NOTE: /articles/grouped MUST be defined before /articles/{article_id}
# to avoid route matching conflict (FastAPI matches routes in order)
@router.get("/articles/grouped", response_model=NewsArticleGroupedResponse)
async def get_articles_grouped(
    current_user: Annotated[User, Depends(get_current_active_user)],
    category: Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[datetime] = Query(None, description="Start date (default: 24h ago)"),
    limit_per_source: int = Query(10, ge=1, le=100, description="Max articles per source"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve articles grouped by news source.

    Useful for displaying articles organized by their source in the UI.
    By default returns articles from the last 24 hours.
    Note: Admin sees all articles, regular users see only their own.

    Args:
        category: Optional category filter
        start_date: Articles published after this date (default: 24h ago)
        limit_per_source: Maximum articles per source (default: 10)

    Returns:
        Articles grouped by source with source metadata
    """
    # 传递用户信息用于数据过滤
    user_id = None if current_user.is_admin else current_user.id

    groups = await NewsService.get_articles_grouped(
        db,
        category=category,
        start_date=start_date,
        limit_per_source=limit_per_source,
        user_id=user_id,
    )

    # Convert to response format
    source_groups = []
    for group in groups:
        source_groups.append(
            NewsArticleGroupedResponse.SourceGroup(
                source_key=group["source_key"],
                source_name=group["source_name"],
                article_count=group["article_count"],
                articles=[NewsArticleResponse.model_validate(a) for a in group["articles"]],
            )
        )

    filters_applied = {}
    if category:
        filters_applied["category"] = category

    return NewsArticleGroupedResponse(
        groups=source_groups,
        total_sources=len(source_groups),
        filters_applied=filters_applied,
    )


@router.get("/articles/{article_id}", response_model=NewsArticleDetailResponse)
async def get_article(
    article_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a single news article by ID.

    Returns detailed article information including URL hash and timestamps.
    Note: Admin can access all articles, regular users only their own.
    """
    # 传递用户信息用于数据过滤
    user_id = None if current_user.is_admin else current_user.id

    article = await NewsService.get_article_by_id(db, article_id, user_id=user_id)

    if not article:
        raise HTTPException(status_code=404, detail=f"Article with id {article_id} not found")

    return NewsArticleDetailResponse.model_validate(article)


@router.get("/sources", response_model=NewsSourceListResponse)
async def get_sources(
    current_user: Annotated[User, Depends(get_current_active_user)],
    enabled_only: bool = Query(False, description="Return only enabled sources"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve list of all news sources.
    Note: Admin sees all sources, regular users see only their own.

    Args:
        enabled_only: If True, only return enabled sources

    Returns:
        List of news sources with their status and configuration
    """
    stmt = select(NewsSource)
    stmt = apply_user_filter(stmt, current_user, NewsSource)
    if enabled_only:
        stmt = stmt.where(NewsSource.enabled == True)  # noqa: E712

    result = await db.execute(stmt)
    sources = result.scalars().all()

    from app.schemas.scraper import NewsSourceResponse

    return NewsSourceListResponse(
        sources=[NewsSourceResponse.model_validate(s) for s in sources],
        total=len(sources),
    )


@router.get("/statistics", response_model=NewsStatisticsResponse)
async def get_statistics(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve aggregated statistics about news collection.
    Note: Admin sees all statistics, regular users see only their own data.

    Returns:
        Statistics including:
        - Total articles count
        - Articles collected today
        - Breakdown by source
        - Breakdown by category
        - Source health status
    """
    # 传递用户信息用于数据过滤
    user_id = None if current_user.is_admin else current_user.id

    stats = await NewsService.get_statistics(db, user_id=user_id)

    return NewsStatisticsResponse(**stats)
