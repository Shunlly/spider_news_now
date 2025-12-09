"""NewsArticle SQLAlchemy model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, Index, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.news_source import NewsSource


class NewsArticle(Base):
    """
    News article entity representing a collected article.

    Core entity storing scraped articles with metadata for querying and display.
    """

    __tablename__ = "news_articles"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Article identification (for duplicate detection)
    url_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    url: Mapped[str] = mapped_column(String(512), nullable=False)

    # Article content metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)

    # Source and category
    source_key: Mapped[str] = mapped_column(
        String(50), ForeignKey("news_sources.source_key"), nullable=False, index=True
    )
    category: Mapped[str | None] = mapped_column(String(50), index=True)

    # Timestamps
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationship
    source: Mapped["NewsSource"] = relationship("NewsSource", back_populates="articles")

    # Composite index for common query patterns
    __table_args__ = (
        Index("idx_source_category_date", "source_key", "category", "published_at"),
    )

    def __repr__(self) -> str:
        return f"<NewsArticle(id={self.id}, title='{self.title[:30]}...', source='{self.source_key}')>"
