"""YiCai News scraper - refactored for async with BaseScraper."""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper


class YicaiScraper(BaseScraper):
    """Scraper for Yicai News (第一财经)."""

    # 第一财经正文选择器
    CONTENT_SELECTORS = [
        ".m-text",
        ".article-content",
        "#article-content",
        ".txt",
    ]

    def __init__(self):
        super().__init__(source_key="yicai", display_name="第一财经")
        self.base_url = "https://www.yicai.com/news/"

    async def fetch_content(self, url: str) -> Optional[str]:
        """Fetch article content from Yicai News."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(url, wait_until='domcontentloaded', timeout=self.CONTENT_FETCH_TIMEOUT)
                await asyncio.sleep(2)

                content = None
                for selector in self.CONTENT_SELECTORS:
                    try:
                        element = page.locator(selector).first
                        if await element.count() > 0:
                            content = await element.inner_text()
                            if content and len(content.strip()) > 30:
                                break
                    except Exception:
                        continue

                await browser.close()

                if content:
                    content = self._clean_content(content)
                    return content if len(content) > 30 else None
                return None

        except Exception as e:
            self.logger.warning(f"Yicai content fetch failed for {url}: {str(e)}")
            return None

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape news from Yicai."""
        news_data = []
        seen_urls = set()
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                page.set_default_timeout(120000)

                await page.goto(self.base_url, wait_until="domcontentloaded", timeout=120000)
                await asyncio.sleep(3)

                # Extract articles from #newslist - structure: a.f-db > div.m-list > h2
                items = await page.locator("#newslist a.f-db").all()

                for item in items:
                    try:
                        href = await item.get_attribute("href")
                        if not href:
                            continue

                        # Skip topic links, only get news articles
                        if "/topic/" in href:
                            continue

                        # Get title from h2 element using locator
                        h2_locator = item.locator("h2")
                        if await h2_locator.count() == 0:
                            continue

                        title = await h2_locator.first.inner_text()
                        if not title or not title.strip():
                            continue

                        # Build full URL
                        full_url = href if href.startswith("http") else f"https://www.yicai.com{href}"

                        # Deduplicate
                        if full_url in seen_urls:
                            continue
                        seen_urls.add(full_url)

                        news_data.append({
                            "url": full_url,
                            "title": title.strip(),
                            "category": "finance",
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
