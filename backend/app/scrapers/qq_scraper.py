"""
腾讯新闻爬虫 - QQ News Scraper

采集腾讯新闻两个频道的文章：
1. 体育频道 (sports): https://news.qq.com/ch/sports
2. 科技频道 (tech): https://news.qq.com/ch/tech

技术实现：
- 使用 Playwright 进行动态页面渲染
- 页面使用无限滚动加载更多内容
- 正文解析支持多个 CSS 选择器尝试

页面结构说明：
- 腾讯新闻使用 CSR 动态渲染
- 新闻列表容器：.channel-feed-list
- 新闻项：.channel-feed-item
- 标题链接：a.article-title > span
"""

import asyncio
from datetime import datetime
from typing import Any

from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper


class QQScraper(BaseScraper):
    """
    腾讯新闻爬虫

    采集两个频道的文章：
    - 体育频道 (sports): 体育赛事、球队动态
    - 科技频道 (tech): 科技资讯、互联网新闻

    采集策略：
    1. 等待新闻列表容器加载完成
    2. 滚动页面触发懒加载，加载更多内容
    3. 提取所有新闻项的标题和链接
    """

    # 腾讯新闻正文选择器（按优先级排序）
    CONTENT_SELECTORS = [
        ".content-article",     # 新版文章正文容器
        "#articleContent",      # 文章内容容器
        ".article-content",     # 通用文章容器
        ".LEFT",                # 老版文章容器
    ]

    def __init__(self):
        super().__init__(source_key="qq", display_name="腾讯新闻")
        self.sports_url = 'https://news.qq.com/ch/sports'
        self.tech_url = 'https://news.qq.com/ch/tech'

    async def fetch_content(self, url: str) -> str | None:
        """Fetch article content from QQ News, preserving images."""
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
            self.logger.warning(f"QQ content fetch failed for {url}: {str(e)}")
            return None

    async def scrape(self) -> list[dict[str, Any]]:
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

    async def _scrape_channel(self, url: str, category: str) -> list[dict[str, Any]]:
        """
        采集指定频道的文章

        采集流程：
        1. 等待新闻列表容器 .channel-feed-list 加载
        2. 多次滚动页面触发懒加载（默认 5 次）
        3. 提取所有新闻项的标题和链接

        页面结构：
        - 列表容器：.channel-feed-list
        - 新闻项：.channel-feed-item
        - 标题链接：a.article-title > span（第一个 span 是标题）

        Args:
            url: 频道页面 URL
            category: 分类标识（sports/tech）

        Returns:
            文章列表（包含 url, title, category, published_at）
        """
        news_data = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                page.set_default_timeout(240000)

                await page.goto(url, wait_until="domcontentloaded", timeout=120000)
                # 等待新闻列表容器出现
                await page.wait_for_selector(".channel-feed-list", state="attached", timeout=60000)

                # 滚动页面触发懒加载，加载更多内容
                # 腾讯新闻使用无限滚动，每次滚动到底部会加载更多
                scroll_times = 5
                for _i in range(scroll_times):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1.5)  # 等待新内容加载

                await asyncio.sleep(2)  # 额外等待确保内容加载完成

                # 提取新闻列表
                # 选择器：.channel-feed-list > .channel-feed-item
                items = await page.locator(".channel-feed-list > .channel-feed-item").all()

                for row in items:
                    try:
                        # 提取标题链接
                        # 结构：a.article-title > span（标题在第一个 span 中）
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
                        self.logger.warning(f"提取文章失败: {str(e)}")
                        continue

                await browser.close()

            self.logger.info(f"从 {category} 频道采集到 {len(news_data)} 篇文章")
            return news_data

        except Exception as e:
            self.logger.error(f"采集 {category} 频道失败: {str(e)}")
            return news_data
