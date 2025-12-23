"""
Platform Adapter Base - 平台适配器基类

定义所有平台适配器必须实现的统一接口。
遵循适配器模式，确保不同平台数据采集的一致性。

平台类型：
- news: 新闻网站爬虫
- twitter: Twitter/X 社交媒体
- telegram: Telegram 频道/群组
- weibo: 微博（未来支持）
- facebook: Facebook（未来支持）
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel


class PlatformType(str, Enum):
    """平台类型枚举"""
    NEWS = "news"
    TWITTER = "twitter"
    TELEGRAM = "telegram"
    WEIBO = "weibo"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    REDDIT = "reddit"


@dataclass
class PlatformCapabilities:
    """
    平台能力声明

    每个平台在注册时声明其支持的功能特性。
    """
    # 基础能力
    supports_auth: bool = False          # 是否需要认证
    supports_pagination: bool = True      # 是否支持分页
    supports_search: bool = False         # 是否支持搜索
    supports_realtime: bool = False       # 是否支持实时推送

    # 内容类型
    has_text: bool = True                 # 是否有文本内容
    has_media: bool = False               # 是否有媒体（图片/视频）
    has_comments: bool = False            # 是否有评论
    has_reactions: bool = False           # 是否有反应（点赞等）
    has_threads: bool = False             # 是否有线程/回复链

    # 元数据
    has_author: bool = True               # 是否有作者信息
    has_timestamp: bool = True            # 是否有时间戳
    has_location: bool = False            # 是否有地理位置


@dataclass
class DataPointerInfo:
    """
    数据指针信息

    用于创建统一的 DataPointer 记录。
    """
    domain: str                           # 域名标识 (news/twitter/telegram)
    domain_table: str                     # 域表名
    domain_id: str                        # 域内唯一 ID
    title: str                            # 标题/摘要
    url: str | None = None                # 原始 URL
    created_at: datetime | None = None    # 创建时间
    extra_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchDocument:
    """
    搜索索引文档

    用于 Meilisearch 索引的标准化文档格式。
    """
    id: str                               # 唯一 ID
    title: str                            # 标题
    content: str | None = None            # 正文内容
    url: str | None = None                # URL
    platform: str = ""                    # 平台标识
    source_key: str = ""                  # 来源键
    category: str | None = None           # 分类
    published_at: datetime | None = None  # 发布时间
    user_id: str | None = None            # 用户 ID（多租户）
    tenant_id: str | None = None          # 租户 ID（多租户）
    extra_fields: dict[str, Any] = field(default_factory=dict)


class SyncResult(BaseModel):
    """同步结果"""
    success: bool
    items_synced: int = 0
    items_failed: int = 0
    error_message: str | None = None
    details: dict[str, Any] = {}


T = TypeVar("T")


class PlatformAdapter(ABC):
    """
    平台适配器抽象基类

    所有平台（新闻、Twitter、Telegram 等）都必须实现此接口。
    提供统一的数据采集、转换和索引能力。
    """

    # 平台标识符（必须覆盖）
    platform_key: str = ""
    platform_name: str = ""
    platform_type: PlatformType = PlatformType.NEWS

    # 平台能力
    capabilities: PlatformCapabilities = PlatformCapabilities()

    @abstractmethod
    async def validate_credentials(
        self,
        credentials: dict[str, Any],
    ) -> tuple[bool, str]:
        """
        验证平台凭证

        Args:
            credentials: 凭证字典（API Key、Token 等）

        Returns:
            (是否有效, 错误信息或成功消息)
        """
        raise NotImplementedError

    @abstractmethod
    async def sync(
        self,
        session_id: str,
        user_id: str,
        options: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        同步数据

        从平台拉取数据，逐条 yield 原始数据字典。
        调用者负责保存和索引。

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            options: 同步选项（时间范围、分页等）

        Yields:
            原始数据字典
        """
        raise NotImplementedError

    @abstractmethod
    def to_model(self, raw_data: dict[str, Any]) -> Any:
        """
        将原始数据转换为 ORM 模型

        Args:
            raw_data: 原始数据字典

        Returns:
            对应的 SQLAlchemy 模型实例
        """
        raise NotImplementedError

    @abstractmethod
    def to_pointer_info(self, item: Any) -> DataPointerInfo:
        """
        从模型生成数据指针信息

        Args:
            item: ORM 模型实例

        Returns:
            DataPointerInfo 用于创建统一指针
        """
        raise NotImplementedError

    @abstractmethod
    def to_search_document(
        self,
        item: Any,
        content: str | None = None,
    ) -> SearchDocument:
        """
        从模型生成搜索文档

        Args:
            item: ORM 模型实例
            content: 可选的正文内容

        Returns:
            SearchDocument 用于 Meilisearch 索引
        """
        raise NotImplementedError

    # ==================== 可选方法（有默认实现）====================

    async def on_before_sync(  # noqa: B027
        self,
        session_id: str,
        options: dict[str, Any] | None = None,
    ) -> None:
        """同步前回调（可选覆盖）"""

    async def on_after_sync(  # noqa: B027
        self,
        session_id: str,
        result: SyncResult,
    ) -> None:
        """同步后回调（可选覆盖）"""

    async def health_check(self) -> tuple[bool, str]:
        """
        健康检查

        Returns:
            (是否健康, 状态消息)
        """
        return True, "OK"

    def get_rate_limit(self) -> tuple[int, int]:
        """
        获取速率限制配置

        Returns:
            (每窗口请求数, 窗口秒数)
        """
        return 60, 60  # 默认 60次/分钟


