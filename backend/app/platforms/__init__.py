"""
Platforms Layer - 平台层

支持多种数据平台的适配器实现：
- news: 新闻网站爬虫
- twitter: Twitter/X 社交媒体
- telegram: Telegram 频道/群组

每个平台目录包含：
- adapter.py: 平台适配器实现
- models.py: 平台特定的数据模型
- schemas.py: 平台特定的 Pydantic 模式
- service.py: 平台业务逻辑

添加新平台：
1. 创建新目录 app/platforms/{platform_name}/
2. 实现继承自 PlatformAdapter 的适配器类
3. 使用 @platform_adapter 装饰器自动注册
"""

from app.platforms.base import (
    DataPointerInfo,
    PlatformAdapter,
    PlatformCapabilities,
    PlatformRegistry,
    PlatformType,
    SearchDocument,
    SyncResult,
    platform_adapter,
)

__all__ = [
    # Base classes
    "PlatformAdapter",
    "PlatformCapabilities",
    "PlatformRegistry",
    "PlatformType",
    "DataPointerInfo",
    "SearchDocument",
    "SyncResult",
    "platform_adapter",
]


def discover_platforms() -> None:
    """
    自动发现并加载所有平台适配器

    导入各平台模块以触发 @platform_adapter 装饰器注册。
    """
    # 导入各平台模块触发注册
    try:
        from app.platforms import news  # noqa: F401
    except ImportError:
        pass

    try:
        from app.platforms import twitter  # noqa: F401
    except ImportError:
        pass

    try:
        from app.platforms import telegram  # noqa: F401
    except ImportError:
        pass
