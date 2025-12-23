"""
Domains Layer - 业务域层

按业务域组织代码：
- data: 统一数据管理（DataPointer、内容提取、分析）
- user_data: 用户数据关系（收藏、标签、笔记）
"""

from app.domains.data import (
    ArticleAnalysis,
    ArticleContent,
    DataPointer,
    DataPointerService,
    DataVisibility,
    get_data_pointer_service,
)

__all__ = [
    # Data domain
    "DataPointer",
    "DataVisibility",
    "ArticleContent",
    "ArticleAnalysis",
    "DataPointerService",
    "get_data_pointer_service",
]
