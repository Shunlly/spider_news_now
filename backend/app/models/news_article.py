"""
新闻文章模型
NewsArticle SQLAlchemy Model

遵循宪法 II.B 数据建模：
- 新闻数据采用 Article 模式
- 支持全文搜索和 SimHash 去重
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, String, Integer, DateTime, Index, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.news_source import NewsSource


class NewsArticle(Base):
    """
    新闻文章实体

    核心实体，存储采集的文章及其元数据。
    支持全文搜索索引和内容去重。
    """

    __tablename__ = "news_articles"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 文章标识（用于去重）
    url_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False,
        comment="URL SHA256 哈希"
    )
    url: Mapped[str] = mapped_column(
        String(512), nullable=False,
        comment="原始 URL"
    )

    # 文章内容
    title: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True,
        comment="文章标题"
    )
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64), index=True, nullable=True,
        comment="内容 SHA256 哈希"
    )

    # 全文搜索和去重字段（新增）
    content_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="正文纯文本（用于全文搜索）"
    )
    simhash: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, index=True,
        comment="内容 SimHash 指纹（用于相似内容检测）"
    )

    # 来源和分类
    source_key: Mapped[str] = mapped_column(
        String(50), ForeignKey("news_sources.source_key"), nullable=False, index=True,
        comment="来源标识"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(50), index=True, nullable=True,
        comment="文章分类"
    )

    # 时间戳
    published_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        comment="发布时间"
    )
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(),
        comment="采集时间"
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
