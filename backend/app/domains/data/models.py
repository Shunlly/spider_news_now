"""
Data Domain Models - 数据域模型

定义统一的数据指针和关联内容模型。
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.mysql import CHAR, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.infrastructure.database import Base


class DataVisibility(str, Enum):
    """数据可见性枚举"""
    PRIVATE = "private"           # 仅创建者可见
    TENANT_SHARED = "tenant_shared"  # 租户内共享
    PUBLIC = "public"             # 所有人可见


class DataPointer(Base):
    """
    统一数据指针

    每条原始数据（文章、推文、消息等）都有一个对应的 DataPointer。
    用于：
    1. 跨平台统一引用
    2. 可见性控制
    3. 内容/分析关联
    4. 用户收藏/标签
    """
    __tablename__ = "data_pointers"

    # 主键
    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # 域信息（指向原始数据）
    domain: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="数据域: news, twitter, telegram, weibo"
    )
    domain_table: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="域表名: news_articles, twitter_tweets, etc."
    )
    domain_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="域内记录ID"
    )

    # 可见性控制
    visibility: Mapped[DataVisibility] = mapped_column(
        SQLEnum(
            DataVisibility,
            values_callable=lambda obj: [e.value for e in obj]
        ),
        default=DataVisibility.PRIVATE,
        nullable=False,
        comment="可见性: private, tenant_shared, public"
    )

    # 创建者信息
    created_by: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="创建者用户ID"
    )
    tenant_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        comment="所属租户ID"
    )

    # 关联状态
    has_content: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否有关联的正文提取"
    )
    has_analysis: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否有关联的分析结果"
    )

    # 缓存的展示信息（避免频繁跨表查询）
    title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="标题/摘要（缓存）"
    )
    url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        comment="原始URL（缓存）"
    )
    platform: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="平台标识（缓存）"
    )

    # 元数据
    extra_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="额外元数据"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # 关系
    contents: Mapped[list["ArticleContent"]] = relationship(
        "ArticleContent",
        back_populates="pointer",
        lazy="dynamic"
    )
    analyses: Mapped[list["ArticleAnalysis"]] = relationship(
        "ArticleAnalysis",
        back_populates="pointer",
        lazy="dynamic"
    )

    __table_args__ = (
        # 确保每个域记录只有一个指针
        UniqueConstraint("domain", "domain_table", "domain_id", name="uq_data_pointer_ref"),
        # 常用查询索引
        Index("ix_data_pointer_domain", "domain"),
        Index("ix_data_pointer_visibility", "visibility"),
        Index("ix_data_pointer_created_by", "created_by"),
        Index("ix_data_pointer_tenant_id", "tenant_id"),
        Index("ix_data_pointer_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<DataPointer {self.domain}:{self.domain_table}:{self.domain_id}>"


class ArticleContent(Base):
    """
    正文提取结果

    存储从原始数据中提取的结构化正文内容。
    一个 DataPointer 可以有多个版本的正文提取。
    """
    __tablename__ = "article_contents"

    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # 关联的数据指针
    pointer_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("data_pointers.id", ondelete="CASCADE"),
        nullable=False
    )

    # 提取的内容
    title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="提取的标题"
    )
    content_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="纯文本正文"
    )
    content_html: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="HTML格式正文"
    )
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="自动生成的摘要"
    )

    # 提取元数据
    extraction_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="提取方法: readability, goose, trafilatura"
    )
    word_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="字数统计"
    )
    language: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="检测到的语言"
    )

    # 版本控制
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="版本号"
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否为主版本"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # 关系
    pointer: Mapped["DataPointer"] = relationship(
        "DataPointer",
        back_populates="contents"
    )

    __table_args__ = (
        Index("ix_article_content_pointer", "pointer_id"),
        Index("ix_article_content_primary", "pointer_id", "is_primary"),
    )


class ArticleAnalysis(Base):
    """
    分析结果

    存储对内容的分析结果，如情感分析、实体识别等。
    一个 DataPointer 可以有多种类型的分析结果。
    """
    __tablename__ = "article_analyses"

    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # 关联的数据指针
    pointer_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("data_pointers.id", ondelete="CASCADE"),
        nullable=False
    )

    # 分析类型和结果
    analysis_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="分析类型: sentiment, entities, keywords, summary"
    )
    result: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="分析结果JSON"
    )

    # 分析元数据
    model_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="使用的模型名称"
    )
    confidence: Mapped[float | None] = mapped_column(
        nullable=True,
        comment="置信度分数"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # 关系
    pointer: Mapped["DataPointer"] = relationship(
        "DataPointer",
        back_populates="analyses"
    )

    __table_args__ = (
        Index("ix_article_analysis_pointer", "pointer_id"),
        Index("ix_article_analysis_type", "pointer_id", "analysis_type"),
    )
