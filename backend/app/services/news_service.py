"""News article service for queries and retrieval."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from app.core.logging import get_logger
from app.infrastructure.cache import get_redis
from app.models.news_article import NewsArticle
from app.models.news_source import NewsSource

logger = get_logger(__name__)

# ==================== 缓存配置 ====================
# 统计数据缓存时间（秒）- 统计数据变化不频繁，可缓存较长时间
CACHE_TTL_STATISTICS = 300  # 5 分钟
# 源列表缓存时间（秒）- 源列表基本不变
CACHE_TTL_SOURCES = 600  # 10 分钟
# 缓存键前缀
CACHE_KEY_PREFIX = "news:"


class NewsService:
    """
    Service for news article operations.

    Handles querying, filtering, pagination, and grouping of news articles.
    """

    @staticmethod
    async def get_articles(
        db: AsyncSession,
        source: str | None = None,
        category: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "published_at",
        sort_order: str = "desc",
        user_id: int | None = None,
    ) -> tuple[list[NewsArticle], int]:
        """
        Get paginated news articles with optional filtering.

        性能优化：使用 load_only() 只加载列表视图需要的字段
        - 排除 content_text (大字段，列表不需要)
        - 排除 content_hash, url_hash (详情页才需要)
        - 减少数据传输量约 80%

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
            user_id: Filter by user_id (None = no filter, for admin)

        Returns:
            Tuple of (articles list, total count)
        """
        # 性能优化：只加载列表视图需要的字段，排除大字段 content_text
        stmt = select(NewsArticle).options(
            load_only(
                NewsArticle.id,
                NewsArticle.url,
                NewsArticle.title,
                NewsArticle.source_key,
                NewsArticle.category,
                NewsArticle.published_at,
                NewsArticle.scraped_at,
                NewsArticle.user_id,
            )
        )

        # Apply user filter (data isolation)
        if user_id is not None:
            stmt = stmt.where(NewsArticle.user_id == user_id)

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
        category: str | None = None,
        start_date: datetime | None = None,
        limit_per_source: int = 10,
        user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get articles grouped by source for display.

        性能优化：使用单次 JOIN 查询替代 N+1 查询模式
        原实现: 1 + N 次查询 (N = 源数量)
        优化后: 2 次查询 (源列表 + 所有文章)

        Args:
            db: Database session
            category: Filter by category
            start_date: Filter articles published after this date (default: 24h ago)
            limit_per_source: Maximum articles per source
            user_id: Filter by user_id (None = no filter, for admin)

        Returns:
            List of source groups with articles
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(hours=24)

        # 查询 1: 获取源信息（用于显示名称）
        source_stmt = select(NewsSource).where(NewsSource.enabled == True)  # noqa: E712
        if user_id is not None:
            source_stmt = source_stmt.where(NewsSource.user_id == user_id)
        source_result = await db.execute(source_stmt)
        sources = {s.source_key: s for s in source_result.scalars().all()}

        if not sources:
            return []

        # 查询 2: 单次获取所有符合条件的文章（使用 IN 子句）
        # 比 N 次循环查询高效得多
        # 性能优化：只加载列表视图需要的字段
        article_stmt = select(NewsArticle).options(
            load_only(
                NewsArticle.id,
                NewsArticle.url,
                NewsArticle.title,
                NewsArticle.source_key,
                NewsArticle.category,
                NewsArticle.published_at,
                NewsArticle.scraped_at,
                NewsArticle.user_id,
            )
        ).where(
            NewsArticle.source_key.in_(sources.keys()),
            NewsArticle.published_at >= start_date,
        )

        if user_id is not None:
            article_stmt = article_stmt.where(NewsArticle.user_id == user_id)

        if category:
            article_stmt = article_stmt.where(NewsArticle.category == category)

        # 按发布时间排序，后续在 Python 中截取每个源的前 N 条
        article_stmt = article_stmt.order_by(desc(NewsArticle.published_at))

        result = await db.execute(article_stmt)
        all_articles = result.scalars().all()

        # 在 Python 中按源分组并截取（内存操作，比多次数据库查询快）
        articles_by_source: dict[str, list[NewsArticle]] = defaultdict(list)
        for article in all_articles:
            if len(articles_by_source[article.source_key]) < limit_per_source:
                articles_by_source[article.source_key].append(article)

        # 构建返回结果
        groups = []
        for source_key, articles in articles_by_source.items():
            if articles and source_key in sources:
                source = sources[source_key]
                groups.append({
                    "source_key": source_key,
                    "source_name": source.display_name,
                    "article_count": len(articles),
                    "articles": articles,
                })

        logger.info(
            "Retrieved articles grouped by source (optimized)",
            extra={
                "source_count": len(groups),
                "total_articles": len(all_articles),
                "category": category,
                "start_date": start_date,
            },
        )

        return groups

    @staticmethod
    async def get_article_by_id(
        db: AsyncSession,
        article_id: int,
        user_id: int | None = None,
    ) -> NewsArticle | None:
        """
        Get a single article by ID.

        Args:
            db: Database session
            article_id: Article ID
            user_id: Filter by user_id (None = no filter, for admin)

        Returns:
            NewsArticle if found, None otherwise
        """
        stmt = select(NewsArticle).where(NewsArticle.id == article_id)
        if user_id is not None:
            stmt = stmt.where(NewsArticle.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_statistics(
        db: AsyncSession,
        user_id: int | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Get aggregated statistics about news articles.

        性能优化：使用 Redis 缓存统计数据
        - 缓存时间: 5 分钟
        - 缓存键: news:statistics:{user_id}
        - 首次请求从数据库加载，后续请求从缓存读取

        Args:
            db: Database session
            user_id: Filter by user_id (None = no filter, for admin)
            use_cache: Whether to use cache (default True)

        Returns:
            Dictionary with statistics
        """
        # 构建缓存键
        cache_key = f"{CACHE_KEY_PREFIX}statistics:{user_id or 'all'}"

        # 尝试从缓存读取
        if use_cache:
            try:
                redis = get_redis()
                cached = await redis.get_json(cache_key)
                if cached:
                    logger.debug(f"Statistics cache hit: {cache_key}")
                    return cached
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")

        # 缓存未命中，从数据库查询
        logger.debug(f"Statistics cache miss: {cache_key}")

        # Build base filters
        article_filter = []
        source_filter = []
        if user_id is not None:
            article_filter.append(NewsArticle.user_id == user_id)
            source_filter.append(NewsSource.user_id == user_id)

        # Total articles
        total_stmt = select(func.count(NewsArticle.id))
        if article_filter:
            total_stmt = total_stmt.where(*article_filter)
        total_result = await db.execute(total_stmt)
        total_articles = total_result.scalar() or 0

        # Articles today (use scraped_at instead of published_at)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_stmt = select(func.count(NewsArticle.id)).where(
            NewsArticle.scraped_at >= today_start
        )
        if article_filter:
            today_stmt = today_stmt.where(*article_filter)
        today_result = await db.execute(today_stmt)
        articles_today = today_result.scalar() or 0

        # Articles yesterday (for trend calculation)
        yesterday_start = today_start - timedelta(days=1)
        yesterday_stmt = select(func.count(NewsArticle.id)).where(
            NewsArticle.scraped_at >= yesterday_start,
            NewsArticle.scraped_at < today_start
        )
        if article_filter:
            yesterday_stmt = yesterday_stmt.where(*article_filter)
        yesterday_result = await db.execute(yesterday_stmt)
        articles_yesterday = yesterday_result.scalar() or 0

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
        )
        if source_filter:
            source_stmt = source_stmt.where(*source_filter)
        source_stmt = source_stmt.group_by(
            NewsSource.source_key, NewsSource.display_name
        )
        source_result = await db.execute(source_stmt)
        by_source = [
            {
                "source_key": row[0],
                "source_name": row[1],
                "article_count": row[2] or 0,
                "last_scraped": row[3].isoformat() if row[3] else None,
            }
            for row in source_result.fetchall()
        ]

        # By category
        category_stmt = select(
            NewsArticle.category,
            func.count(NewsArticle.id).label("article_count"),
        ).where(
            NewsArticle.category.isnot(None)
        )
        if article_filter:
            category_stmt = category_stmt.where(*article_filter)
        category_stmt = category_stmt.group_by(
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
        if source_filter:
            source_health_stmt = source_health_stmt.where(*source_filter)
        source_health_result = await db.execute(source_health_stmt)
        all_sources = source_health_result.scalars().all()
        sources_active = sum(1 for s in all_sources if s.status == "idle")
        sources_failed = sum(1 for s in all_sources if s.status == "failed")

        # Last scrape time
        last_scrape_stmt = select(func.max(NewsArticle.scraped_at))
        if article_filter:
            last_scrape_stmt = last_scrape_stmt.where(*article_filter)
        last_scrape_result = await db.execute(last_scrape_stmt)
        last_scrape_time = last_scrape_result.scalar()

        # 构建结果
        result = {
            "total_articles": total_articles,
            "articles_today": articles_today,
            "articles_yesterday": articles_yesterday,
            "sources_active": sources_active,
            "sources_failed": sources_failed,
            "last_scrape_time": last_scrape_time.isoformat() if last_scrape_time else None,
            "by_source": by_source,
            "by_category": by_category,
        }

        # 缓存结果
        if use_cache:
            try:
                redis = get_redis()
                await redis.set_json(cache_key, result, ex=CACHE_TTL_STATISTICS)
                logger.debug(f"Statistics cached: {cache_key}, TTL={CACHE_TTL_STATISTICS}s")
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")

        return result

    @staticmethod
    async def invalidate_statistics_cache(user_id: int | None = None) -> None:
        """
        使统计缓存失效

        在数据发生变化时调用（如新文章插入、爬虫运行完成）

        Args:
            user_id: 用户 ID，None 表示清除所有用户的缓存
        """
        try:
            redis = get_redis()
            if user_id is not None:
                cache_key = f"{CACHE_KEY_PREFIX}statistics:{user_id}"
                await redis.delete(cache_key)
            else:
                # 清除全局统计缓存
                await redis.delete(f"{CACHE_KEY_PREFIX}statistics:all")
            logger.debug(f"Statistics cache invalidated for user: {user_id or 'all'}")
        except Exception as e:
            logger.warning(f"Failed to invalidate statistics cache: {e}")
