"""
Telegram Platform Adapter - Telegram 平台适配器

实现 Telegram 频道/群组的统一接口。
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
class TelegramAdapter(PlatformAdapter):
    """
    Telegram 平台适配器

    处理 Telegram 频道和群组的数据采集。
    支持消息、媒体、用户等多种数据类型。
    """

    platform_key = "telegram"
    platform_name = "Telegram"
    platform_type = PlatformType.TELEGRAM

    capabilities = PlatformCapabilities(
        supports_auth=True,           # 需要 Bot Token 或 MTProto
        supports_pagination=True,
        supports_search=True,          # 支持频道内搜索
        supports_realtime=True,        # 支持实时更新
        has_text=True,
        has_media=True,                # 图片/视频/文件
        has_comments=True,             # 频道评论
        has_reactions=True,            # 反应表情
        has_threads=True,              # 消息回复链
        has_author=True,
        has_timestamp=True,
        has_location=False,
    )

    async def validate_credentials(
        self,
        credentials: dict[str, Any],
    ) -> tuple[bool, str]:
        """验证 Telegram 凭证"""
        # Bot Token 或 API credentials
        if "bot_token" in credentials and credentials["bot_token"]:
            return True, "Bot Token 格式有效"

        if "api_id" in credentials and "api_hash" in credentials:
            return True, "API credentials 格式有效"

        return False, "需要 bot_token 或 api_id + api_hash"

    async def sync(
        self,
        session_id: str,
        user_id: str,
        options: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        同步 Telegram 数据

        使用 telegram_service 进行实际的数据拉取。
        """
        # 实际同步逻辑委托给现有服务
        # TODO: 重构 telegram_service 以更好地集成适配器模式
        return
        yield  # type: ignore[misc]

    def to_model(self, raw_data: dict[str, Any]) -> Any:
        """转换为 Telegram 模型"""
        # TODO: 定义 TelegramMessage 模型
        raise NotImplementedError("Telegram model not yet implemented")

    def to_pointer_info(self, item: Any) -> DataPointerInfo:
        """生成数据指针信息"""
        return DataPointerInfo(
            domain="telegram",
            domain_table="telegram_messages",
            domain_id=str(getattr(item, "message_id", item.id)),
            title=getattr(item, "text", "")[:100] if getattr(item, "text", None) else "[Media]",
            url=None,  # Telegram 消息通常没有公开 URL
            created_at=getattr(item, "date", None),
            extra_metadata={
                "chat_id": getattr(item, "chat_id", None),
                "channel_name": getattr(item, "channel_name", None),
                "has_media": getattr(item, "has_media", False),
            },
        )

    def to_search_document(
        self,
        item: Any,
        content: str | None = None,
    ) -> SearchDocument:
        """生成搜索文档"""
        return SearchDocument(
            id=f"telegram_{getattr(item, 'chat_id', '')}_{getattr(item, 'message_id', item.id)}",
            title=getattr(item, "text", "")[:100] if getattr(item, "text", None) else "[Media]",
            content=content or getattr(item, "text", ""),
            url=None,
            platform="telegram",
            source_key=f"telegram:{getattr(item, 'channel_name', 'unknown')}",
            category="social",
            published_at=getattr(item, "date", None),
            extra_fields={
                "message_id": getattr(item, "message_id", None),
                "chat_id": getattr(item, "chat_id", None),
                "channel_name": getattr(item, "channel_name", None),
            },
        )

    def get_rate_limit(self) -> tuple[int, int]:
        """Telegram API 速率限制"""
        return 30, 60  # 30次/分钟
