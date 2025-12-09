"""Base scraper class defining the interface for all news scrapers."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any
import hashlib

from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for all news scrapers.

    All scrapers must inherit from this class and implement the required methods.
    This ensures consistent interface and behavior across all scrapers.
    """

    def __init__(self, source_key: str, display_name: str):
        """
        Initialize the scraper.

        Args:
            source_key: Unique identifier for the news source (e.g., 'sina', 'qq')
            display_name: Human-readable name for the source (e.g., '新浪新闻')
        """
        self.source_key = source_key
        self.display_name = display_name
        self.logger = get_logger(f"{__name__}.{source_key}")

    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape news articles from the source.

        This method must be implemented by each scraper to collect articles
        from their respective news source.

        Returns:
            List of article dictionaries with keys:
                - url: str (article URL)
                - title: str (article title)
                - category: str (article category, e.g., 'ent', 'china', 'world')
                - published_at: datetime (when article was published)

        Raises:
            Exception: If scraping fails
        """
        pass

    def parse(self, raw_article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and normalize a raw article dictionary.

        Converts raw scraper output to standardized format with validation.

        Args:
            raw_article: Raw article data from scraper

        Returns:
            Normalized article dictionary with:
                - url: str (normalized URL)
                - url_hash: str (SHA-256 hash of URL)
                - title: str (cleaned title)
                - source_key: str (source identifier)
                - category: str (normalized category)
                - published_at: datetime

        Example:
            Input: {"url": "https://news.sina.com.cn/article", "title": "Title", ...}
            Output: {"url_hash": "abc123...", "url": "https://...", ...}
        """
        # Normalize URL (remove trailing slashes, query params for hashing)
        url = raw_article["url"].strip()
        normalized_url = self._normalize_url(url)

        # Generate URL hash for duplicate detection
        url_hash = self._generate_hash(normalized_url)

        # Clean title
        title = raw_article["title"].strip()[:255]  # Limit to 255 chars

        # Get category (default to None if not present)
        category = raw_article.get("category") or raw_article.get("type")

        # Parse published_at or default to now
        published_at = raw_article.get("published_at", datetime.now())

        return {
            "url": url,
            "url_hash": url_hash,
            "title": title,
            "source_key": self.source_key,
            "category": category,
            "published_at": published_at,
        }

    def validate(self, article: Dict[str, Any]) -> bool:
        """
        Validate that an article has all required fields.

        Args:
            article: Article dictionary to validate

        Returns:
            True if valid, False otherwise

        Validation checks:
            - Required fields present (url, title, source_key)
            - URL is valid HTTP/HTTPS
            - Title is non-empty
            - URL hash is 64 characters (SHA-256)
        """
        required_fields = ["url", "url_hash", "title", "source_key", "published_at"]

        # Check required fields
        for field in required_fields:
            if field not in article or article[field] is None:
                self.logger.warning(
                    f"Article missing required field: {field}",
                    extra={"article": article},
                )
                return False

        # Validate URL format
        url = article["url"]
        if not (url.startswith("http://") or url.startswith("https://")):
            self.logger.warning(f"Invalid URL format: {url}")
            return False

        # Validate title is non-empty
        if not article["title"].strip():
            self.logger.warning("Article has empty title")
            return False

        # Validate URL hash length (SHA-256 = 64 hex chars)
        if len(article["url_hash"]) != 64:
            self.logger.warning(
                f"Invalid url_hash length: {len(article['url_hash'])} (expected 64)"
            )
            return False

        return True

    @staticmethod
    def _normalize_url(url: str) -> str:
        """
        Normalize URL for consistent hashing.

        Removes trailing slashes and fragments.
        Query parameters are kept as they may affect content.

        Args:
            url: Raw URL string

        Returns:
            Normalized URL string
        """
        # Remove trailing slash
        url = url.rstrip("/")

        # Remove URL fragments (#...)
        if "#" in url:
            url = url.split("#")[0]

        return url

    @staticmethod
    def _generate_hash(text: str) -> str:
        """
        Generate SHA-256 hash of text.

        Args:
            text: Text to hash

        Returns:
            64-character hexadecimal hash string
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def run(self) -> List[Dict[str, Any]]:
        """
        Execute the complete scraping workflow.

        This is the main entry point that orchestrates:
        1. Scrape raw articles
        2. Parse and normalize each article
        3. Validate each article
        4. Return valid articles

        Returns:
            List of validated, normalized article dictionaries

        Example:
            ```python
            scraper = SinaScraper()
            articles = await scraper.run()
            # articles = [{"url": "...", "url_hash": "...", ...}, ...]
            ```
        """
        self.logger.info(f"Starting scraper for {self.display_name}")

        try:
            # Step 1: Scrape raw articles
            raw_articles = await self.scrape()
            self.logger.info(
                f"Scraped {len(raw_articles)} raw articles",
                extra={"source_key": self.source_key, "article_count": len(raw_articles)},
            )

            # Step 2: Parse and validate
            validated_articles = []
            for raw_article in raw_articles:
                try:
                    # Parse
                    parsed_article = self.parse(raw_article)

                    # Validate
                    if self.validate(parsed_article):
                        validated_articles.append(parsed_article)
                    else:
                        self.logger.warning(
                            f"Article failed validation: {parsed_article.get('title', 'Unknown')}"
                        )
                except Exception as e:
                    self.logger.error(
                        f"Error parsing article: {str(e)}",
                        extra={"raw_article": raw_article},
                    )
                    continue

            self.logger.info(
                f"Validated {len(validated_articles)} articles",
                extra={
                    "source_key": self.source_key,
                    "article_count": len(validated_articles),
                },
            )

            return validated_articles

        except Exception as e:
            self.logger.error(
                f"Scraper failed for {self.display_name}: {str(e)}",
                extra={"source_key": self.source_key},
                exc_info=True,
            )
            # Return empty list on failure (graceful degradation)
            return []
