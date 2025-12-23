"""
导出任务模型 - 数据导出管理
Export Task Model - Data Export Management

支持将采集的数据导出为各种格式（CSV、JSON、Excel）。
数据隔离：通过 user_id 关联到创建者
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


def generate_uuid() -> str:
    """生成 UUID 字符串"""
    return str(uuid.uuid4())


class ExportFormat(str, Enum):
    """导出格式枚举"""
    CSV = "CSV"
    JSON = "JSON"
    EXCEL = "EXCEL"


class ExportStatus(str, Enum):
    """导出状态枚举"""
    PENDING = "PENDING"      # 等待处理
    PROCESSING = "PROCESSING"  # 处理中
    COMPLETED = "COMPLETED"  # 已完成
    FAILED = "FAILED"        # 失败
    EXPIRED = "EXPIRED"      # 已过期


def generate_task_id() -> str:
    """生成任务 ID"""
    return str(uuid.uuid4())


class ExportTask(Base):
    """
    数据导出任务实体

    管理数据导出任务，支持后台异步处理。
    导出文件存储在对象存储中，提供下载链接。
    数据隔离：通过 user_id 关联到创建者
    """

    __tablename__ = "export_tasks"

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

    # 任务标识
    task_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, nullable=False,
        default=generate_uuid,
        comment="任务 UUID"
    )

    # 导出配置
    data_source: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="数据源类型：news, social_sessions, social_messages"
    )
    export_format: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="导出格式: CSV, JSON, EXCEL"
    )
    filters: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="过滤条件（JSON 格式）"
    )
    filename: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="导出文件名"
    )

    # 状态
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        index=True,
        comment="任务状态"
    )
    progress: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="进度百分比 (0-100)"
    )

    # 结果
    total_records: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="总记录数"
    )
    exported_records: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="已导出记录数"
    )

    # 输出文件
    file_key: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="存储文件键"
    )
    file_path: Mapped[str | None] = mapped_column(
        String(512), nullable=True,
        comment="本地文件路径"
    )
    file_size: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="文件大小（字节）"
    )
    download_url: Mapped[str | None] = mapped_column(
        String(512), nullable=True,
        comment="下载 URL"
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
        comment="下载链接过期时间"
    )

    # 错误信息
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="错误信息"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
        comment="开始处理时间"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
        comment="完成时间"
    )

    # 关联关系
    owner: Mapped["User"] = relationship("User", back_populates="export_tasks")

    # 索引定义
    __table_args__ = (
        Index("idx_export_status_created", "status", "created_at"),
        Index("idx_export_source_status", "data_source", "status"),
        {"comment": "数据导出任务表"},
    )

    def __repr__(self) -> str:
        return (
            f"<ExportTask(id={self.id}, "
            f"task_id='{self.task_id}', "
            f"source='{self.data_source}', "
            f"status='{self.status}')>"
        )
