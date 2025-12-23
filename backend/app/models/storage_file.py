"""
存储文件模型 - 媒体文件元数据管理
Storage File Model - Media File Metadata Management

遵循宪法 II.A 存储适配器模式：
- 记录文件元数据
- 支持多存储后端
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    String,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def generate_uuid() -> str:
    """生成 UUID 字符串"""
    return str(uuid.uuid4())


class StorageBackend(str, Enum):
    """存储后端枚举"""
    LOCAL = "local"
    MINIO = "minio"
    S3 = "s3"
    OSS = "oss"


class FileType(str, Enum):
    """文件类型枚举"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    OTHER = "other"


class StorageFile(Base):
    """
    存储文件元数据实体

    记录上传到对象存储的文件信息。
    支持按来源（新闻/社交）和类型分类。
    """

    __tablename__ = "storage_files"

    # 主键 (UUID)
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid,
        comment="主键UUID"
    )

    # 文件标识
    file_key: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        comment="存储键（文件路径）"
    )
    file_hash: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False,
        comment="文件 SHA256 哈希"
    )

    # 文件信息
    original_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="原始文件名"
    )
    file_type: Mapped[FileType] = mapped_column(
        SQLEnum(FileType), nullable=False, index=True,
        comment="文件类型"
    )
    mime_type: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="MIME 类型"
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="文件大小（字节）"
    )

    # 存储信息
    storage_backend: Mapped[StorageBackend] = mapped_column(
        SQLEnum(StorageBackend), nullable=False, index=True,
        comment="存储后端类型"
    )
    bucket: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="存储桶名称"
    )
    public_url: Mapped[str | None] = mapped_column(
        String(512), nullable=True,
        comment="公开访问 URL"
    )

    # 关联来源（逻辑外键）
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="来源类型：news_article, social_message"
    )
    source_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True,
        comment="来源记录UUID"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )

    # 索引定义
    __table_args__ = (
        Index("idx_source", "source_type", "source_id"),
        Index("idx_type_created", "file_type", "created_at"),
        {"comment": "存储文件元数据表"},
    )

    def __repr__(self) -> str:
        return (
            f"<StorageFile(id={self.id}, "
            f"key='{self.file_key}', "
            f"type='{self.file_type.value}')>"
        )
