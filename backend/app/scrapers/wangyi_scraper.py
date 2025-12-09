"""Wangyi News scraper - refactored for async with BaseScraper."""

import asyncio
from datetime import datetime
from typing import List, Dict, Any

from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper


class WangyiScraper(BaseScraper):
    """Scraper for Wangyi News (网易新闻) - Culture channel."""

    def __init__(self):
        super().__init__(source_key="wangyi", display_name="网易新闻")
        self.base_url = "https://culture.163.com/"

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape culture channel from Wangyi News."""
        news_data = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                page.set_default_timeout(120000)

                await page.goto(self.base_url, wait_until="domcontentloaded", timeout=120000)
                await asyncio.sleep(3)

                # Extract articles (simplified - adapt to actual site structure)
                items = await page.locator("div.cm_mod_tab_panel div.cm_smallimg_list li").all()

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
                                "category": "culture",
                                "published_at": datetime.now(),
                            })
                    except Exception as e:
                        self.logger.warning(f"Failed to extract article: {str(e)}")
                        continue

                await browser.close()

            self.logger.info(f"Scraped {len(news_data)} articles")
            return news_data

        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            return news_data
