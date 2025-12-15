"""Ifeng News scraper - refactored for async with BaseScraper."""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper


class IfengScraper(BaseScraper):
    """Scraper for Ifeng News (凤凰网) - Finance and Military channels."""

    # 凤凰网正文选择器
    CONTENT_SELECTORS = [
        "#main_content",
        ".main_content",
        ".article-content",
        ".article-body",
    ]

    # Data keys in allData that contain news articles
    NEWS_DATA_KEYS = [
        "newsData",
        "hotspotsData",
        "globalData",
        "stormData",
        "newsflashData",
        "researchData",
        "investData",
        "bankEyeData",
        "featuredData",
    ]

    def __init__(self):
        super().__init__(source_key="ifeng", display_name="凤凰网")
        self.finance_url = "https://finance.ifeng.com/"
        self.military_url = "https://mil.ifeng.com/"

    async def fetch_content(self, url: str) -> Optional[str]:
        """Fetch article content from Ifeng News, preserving images."""
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
                            # Get HTML to preserve images
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
            self.logger.warning(f"Ifeng content fetch failed for {url}: {str(e)}")
            return None

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
        """Scrape a specific channel using JavaScript data extraction."""
        news_data = []
        seen_urls = set()
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                page.set_default_timeout(120000)

                await page.goto(url, wait_until="domcontentloaded", timeout=120000)
                await asyncio.sleep(8)  # Increased wait time for JS to load

                # Method 1: Extract allData from JavaScript
                all_data = await page.evaluate("() => window.allData")

                if all_data:
                    # Extract articles from various data arrays
                    for key in self.NEWS_DATA_KEYS:
                        if key in all_data and isinstance(all_data[key], list):
                            for item in all_data[key]:
                                try:
                                    if not isinstance(item, dict):
                                        continue

                                    article_url = item.get("url", "")
                                    title = item.get("title", "")

                                    if not article_url or not title:
                                        continue

                                    if article_url in seen_urls:
                                        continue
                                    seen_urls.add(article_url)

                                    # Parse news time if available
                                    news_time = item.get("newsTime", "")
                                    published_at = datetime.now()
                                    if news_time:
                                        try:
                                            published_at = datetime.strptime(news_time, "%Y-%m-%d %H:%M:%S")
                                        except ValueError:
                                            pass

                                    news_data.append({
                                        "url": article_url,
                                        "title": title.strip(),
                                        "category": category,
                                        "published_at": published_at,
                                    })
                                except Exception as e:
                                    self.logger.warning(f"Failed to extract article from {key}: {str(e)}")
                                    continue

                # Method 2: Fallback to DOM extraction if allData didn't yield results
                if len(news_data) == 0:
                    self.logger.info(f"allData extraction yielded 0 results, trying DOM extraction for {category}")
                    # Try extracting from common link patterns
                    article_links = await page.locator("a[href*='ifeng.com'][href*='/c/']").all()
                    for item in article_links:
                        try:
                            href = await item.get_attribute("href")
                            if not href or href in seen_urls:
                                continue

                            title = await item.inner_text()
                            if not title or not title.strip() or len(title.strip()) < 5:
                                continue

                            seen_urls.add(href)
                            news_data.append({
                                "url": href,
                                "title": title.strip(),
                                "category": category,
                                "published_at": datetime.now(),
                            })
                        except Exception:
                            continue

                await browser.close()

            self.logger.info(f"Scraped {len(news_data)} articles from {category}")
            return news_data

        except Exception as e:
            self.logger.error(f"Failed to scrape {category}: {str(e)}")
            return news_data
