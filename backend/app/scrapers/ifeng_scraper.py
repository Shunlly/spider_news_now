"""Ifeng News scraper - refactored for async with BaseScraper."""

import asyncio
from datetime import datetime
from typing import List, Dict, Any

from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper


class IfengScraper(BaseScraper):
    """Scraper for Ifeng News (凤凰网) - Finance and Military channels."""

    def __init__(self):
        super().__init__(source_key="ifeng", display_name="凤凰网")
        self.finance_url = "https://finance.ifeng.com/"
        self.military_url = "https://mil.ifeng.com/"

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape finance and military channels."""
        all_articles = []

        finance_task = self._scrape_channel(self.finance_url, "finance")
        military_task = self._scrape_channel(self.military_url, "military")

        results = await asyncio.gather(finance_task, military_task, return_exceptions=True)

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
                page.set_default_timeout(120000)

                await page.goto(url, wait_until="domcontentloaded", timeout=120000)
                await asyncio.sleep(3)

                # Extract articles (simplified - adapt to actual site structure)
                items = await page.locator("div.box_list ul li").all()

                for item in items:
                    try:
                        a = await item.query_selector("a")
                        if not a:
                            continue

                        href = await a.get_attribute("href")
                        text = await a.inner_text()

                        if href and text:
                            news_data.append({
                                "url": href,
                                "title": text.strip(),
                                "category": category,
                                "published_at": datetime.now(),
                            })
                    except Exception as e:
                        self.logger.warning(f"Failed to extract article: {str(e)}")
                        continue

                await browser.close()

            self.logger.info(f"Scraped {len(news_data)} articles from {category}")
            return news_data

        except Exception as e:
            self.logger.error(f"Failed to scrape {category}: {str(e)}")
            return news_data
