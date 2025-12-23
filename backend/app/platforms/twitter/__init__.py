"""
Twitter Platform Adapter - Twitter 平台适配器

实现 Twitter/X 社交媒体的统一接口。
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


@platform_adapter
class TwitterAdapter(PlatformAdapter):
    """
    Twitter 平台适配器

    处理 Twitter/X 数据采集。
    支持推文、用户、媒体等多种数据类型。
    """

    platform_key = "twitter"
    platform_name = "Twitter/X"
    platform_type = PlatformType.TWITTER

    capabilities = PlatformCapabilities(
        supports_auth=True,           # 需要 API 认证
        supports_pagination=True,
        supports_search=True,          # 支持搜索
        supports_realtime=True,        # 支持实时流
        has_text=True,
        has_media=True,                # 图片/视频
        has_comments=True,             # 回复
        has_reactions=True,            # 点赞/转发
        has_threads=True,              # 推文线程
        has_author=True,
        has_timestamp=True,
        has_location=True,             # 地理标签
    )

    async def validate_credentials(
        self,
        credentials: dict[str, Any],
    ) -> tuple[bool, str]:
        """验证 Twitter API 凭证"""
        required_keys = ["api_key", "api_secret", "access_token", "access_secret"]
        for key in required_keys:
            if key not in credentials or not credentials[key]:
                return False, f"缺少必要的凭证: {key}"

        # TODO: 调用 Twitter API 验证凭证有效性
        return True, "凭证格式有效"

    async def sync(
        self,
        session_id: str,
        user_id: str,
        options: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        同步 Twitter 数据

        使用 twitter_service 进行实际的数据拉取。
        """
        # 实际同步逻辑委托给现有服务
        # TODO: 重构 twitter_service 以更好地集成适配器模式
        return
        yield  # type: ignore[misc]

    def to_model(self, raw_data: dict[str, Any]) -> Any:
        """转换为 Twitter 模型"""
        # TODO: 定义 TwitterTweet 模型
        raise NotImplementedError("Twitter model not yet implemented")

    def to_pointer_info(self, item: Any) -> DataPointerInfo:
        """生成数据指针信息"""
        return DataPointerInfo(
            domain="twitter",
            domain_table="twitter_tweets",
            domain_id=str(getattr(item, "tweet_id", item.id)),
            title=getattr(item, "text", "")[:100],
            url=f"https://twitter.com/i/status/{getattr(item, 'tweet_id', '')}",
            created_at=getattr(item, "created_at", None),
            extra_metadata={
                "author_id": getattr(item, "author_id", None),
                "retweet_count": getattr(item, "retweet_count", 0),
                "like_count": getattr(item, "like_count", 0),
            },
        )

    def to_search_document(
        self,
        item: Any,
        content: str | None = None,
    ) -> SearchDocument:
        """生成搜索文档"""
        return SearchDocument(
            id=f"twitter_{getattr(item, 'tweet_id', item.id)}",
            title=getattr(item, "text", "")[:100],
            content=content or getattr(item, "text", ""),
            url=f"https://twitter.com/i/status/{getattr(item, 'tweet_id', '')}",
            platform="twitter",
            source_key="twitter",
            category="social",
            published_at=getattr(item, "created_at", None),
            extra_fields={
                "tweet_id": getattr(item, "tweet_id", None),
                "author_id": getattr(item, "author_id", None),
            },
        )

    def get_rate_limit(self) -> tuple[int, int]:
        """Twitter API 有严格的速率限制"""
        return 15, 900  # 15次/15分钟
