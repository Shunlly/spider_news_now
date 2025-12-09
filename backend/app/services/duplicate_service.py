"""Duplicate detection service."""

import hashlib
from typing import Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news_article import NewsArticle
from app.core.logging import get_logger

logger = get_logger(__name__)


class DuplicateService:
    """
    Service for detecting duplicate articles.

    Uses URL hashing for primary duplicate detection.
    """

    @staticmethod
    def compute_url_hash(url: str) -> str:
        """
        Compute SHA-256 hash of normalized URL.

        Args:
            url: Article URL

        Returns:
            64-character hexadecimal hash
        """
        # Normalize URL
        normalized_url = url.strip().rstrip("/")

        # Remove fragments
        if "#" in normalized_url:
            normalized_url = normalized_url.split("#")[0]

        # Compute hash
        return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()

    @staticmethod
    async def get_existing_url_hashes(
        db: AsyncSession, url_hashes: Set[str]
    ) -> Set[str]:
        """
        Get set of URL hashes that already exist in database.

        Args:
            db: Database session
            url_hashes: Set of URL hashes to check

        Returns:
            Set of URL hashes that exist in database
        """
        if not url_hashes:
            return set()

        # Query database for existing hashes
        stmt = select(NewsArticle.url_hash).where(NewsArticle.url_hash.in_(url_hashes))
        result = await db.execute(stmt)
        existing_hashes = {row[0] for row in result.fetchall()}

        logger.info(
            f"Checked {len(url_hashes)} hashes, found {len(existing_hashes)} duplicates"
        )

        return existing_hashes

    @staticmethod
    async def filter_duplicates(
        db: AsyncSession, articles: list[dict]
    ) -> tuple[list[dict], list[dict]]:
        """
        Filter out duplicate articles.

        Args:
            db: Database session
            articles: List of article dictionaries with url_hash

        Returns:
            Tuple of (new_articles, duplicate_articles)
        """
        if not articles:
            return [], []

        # Extract URL hashes
        url_hashes = {article["url_hash"] for article in articles}

        # Get existing hashes from database
        existing_hashes = await DuplicateService.get_existing_url_hashes(db, url_hashes)

        # Split into new and duplicates
        new_articles = [a for a in articles if a["url_hash"] not in existing_hashes]
        duplicate_articles = [a for a in articles if a["url_hash"] in existing_hashes]

        logger.info(
            f"Filtered {len(articles)} articles: {len(new_articles)} new, {len(duplicate_articles)} duplicates",
            extra={
                "total": len(articles),
                "new": len(new_articles),
                "duplicates": len(duplicate_articles),
            },
        )

        return new_articles, duplicate_articles
