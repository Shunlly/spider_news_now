"""News article API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.news import (
    NewsArticleResponse,
    NewsArticleListResponse,
    NewsArticleDetailResponse,
    NewsArticleGroupedResponse,
    NewsStatisticsResponse,
)
from app.schemas.scraper import NewsSourceListResponse
from app.services.news_service import NewsService
from app.models.news_source import NewsSource
from sqlalchemy import select

logger = get_logger(__name__)

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/articles", response_model=NewsArticleListResponse)
async def get_articles(
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
    """
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
    category: Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[datetime] = Query(None, description="Start date (default: 24h ago)"),
    limit_per_source: int = Query(10, ge=1, le=100, description="Max articles per source"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve articles grouped by news source.

    Useful for displaying articles organized by their source in the UI.
    By default returns articles from the last 24 hours.

    Args:
        category: Optional category filter
        start_date: Articles published after this date (default: 24h ago)
        limit_per_source: Maximum articles per source (default: 10)

    Returns:
        Articles grouped by source with source metadata
    """
    groups = await NewsService.get_articles_grouped(
        db,
        category=category,
        start_date=start_date,
        limit_per_source=limit_per_source,
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
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a single news article by ID.

    Returns detailed article information including URL hash and timestamps.
    """
    article = await NewsService.get_article_by_id(db, article_id)

    if not article:
        raise HTTPException(status_code=404, detail=f"Article with id {article_id} not found")

    return NewsArticleDetailResponse.model_validate(article)


@router.get("/sources", response_model=NewsSourceListResponse)
async def get_sources(
    enabled_only: bool = Query(False, description="Return only enabled sources"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve list of all news sources.

    Args:
        enabled_only: If True, only return enabled sources

    Returns:
        List of news sources with their status and configuration
    """
    stmt = select(NewsSource)
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
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve aggregated statistics about news collection.

    Returns:
        Statistics including:
        - Total articles count
        - Articles collected today
        - Breakdown by source
        - Breakdown by category
        - Source health status
    """
    stats = await NewsService.get_statistics(db)

    return NewsStatisticsResponse(**stats)
