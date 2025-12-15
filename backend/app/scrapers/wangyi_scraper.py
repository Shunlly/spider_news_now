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
        """Fetch article content from Wangyi News, preserving images."""
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

                # Method 1: Extract from article links with /dy/article/ pattern
                article_links = await page.locator("a[href*='/dy/article/']").all()
                for item in article_links:
                    try:
                        href = await item.get_attribute("href")
                        if not href or href in seen_urls:
                            continue

                        # Get title - try multiple ways
                        title = None
                        # Try h3 first
                        h3_locator = item.locator("h3")
                        if await h3_locator.count() > 0:
                            title = await h3_locator.first.inner_text()
                        else:
                            # Try getting text content directly
                            title = await item.inner_text()

                        if not title or not title.strip() or len(title.strip()) < 5:
                            continue

                        seen_urls.add(href)
                        news_data.append({
                            "url": href,
                            "title": title.strip(),
                            "category": "culture",
                            "published_at": datetime.now(),
                        })
                    except Exception as e:
                        self.logger.warning(f"Failed to extract dy/article link: {str(e)}")
                        continue

                # Method 2: Extract from regular article links
                regular_links = await page.locator("a[href*='/article/']").all()
                for item in regular_links:
                    try:
                        href = await item.get_attribute("href")
                        if not href or href in seen_urls:
                            continue
                        if "163.com" not in href:
                            continue

                        title = None
                        h3_locator = item.locator("h3")
                        if await h3_locator.count() > 0:
                            title = await h3_locator.first.inner_text()
                        else:
                            title = await item.inner_text()

                        if not title or not title.strip() or len(title.strip()) < 5:
                            continue

                        seen_urls.add(href)
                        news_data.append({
                            "url": href,
                            "title": title.strip(),
                            "category": "culture",
                            "published_at": datetime.now(),
                        })
                    except Exception:
                        continue

                # Method 3: Extract from img alt attributes for image-based links
                img_links = await page.locator("a[href*='163.com'] img[alt]").all()
                for img in img_links:
                    try:
                        parent_link = img.locator("xpath=..")
                        href = await parent_link.get_attribute("href")
                        if not href or href in seen_urls:
                            continue
                        if "/article/" not in href and "/dy/article/" not in href:
                            continue

                        title = await img.get_attribute("alt")
                        if not title or not title.strip() or len(title.strip()) < 5:
                            continue

                        seen_urls.add(href)
                        news_data.append({
                            "url": href,
                            "title": title.strip(),
                            "category": "culture",
                            "published_at": datetime.now(),
                        })
                    except Exception:
                        continue

                await browser.close()

            self.logger.info(f"Scraped {len(news_data)} articles")
            return news_data

        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            return news_data
