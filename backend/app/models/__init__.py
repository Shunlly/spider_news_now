# Models package
"""
数据模型模块
Database Models Module

包含所有 SQLAlchemy ORM 模型：
- Tenant: 租户（多租户隔离）
- Role: 角色（RBAC权限）
- User: 用户（认证和权限）
- Quota: 配额（使用量限制）
- NewsArticle: 新闻文章
- NewsSource: 新闻来源
- ScraperRun: 爬虫运行记录
- SocialSession: 社交数据会话
- SocialMessage: 社交消息
- AccountCredential: 账号凭证
- ProxyConfig: 代理配置
- StorageFile: 存储文件元数据
- ExportTask: 导出任务
- AuditLog: 审计日志
- CaptchaAttempt: 验证码尝试
"""

# 多租户模型
# 账号凭证
from app.models.account_credential import (
    AccountCredential,
    CredentialStatus,
)
from app.models.audit import AuditAction, AuditLog
from app.models.captcha import CAPTCHA_CONFIG, CaptchaAttempt

# 导出任务
from app.models.export_task import (
    ExportFormat,
    ExportStatus,
    ExportTask,
)

# 新闻模型
from app.models.news_article import NewsArticle
from app.models.news_source import NewsSource

# 代理配置
from app.models.proxy_config import (
    ProxyConfig,
    ProxyProtocol,
    ProxyStatus,
)
from app.models.quota import TIER_CONFIG, Quota, QuotaTier
from app.models.role import (
    PREDEFINED_ROLES,
    ROLE_PERMISSIONS,
    Permission,
    Role,
    RoleType,
)
from app.models.scraper_run import ScraperRun
from app.models.social_message import SocialMessage

# 社交数据模型
from app.models.social_session import (
    Platform,
    SessionStatus,
    SocialSession,
    TargetType,
)

# 存储文件
from app.models.storage_file import (
    FileType,
    StorageBackend,
    StorageFile,
)
from app.models.tenant import Tenant
from app.models.user import SYSTEM_USER_ID, User, UserRole

__all__ = [
    # 多租户模型
    "Tenant",
    "Role",
    "RoleType",
    "Permission",
    "ROLE_PERMISSIONS",
    "PREDEFINED_ROLES",
    # 用户模型
    "User",
    "UserRole",
    "SYSTEM_USER_ID",
    # 配额模型
    "Quota",
    "QuotaTier",
    "TIER_CONFIG",
    # 审计日志
    "AuditAction",
    "AuditLog",
    # 验证码
    "CaptchaAttempt",
    "CAPTCHA_CONFIG",
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
