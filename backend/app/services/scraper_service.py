"""Scraper orchestration service."""

import importlib
from datetime import datetime
from typing import Optional

from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.news_article import NewsArticle
from app.models.news_source import NewsSource
from app.models.scraper_run import ScraperRun
from app.services.duplicate_service import DuplicateService
from app.services.search_service import get_search_service

logger = get_logger(__name__)


class ScraperService:
    """
    Service for orchestrating scraper execution.

    Handles:
    - Dynamic scraper loading
    - Scraper execution with error handling
    - Duplicate detection and article insertion
    - ScraperRun tracking and statistics
    """

    # Special case mappings for source_key to class name
    CLASS_NAME_MAPPINGS = {
        "qq": "QQScraper",
    }

    @staticmethod
    async def load_scraper(source_key: str, scraper_module: str):
        """
        Dynamically load a scraper class.

        Args:
            source_key: Source identifier (e.g., 'sina')
            scraper_module: Python module path (e.g., 'app.scrapers.sina_scraper')

        Returns:
            Scraper instance

        Raises:
            ImportError: If scraper module cannot be loaded
        """
        try:
            # Import module
            module = importlib.import_module(scraper_module)

            # Get scraper class name (check special mappings first, then use default CamelCase)
            class_name = ScraperService.CLASS_NAME_MAPPINGS.get(
                source_key, f"{source_key.capitalize()}Scraper"
            )
            scraper_class = getattr(module, class_name)

            # Instantiate scraper
            scraper = scraper_class()

            logger.info(f"Loaded scraper: {source_key}")
            return scraper

        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to load scraper {source_key}: {str(e)}")
            raise

    @staticmethod
    async def run_scraper(db: AsyncSession, source_key: str) -> Optional[int]:
        """
        Execute a scraper and save results to database.

        Args:
            db: Database session
            source_key: Source identifier to scrape

        Returns:
            ScraperRun ID if successful, None if failed

        Workflow:
            1. Get source configuration from database
            2. Create ScraperRun record (status=running)
            3. Load and execute scraper
            4. Filter duplicates
            5. Insert new articles
            6. Update ScraperRun with statistics
            7. Update NewsSource status
        """
        start_time = datetime.now()

        # Step 1: Get source configuration
        stmt = select(NewsSource).where(NewsSource.source_key == source_key)
        result = await db.execute(stmt)
        source = result.scalar_one_or_none()

        if not source:
            logger.error(f"Source not found: {source_key}")
            return None

        if not source.enabled:
            logger.warning(f"Source is disabled: {source_key}")
            return None

        # Step 2: Create ScraperRun record
        scraper_run = ScraperRun(
            source_key=source_key,
            started_at=start_time,
            status="running",
        )
        db.add(scraper_run)
        await db.commit()
        await db.refresh(scraper_run)

        # Update source status
        await db.execute(
            update(NewsSource)
            .where(NewsSource.source_key == source_key)
            .values(status="running", last_run_at=start_time)
        )
        await db.commit()

        try:
            # Step 3: Load and execute scraper
            scraper = await ScraperService.load_scraper(source_key, source.scraper_module)
            articles = await scraper.run()

            logger.info(
                "Scraper completed",
                extra={"source_key": source_key, "article_count": len(articles)},
            )

            # Step 4: Filter duplicates
            new_articles, duplicate_articles = await DuplicateService.filter_duplicates(
                db, articles
            )

            # Step 4.5: Update existing articles with content if they don't have it
            content_updated = 0
            for article in duplicate_articles:
                if (article.get("content_text") or article.get("content_url")) and article.get("url_hash"):
                    # Check if existing article needs content update
                    existing = await db.execute(
                        select(NewsArticle).where(
                            NewsArticle.url_hash == article["url_hash"],
                            NewsArticle.content_url.is_(None)
                        )
                    )
                    existing_article = existing.scalar_one_or_none()
                    if existing_article:
                        update_values = {
                            "content_hash": article.get("content_hash")
                        }
                        if article.get("content_url"):
                            update_values["content_url"] = article["content_url"]
                        if article.get("content_text"):
                            update_values["content_text"] = article["content_text"]

                        await db.execute(
                            update(NewsArticle)
                            .where(NewsArticle.id == existing_article.id)
                            .values(**update_values)
                        )
                        content_updated += 1

            if content_updated > 0:
                await db.commit()
                logger.info(f"Updated {content_updated} existing articles with content")

            # Step 5: Insert new articles (逐个插入，跳过重复)
            inserted_count = 0
            inserted_articles = []
            if new_articles:
                for article_data in new_articles:
                    try:
                        article_model = NewsArticle(**article_data)
                        db.add(article_model)
                        await db.commit()
                        await db.refresh(article_model)
                        inserted_count += 1
                        inserted_articles.append(article_model)
                    except Exception as insert_e:
                        await db.rollback()
                        if "Duplicate entry" in str(insert_e):
                            logger.debug(f"Skipping duplicate article: {article_data.get('title', 'Unknown')[:30]}")
                        else:
                            logger.warning(f"Failed to insert article: {insert_e}")
                        continue

                logger.info(f"Inserted {inserted_count} new articles")

                # 批量索引到 Meilisearch（在插入循环外）
                if inserted_articles:
                    try:
                        search_service = get_search_service()
                        index_docs = [{
                            "id": m.id,
                            "title": m.title,
                            "url": m.url,
                            "source_key": m.source_key,
                            "category": m.category,
                            "content": m.content_text,
                            "published_at": m.published_at,
                            "created_at": m.created_at,
                        } for m in inserted_articles]
                        await search_service.index_documents(index_docs)
                        logger.info(f"Indexed {len(index_docs)} articles to Meilisearch")
                    except Exception as search_e:
                        logger.warning(f"Failed to index articles to Meilisearch: {search_e}")

            # Step 6: Update ScraperRun with statistics
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())

            await db.execute(
                update(ScraperRun)
                .where(ScraperRun.id == scraper_run.id)
                .values(
                    completed_at=end_time,
                    status="success",
                    articles_scraped=len(articles),
                    articles_new=inserted_count,
                    articles_duplicate=len(duplicate_articles),
                    duration_seconds=duration,
                )
            )
            await db.commit()

            # Step 7: Update NewsSource status
            await db.execute(
                update(NewsSource)
                .where(NewsSource.source_key == source_key)
                .values(
                    status="idle",
                    last_success_at=end_time,
                    failure_count=0,
                )
            )
            await db.commit()

            logger.info(
                "Scraper run completed successfully",
                extra={
                    "source_key": source_key,
                    "run_id": scraper_run.id,
                    "articles_scraped": len(articles),
                    "articles_new": inserted_count,
                    "duration": duration,
                },
            )

            return scraper_run.id

        except Exception as e:
            # 确保回滚任何未完成的事务
            await db.rollback()

            # Update ScraperRun with error
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())

            try:
                await db.execute(
                    update(ScraperRun)
                    .where(ScraperRun.id == scraper_run.id)
                    .values(
                        completed_at=end_time,
                        status="failed",
                        duration_seconds=duration,
                        error_message=str(e)[:500],  # 限制错误信息长度
                    )
                )
                await db.commit()

                # Update NewsSource status
                await db.execute(
                    update(NewsSource)
                    .where(NewsSource.source_key == source_key)
                    .values(
                        status="failed",
                        failure_count=NewsSource.failure_count + 1,
                    )
                )
                await db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update scraper status: {update_error}")
                await db.rollback()

            logger.error(
                "Scraper run failed",
                extra={
                    "source_key": source_key,
                    "run_id": scraper_run.id,
                    "error": str(e),
                },
                exc_info=True,
            )

            return None

    @staticmethod
    async def get_scraper_status(db: AsyncSession) -> dict:
        """
        Get status of all scrapers.

        Args:
            db: Database session

        Returns:
            Dictionary with scraper statistics
        """
        # Get all sources
        stmt = select(NewsSource)
        result = await db.execute(stmt)
        sources = result.scalars().all()

        return {
            "total_scrapers": len(sources),
            "enabled": sum(1 for s in sources if s.enabled),
            "running": sum(1 for s in sources if s.status == "running"),
            "failed": sum(1 for s in sources if s.status == "failed"),
        }
