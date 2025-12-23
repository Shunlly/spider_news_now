"""
网易新闻爬虫 - Wangyi News Scraper

采集网易新闻两个频道的文章：
1. 新闻频道 (china): https://news.163.com/
2. 文化频道 (culture): https://culture.163.com/

技术实现：
- 优先使用 httpx 直接请求（速度快、资源占用低）
- 备用方案：Playwright 动态渲染
- 使用正则表达式匹配文章链接模式
- 正文解析支持多个 CSS 选择器尝试

链接匹配模式：
- 标准文章：https://www.163.com/news/article/XXXXX.html
- dy 文章：https://www.163.com/dy/article/XXXXX.html
"""

import asyncio
from datetime import datetime
from typing import Any

import httpx
from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper


class WangyiScraper(BaseScraper):
    """
    网易新闻爬虫

    采集两个频道的文章：
    - 新闻频道 (china): 国内新闻、时政要闻
    - 文化频道 (culture): 文化资讯、历史人文

    采集策略：
    1. 优先使用 httpx 直接请求 HTML（速度快）
    2. 使用正则表达式提取文章链接
    3. 如果 httpx 失败，降级为 Playwright
    """

    # 网易新闻正文选择器（按优先级排序）
    CONTENT_SELECTORS = [
        "#endText",         # 主要文章正文容器
        ".post_body",       # 文章主体
        ".post_text",       # 文章文本
        "#article-body",    # 备选文章容器
    ]

    # 网易新闻频道配置
    CHANNELS = [
        {"name": "news", "url": "https://news.163.com/", "category": "china"},
        {"name": "culture", "url": "https://culture.163.com/", "category": "culture"},
    ]

    def __init__(self):
        super().__init__(source_key="wangyi", display_name="网易新闻")

    async def fetch_content(self, url: str) -> str | None:
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

    async def scrape(self) -> list[dict[str, Any]]:
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

    async def _scrape_channel_httpx(self, channel: dict) -> list[dict[str, Any]]:
        """
        使用 httpx 采集频道页面（推荐方式）

        使用 httpx 直接请求 HTML，比 Playwright 更快、资源占用更低。
        通过正则表达式匹配网易新闻的文章链接模式。

        Args:
            channel: 频道配置字典（包含 name, url, category）

        Returns:
            文章列表（包含 url, title, category, published_at）
        """
        news_data = []
        seen_urls = set()  # URL 去重
        url = channel["url"]
        category = channel["category"]

        try:
            # 模拟浏览器请求头，避免被反爬
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                html = response.text

                # 使用正则表达式提取文章链接和标题
                import re

                # 网易新闻文章链接匹配模式
                # 格式1：标准文章 https://www.163.com/news/article/XXXXX.html
                # 格式2：dy文章 https://www.163.com/dy/article/XXXXX.html
                patterns = [
                    # 标准文章链接：匹配 href="URL">标题</a> 模式
                    r'href="(https?://[^"]*\.163\.com/[^"]*article/[A-Z0-9]+\.html)"[^>]*>([^<]+)</a>',
                    # dy 文章链接
                    r'href="(https?://[^"]*\.163\.com/dy/article/[A-Z0-9]+\.html)"[^>]*>([^<]+)</a>',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        article_url = match[0]
                        title = match[1].strip()

                        # 过滤无效标题
                        if not title or len(title) < 5:
                            continue

                        # URL 去重
                        if article_url in seen_urls:
                            continue

                        seen_urls.add(article_url)
                        news_data.append({
                            "url": article_url,
                            "title": title,
                            "category": category,
                            "published_at": datetime.now(),
                        })

            self.logger.info(f"从 {channel['name']} 频道采集到 {len(news_data)} 篇文章")
            return news_data

        except Exception as e:
            self.logger.error(f"httpx 采集 {channel['name']} 失败: {str(e)}")
            # 失败时使用 Playwright 作为备用
            return await self._scrape_channel_playwright(channel)

    async def _scrape_channel_playwright(self, channel: dict) -> list[dict[str, Any]]:
        """
        使用 Playwright 采集频道（备用方式）

        当 httpx 请求失败时使用此方法，可以处理需要 JS 渲染的页面。

        Args:
            channel: 频道配置字典

        Returns:
            文章列表
        """
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
                # 选择器：匹配包含 163.com 和 article 的链接
                article_links = await page.locator("a[href*='163.com'][href*='article']").all()
                for item in article_links[:100]:  # 限制数量避免超时
                    try:
                        href = await item.get_attribute("href")
                        if not href or href in seen_urls:
                            continue
                        # 过滤非文章链接
                        if "/article/" not in href:
                            continue

                        title = await item.inner_text()
                        # 过滤无效标题
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

            self.logger.info(f"Playwright 从 {channel['name']} 采集到 {len(news_data)} 篇文章")
            return news_data

        except Exception as e:
            self.logger.error(f"Playwright 采集 {channel['name']} 失败: {str(e)}")
            return news_data
