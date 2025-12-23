"""
Platform Base - 平台适配器基础模块

提供所有平台适配器的抽象基类和注册机制。
"""

from app.platforms.base.adapter import (
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
    "PlatformAdapter",
    "PlatformCapabilities",
    "PlatformRegistry",
    "PlatformType",
    "DataPointerInfo",
    "SearchDocument",
    "SyncResult",
    "platform_adapter",
]
