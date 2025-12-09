# Data Model: Web Scraper API System

**Feature**: 001-scraper-api-system
**Date**: 2025-12-08
**Status**: Design Complete

This document defines the data entities, relationships, and validation rules for the news scraper system.

## Entity Relationship Diagram

```
┌─────────────────┐         ┌──────────────────┐
│  NewsSource     │1      * │  NewsArticle     │
│─────────────────│◄────────│──────────────────│
│ id (PK)         │         │ id (PK)          │
│ source_key      │         │ url_hash (UK)    │
│ display_name    │         │ url              │
│ enabled         │         │ title            │
│ last_run_at     │         │ content_hash     │
│ status          │         │ source_key (FK)  │
└─────────────────┘         │ category         │
                            │ published_at     │
        │                   │ scraped_at       │
        │                   └──────────────────┘
        │
        │1
        │
        │*
┌─────────────────┐
│  ScraperRun     │
│─────────────────│
│ id (PK)         │
│ source_key (FK) │
│ started_at      │
│ completed_at    │
│ status          │
│ articles_count  │
│ error_message   │
└─────────────────┘
```

## Entity Definitions

### NewsArticle

Represents a single news article collected from a source.

**Purpose**: Core entity storing scraped news articles with metadata for querying and display.

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key, Auto-increment | Unique article identifier |
| `url_hash` | String(64) | Unique, Indexed, NOT NULL | SHA-256 hash of normalized URL for duplicate detection |
| `url` | String(512) | NOT NULL | Original article URL |
| `title` | String(255) | NOT NULL, Indexed | Article headline/title |
| `content_hash` | String(64) | Indexed | SHA-256 hash of article content for near-duplicate detection |
| `source_key` | String(50) | Foreign Key, Indexed, NOT NULL | Source identifier (sina, qq, wangyi, etc.) |
| `category` | String(50) | Indexed, Nullable | Article category (ent, china, world, finance, etc.) |
| `published_at` | DateTime | Indexed, NOT NULL | When article was published by source |
| `scraped_at` | DateTime | Default: now(), NOT NULL | When article was collected by scraper |
| `created_at` | DateTime | Default: now(), NOT NULL | Database record creation timestamp |
| `updated_at` | DateTime | Default: now(), On Update: now() | Last modification timestamp |

**Indexes**:
1. `idx_url_hash` (UNIQUE): Primary duplicate detection
2. `idx_source_category_date` (source_key, category, published_at): Query optimization for filtered views
3. `idx_published_at`: Date-range queries and newest-first sorting
4. `idx_content_hash`: Near-duplicate detection
5. `idx_title`: Full-text search (optional, for future enhancement)

**Validation Rules**:
- `url` must be valid HTTP/HTTPS URL
- `url_hash` must be exactly 64 characters (SHA-256 hex)
- `title` cannot be empty string
- `published_at` cannot be in the future
- `source_key` must exist in NewsSource table
- `category` matches predefined set (validated in application layer)

**State Transitions**: None (immutable once created, updates only for scrape timestamps)

**Relationships**:
- **Many-to-One** with NewsSource: Each article belongs to one source
- **Implicit One-to-Many** with ScraperRun: Article associated with run that created it (via scraped_at timestamp correlation)

---

### NewsSource

Represents a news website source with scraper configuration.

**Purpose**: Manage available news sources, enable/disable scrapers, track last execution status.

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key, Auto-increment | Unique source identifier |
| `source_key` | String(50) | Unique, Indexed, NOT NULL | Machine-readable identifier (sina, qq, wangyi, etc.) |
| `display_name` | String(100) | NOT NULL | Human-readable name (新浪新闻, 腾讯新闻, etc.) |
| `enabled` | Boolean | Default: True, NOT NULL | Whether scraper is active |
| `scraper_module` | String(100) | NOT NULL | Python module path (app.scrapers.sina_scraper) |
| `schedule_interval` | Integer | Default: 1800, NOT NULL | Scrape interval in seconds (default 30 min) |
| `last_run_at` | DateTime | Nullable | Timestamp of most recent scraper execution |
| `last_success_at` | DateTime | Nullable | Timestamp of most recent successful run |
| `status` | Enum | Default: 'idle', NOT NULL | Current status: idle, running, failed, disabled |
| `failure_count` | Integer | Default: 0, NOT NULL | Consecutive failures (reset on success) |
| `created_at` | DateTime | Default: now(), NOT NULL | Record creation timestamp |
| `updated_at` | DateTime | Default: now(), On Update: now() | Last modification timestamp |