class PlatformRegistry:
    """
    平台注册表

    管理所有已注册的平台适配器。
    支持自动发现和动态注册。
    """

    _adapters: dict[str, type[PlatformAdapter]] = {}
    _instances: dict[str, PlatformAdapter] = {}

    @classmethod
    def register(cls, adapter_class: type[PlatformAdapter]) -> type[PlatformAdapter]:
        """
        注册平台适配器

        可用作装饰器或直接调用。

        Example:
            @PlatformRegistry.register
            class TwitterAdapter(PlatformAdapter):
                platform_key = "twitter"
                ...
        """
        if not adapter_class.platform_key:
            raise ValueError(f"Adapter {adapter_class.__name__} must define platform_key")

        cls._adapters[adapter_class.platform_key] = adapter_class
        return adapter_class

    @classmethod
    def get(cls, platform_key: str) -> PlatformAdapter | None:
        """
        获取平台适配器实例

        使用单例模式，相同 platform_key 返回相同实例。

        Args:
            platform_key: 平台标识符

        Returns:
            平台适配器实例或 None
        """
        if platform_key not in cls._adapters:
            return None

        if platform_key not in cls._instances:
            cls._instances[platform_key] = cls._adapters[platform_key]()

        return cls._instances[platform_key]

    @classmethod
    def get_all(cls) -> dict[str, type[PlatformAdapter]]:
        """获取所有已注册的适配器类"""
        return cls._adapters.copy()

    @classmethod
    def list_platforms(cls) -> list[dict[str, Any]]:
        """
        列出所有已注册平台的信息

        Returns:
            平台信息列表
        """
        platforms = []
        for key, _adapter_cls in cls._adapters.items():
            adapter = cls.get(key)
            if adapter:
                platforms.append({
                    "key": adapter.platform_key,
                    "name": adapter.platform_name,
                    "type": adapter.platform_type.value,
                    "capabilities": {
                        "supports_auth": adapter.capabilities.supports_auth,
                        "supports_search": adapter.capabilities.supports_search,
                        "has_media": adapter.capabilities.has_media,
                        "has_comments": adapter.capabilities.has_comments,
                    }
                })
        return platforms

    @classmethod
    def clear(cls) -> None:
        """清空注册表（用于测试）"""
        cls._adapters.clear()
        cls._instances.clear()


def platform_adapter(cls: type[PlatformAdapter]) -> type[PlatformAdapter]:
    """
    平台适配器装饰器

    用于自动注册平台适配器。

    Example:
        @platform_adapter
        class TwitterAdapter(PlatformAdapter):
            platform_key = "twitter"
            ...
    """
    return PlatformRegistry.register(cls)
