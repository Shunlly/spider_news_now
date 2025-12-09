"""QQ News scraper - refactored for async with BaseScraper."""

import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any

from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper


class QQScraper(BaseScraper):
    """
    Scraper for QQ News (腾讯新闻).

    Collects articles from two channels:
    - Sports (sports): https://news.qq.com/ch/sports
    - Tech (tech): https://news.qq.com/ch/tech
    """

    def __init__(self):
        super().__init__(source_key="qq", display_name="腾讯新闻")
        self.sports_url = 'https://news.qq.com/ch/sports'
        self.tech_url = 'https://news.qq.com/ch/tech'

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape all channels from QQ News."""
        all_articles = []

        # Scrape channels concurrently
        sports_task = self._scrape_channel(self.sports_url, "sports")
        tech_task = self._scrape_channel(self.tech_url, "tech")

        results = await asyncio.gather(sports_task, tech_task, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Channel scraping failed: {str(result)}")
            elif isinstance(result, list):
                all_articles.extend(result)

        return all_articles

    async def _scrape_channel(self, url: str, category: str) -> List[Dict[str, Any]]:
        """Scrape a specific channel."""
        news_data = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                page.set_default_timeout(240000)

                await page.goto(url, wait_until="domcontentloaded", timeout=120000)
                await page.wait_for_selector(".channel-feed-list", state="attached", timeout=60000)

                # Scroll to load more content
                scroll_times = 5
                for i in range(scroll_times):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1.5)

                await asyncio.sleep(2)

                # Extract articles
                items = await page.locator(".channel-feed-list > .channel-feed-item").all()

                for row in items:
                    try:
                        a = row.locator("a.article-title")
                        href = await a.get_attribute("href")
                        text = await a.locator("span").nth(0).inner_text()

                        if href and text:
                            news_data.append({
                                "title": text,
                                "url": href,
                                "category": category,
                                "published_at": datetime.now(),
                            })
                    except Exception as e:
                        self.logger.warning(f"Failed to extract article: {str(e)}")
                        continue

                await browser.close()

            self.logger.info(f"Scraped {len(news_data)} articles from {category} channel")
            return news_data

        except Exception as e:
            self.logger.error(f"Failed to scrape {category} channel: {str(e)}")
            return news_data
