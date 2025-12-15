"""Sina News scraper - refactored for async with BaseScraper."""

import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from playwright.async_api import async_playwright, Page

from app.scrapers.base import BaseScraper


class SinaScraper(BaseScraper):
    """
    Scraper for Sina News (新浪新闻).

    Collects articles from three channels:
    - Entertainment (ent): https://ent.sina.com.cn/
    - China News (china): https://news.sina.com.cn/china/
    - World News (world): https://news.sina.com.cn/world/
    """

    # 新浪新闻正文选择器
    CONTENT_SELECTORS = [
        "#article",          # 文章正文主容器
        "#artibody",         # 旧版文章容器
        ".article",
        ".article-content",
    ]

    def __init__(self):
        super().__init__(source_key="sina", display_name="新浪新闻")
        self.ent_url = "https://ent.sina.com.cn/"
        self.china_url = "https://news.sina.com.cn/china/"
        self.world_url = "https://news.sina.com.cn/world/"

    async def fetch_content(self, url: str) -> Optional[str]:
        """
        Fetch article content from Sina News, preserving images.

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

                # Try Sina-specific selectors - get HTML to preserve images
                for selector in self.CONTENT_SELECTORS:
                    try:
                        element = page.locator(selector).first
                        if await element.count() > 0:
                            content = await element.inner_html()
                            if content and len(content.strip()) > 50:
                                break
                    except Exception:
                        continue

                await browser.close()

                if content:
                    content = self._clean_html_content(content, url)
                    return content if len(content) > 50 else None

                return None

        except Exception as e:
            self.logger.warning(f"Sina content fetch failed for {url}: {str(e)}")
            return None

    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape all channels from Sina News.

        Returns:
            List of raw article dictionaries
        """
        all_articles = []

        # Scrape all channels concurrently
        ent_task = self._scrape_ent_channel()
        china_task = self._scrape_china_channel(page_num=3)
        world_task = self._scrape_world_channel()

        results = await asyncio.gather(ent_task, china_task, world_task, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Channel scraping failed: {str(result)}")
            elif isinstance(result, list):
                all_articles.extend(result)

        self.logger.info(f"Scraped {len(all_articles)} total articles from Sina")
        return all_articles

    async def _scrape_ent_channel(self) -> List[Dict[str, Any]]:
        """Scrape entertainment channel."""
        news_data = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(self.ent_url, wait_until='domcontentloaded', timeout=120000)

                # Scroll to bottom to load more content
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(10)  # Wait for JS to load data

                # Locate cards
                cards = page.locator('div.cardlist-a__list > div.ty-card')
                count = await cards.count()

                for i in range(count):
                    try:
                        a = cards.nth(i).locator('div:nth-child(2) > h3 > a').first
                        href = await a.get_attribute('href')
                        text = await a.inner_text()

                        if href and text:
                            news_data.append({
                                "url": href.strip(),
                                "title": text.strip(),
                                "category": "ent",
                                "published_at": datetime.now(),
                            })
                    except Exception as e:
                        self.logger.warning(f"Failed to extract ent article {i}: {str(e)}")
                        continue

                await browser.close()

            self.logger.info(f"Scraped {len(news_data)} articles from ent channel")
            return news_data

        except Exception as e:
            self.logger.error(f"Failed to scrape ent channel: {str(e)}")
            return news_data

    async def _scrape_china_channel(self, page_num: int = 3) -> List[Dict[str, Any]]:
        """Scrape China news channel with pagination."""
        news_data = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                page.set_default_timeout(120000)
                await page.goto(self.china_url, wait_until='domcontentloaded', timeout=240000)

                # Wait for news list to load
                try:
                    await page.wait_for_selector(
                        'div.feed-card-content > div:first-child > div.feed-card-item',
                        timeout=60000
                    )
                except Exception as e:
                    self.logger.warning(f"News list timeout: {str(e)}")
                    await browser.close()
                    return news_data

                # Wait for pagination button
                try:
                    await page.wait_for_selector('.pagebox_next', timeout=60000)
                except Exception as e:
                    self.logger.warning(f"Pagination button timeout: {str(e)}")

                await asyncio.sleep(3)  # Extra wait for dynamic content

                # Paginate through pages
                for round_num in range(page_num):
                    self.logger.info(f"Scraping china channel page {round_num + 1}")

                    items = page.locator(
                        'div.feed-card-content > div:first-child > div.feed-card-item'
                    )
                    count = await items.count()

                    for i in range(count):
                        try:
                            a = items.nth(i).locator('h2 > a').first
                            href = await a.get_attribute('href')
                            text = await a.inner_text()

                            if href and text:
                                news_data.append({
                                    'url': href.strip(),
                                    'title': text.strip(),
                                    "category": "china",
                                    "published_at": datetime.now(),
                                })
                        except Exception as e:
                            self.logger.warning(f"Failed to extract china article {i}: {str(e)}")
                            continue

                    self.logger.info(f"Page {round_num + 1} scraped {count} articles")

                    # Click next page (if not last round)
                    if round_num < page_num - 1:
                        try:
                            next_button = page.locator('.pagebox_next').filter(has_text='下一页')
                            button_count = await next_button.count()

                            if button_count > 0:
                                await next_button.click()
                                await asyncio.sleep(2)
                                await page.wait_for_load_state('domcontentloaded', timeout=60000)
                                await asyncio.sleep(2)
                            else:
                                self.logger.warning(f"Next button not found on page {round_num + 1}")
                                break
                        except Exception as e:
                            self.logger.warning(f"Failed to click next page: {str(e)}")
                            break

                await browser.close()

            self.logger.info(f"Scraped {len(news_data)} articles from china channel")
            return news_data

        except Exception as e:
            self.logger.error(f"Failed to scrape china channel: {str(e)}")
            return news_data

    async def _scrape_world_channel(self) -> List[Dict[str, Any]]:
        """Scrape world news channel."""
        news_data = []
        SELECTOR_BOX = 'div#subShowContent1_static'
        NEWS_IDS = [
            'subShowContent1_news1',
            'subShowContent1_news2',
            'subShowContent1_news3',
            'subShowContent1_news4'
        ]

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(self.world_url, wait_until='domcontentloaded', timeout=120000)
                await page.wait_for_selector(SELECTOR_BOX, timeout=60000)

                for news_id in NEWS_IDS:
                    block = await page.query_selector(f'div#{news_id}')
                    if not block:
                        continue

                    items = await block.query_selector_all('div.news-item')
                    for item in items:
                        a = await item.query_selector('h2 a')
                        if not a:
                            continue

                        href = await a.get_attribute('href')
                        text = await a.inner_text()

                        if href and text:
                            news_data.append({
                                'url': href.strip(),
                                'title': text.strip(),
                                "category": "world",
                                "published_at": datetime.now(),
                            })

                await browser.close()

            self.logger.info(f"Scraped {len(news_data)} articles from world channel")
            return news_data

        except Exception as e:
            self.logger.error(f"Failed to scrape world channel: {str(e)}")
            return news_data
