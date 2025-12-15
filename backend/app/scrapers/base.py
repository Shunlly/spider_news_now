"""Base scraper class defining the interface for all news scrapers."""

import asyncio
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional

from playwright.async_api import async_playwright, Page, Browser

from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for all news scrapers.

    All scrapers must inherit from this class and implement the required methods.
    This ensures consistent interface and behavior across all scrapers.
    """

    # 是否启用正文提取（子类可覆盖）
    FETCH_CONTENT_ENABLED = True
    # 正文提取并发数
    CONTENT_FETCH_CONCURRENCY = 3
    # 正文提取超时（秒）
    CONTENT_FETCH_TIMEOUT = 30000

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

            # Step 3: Fetch content for new articles (if enabled)
            if self.FETCH_CONTENT_ENABLED and validated_articles:
                self.logger.info(f"Starting content extraction for {len(validated_articles)} articles")
                validated_articles = await self._fetch_all_content(validated_articles)

            return validated_articles

        except Exception as e:
            self.logger.error(
                f"Scraper failed for {self.display_name}: {str(e)}",
                extra={"source_key": self.source_key},
                exc_info=True,
            )
            # Return empty list on failure (graceful degradation)
            return []

    async def _fetch_all_content(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fetch content for all articles with concurrency control.
        Upload content to MinIO/RustFS storage.

        Args:
            articles: List of article dictionaries

        Returns:
            Articles with content_url populated (storage path)
        """
        from app.services.storage_service import get_storage_service
        from datetime import datetime
        import re

        storage_service = get_storage_service()
        semaphore = asyncio.Semaphore(self.CONTENT_FETCH_CONCURRENCY)

        def extract_plain_text(html_content: str) -> str:
            """Extract plain text from HTML for search indexing."""
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', html_content)
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:10000]  # Limit for search index

        async def fetch_with_semaphore(article: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                try:
                    content = await self.fetch_content(article["url"])
                    if content:
                        # Generate storage path: articles/{source}/{date}/{url_hash}.html
                        date_str = datetime.now().strftime("%Y/%m/%d")
                        file_path = f"articles/{self.source_key}/{date_str}/{article['url_hash']}.html"

                        # Upload to MinIO/RustFS
                        try:
                            content_url = await storage_service.upload(
                                file_path,
                                content.encode('utf-8'),
                                content_type="text/html; charset=utf-8"
                            )
                            article["content_url"] = file_path  # Store path, not full URL
                            article["content_hash"] = self._generate_hash(content)
                            # Extract plain text for search indexing (optional, limited)
                            article["content_text"] = extract_plain_text(content)
                            self.logger.debug(f"Uploaded content for: {article['title'][:30]}...")
                        except Exception as e:
                            self.logger.warning(f"Failed to upload content to storage: {str(e)}")
                            # Fallback: store content directly if upload fails
                            article["content_text"] = content
                            article["content_hash"] = self._generate_hash(content)
                except Exception as e:
                    self.logger.warning(f"Failed to fetch content for {article['url']}: {str(e)}")
                return article

        # Fetch content concurrently
        tasks = [fetch_with_semaphore(article) for article in articles]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        fetched_articles = []
        for result in results:
            if isinstance(result, dict):
                fetched_articles.append(result)
            else:
                self.logger.warning(f"Content fetch exception: {result}")

        success_count = sum(1 for a in fetched_articles if a.get("content_url") or a.get("content_text"))
        self.logger.info(f"Content extraction completed: {success_count}/{len(articles)} successful")

        return fetched_articles

    async def fetch_content(self, url: str) -> Optional[str]:
        """
        Fetch article content from URL.

        This method should be overridden by subclasses to implement
        source-specific content extraction logic.

        Default implementation uses generic extraction.

        Args:
            url: Article URL

        Returns:
            Article content text, or None if extraction fails
        """
        return await self._generic_content_fetch(url)

    async def _generic_content_fetch(self, url: str) -> Optional[str]:
        """
        Generic content extraction using common article selectors.
        Extracts HTML content to preserve images.

        Args:
            url: Article URL

        Returns:
            Extracted content HTML with images preserved
        """
        # Common article content selectors
        CONTENT_SELECTORS = [
            "article",
            ".article-content",
            ".article-body",
            ".post-content",
            ".entry-content",
            ".content-article",
            "#article-content",
            "#artibody",
            ".art_content",
            ".main-content",
            "[itemprop='articleBody']",
        ]

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(url, wait_until='domcontentloaded', timeout=self.CONTENT_FETCH_TIMEOUT)
                await asyncio.sleep(2)  # Wait for JS to load

                content = None

                # Try each selector - get HTML to preserve images
                for selector in CONTENT_SELECTORS:
                    try:
                        element = page.locator(selector).first
                        if await element.count() > 0:
                            # Get HTML content to preserve images
                            content = await element.inner_html()
                            if content and len(content.strip()) > 50:
                                break
                    except Exception:
                        continue

                # Fallback: extract paragraphs and images
                if not content or len(content.strip()) < 50:
                    parts = []
                    # Get paragraphs
                    paragraphs = page.locator("p")
                    p_count = await paragraphs.count()
                    for i in range(min(p_count, 50)):
                        try:
                            html = await paragraphs.nth(i).inner_html()
                            if html and len(html.strip()) > 20:
                                parts.append(f"<p>{html}</p>")
                        except Exception:
                            continue

                    # Get images from article area
                    images = page.locator("article img, .article img, .content img, .main img")
                    img_count = await images.count()
                    for i in range(min(img_count, 20)):
                        try:
                            img_html = await images.nth(i).evaluate("el => el.outerHTML")
                            if img_html:
                                parts.append(img_html)
                        except Exception:
                            continue

                    if parts:
                        content = "\n".join(parts)

                await browser.close()

                if content:
                    # Clean and fix image URLs
                    content = self._clean_html_content(content, url)
                    return content if len(content) > 50 else None

                return None

        except Exception as e:
            self.logger.warning(f"Generic content fetch failed for {url}: {str(e)}")
            return None

    def _clean_content(self, content: str) -> str:
        """
        Clean extracted content text.

        Args:
            content: Raw content text

        Returns:
            Cleaned content text
        """
        import re

        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)

        # Remove common unwanted patterns
        patterns_to_remove = [
            r'点击进入专题.*',
            r'责任编辑.*',
            r'相关阅读.*',
            r'延伸阅读.*',
            r'原标题.*',
            r'来源：.*',
            r'\[责编.*\]',
            r'编辑：.*',
            r'记者：.*',
        ]

        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)

        return content.strip()

    def _clean_html_content(self, content: str, base_url: str) -> str:
        """
        Clean HTML content and fix image URLs.

        Args:
            content: Raw HTML content
            base_url: Base URL for resolving relative paths

        Returns:
            Cleaned HTML content with absolute image URLs
        """
        import re
        from urllib.parse import urljoin, urlparse

        # Remove script and style tags
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # Remove comments
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

        # Remove unwanted tags but keep content
        unwanted_tags = ['iframe', 'noscript', 'form', 'input', 'button', 'nav', 'footer', 'aside']
        for tag in unwanted_tags:
            content = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', content, flags=re.DOTALL | re.IGNORECASE)
            content = re.sub(rf'<{tag}[^>]*/>', '', content, flags=re.IGNORECASE)

        # Fix relative image URLs to absolute URLs
        def fix_img_url(match):
            full_tag = match.group(0)
            src_match = re.search(r'src=["\']([^"\']+)["\']', full_tag)
            if src_match:
                src = src_match.group(1)
                # Skip data URLs and already absolute URLs
                if src.startswith('data:') or src.startswith('http://') or src.startswith('https://'):
                    return full_tag
                # Convert relative URL to absolute
                absolute_url = urljoin(base_url, src)
                return full_tag.replace(src_match.group(0), f'src="{absolute_url}"')
            return full_tag

        content = re.sub(r'<img[^>]+>', fix_img_url, content, flags=re.IGNORECASE)

        # Also handle data-src (lazy loading images)
        def fix_data_src(match):
            full_tag = match.group(0)
            # If has data-src but src is placeholder, use data-src
            data_src_match = re.search(r'data-src=["\']([^"\']+)["\']', full_tag)
            if data_src_match:
                data_src = data_src_match.group(1)
                if not data_src.startswith('data:'):
                    absolute_url = urljoin(base_url, data_src) if not data_src.startswith('http') else data_src
                    # Replace or add src attribute
                    if 'src=' in full_tag:
                        full_tag = re.sub(r'src=["\'][^"\']*["\']', f'src="{absolute_url}"', full_tag)
                    else:
                        full_tag = full_tag.replace('<img', f'<img src="{absolute_url}"')
            return full_tag

        content = re.sub(r'<img[^>]+>', fix_data_src, content, flags=re.IGNORECASE)

        # Remove empty tags
        content = re.sub(r'<(\w+)[^>]*>\s*</\1>', '', content)

        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r'  +', ' ', content)

        return content.strip()
