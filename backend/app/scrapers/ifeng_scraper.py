"""
凤凰网新闻爬虫 - Ifeng News Scraper

采集凤凰网两个频道的文章：
1. 财经频道 (finance): https://finance.ifeng.com/
2. 军事频道 (military): https://mil.ifeng.com/

技术实现：
- 使用 Playwright 进行动态页面渲染
- 优先从 window.allData 全局变量提取数据（SSR 注水数据）
- 备用方案：DOM 选择器提取文章链接
- 正文解析支持多个 CSS 选择器尝试

页面结构说明：
- 凤凰网使用 SSR + CSR 混合渲染
- 首屏数据存储在 window.allData 对象中
- allData 包含多个数据数组：newsData, hotspotsData 等
"""

import asyncio
from datetime import datetime
from typing import Any

from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper


class IfengScraper(BaseScraper):
    """
    凤凰网新闻爬虫

    采集两个频道的文章：
    - 财经频道 (finance): 财经新闻、股市资讯
    - 军事频道 (military): 军事新闻、国防资讯

    数据提取策略：
    1. 优先从 window.allData 提取（速度快、数据完整）
    2. 如果 allData 为空，降级为 DOM 提取
    """

    # 凤凰网正文选择器（按优先级排序）
    CONTENT_SELECTORS = [
        "#main_content",        # 新版文章正文容器
        ".main_content",        # 备选正文容器
        ".article-content",     # 通用文章容器
        ".article-body",        # 文章主体
    ]

    # allData 中包含新闻数据的键名
    # 不同频道的数据存储在不同的键下
    NEWS_DATA_KEYS = [
        "newsData",         # 主新闻列表
        "hotspotsData",     # 热点新闻
        "globalData",       # 国际新闻
        "stormData",        # 风暴/热点专题
        "newsflashData",    # 快讯
        "researchData",     # 研究报告
        "investData",       # 投资资讯
        "bankEyeData",      # 银行观察
        "featuredData",     # 精选文章
    ]

    def __init__(self):
        super().__init__(source_key="ifeng", display_name="凤凰网")
        self.finance_url = "https://finance.ifeng.com/"
        self.military_url = "https://mil.ifeng.com/"

    async def fetch_content(self, url: str) -> str | None:
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

    async def scrape(self) -> list[dict[str, Any]]:
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

    async def _scrape_channel(self, url: str, category: str) -> list[dict[str, Any]]:
        """
        采集指定频道的文章

        数据提取流程：
        1. 等待页面加载完成（包括 JS 执行）
        2. 尝试从 window.allData 提取 SSR 注水数据
        3. 如果 allData 为空，降级为 DOM 链接提取

        Args:
            url: 频道页面 URL
            category: 分类标识（finance/military）

        Returns:
            文章列表（包含 url, title, category, published_at）
        """
        news_data = []
        seen_urls = set()  # 用于 URL 去重，同一页面可能有重复链接
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                page.set_default_timeout(120000)

                await page.goto(url, wait_until="domcontentloaded", timeout=120000)
                # 等待 JS 执行完成，凤凰网页面需要较长时间加载数据
                await asyncio.sleep(8)

                # 方法一：从 JavaScript 全局变量 allData 提取
                # allData 是 SSR 渲染时注入的页面数据，包含所有新闻信息
                all_data = await page.evaluate("() => window.allData")

                if all_data:
                    # 遍历所有可能包含新闻的数据数组
                    # 不同类型的新闻存储在不同的键下
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

                                    # 修复协议相对 URL（以 // 开头）
                                    # 凤凰网部分链接省略了 https: 前缀
                                    if article_url.startswith("//"):
                                        article_url = "https:" + article_url

                                    # URL 去重
                                    if article_url in seen_urls:
                                        continue
                                    seen_urls.add(article_url)

                                    # 解析发布时间（格式：YYYY-MM-DD HH:MM:SS）
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
                                    self.logger.warning(f"从 {key} 提取文章失败: {str(e)}")
                                    continue

                # 方法二：DOM 提取（当 allData 为空时的降级方案）
                # 通过匹配文章链接模式提取
                if len(news_data) == 0:
                    self.logger.info(f"allData 提取结果为空，尝试 DOM 提取: {category}")
                    # 凤凰网文章链接特征：包含 ifeng.com 和 /c/（文章路径标识）
                    article_links = await page.locator("a[href*='ifeng.com'][href*='/c/']").all()
                    for item in article_links:
                        try:
                            href = await item.get_attribute("href")
                            if not href or href in seen_urls:
                                continue

                            # 修复协议相对 URL
                            if href.startswith("//"):
                                href = "https:" + href

                            title = await item.inner_text()
                            # 过滤无效标题（空白或太短的标题）
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
