"""News article Pydantic schemas (request/response models)."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, HttpUrl, Field, ConfigDict


class NewsArticleBase(BaseModel):
    """Base article schema with common fields."""

    url: HttpUrl
    title: str = Field(..., min_length=1, max_length=255)
    source_key: str = Field(..., pattern="^[a-z0-9_]+$")
    category: Optional[str] = Field(None, max_length=50)
    published_at: datetime


class NewsArticleCreate(NewsArticleBase):
    """Schema for creating a new article."""

    url_hash: str = Field(..., min_length=64, max_length=64)
    content_hash: Optional[str] = Field(None, min_length=64, max_length=64)


class NewsArticleResponse(NewsArticleBase):
    """Schema for article API responses."""

    id: int
    scraped_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NewsArticleDetailResponse(NewsArticleResponse):
    """Schema for detailed article response with additional fields."""

    created_at: datetime
    url_hash: str


class NewsArticleListResponse(BaseModel):
    """Schema for paginated article list responses."""

    data: List[NewsArticleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class NewsArticleGroupedResponse(BaseModel):
    """Schema for articles grouped by source."""

    class SourceGroup(BaseModel):
        source_key: str
        source_name: str
        article_count: int
        articles: List[NewsArticleResponse]

    groups: List[SourceGroup]
    total_sources: int
    filters_applied: dict = {}


class NewsStatisticsResponse(BaseModel):
    """Schema for news statistics."""

    class SourceStats(BaseModel):
        source_key: str
        source_name: str
        article_count: int
        last_scraped: Optional[datetime]

    class CategoryStats(BaseModel):
        category: str
        article_count: int

    total_articles: int
    articles_today: int
    sources_active: int
    sources_failed: int
    last_scrape_time: Optional[datetime]
    by_source: List[SourceStats]
    by_category: List[CategoryStats]
