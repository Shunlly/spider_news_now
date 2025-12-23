"""Scraper and news source Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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

    id: str
    status: str  # idle|running|failed|disabled
    last_run_at: datetime | None
    last_success_at: datetime | None
    failure_count: int

    model_config = ConfigDict(from_attributes=True)


class NewsSourceListResponse(BaseModel):
    """Schema for list of news sources."""

    sources: list[NewsSourceResponse]
    total: int


# ScraperRun Schemas
class ScraperRunBase(BaseModel):
    """Base scraper run schema."""

    source_key: str
    status: str  # running|success|failed|timeout


class ScraperRunResponse(ScraperRunBase):
    """Schema for scraper run API responses."""

    id: str
    started_at: datetime
    completed_at: datetime | None
    articles_scraped: int
    articles_new: int
    articles_duplicate: int
    duration_seconds: int | None
    error_message: str | None

    model_config = ConfigDict(from_attributes=True)


class ScraperRunListResponse(BaseModel):
    """Schema for paginated scraper run list."""

    runs: list[ScraperRunResponse]
    total: int
    page: int
    page_size: int


# Scraper Status Schemas
class RunSummary(BaseModel):
    """Summary of a scraper run."""

    started_at: datetime
    completed_at: datetime | None
    status: str
    articles_scraped: int
    articles_new: int
    articles_duplicate: int
    duration_seconds: int | None


class ScraperStatusResponse(BaseModel):
    """Detailed scraper status response."""

    source_key: str
    source_name: str
    enabled: bool
    status: str  # idle|running|failed|disabled
    last_run: RunSummary | None
    current_run: RunSummary | None
    next_run_at: datetime | None
    failure_count: int


class ScraperStatusListResponse(BaseModel):
    """List of all scraper statuses."""

    scrapers: list[ScraperStatusResponse]
    total_scrapers: int
    active_runs: int


# Scraper Action Schemas
class ScraperTriggerResponse(BaseModel):
    """Response after manually triggering a scraper."""

    message: str
    run_id: str
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
    next_run_at: datetime | None
