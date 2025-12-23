"""
News Platform Adapter - 新闻平台适配器

实现新闻网站爬虫的统一接口。
"""

from collections.abc import AsyncIterator
from typing import Any

from app.platforms.base import (
    DataPointerInfo,
    PlatformAdapter,
    PlatformCapabilities,
    PlatformType,
    SearchDocument,
    platform_adapter,
)
from app.platforms.base import (
    SyncResult as SyncResult,  # Re-export
)


@platform_adapter
class NewsAdapter(PlatformAdapter):
    """
    新闻平台适配器

    处理各种新闻源的数据采集。
    不同新闻源通过 source_key 区分。
    """

    platform_key = "news"
    platform_name = "新闻爬虫"
    platform_type = PlatformType.NEWS

    capabilities = PlatformCapabilities(
        supports_auth=False,
        supports_pagination=True,
        supports_search=False,
        supports_realtime=False,
        has_text=True,
        has_media=True,
        has_comments=False,
        has_reactions=False,
        has_threads=False,
        has_author=True,
        has_timestamp=True,
        has_location=False,
    )

    async def validate_credentials(
        self,
        credentials: dict[str, Any],
    ) -> tuple[bool, str]:
        """新闻爬虫通常不需要凭证"""
        return True, "新闻爬虫无需认证"

    async def sync(
        self,
        session_id: str,
        user_id: str,
        options: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        同步新闻数据

        新闻的同步由 scraper 模块处理，
        这里只是适配器接口的占位实现。
        """
        # 新闻爬虫的实际逻辑在 scrapers 模块
        # 这里提供一个空迭代器
        return
        yield  # 使其成为异步生成器

    def to_model(self, raw_data: dict[str, Any]) -> Any:
        """
        转换为 NewsArticle 模型

        实际转换逻辑在 scraper_service 中处理。
        """
        from app.models.news_article import NewsArticle

        return NewsArticle(
            title=raw_data.get("title", ""),
            url=raw_data.get("url", ""),
            url_hash=raw_data.get("url_hash", ""),
            source_key=raw_data.get("source_key", ""),
            category=raw_data.get("category"),
            published_at=raw_data.get("published_at"),
            content_html=raw_data.get("content_html"),
            content_text=raw_data.get("content_text"),
            user_id=raw_data.get("user_id"),
        )

    def to_pointer_info(self, item: Any) -> DataPointerInfo:
        """生成数据指针信息"""
        return DataPointerInfo(
            domain="news",
            domain_table="news_articles",
            domain_id=str(item.id),
            title=item.title,
            url=item.url,
            created_at=item.created_at,
            extra_metadata={
                "source_key": item.source_key,
                "category": item.category,
            },
        )

    def to_search_document(
        self,
        item: Any,
        content: str | None = None,
    ) -> SearchDocument:
        """生成搜索文档"""
        return SearchDocument(
            id=str(item.id),
            title=item.title,
            content=content or item.content_text,
            url=item.url,
            platform="news",
            source_key=item.source_key,
            category=item.category,
            published_at=item.published_at,
            user_id=str(item.user_id) if item.user_id else None,
            extra_fields={
                "url_hash": item.url_hash,
            },
        )
