"""Huanqiu News scraper - refactored for async with BaseScraper."""

import asyncio
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx
from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper


class HuanqiuScraper(BaseScraper):
    """Scraper for Huanqiu News (环球网) - Military channel."""

    # 环球网正文选择器 - 使用textarea选择器提取CSR页面内容
    CONTENT_SELECTORS = [
        "textarea.article-content",  # CSR页面的内容存储在textarea中
        ".l-con",
        ".article-content",
        "#article-content",
        ".a-con",
    ]

    def __init__(self):
        super().__init__(source_key="huanqiu", display_name="环球网")
        self.base_url = "https://mil.huanqiu.com/api/list2"
        self.article_url = "https://mil.huanqiu.com/article/"

    def _strip_html_tags(self, html_content: str) -> str:
        """Strip HTML tags from content."""
        # Remove script and style elements
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        html_content = re.sub(r'<[^>]+>', '', html_content)
        # Decode common HTML entities
        html_content = html_content.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        return html_content.strip()

    async def fetch_content(self, url: str) -> Optional[str]:
        """
        Fetch article content from Huanqiu News, preserving images.

        Args:
            url: Article URL

        Returns:
            Article content HTML with images
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(url, wait_until='domcontentloaded', timeout=self.CONTENT_FETCH_TIMEOUT)
                await asyncio.sleep(2)

                content = None

                # Try Huanqiu-specific selectors
                for selector in self.CONTENT_SELECTORS:
                    try:
                        element = page.locator(selector).first
                        if await element.count() > 0:
                            # For textarea elements, get raw HTML content
                            if 'textarea' in selector:
                                raw_content = await element.text_content()
                                if raw_content:
                                    # Keep HTML to preserve images
                                    content = raw_content
                            else:
                                # Get HTML to preserve images
                                content = await element.inner_html()

                            # Accept content with at least 50 characters
                            if content and len(content.strip()) > 50:
                                break
                            else:
                                content = None
                    except Exception:
                        continue

                await browser.close()

                if content:
                    content = self._clean_html_content(content, url)
                    return content if len(content) > 50 else None

                return None

        except Exception as e:
            self.logger.warning(f"Huanqiu content fetch failed for {url}: {str(e)}")
            return None

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape military news from Huanqiu using API."""
        news_data = []
        try:
            params = {
                'node': '/e3pmh1dm8/e3pmt7hva',
                'offset': 0,
                'limit': 24
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                # Fetch 3 pages
                for page_num in range(3):
                    params['offset'] = page_num * 24

                    response = await client.get(self.base_url, params=params)
                    response.raise_for_status()

                    data = response.json()
                    articles = data.get('list', [])

                    for article in articles:
                        aid = article.get('aid')
                        title = article.get('title')

                        if aid and title:
                            news_data.append({
                                "url": f"{self.article_url}{aid}",
                                "title": title,
                                "category": "military",
                                "published_at": datetime.now(),
                            })

                    await asyncio.sleep(1)  # Rate limiting

            self.logger.info(f"Scraped {len(news_data)} articles")
            return news_data

        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            return news_data
