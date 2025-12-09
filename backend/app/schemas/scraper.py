"""Scraper and news source Pydantic schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


# NewsSource Schemas
class NewsSourceBase(BaseModel):
    """Base news source schema."""

    source_key: str = Field(..., pattern="^[a-z0-9_]+$")
    display_name: str = Field(..., max_length=100)
    enabled: bool = True
    schedule_interval: int = Field(default=1800, ge=60)


class NewsSourceCreate(NewsSourceBase):
    """Schema for creating a new news source."""

    scraper_module: str


class NewsSourceResponse(NewsSourceBase):
    """Schema for news source API responses."""

    id: int
    status: str  # idle|running|failed|disabled
    last_run_at: Optional[datetime]
    last_success_at: Optional[datetime]
    failure_count: int

    model_config = ConfigDict(from_attributes=True)


class NewsSourceListResponse(BaseModel):
    """Schema for list of news sources."""

    sources: List[NewsSourceResponse]
    total: int


# ScraperRun Schemas
class ScraperRunBase(BaseModel):
    """Base scraper run schema."""

    source_key: str
    status: str  # running|success|failed|timeout


class ScraperRunResponse(ScraperRunBase):
    """Schema for scraper run API responses."""

    id: int
    started_at: datetime
    completed_at: Optional[datetime]
    articles_scraped: int
    articles_new: int
    articles_duplicate: int
    duration_seconds: Optional[int]
    error_message: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ScraperRunListResponse(BaseModel):
    """Schema for paginated scraper run list."""

    runs: List[ScraperRunResponse]
    total: int
    page: int
    page_size: int


# Scraper Status Schemas
class RunSummary(BaseModel):
    """Summary of a scraper run."""

    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    articles_scraped: int
    articles_new: int
    articles_duplicate: int
    duration_seconds: Optional[int]


class ScraperStatusResponse(BaseModel):
    """Detailed scraper status response."""

    source_key: str
    source_name: str
    enabled: bool
    status: str  # idle|running|failed|disabled
    last_run: Optional[RunSummary]
    current_run: Optional[RunSummary]
    next_run_at: Optional[datetime]
    failure_count: int


class ScraperStatusListResponse(BaseModel):
    """List of all scraper statuses."""

    scrapers: List[ScraperStatusResponse]
    total_scrapers: int
    active_runs: int


# Scraper Action Schemas
class ScraperTriggerResponse(BaseModel):
    """Response after manually triggering a scraper."""

    message: str
    run_id: int
    source_key: str
    started_at: datetime
    status: str


class ScraperConfigUpdate(BaseModel):
    """Schema for updating scraper configuration."""

    schedule_interval: int = Field(..., ge=60)


class ScraperEnableResponse(BaseModel):
    """Response after enabling a scraper."""

    message: str
    source_key: str
    enabled: bool
    next_run_at: Optional[datetime]