**Validation Rules**:
- `source_key` must be lowercase, alphanumeric + underscores only
- `scraper_module` must be valid Python module path
- `schedule_interval` must be >= 60 seconds (minimum 1 minute)
- `status` must be one of: 'idle', 'running', 'failed', 'disabled'
- `failure_count` must be >= 0

**State Transitions**:
```
idle → running → [success] → idle
              → [failure] → failed → [retry] → running
              → [disabled] → disabled → [enabled] → idle
```

**Relationships**:
- **One-to-Many** with NewsArticle: Source has many articles
- **One-to-Many** with ScraperRun: Source has many execution records

---

### ScraperRun

Represents a single execution of a news scraper.

**Purpose**: Track scraper execution history, monitor performance, debug failures.

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key, Auto-increment | Unique run identifier |
| `source_key` | String(50) | Foreign Key, Indexed, NOT NULL | Which source was scraped |
| `started_at` | DateTime | Default: now(), NOT NULL | Run start timestamp |
| `completed_at` | DateTime | Nullable | Run completion timestamp (NULL if still running) |
| `status` | Enum | NOT NULL | Execution status: running, success, failed, timeout |
| `articles_scraped` | Integer | Default: 0, NOT NULL | Number of articles collected |
| `articles_new` | Integer | Default: 0, NOT NULL | Number of new articles (not duplicates) |
| `articles_duplicate` | Integer | Default: 0, NOT NULL | Number of duplicates detected |
| `duration_seconds` | Integer | Nullable | Total execution time in seconds |
| `error_message` | Text | Nullable | Error details if failed |
| `error_traceback` | Text | Nullable | Full stack trace for debugging |

**Indexes**:
1. `idx_source_started` (source_key, started_at DESC): Query runs by source ordered by recency
2. `idx_status_started` (status, started_at DESC): Find failed/running tasks

**Validation Rules**:
- `status` must be one of: 'running', 'success', 'failed', 'timeout'
- `completed_at` must be >= `started_at` if not NULL
- `duration_seconds` must be >= 0 if not NULL
- `articles_scraped` = `articles_new` + `articles_duplicate`
- `error_message` required if status is 'failed' or 'timeout'

**State Transitions**:
```
running → [success] → success (completed_at set)
        → [failure] → failed (error_message set)
        → [timeout] → timeout (after 60s)
```

**Relationships**:
- **Many-to-One** with NewsSource: Each run belongs to one source

---

## SQLAlchemy Model Examples

### NewsArticle Model

```python
from sqlalchemy import String, Integer, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base import Base

class NewsArticle(Base):
    __tablename__ = 'news_articles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    source_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(50), index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now()
    )

    # Relationship
    source: Mapped["NewsSource"] = relationship("NewsSource", back_populates="articles")

    __table_args__ = (
        Index('idx_source_category_date', 'source_key', 'category', 'published_at'),
    )
```

### NewsSource Model

```python
class NewsSource(Base):
    __tablename__ = 'news_sources'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_key: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    scraper_module: Mapped[str] = mapped_column(String(100), nullable=False)
    schedule_interval: Mapped[int] = mapped_column(Integer, default=1800, nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default='idle', nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    articles: Mapped[list["NewsArticle"]] = relationship("NewsArticle", back_populates="source")
    runs: Mapped[list["ScraperRun"]] = relationship("ScraperRun", back_populates="source")
```

### ScraperRun Model

```python
class ScraperRun(Base):
    __tablename__ = 'scraper_runs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    articles_scraped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    articles_new: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    articles_duplicate: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    error_traceback: Mapped[str | None] = mapped_column(Text)

    # Relationship
    source: Mapped["NewsSource"] = relationship("NewsSource", back_populates="runs")

    __table_args__ = (
        Index('idx_source_started', 'source_key', 'started_at'),
        Index('idx_status_started', 'status', 'started_at'),
    )
```

---

## Pydantic Schemas (API Contracts)

### NewsArticle Schemas

```python
from pydantic import BaseModel, HttpUrl, Field, field_validator
from datetime import datetime

class NewsArticleBase(BaseModel):
    url: HttpUrl
    title: str = Field(..., min_length=1, max_length=255)
    source_key: str = Field(..., pattern="^[a-z0-9_]+$")
    category: str | None = Field(None, max_length=50)
    published_at: datetime

class NewsArticleCreate(NewsArticleBase):
    url_hash: str = Field(..., min_length=64, max_length=64)
    content_hash: str | None = Field(None, min_length=64, max_length=64)

class NewsArticleResponse(NewsArticleBase):
    id: int
    scraped_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class NewsArticleListResponse(BaseModel):
    articles: list[NewsArticleResponse]
    total: int
    page: int
    page_size: int
```

