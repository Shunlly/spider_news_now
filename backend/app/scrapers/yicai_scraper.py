"""
第一财经新闻爬虫 - Yicai News Scraper

采集第一财经新闻频道的文章：
- 新闻频道 (finance): https://www.yicai.com/news/

技术实现：
- 使用 Playwright 进行动态页面渲染
- 优先从 window.firstlist 全局变量提取数据
- 备用方案：DOM 选择器提取文章链接
- 正文解析支持多个 CSS 选择器尝试

页面结构说明：
- 第一财经使用 SSR + CSR 混合渲染
- 首屏数据存储在 window.firstlist 数组中
- firstlist 每项包含 url 和 NewsTitle 字段
- DOM 结构：li > a[href*='/news/'] > span.f-toe（标题）
"""

import asyncio
from datetime import datetime
from typing import Any

from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper


class YicaiScraper(BaseScraper):
    """
    第一财经新闻爬虫

    采集财经新闻：
    - 财经资讯、股市动态、宏观经济

    采集策略：
    1. 优先从 window.firstlist 提取（速度快、数据完整）
    2. 如果 firstlist 为空，降级为 DOM 提取
    3. 过滤专题页面（/topic/ 路径）
    """

    # 第一财经正文选择器（按优先级排序）
    CONTENT_SELECTORS = [
        ".m-text",              # 主要文章正文容器
        ".article-content",     # 文章内容
        "#article-content",     # 文章内容 ID
        ".txt",                 # 文本容器
    ]

    def __init__(self):
        super().__init__(source_key="yicai", display_name="第一财经")
        self.base_url = "https://www.yicai.com/news/"

    async def fetch_content(self, url: str) -> str | None:
        """Fetch article content from Yicai News, preserving images."""
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
            self.logger.warning(f"Yicai content fetch failed for {url}: {str(e)}")
            return None

    async def scrape(self) -> list[dict[str, Any]]:
        """
        采集第一财经新闻

        数据提取流程：
        1. 等待页面加载完成（包括 JS 执行）
        2. 尝试从 window.firstlist 提取 SSR 注水数据
        3. 如果 firstlist 为空，降级为 DOM 链接提取

        Returns:
            文章列表（包含 url, title, category, published_at）
        """
        news_data = []
        seen_urls = set()  # URL 去重
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                page.set_default_timeout(120000)

                await page.goto(self.base_url, wait_until="domcontentloaded", timeout=120000)
                await asyncio.sleep(3)  # 等待 JS 执行完成

                # 方法一：从 JavaScript 全局变量 firstlist 提取
                # firstlist 是 SSR 渲染时注入的新闻列表数据
                firstlist = await page.evaluate("() => window.firstlist || []")
                if firstlist and isinstance(firstlist, list):
                    for item in firstlist:
                        try:
                            if not isinstance(item, dict):
                                continue
                            url = item.get("url", "")
                            title = item.get("NewsTitle", "")  # 注意：字段名是 NewsTitle
                            if not url or not title:
                                continue
                            # 过滤专题页面（不是真正的新闻文章）
                            if "/topic/" in url:
                                continue
                            # 处理相对 URL
                            full_url = url if url.startswith("http") else f"https://www.yicai.com{url}"
                            if full_url not in seen_urls:
                                seen_urls.add(full_url)
                                news_data.append({
                                    "url": full_url,
                                    "title": title.strip(),
                                    "category": "finance",
                                    "published_at": datetime.now(),
                                })
                        except Exception as e:
                            self.logger.warning(f"从 firstlist 提取失败: {str(e)}")
                            continue

                # 方法二：DOM 提取（当 firstlist 数据不足时补充）
                # 选择器：li > a[href*='/news/'] > span.f-toe（标题在 span.f-toe 中）
                items = await page.locator("li a[href*='/news/']").all()
                for item in items:
                    try:
                        href = await item.get_attribute("href")
                        # 过滤专题页面
                        if not href or "/topic/" in href:
                            continue

                        # 尝试获取标题：优先从 span.f-toe 提取，否则取链接文本
                        title = None
                        title_locator = item.locator("span.f-toe")
                        if await title_locator.count() > 0:
                            title = await title_locator.first.inner_text()
                        else:
                            title = await item.inner_text()

                        if not title or not title.strip():
                            continue

                        # 处理相对 URL
                        full_url = href if href.startswith("http") else f"https://www.yicai.com{href}"
                        if full_url not in seen_urls:
                            seen_urls.add(full_url)
                            news_data.append({
                                "url": full_url,
                                "title": title.strip(),
                                "category": "finance",
                                "published_at": datetime.now(),
                            })
                    except Exception as e:
                        self.logger.warning(f"DOM 提取文章失败: {str(e)}")
                        continue

                await browser.close()

            self.logger.info(f"采集到 {len(news_data)} 篇财经新闻")
            return news_data

        except Exception as e:
            self.logger.error(f"采集失败: {str(e)}")
            return news_data
