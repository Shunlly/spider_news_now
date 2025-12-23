"""
新闻文章模型
NewsArticle SQLAlchemy Model

遵循宪法 II.B 数据建模：
- 新闻数据采用 Article 模式
- 支持全文搜索和 SimHash 去重
- 数据隔离：通过 user_id 关联到创建者
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def generate_uuid() -> str:
    """生成 UUID 字符串"""
    return str(uuid.uuid4())

if TYPE_CHECKING:
    from app.models.news_source import NewsSource
    from app.models.user import User


class NewsArticle(Base):
    """
    新闻文章实体

    核心实体，存储采集的文章及其元数据。
    支持全文搜索索引和内容去重。
    数据隔离：通过 user_id 关联到创建者
    """

    __tablename__ = "news_articles"

    # 主键 (UUID)
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
    content_hash: Mapped[str | None] = mapped_column(
        String(64), index=True, nullable=True,
        comment="内容 SHA256 哈希"
    )

    # 全文搜索和去重字段（新增）
    content_text: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="正文纯文本（用于全文搜索）"
    )
    content_url: Mapped[str | None] = mapped_column(
        String(512), nullable=True,
        comment="正文存储路径（MinIO/RustFS）"
    )
    simhash: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, index=True,
        comment="内容 SimHash 指纹（用于相似内容检测）"
    )

    # 正文解析状态：pending=待解析, parsing=解析中, completed=已完成, failed=失败
    content_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True,
        comment="正文解析状态"
    )
    content_retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="正文解析重试次数"
    )

    # 来源和分类（逻辑外键）
    # ForeignKey 用于 ORM 关系映射，但数据库层面不创建约束
    source_key: Mapped[str] = mapped_column(
        String(50), ForeignKey("news_sources.source_key"), nullable=False, index=True,
        comment="来源标识"
    )
    category: Mapped[str | None] = mapped_column(
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

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="news_articles")
    source: Mapped["NewsSource"] = relationship("NewsSource", back_populates="articles")

    # Composite index for common query patterns
    __table_args__ = (
        Index("idx_source_category_date", "source_key", "category", "published_at"),
        Index("idx_article_user_date", "user_id", "published_at"),
    )

    def __repr__(self) -> str:
        return f"<NewsArticle(id={self.id}, title='{self.title[:30]}...', source='{self.source_key}')>"
