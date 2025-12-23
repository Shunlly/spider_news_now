"""
新浪新闻爬虫 - Sina News Scraper

采集新浪新闻三个频道的文章：
1. 娱乐频道 (ent): https://ent.sina.com.cn/
2. 国内新闻 (china): https://news.sina.com.cn/china/
3. 国际新闻 (world): https://news.sina.com.cn/world/

技术实现：
- 使用 Playwright 进行动态页面渲染
- 支持翻页采集（国内新闻频道）
- 正文解析时尝试多个 CSS 选择器
"""

import asyncio
from datetime import datetime
from typing import Any

from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper


class SinaScraper(BaseScraper):
    """
    新浪新闻爬虫

    采集三个频道的文章：
    - 娱乐频道 (ent): 卡片式列表页，需滚动加载
    - 国内新闻 (china): 支持翻页，每页约 20 条
    - 国际新闻 (world): 分区块展示，按新闻类型分组
    """

    # 新浪新闻正文选择器（按优先级排序）
    CONTENT_SELECTORS = [
        "#article",          # 新版文章正文主容器
        "#artibody",         # 旧版文章正文容器
        ".article",          # 通用文章容器
        ".article-content",  # 备选文章容器
    ]

    def __init__(self):
        super().__init__(source_key="sina", display_name="新浪新闻")
        self.ent_url = "https://ent.sina.com.cn/"
        self.china_url = "https://news.sina.com.cn/china/"
        self.world_url = "https://news.sina.com.cn/world/"

    async def fetch_content(self, url: str) -> str | None:
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

    async def scrape(self) -> list[dict[str, Any]]:
        """
        采集所有新浪新闻频道

        使用 asyncio.gather 并发采集三个频道，提高效率。
        如果某个频道采集失败，不影响其他频道的结果。

        Returns:
            所有频道文章的合并列表
        """
        all_articles = []

        # 并发采集三个频道
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

    async def _scrape_ent_channel(self) -> list[dict[str, Any]]:
        """
        采集娱乐频道

        页面结构：
        - 卡片式布局 (div.cardlist-a__list > div.ty-card)
        - 需要滚动到底部触发懒加载
        - 每个卡片包含标题链接 (div:nth-child(2) > h3 > a)
        """
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

    async def _scrape_china_channel(self, page_num: int = 3) -> list[dict[str, Any]]:
        """
        采集国内新闻频道（支持翻页）

        页面结构：
        - 新闻列表 (div.feed-card-content > div:first-child > div.feed-card-item)
        - 翻页按钮 (.pagebox_next)
        - 每页约 20 条新闻

        Args:
            page_num: 采集页数（默认 3 页）

        Note:
            翻页时需等待 DOM 更新完成，避免获取到旧数据
        """
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

    async def _scrape_world_channel(self) -> list[dict[str, Any]]:
        """
        采集国际新闻频道

        页面结构：
        - 主容器 (div#subShowContent1_static)
        - 分区块展示：news1/news2/news3/news4 对应不同地区新闻
        - 每个区块包含 div.news-item 列表

        区块说明：
        - news1: 热点国际新闻
        - news2: 美洲新闻
        - news3: 欧洲新闻
        - news4: 亚太新闻
        """
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
