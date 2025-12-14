"""Wangyi News scraper - refactored for async with BaseScraper."""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper


class WangyiScraper(BaseScraper):
    """Scraper for Wangyi News (网易新闻) - Culture channel."""

    # 网易新闻正文选择器
    CONTENT_SELECTORS = [
        "#endText",
        ".post_body",
        ".post_text",
        "#article-body",
    ]

    def __init__(self):
        super().__init__(source_key="wangyi", display_name="网易新闻")
        self.base_url = "https://culture.163.com/"

    async def fetch_content(self, url: str) -> Optional[str]:
        """Fetch article content from Wangyi News."""
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
            self.logger.warning(f"Wangyi content fetch failed for {url}: {str(e)}")
            return None

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape culture channel from Wangyi News."""
        news_data = []
        seen_urls = set()
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                page.set_default_timeout(120000)

                await page.goto(self.base_url, wait_until="domcontentloaded", timeout=120000)
                await asyncio.sleep(5)

                # Method 1: Extract from swiper-slide carousel items
                carousel_items = await page.locator("div.swiper-slide a").all()
                for item in carousel_items:
                    try:
                        href = await item.get_attribute("href")
                        if not href or "163.com" not in href:
                            continue

                        # Get title from h3 or alt attribute of img
                        h3_locator = item.locator("h3")
                        if await h3_locator.count() > 0:
                            title = await h3_locator.first.inner_text()
                        else:
                            img_locator = item.locator("img")
                            if await img_locator.count() > 0:
                                title = await img_locator.first.get_attribute("alt")
                            else:
                                continue

                        if not title or not title.strip():
                            continue

                        if href not in seen_urls:
                            seen_urls.add(href)
                            news_data.append({
                                "url": href,
                                "title": title.strip(),
                                "category": "culture",
                                "published_at": datetime.now(),
                            })
                    except Exception as e:
                        self.logger.warning(f"Failed to extract carousel article: {str(e)}")
                        continue

                # Method 2: Extract from a.item list
                list_items = await page.locator("a.item").all()
                for item in list_items:
                    try:
                        href = await item.get_attribute("href")
                        if not href or "163.com" not in href:
                            continue

                        h3_locator = item.locator("h3")
                        if await h3_locator.count() > 0:
                            title = await h3_locator.first.inner_text()
                        else:
                            continue

                        if not title or not title.strip():
                            continue

                        if href not in seen_urls:
                            seen_urls.add(href)
                            news_data.append({
                                "url": href,
                                "title": title.strip(),
                                "category": "culture",
                                "published_at": datetime.now(),
                            })
                    except Exception as e:
                        self.logger.warning(f"Failed to extract list article: {str(e)}")
                        continue

                # Method 3: Extract from any remaining news links with title h3
                all_links = await page.locator("a[href*='163.com']").all()
                for item in all_links:
                    try:
                        href = await item.get_attribute("href")
                        if not href or href in seen_urls:
                            continue
                        if "/article/" not in href and "/dy/article/" not in href:
                            continue

                        h3_locator = item.locator("h3")
                        title_locator = item.locator(".title h3")
                        if await title_locator.count() > 0:
                            title = await title_locator.first.inner_text()
                        elif await h3_locator.count() > 0:
                            title = await h3_locator.first.inner_text()
                        else:
                            continue

                        if not title or not title.strip():
                            continue

                        seen_urls.add(href)
                        news_data.append({
                            "url": href,
                            "title": title.strip(),
                            "category": "culture",
                            "published_at": datetime.now(),
                        })
                    except Exception as e:
                        continue

                await browser.close()

            self.logger.info(f"Scraped {len(news_data)} articles")
            return news_data

        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            return news_data
