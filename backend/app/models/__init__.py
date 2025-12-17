# Models package
"""
数据模型模块
Database Models Module

包含所有 SQLAlchemy ORM 模型：
- User: 用户（认证和权限）
- NewsArticle: 新闻文章
- NewsSource: 新闻来源
- ScraperRun: 爬虫运行记录
- SocialSession: 社交数据会话
- SocialMessage: 社交消息
- AccountCredential: 账号凭证
- ProxyConfig: 代理配置
- StorageFile: 存储文件元数据
- ExportTask: 导出任务
"""

from app.models.user import User, UserRole
from app.models.news_article import NewsArticle
from app.models.news_source import NewsSource
from app.models.scraper_run import ScraperRun
from app.models.social_session import (
    Platform,
    SessionStatus,
    SocialSession,
    TargetType,
)
from app.models.social_message import SocialMessage
from app.models.account_credential import (
    AccountCredential,
    CredentialStatus,
)
from app.models.proxy_config import (
    ProxyConfig,
    ProxyProtocol,
    ProxyStatus,
)
from app.models.storage_file import (
    FileType,
    StorageBackend,
    StorageFile,
)
from app.models.export_task import (
    ExportFormat,
    ExportStatus,
    ExportTask,
)

__all__ = [
    # 用户模型
    "User",
    "UserRole",
    # 新闻模型
    "NewsArticle",
    "NewsSource",
    "ScraperRun",
    # 社交数据模型
    "Platform",
    "SessionStatus",
    "SocialSession",
    "SocialMessage",
    "TargetType",
    # 账号凭证
    "AccountCredential",
    "CredentialStatus",
    # 代理配置
    "ProxyConfig",
    "ProxyProtocol",
    "ProxyStatus",
    # 存储文件
    "FileType",
    "StorageBackend",
    "StorageFile",
    # 导出任务
    "ExportFormat",
    "ExportStatus",
    "ExportTask",
]
