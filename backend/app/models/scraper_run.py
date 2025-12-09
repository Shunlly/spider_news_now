"""ScraperRun SQLAlchemy model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, Text, Index, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.news_source import NewsSource


class ScraperRun(Base):
    """
    Scraper run entity representing a single execution.

    Tracks scraper execution history for monitoring and debugging.
    """

    __tablename__ = "scraper_runs"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Source identification
    source_key: Mapped[str] = mapped_column(
        String(50), ForeignKey("news_sources.source_key"), nullable=False, index=True
    )

    # Execution timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Execution status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # running|success|failed|timeout

    # Article statistics
    articles_scraped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    articles_new: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    articles_duplicate: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Performance metrics
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    source: Mapped["NewsSource"] = relationship("NewsSource", back_populates="runs")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_source_started", "source_key", "started_at"),
        Index("idx_status_started", "status", "started_at"),
    )

    def __repr__(self) -> str:
        return f"<ScraperRun(id={self.id}, source='{self.source_key}', status='{self.status}')>"
