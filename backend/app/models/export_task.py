"""
导出任务模型 - 数据导出管理
Export Task Model - Data Export Management

支持将采集的数据导出为各种格式（CSV、JSON、Excel）。
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    DateTime,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


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
    """

    __tablename__ = "export_tasks"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 任务标识
    task_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, nullable=False,
        default=generate_task_id,
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
    filters: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="过滤条件（JSON 格式）"
    )
    filename: Mapped[Optional[str]] = mapped_column(
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
    file_key: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="存储文件键"
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True,
        comment="本地文件路径"
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="文件大小（字节）"
    )
    download_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True,
        comment="下载 URL"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="下载链接过期时间"
    )

    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="错误信息"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="开始处理时间"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="完成时间"
    )

    # 索引定义
    __table_args__ = (
        Index("idx_status_created", "status", "created_at"),
        Index("idx_source_status", "data_source", "status"),
        {"comment": "数据导出任务表"},
    )

    def __repr__(self) -> str:
        return (
            f"<ExportTask(id={self.id}, "
            f"task_id='{self.task_id}', "
            f"source='{self.data_source}', "
            f"status='{self.status.value}')>"
        )