### NewsSource Schemas

```python
class NewsSourceBase(BaseModel):
    source_key: str = Field(..., pattern="^[a-z0-9_]+$")
    display_name: str = Field(..., max_length=100)
    enabled: bool = True
    schedule_interval: int = Field(default=1800, ge=60)

class NewsSourceCreate(NewsSourceBase):
    scraper_module: str

class NewsSourceResponse(NewsSourceBase):
    id: int
    status: str
    last_run_at: datetime | None
    last_success_at: datetime | None
    failure_count: int

    class Config:
        from_attributes = True
```

### ScraperRun Schemas

```python
class ScraperRunResponse(BaseModel):
    id: int
    source_key: str
    started_at: datetime
    completed_at: datetime | None
    status: str
    articles_scraped: int
    articles_new: int
    articles_duplicate: int
    duration_seconds: int | None
    error_message: str | None

    class Config:
        from_attributes = True
```

---

## Migration Strategy

### Initial Migration (Alembic)

```python
"""Initial schema

Revision ID: 001_initial
Create Date: 2025-12-08
"""

def upgrade():
    # Create news_sources table
    op.create_table(
        'news_sources',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_key', sa.String(50), unique=True, nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('scraper_module', sa.String(100), nullable=False),
        sa.Column('schedule_interval', sa.Integer(), default=1800, nullable=False),
        sa.Column('last_run_at', sa.DateTime()),
        sa.Column('last_success_at', sa.DateTime()),
        sa.Column('status', sa.String(20), default='idle', nullable=False),
        sa.Column('failure_count', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('idx_source_key', 'news_sources', ['source_key'])

    # Create news_articles table
    op.create_table(
        'news_articles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('url_hash', sa.String(64), unique=True, nullable=False),
        sa.Column('url', sa.String(512), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content_hash', sa.String(64)),
        sa.Column('source_key', sa.String(50), sa.ForeignKey('news_sources.source_key'), nullable=False),
        sa.Column('category', sa.String(50)),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('scraped_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('idx_url_hash', 'news_articles', ['url_hash'], unique=True)
    op.create_index('idx_source_category_date', 'news_articles', ['source_key', 'category', 'published_at'])
    op.create_index('idx_published_at', 'news_articles', ['published_at'])
    op.create_index('idx_content_hash', 'news_articles', ['content_hash'])

    # Create scraper_runs table
    op.create_table(
        'scraper_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_key', sa.String(50), sa.ForeignKey('news_sources.source_key'), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('articles_scraped', sa.Integer(), default=0, nullable=False),
        sa.Column('articles_new', sa.Integer(), default=0, nullable=False),
        sa.Column('articles_duplicate', sa.Integer(), default=0, nullable=False),
        sa.Column('duration_seconds', sa.Integer()),
        sa.Column('error_message', sa.Text()),
        sa.Column('error_traceback', sa.Text())
    )
    op.create_index('idx_source_started', 'scraper_runs', ['source_key', 'started_at'])
    op.create_index('idx_status_started', 'scraper_runs', ['status', 'started_at'])

    # Seed initial news sources
    op.execute("""
        INSERT INTO news_sources (source_key, display_name, scraper_module, enabled)
        VALUES
            ('sina', '新浪新闻', 'app.scrapers.sina_scraper', TRUE),
            ('qq', '腾讯新闻', 'app.scrapers.qq_scraper', TRUE),
            ('wangyi', '网易新闻', 'app.scrapers.wangyi_scraper', TRUE),
            ('yicai', '第一财经', 'app.scrapers.yicai_scraper', TRUE),
            ('huanqiu', '环球网', 'app.scrapers.huanqiu_scraper', TRUE),
            ('ifeng', '凤凰网', 'app.scrapers.ifeng_scraper', TRUE)
    """)
```

---

## Performance Considerations

1. **Index Usage**: All common query patterns covered by composite indexes
2. **Partitioning**: Consider date-based partitioning if article volume exceeds 1M rows
3. **Archival Strategy**: Move articles older than 6 months to archive table
4. **Connection Pooling**: SQLAlchemy AsyncEngine with pool_size=20, max_overflow=40
5. **Query Optimization**: Use `offset` and `limit` for pagination, never fetch all rows
