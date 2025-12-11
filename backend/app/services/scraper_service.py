"""Scraper orchestration service."""

import importlib
from datetime import datetime
from typing import List, Optional

from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.news_article import NewsArticle
from app.models.news_source import NewsSource
from app.models.scraper_run import ScraperRun
from app.services.duplicate_service import DuplicateService

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
                f"Scraper completed",
                extra={"source_key": source_key, "article_count": len(articles)},
            )

            # Step 4: Filter duplicates
            new_articles, duplicate_articles = await DuplicateService.filter_duplicates(
                db, articles
            )

            # Step 5: Insert new articles
            if new_articles:
                article_models = [NewsArticle(**article) for article in new_articles]
                db.add_all(article_models)
                await db.commit()

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
                    articles_new=len(new_articles),
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
                f"Scraper run completed successfully",
                extra={
                    "source_key": source_key,
                    "run_id": scraper_run.id,
                    "articles_scraped": len(articles),
                    "articles_new": len(new_articles),
                    "duration": duration,
                },
            )

            return scraper_run.id

        except Exception as e:
            # Update ScraperRun with error
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())

            await db.execute(
                update(ScraperRun)
                .where(ScraperRun.id == scraper_run.id)
                .values(
                    completed_at=end_time,
                    status="failed",
                    duration_seconds=duration,
                    error_message=str(e),
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

            logger.error(
                f"Scraper run failed",
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
