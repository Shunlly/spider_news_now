"""
环球网新闻爬虫 - Huanqiu News Scraper

采集环球网军事频道的文章：
- 军事频道 (military): https://mil.huanqiu.com/

技术实现：
- 使用 httpx 直接请求 API（环球网提供 JSON 接口）
- API 端点：https://mil.huanqiu.com/api/list2
- 正文解析需要处理 CSR 页面（内容存储在 textarea 中）

API 参数说明：
- node: 频道节点路径（/e3pmh1dm8/e3pmt7hva 为军事频道）
- offset: 分页偏移量
- limit: 每页数量（默认 24）

页面结构说明：
- 环球网文章页面使用 CSR 渲染
- 正文内容存储在 textarea.article-content 元素中
- 需要从 textarea 提取 HTML 内容
"""

import asyncio
import re
from datetime import datetime
from typing import Any

import httpx
from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper


class HuanqiuScraper(BaseScraper):
    """
    环球网新闻爬虫

    采集军事频道的文章：
    - 军事频道 (military): 军事新闻、国防资讯

    采集策略：
    1. 通过 JSON API 获取文章列表（速度快、数据完整）
    2. API 返回文章 ID 和标题，拼接完整 URL
    3. 支持分页采集（默认 3 页）
    """

    # 环球网正文选择器
    # 注意：CSR 页面的内容存储在 textarea 中，需要特殊处理
    CONTENT_SELECTORS = [
        "textarea.article-content",  # CSR 页面的内容存储在 textarea 中
        ".l-con",                    # 左侧内容容器
        ".article-content",          # 文章内容
        "#article-content",          # 文章内容 ID
        ".a-con",                    # 文章容器
    ]

    def __init__(self):
        super().__init__(source_key="huanqiu", display_name="环球网")
        # JSON API 端点
        self.base_url = "https://mil.huanqiu.com/api/list2"
        # 文章页面 URL 前缀
        self.article_url = "https://mil.huanqiu.com/article/"

    def _strip_html_tags(self, html_content: str) -> str:
        """
        去除 HTML 标签，提取纯文本

        用于从 HTML 内容中提取可搜索的纯文本。

        Args:
            html_content: 原始 HTML 内容

        Returns:
            去除标签后的纯文本
        """
        # 移除 script 和 style 元素
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        # 移除 HTML 标签
        html_content = re.sub(r'<[^>]+>', '', html_content)
        # 解码常见 HTML 实体
        html_content = html_content.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        return html_content.strip()

    async def fetch_content(self, url: str) -> str | None:
        """
        提取环球网文章正文

        环球网使用 CSR 渲染，文章内容存储在 textarea.article-content 中。
        需要先从 textarea 提取 HTML，再进行清理。

        Args:
            url: 文章 URL

        Returns:
            清理后的 HTML 内容（保留图片）
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(url, wait_until='domcontentloaded', timeout=self.CONTENT_FETCH_TIMEOUT)
                await asyncio.sleep(2)

                content = None

                # 尝试环球网特定的选择器
                for selector in self.CONTENT_SELECTORS:
                    try:
                        element = page.locator(selector).first
                        if await element.count() > 0:
                            # textarea 元素需要特殊处理：获取 text_content 而非 inner_html
                            if 'textarea' in selector:
                                raw_content = await element.text_content()
                                if raw_content:
                                    # textarea 中存储的是 HTML 字符串
                                    content = raw_content
                            else:
                                # 普通元素获取 inner_html
                                content = await element.inner_html()

                            # 验证内容长度
                            if content and len(content.strip()) > 50:
                                break
                            else:
                                content = None
                    except Exception:
                        continue

                await browser.close()

                if content:
                    # 清理 HTML 并修复图片 URL
                    content = self._clean_html_content(content, url)
                    return content if len(content) > 50 else None

                return None

        except Exception as e:
            self.logger.warning(f"环球网正文提取失败 {url}: {str(e)}")
            return None

    async def scrape(self) -> list[dict[str, Any]]:
        """
        采集环球网军事新闻

        通过 JSON API 获取文章列表，支持分页。

        API 参数：
        - node: 频道节点路径
        - offset: 分页偏移量
        - limit: 每页数量

        Returns:
            文章列表（包含 url, title, category, published_at）
        """
        news_data = []
        try:
            # API 请求参数
            params = {
                'node': '/e3pmh1dm8/e3pmt7hva',  # 军事频道节点
                'offset': 0,
                'limit': 24  # 每页 24 条
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                # 采集 3 页数据
                for page_num in range(3):
                    params['offset'] = page_num * 24

                    response = await client.get(self.base_url, params=params)
                    response.raise_for_status()

                    data = response.json()
                    articles = data.get('list', [])

                    for article in articles:
                        # API 返回的字段：aid（文章 ID）、title（标题）
                        aid = article.get('aid')
                        title = article.get('title')

                        if aid and title:
                            news_data.append({
                                "url": f"{self.article_url}{aid}",  # 拼接完整 URL
                                "title": title,
                                "category": "military",
                                "published_at": datetime.now(),
                            })

                    # 请求间隔，避免触发限流
                    await asyncio.sleep(1)

            self.logger.info(f"采集到 {len(news_data)} 篇军事新闻")
            return news_data

        except Exception as e:
            self.logger.error(f"采集失败: {str(e)}")
            return news_data
