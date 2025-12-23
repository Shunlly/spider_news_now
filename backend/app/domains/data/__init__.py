"""
Data Domain - 数据域

统一数据指针和内容管理。

DataPointer: 跨平台的统一数据引用
- 每条原始数据（文章、推文、消息）都有一个 DataPointer
- 用于统一的收藏、标签、可见性控制
- 支持关联内容提取和分析结果
"""

from app.domains.data.models import (
    ArticleAnalysis,
    ArticleContent,
    DataPointer,
    DataVisibility,
)
from app.domains.data.service import DataPointerService, get_data_pointer_service

__all__ = [
    # Models
    "DataPointer",
    "DataVisibility",
    "ArticleContent",
    "ArticleAnalysis",
    # Service
    "DataPointerService",
    "get_data_pointer_service",
]
