"""Wangyi News scraper - refactored for async with BaseScraper."""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx
from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper


class WangyiScraper(BaseScraper):
    """Scraper for Wangyi News (网易新闻) - Multiple channels."""

    # 网易新闻正文选择器
    CONTENT_SELECTORS = [
        "#endText",
        ".post_body",
        ".post_text",
        "#article-body",
    ]

    # 网易新闻频道配置
    CHANNELS = [
        {"name": "news", "url": "https://news.163.com/", "category": "china"},
        {"name": "culture", "url": "https://culture.163.com/", "category": "culture"},
    ]

    def __init__(self):
        super().__init__(source_key="wangyi", display_name="网易新闻")

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
        """Scrape multiple channels from Wangyi News."""
        all_articles = []

        # 并发抓取多个频道
        tasks = [
            self._scrape_channel_httpx(channel)
            for channel in self.CHANNELS
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Channel scraping failed: {str(result)}")
            elif isinstance(result, list):
                all_articles.extend(result)

        self.logger.info(f"Scraped {len(all_articles)} total articles")
        return all_articles

    async def _scrape_channel_httpx(self, channel: dict) -> List[Dict[str, Any]]:
        """使用 httpx 抓取频道页面，更稳定快速。"""
        news_data = []
        seen_urls = set()
        url = channel["url"]
        category = channel["category"]

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                html = response.text

                # 提取文章链接和标题
                import re

                # 匹配网易新闻文章链接模式
                patterns = [
                    # 标准文章链接: https://www.163.com/news/article/XXXXX.html
                    r'href="(https?://[^"]*\.163\.com/[^"]*article/[A-Z0-9]+\.html)"[^>]*>([^<]+)</a>',
                    # dy文章链接: https://www.163.com/dy/article/XXXXX.html
                    r'href="(https?://[^"]*\.163\.com/dy/article/[A-Z0-9]+\.html)"[^>]*>([^<]+)</a>',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        article_url = match[0]
                        title = match[1].strip()

                        if not title or len(title) < 5:
                            continue

                        if article_url in seen_urls:
                            continue

                        seen_urls.add(article_url)
                        news_data.append({
                            "url": article_url,
                            "title": title,
                            "category": category,
                            "published_at": datetime.now(),
                        })

            self.logger.info(f"Scraped {len(news_data)} articles from {channel['name']}")
            return news_data

        except Exception as e:
            self.logger.error(f"Failed to scrape {channel['name']}: {str(e)}")
            # 失败时尝试使用 Playwright 作为备用
            return await self._scrape_channel_playwright(channel)

    async def _scrape_channel_playwright(self, channel: dict) -> List[Dict[str, Any]]:
        """使用 Playwright 作为备用抓取方式。"""
        news_data = []
        seen_urls = set()
        url = channel["url"]
        category = channel["category"]

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                page.set_default_timeout(60000)

                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)

                # 提取文章链接
                article_links = await page.locator("a[href*='163.com'][href*='article']").all()
                for item in article_links[:100]:  # 限制数量避免超时
                    try:
                        href = await item.get_attribute("href")
                        if not href or href in seen_urls:
                            continue
                        if "/article/" not in href:
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

            self.logger.info(f"Scraped {len(news_data)} articles from {channel['name']} (playwright)")
            return news_data

        except Exception as e:
            self.logger.error(f"Playwright scrape failed for {channel['name']}: {str(e)}")
            return news_data
