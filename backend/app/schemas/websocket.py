"""
WebSocket 消息类型定义 - WebSocket Message Types
T137: WebSocket message types for real-time updates

定义 WebSocket 通信的消息格式。
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WSMessageType(str, Enum):
    """WebSocket 消息类型"""
    # 连接管理
    CONNECTED = "connected"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"

    # Dashboard 更新
    STATS_UPDATE = "stats_update"
    SCRAPER_STATUS = "scraper_status"
    TASK_PROGRESS = "task_progress"

    # 告警
    ALERT = "alert"
    QUOTA_WARNING = "quota_warning"


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class WSMessage(BaseModel):
    """WebSocket 基础消息"""
    type: WSMessageType
    timestamp: datetime = Field(default_factory=datetime.now)
    data: dict[str, Any] | None = None


class WSConnectedMessage(BaseModel):
    """连接成功消息"""
    type: WSMessageType = WSMessageType.CONNECTED
    timestamp: datetime = Field(default_factory=datetime.now)
    client_id: str
    message: str = "连接成功"


class WSStatsUpdate(BaseModel):
    """Dashboard 统计更新消息"""
    type: WSMessageType = WSMessageType.STATS_UPDATE
    timestamp: datetime = Field(default_factory=datetime.now)
    total_articles: int = 0
    articles_today: int = 0
    active_scrapers: int = 0
    total_scrapers: int = 0
    active_social_sessions: int = 0
    total_social_messages: int = 0
    quota_used: int = 0
    quota_limit: int = 0


class WSScraperStatus(BaseModel):
    """爬虫状态更新消息"""
    type: WSMessageType = WSMessageType.SCRAPER_STATUS
    timestamp: datetime = Field(default_factory=datetime.now)
    source_key: str
    status: str  # running, completed, failed, idle
    articles_scraped: int = 0
    last_run: datetime | None = None
    error_message: str | None = None


class WSTaskProgress(BaseModel):
    """任务进度更新消息"""
    type: WSMessageType = WSMessageType.TASK_PROGRESS
    timestamp: datetime = Field(default_factory=datetime.now)
    task_id: str
    task_type: str  # scraping, export, index
    progress: int  # 0-100
    status: str  # pending, running, completed, failed
    message: str | None = None


class WSAlert(BaseModel):
    """告警消息"""
    type: WSMessageType = WSMessageType.ALERT
    timestamp: datetime = Field(default_factory=datetime.now)
    level: AlertLevel
    title: str
    message: str
    source: str | None = None  # 触发源


class WSQuotaWarning(BaseModel):
    """配额警告消息"""
    type: WSMessageType = WSMessageType.QUOTA_WARNING
    timestamp: datetime = Field(default_factory=datetime.now)
    quota_used: int
    quota_limit: int
    percentage: float
    message: str


class WSError(BaseModel):
    """错误消息"""
    type: WSMessageType = WSMessageType.ERROR
    timestamp: datetime = Field(default_factory=datetime.now)
    code: str
    message: str
    details: dict[str, Any] | None = None
