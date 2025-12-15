"""News article service for queries and retrieval."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.news_article import NewsArticle
from app.models.news_source import NewsSource

logger = get_logger(__name__)


class NewsService:
    """
    Service for news article operations.

    Handles querying, filtering, pagination, and grouping of news articles.
    """

    @staticmethod
    async def get_articles(
        db: AsyncSession,
        source: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "published_at",
        sort_order: str = "desc",
    ) -> tuple[List[NewsArticle], int]:
        """
        Get paginated news articles with optional filtering.

        Args:
            db: Database session
            source: Filter by source key
            category: Filter by category
            start_date: Filter articles published after this date
            end_date: Filter articles published before this date
            search: Search query for title
            page: Page number (1-indexed)
            page_size: Items per page (max 1000)
            sort_by: Sort field (published_at, scraped_at, title)
            sort_order: Sort order (asc, desc)

        Returns:
            Tuple of (articles list, total count)
        """
        # Build query
        stmt = select(NewsArticle)

        # Apply filters
        if source:
            stmt = stmt.where(NewsArticle.source_key == source)
        if category:
            stmt = stmt.where(NewsArticle.category == category)
        if start_date:
            stmt = stmt.where(NewsArticle.published_at >= start_date)
        if end_date:
            stmt = stmt.where(NewsArticle.published_at <= end_date)
        if search:
            stmt = stmt.where(NewsArticle.title.ilike(f"%{search}%"))

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(NewsArticle, sort_by, NewsArticle.published_at)
        if sort_order == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(sort_column)

        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        # Execute query
        result = await db.execute(stmt)
        articles = result.scalars().all()

        logger.info(
            f"Retrieved {len(articles)} articles (page {page}/{(total + page_size - 1) // page_size})",
            extra={
                "total": total,
                "page": page,
                "filters": {
                    "source": source,
                    "category": category,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            },
        )

        return list(articles), total

    @staticmethod
    async def get_articles_grouped(
        db: AsyncSession,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        limit_per_source: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get articles grouped by source for display.

        Args:
            db: Database session
            category: Filter by category
            start_date: Filter articles published after this date (default: 24h ago)
            limit_per_source: Maximum articles per source

        Returns:
            List of source groups with articles
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(hours=24)

        # Get all sources
        source_stmt = select(NewsSource).where(NewsSource.enabled == True)  # noqa: E712
        source_result = await db.execute(source_stmt)
        sources = source_result.scalars().all()

        groups = []

        for source in sources:
            # Build query for this source
            stmt = select(NewsArticle).where(
                NewsArticle.source_key == source.source_key,
                NewsArticle.published_at >= start_date,
            )

            if category:
                stmt = stmt.where(NewsArticle.category == category)

            stmt = stmt.order_by(desc(NewsArticle.published_at)).limit(limit_per_source)

            # Execute query
            result = await db.execute(stmt)
            articles = result.scalars().all()

            if articles:  # Only include sources with articles
                groups.append({
                    "source_key": source.source_key,
                    "source_name": source.display_name,
                    "article_count": len(articles),
                    "articles": articles,
                })

        logger.info(
            "Retrieved articles grouped by source",
            extra={
                "source_count": len(groups),
                "category": category,
                "start_date": start_date,
            },
        )

        return groups

    @staticmethod
    async def get_article_by_id(
        db: AsyncSession, article_id: int
    ) -> Optional[NewsArticle]:
        """
        Get a single article by ID.

        Args:
            db: Database session
            article_id: Article ID

        Returns:
            NewsArticle if found, None otherwise
        """
        stmt = select(NewsArticle).where(NewsArticle.id == article_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_statistics(db: AsyncSession) -> Dict[str, Any]:
        """
        Get aggregated statistics about news articles.

        Args:
            db: Database session

        Returns:
            Dictionary with statistics
        """
        # Total articles
        total_stmt = select(func.count(NewsArticle.id))
        total_result = await db.execute(total_stmt)
        total_articles = total_result.scalar() or 0

        # Articles today (use scraped_at instead of published_at)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_stmt = select(func.count(NewsArticle.id)).where(
            NewsArticle.scraped_at >= today_start
        )
        today_result = await db.execute(today_stmt)
        articles_today = today_result.scalar() or 0

        # By source (today's articles only for pie chart)
        source_stmt = select(
            NewsSource.source_key,
            NewsSource.display_name,
            func.count(NewsArticle.id).label("article_count"),
            func.max(NewsArticle.scraped_at).label("last_scraped"),
        ).join(
            NewsArticle,
            (NewsSource.source_key == NewsArticle.source_key) & (NewsArticle.scraped_at >= today_start),
            isouter=True
        ).group_by(
            NewsSource.source_key, NewsSource.display_name
        )
        source_result = await db.execute(source_stmt)
        by_source = [
            {
                "source_key": row[0],
                "source_name": row[1],
                "article_count": row[2] or 0,
                "last_scraped": row[3],
            }
            for row in source_result.fetchall()
        ]

        # By category
        category_stmt = select(
            NewsArticle.category,
            func.count(NewsArticle.id).label("article_count"),
        ).where(
            NewsArticle.category.isnot(None)
        ).group_by(
            NewsArticle.category
        ).order_by(
            desc("article_count")
        )
        category_result = await db.execute(category_stmt)
        by_category = [
            {"category": row[0], "article_count": row[1]}
            for row in category_result.fetchall()
        ]

        # Source health
        source_health_stmt = select(NewsSource)
        source_health_result = await db.execute(source_health_stmt)
        all_sources = source_health_result.scalars().all()
        sources_active = sum(1 for s in all_sources if s.status == "idle")
        sources_failed = sum(1 for s in all_sources if s.status == "failed")

        # Last scrape time
        last_scrape_stmt = select(func.max(NewsArticle.scraped_at))
        last_scrape_result = await db.execute(last_scrape_stmt)
        last_scrape_time = last_scrape_result.scalar()

        return {
            "total_articles": total_articles,
            "articles_today": articles_today,
            "sources_active": sources_active,
            "sources_failed": sources_failed,
            "last_scrape_time": last_scrape_time,
            "by_source": by_source,
            "by_category": by_category,
        }
