"""News article Pydantic schemas (request/response models)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class NewsArticleBase(BaseModel):
    """Base article schema with common fields."""

    url: HttpUrl
    title: str = Field(..., min_length=1, max_length=255)
    source_key: str = Field(..., pattern="^[a-z0-9_]+$")
    category: str | None = Field(None, max_length=50)
    published_at: datetime


class NewsArticleCreate(NewsArticleBase):
    """Schema for creating a new article."""

    url_hash: str = Field(..., min_length=64, max_length=64)
    content_hash: str | None = Field(None, min_length=64, max_length=64)


class NewsArticleResponse(NewsArticleBase):
    """Schema for article API responses."""

    id: str
    scraped_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NewsArticleDetailResponse(NewsArticleResponse):
    """Schema for detailed article response with additional fields."""

    created_at: datetime
    url_hash: str
    content_text: str | None = None
    content_hash: str | None = None


class NewsArticleListResponse(BaseModel):
    """Schema for paginated article list responses."""

    data: list[NewsArticleResponse]
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
        articles: list[NewsArticleResponse]

    groups: list[SourceGroup]
    total_sources: int
    filters_applied: dict = {}


class NewsStatisticsResponse(BaseModel):
    """Schema for news statistics."""

    class SourceStats(BaseModel):
        source_key: str
        source_name: str
        article_count: int
        last_scraped: datetime | None

    class CategoryStats(BaseModel):
        category: str
        article_count: int

    total_articles: int
    articles_today: int
    articles_yesterday: int
    sources_active: int
    sources_failed: int
    last_scrape_time: datetime | None
    by_source: list[SourceStats]
    by_category: list[CategoryStats]
