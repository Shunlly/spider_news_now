"""
搜索相关 Pydantic Schema
Search Pydantic Schemas

定义全文搜索的请求/响应模型。
遵循宪法 II.B 全文检索要求：响应时间 < 500ms。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================
# 请求模型
# =============================================================

class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., min_length=1, max_length=200, description="搜索关键词")
    page: int = Field(1, ge=1, description="页码")
    hits_per_page: int = Field(20, ge=1, le=100, description="每页结果数")
    source_key: Optional[str] = Field(None, description="按来源过滤")
    category: Optional[str] = Field(None, description="按分类过滤")
    start_date: Optional[datetime] = Field(None, description="时间范围起始")
    end_date: Optional[datetime] = Field(None, description="时间范围结束")
    sort_by: Optional[str] = Field(None, description="排序字段")
    highlight: bool = Field(True, description="是否返回高亮结果")


# =============================================================
# 响应模型
# =============================================================

class SearchHitResponse(BaseModel):
    """搜索结果条目"""
    id: int
    title: str
    url: str
    source_key: str
    category: Optional[str] = None
    published_at: datetime

    # 高亮字段（可选）
    title_highlighted: Optional[str] = Field(None, description="高亮后的标题")
    content_highlighted: Optional[str] = Field(None, description="高亮后的内容片段")


class FacetCount(BaseModel):
    """分面统计项"""
    value: str
    count: int


class FacetDistributionResponse(BaseModel):
    """分面统计响应"""
    source_key: List[FacetCount] = Field(default_factory=list, description="来源分布")
    category: List[FacetCount] = Field(default_factory=list, description="分类分布")


class SearchResponse(BaseModel):
    """搜索响应模型"""
    hits: List[SearchHitResponse] = Field(..., description="搜索结果列表")
    query: str = Field(..., description="原始查询词")
    total_hits: int = Field(..., description="匹配结果总数")
    page: int = Field(..., description="当前页码")
    hits_per_page: int = Field(..., description="每页结果数")
    total_pages: int = Field(..., description="总页数")
    processing_time_ms: int = Field(..., description="处理时间（毫秒）")

    # 分面统计（可选）
    facets: Optional[FacetDistributionResponse] = Field(
        None, description="分面统计"
    )


class SearchSuggestionResponse(BaseModel):
    """搜索建议响应"""
    suggestions: List[str] = Field(..., description="搜索建议列表")
    query: str = Field(..., description="原始查询词")


# =============================================================
# 索引管理响应
# =============================================================

class IndexStatsResponse(BaseModel):
    """索引统计响应"""
    index_name: str
    number_of_documents: int
    is_indexing: bool
    field_distribution: Dict[str, int] = Field(
        default_factory=dict, description="字段分布统计"
    )


class IndexTaskResponse(BaseModel):
    """索引任务响应"""
    task_id: str
    status: str
    message: str
