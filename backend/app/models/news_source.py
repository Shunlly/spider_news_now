"""NewsSource SQLAlchemy model."""

from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.news_article import NewsArticle
    from app.models.scraper_run import ScraperRun


class NewsSource(Base):
    """
    News source entity representing a website with scraper configuration.

    Tracks source metadata, scheduling, and health status.
    """

    __tablename__ = "news_sources"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Source identification
    source_key: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Scraper configuration
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    scraper_module: Mapped[str] = mapped_column(String(100), nullable=False)
    schedule_interval: Mapped[int] = mapped_column(
        Integer, default=1800, nullable=False
    )  # seconds

    # Status tracking
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="idle", nullable=False
    )  # idle|running|failed|disabled
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    articles: Mapped[List["NewsArticle"]] = relationship(
        "NewsArticle", back_populates="source"
    )
    runs: Mapped[List["ScraperRun"]] = relationship(
        "ScraperRun", back_populates="source"
    )

    def __repr__(self) -> str:
        return f"<NewsSource(source_key='{self.source_key}', display_name='{self.display_name}')>"
