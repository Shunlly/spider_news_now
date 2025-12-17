"""ScraperRun SQLAlchemy model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, Text, Index, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def generate_uuid() -> str:
    """生成 UUID 字符串"""
    return str(uuid.uuid4())

if TYPE_CHECKING:
    from app.models.news_source import NewsSource
    from app.models.user import User


class ScraperRun(Base):
    """
    Scraper run entity representing a single execution.

    Tracks scraper execution history for monitoring and debugging.
    数据隔离：通过 user_id 关联到执行者
    """

    __tablename__ = "scraper_runs"

    # Primary Key (UUID)
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid,
        comment="主键UUID"
    )

    # 用户关联（逻辑外键，数据隔离）
    # ForeignKey 用于 ORM 关系映射，但数据库层面不创建约束
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="所属用户UUID"
    )

    # Source identification（逻辑外键）
    # ForeignKey 用于 ORM 关系映射，但数据库层面不创建约束
    source_key: Mapped[str] = mapped_column(
        String(50), ForeignKey("news_sources.source_key"), nullable=False, index=True,
        comment="来源标识"
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

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="scraper_runs")
    source: Mapped["NewsSource"] = relationship("NewsSource", back_populates="runs")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_source_started", "source_key", "started_at"),
        Index("idx_status_started", "status", "started_at"),
    )

    def __repr__(self) -> str:
        return f"<ScraperRun(id={self.id}, source='{self.source_key}', status='{self.status}')>"
