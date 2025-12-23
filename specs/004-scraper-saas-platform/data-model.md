# Data Model: 全栈爬虫 SaaS 平台

**Branch**: `004-scraper-saas-platform` | **Date**: 2025-12-18

## 实体关系图 (ERD)

```text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              多租户爬虫 SaaS 平台数据模型                              │
└─────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌───────────────┐
                                    │     Role      │
                                    ├───────────────┤
                                    │ id (PK)       │
                                    │ name          │
                                    │ permissions[] │
                                    └───────┬───────┘
                                            │
                                            │ 1:N
                                            ▼
┌───────────────┐       1:N       ┌───────────────┐       1:N       ┌───────────────┐
│    Tenant     │◄────────────────│     User      │────────────────►│  AuditLog     │
├───────────────┤                 ├───────────────┤                 ├───────────────┤
│ id (PK)       │                 │ id (PK)       │                 │ id (PK)       │
│ name          │                 │ tenant_id(FK) │                 │ user_id (FK)  │
│ quota_config  │                 │ role_id (FK)  │                 │ action        │
│ settings      │                 │ email         │                 │ resource_type │
│ created_at    │                 │ password_hash │                 │ resource_id   │
│ updated_at    │                 │ quota_tier    │                 │ ip_address    │
└───────┬───────┘                 │ is_verified   │                 │ details       │
        │                         │ is_active     │                 │ created_at    │
        │                         │ last_login_at │                 └───────────────┘
        │                         │ created_at    │
        │                         └───────┬───────┘
        │                                 │
        │       ┌─────────────────────────┼─────────────────────────┐
        │       │                         │                         │
        │       ▼                         ▼                         ▼
        │ ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
        │ │    Quota      │       │ ScrapingTask  │       │CaptchaAttempt │
        │ ├───────────────┤       ├───────────────┤       ├───────────────┤
        │ │ id (PK)       │       │ id (PK)       │       │ id (PK)       │
        │ │ user_id (FK)  │       │ tenant_id(FK) │       │ user_id (FK)  │
        │ │ daily_limit   │       │ user_id (FK)  │       │ success       │
        │ │ daily_used    │       │ task_type     │       │ ip_address    │
        │ │ concurrent_lmt│       │ target_url    │       │ user_agent    │
        │ │ concurrent_use│       │ status        │       │ created_at    │
        │ │ reset_at      │       │ config (JSON) │       └───────────────┘
        │ └───────────────┘       │ progress (JSON)│
        │                         │ error_message │
        │                         │ started_at    │
        │                         │ completed_at  │
        │                         │ created_at    │
        │                         └───────┬───────┘
        │                                 │
        │         ┌───────────────────────┴───────────────────────┐
        │         │                                               │
        │         ▼                                               ▼
        │ ┌───────────────┐                               ┌───────────────┐
        └►│ NewsArticle   │                               │SocialSession  │
          ├───────────────┤                               ├───────────────┤
          │ id (PK)       │                               │ id (PK)       │
          │ tenant_id(FK) │                               │ tenant_id(FK) │
          │ task_id (FK)  │                               │ task_id (FK)  │
          │ title         │                               │ platform      │
          │ content       │                               │ thread_id     │
          │ summary       │                               │ source_url    │
          │ author        │                               │ title         │
          │ source        │                               │ message_count │
          │ source_url    │                               │ first_msg_at  │
          │ url_hash      │                               │ last_msg_at   │
          │ simhash       │                               │ created_at    │
          │ published_at  │                               └───────┬───────┘
          │ raw_html_key  │                                       │
          │ created_at    │                                       │ 1:N
          └───────────────┘                                       ▼
                                                          ┌───────────────┐
                                                          │SocialMessage  │
                                                          ├───────────────┤
                                                          │ id (PK)       │
                                                          │ session_id(FK)│
                                                          │ parent_id(FK) │◄─┐ self-ref
                                                          │ quoted_id(FK) │  │ (回复)
                                                          │ platform_id   │──┘
                                                          │ sender_id     │
                                                          │ sender_name   │
                                                          │ content       │
                                                          │ media_urls[]  │
                                                          │ sent_at       │
                                                          │ raw_data(JSON)│
                                                          │ created_at    │
                                                          └───────────────┘
```

## 实体详细定义

### 1. Tenant (租户)

```python
class Tenant(Base):
    """租户/组织实体

    用于多租户数据隔离，所有业务数据都归属于特定租户
    """
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, comment="租户名称")
    quota_config: Mapped[dict] = mapped_column(
        JSON,
        default={"daily_limit": 1000, "concurrent_limit": 5},
        comment="租户级配额配置"
    )
    settings: Mapped[dict] = mapped_column(JSON, default={}, comment="租户设置")
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否启用")
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    # 关系
    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    tasks: Mapped[list["ScrapingTask"]] = relationship(back_populates="tenant")
    news_articles: Mapped[list["NewsArticle"]] = relationship(back_populates="tenant")
    social_sessions: Mapped[list["SocialSession"]] = relationship(back_populates="tenant")
```

### 2. Role (角色)

```python
class Role(Base):
    """角色实体

    RBAC 权限模型的角色定义
    """
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, comment="角色名称")
    permissions: Mapped[list[str]] = mapped_column(
        JSON,
        default=[],
        comment="权限列表"
    )
    description: Mapped[str | None] = mapped_column(String(200))

    # 预定义角色
    # 1: super_admin - 超级管理员，全局权限
    # 2: tenant_admin - 租户管理员，租户内管理权限
    # 3: user - 普通用户，基础操作权限
```

### 3. User (用户)

```python
class User(Base):
    """用户实体

    支持邮箱注册、多角色、配额管理
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True,
        comment="所属租户ID (super_admin 可为空)"
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"),
        default=3,
        comment="角色ID"
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    quota_tier: Mapped[str] = mapped_column(
        String(20),
        default="free",
        comment="配额等级: free, basic, pro"
    )
    is_verified: Mapped[bool] = mapped_column(default=False, comment="邮箱已验证")
    is_active: Mapped[bool] = mapped_column(default=True)
    verification_token: Mapped[str | None] = mapped_column(String(100))
    verification_expires: Mapped[datetime | None] = mapped_column()
    last_login_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # 关系
    tenant: Mapped["Tenant | None"] = relationship(back_populates="users")
    role: Mapped["Role"] = relationship()
    quota: Mapped["Quota"] = relationship(back_populates="user", uselist=False)
    tasks: Mapped[list["ScrapingTask"]] = relationship(back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")
```

### 4. Quota (配额)

```python
class Quota(Base):
    """配额实体

    追踪用户的配额使用情况
    """
    __tablename__ = "quotas"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True
    )
    daily_limit: Mapped[int] = mapped_column(default=100, comment="每日采集限额")
    daily_used: Mapped[int] = mapped_column(default=0, comment="今日已使用")
    concurrent_limit: Mapped[int] = mapped_column(default=3, comment="并发任务限额")
    concurrent_used: Mapped[int] = mapped_column(default=0, comment="当前并发数")
    reset_at: Mapped[datetime] = mapped_column(comment="配额重置时间 (UTC)")
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    # 关系
    user: Mapped["User"] = relationship(back_populates="quota")

    # 配额等级配置
    TIER_CONFIG = {
        "free": {"daily_limit": 100, "concurrent_limit": 1},
        "basic": {"daily_limit": 1000, "concurrent_limit": 3},
        "pro": {"daily_limit": 10000, "concurrent_limit": 10},
    }
```

### 5. ScrapingTask (采集任务)

```python
class TaskType(str, Enum):
    NEWS = "news"
    TWITTER = "twitter"
    TELEGRAM = "telegram"

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ScrapingTask(Base):
    """采集任务实体

    记录用户创建的采集作业
    """
    __tablename__ = "scraping_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    task_type: Mapped[TaskType] = mapped_column(comment="任务类型")
    target_url: Mapped[str] = mapped_column(String(2048), comment="目标 URL")
    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.PENDING)
    config: Mapped[dict] = mapped_column(
        JSON,
        default={},
        comment="任务配置 (如: 分页深度, 筛选条件)"
    )
    progress: Mapped[dict] = mapped_column(
        JSON,
        default={"total": 0, "completed": 0, "failed": 0},
        comment="进度信息"
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    celery_task_id: Mapped[str | None] = mapped_column(String(100), comment="Celery 任务 ID")
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # 关系
    tenant: Mapped["Tenant"] = relationship(back_populates="tasks")
    user: Mapped["User"] = relationship(back_populates="tasks")
    news_articles: Mapped[list["NewsArticle"]] = relationship(back_populates="task")
    social_sessions: Mapped[list["SocialSession"]] = relationship(back_populates="task")

    # 索引
    __table_args__ = (
        Index("ix_tasks_tenant_status", "tenant_id", "status"),
        Index("ix_tasks_user_created", "user_id", "created_at"),
    )
```

### 6. NewsArticle (新闻文章)

```python
class NewsArticle(Base):
    """新闻文章实体

    存储从新闻站点采集的结构化内容
    """
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey("scraping_tasks.id", ondelete="SET NULL"),
        nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), comment="标题")
    content: Mapped[str] = mapped_column(Text, comment="正文内容")
    summary: Mapped[str | None] = mapped_column(String(1000), comment="摘要")
    author: Mapped[str | None] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(100), comment="来源站点名称")
    source_url: Mapped[str] = mapped_column(String(2048), comment="原文 URL")
    url_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        comment="URL SHA256 哈希"
    )
    simhash: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
        comment="内容 SimHash 指纹"
    )
    published_at: Mapped[datetime | None] = mapped_column(comment="发布时间")
    raw_html_key: Mapped[str | None] = mapped_column(
        String(255),
        comment="原始 HTML 存储 Key (MinIO/S3)"
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # 关系
    tenant: Mapped["Tenant"] = relationship(back_populates="news_articles")
    task: Mapped["ScrapingTask | None"] = relationship(back_populates="news_articles")

    # 索引
    __table_args__ = (
        Index("ix_news_tenant_source", "tenant_id", "source"),
        Index("ix_news_tenant_published", "tenant_id", "published_at"),
        Index("ix_news_simhash", "simhash"),  # 用于相似度查询
    )
```

### 7. SocialSession (社交会话)

```python
class SocialPlatform(str, Enum):
    TWITTER = "twitter"
    TELEGRAM = "telegram"

class SocialSession(Base):
    """社交会话实体

    Twitter Thread 或 Telegram 对话的容器
    """
    __tablename__ = "social_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey("scraping_tasks.id", ondelete="SET NULL"),
        nullable=True
    )
    platform: Mapped[SocialPlatform] = mapped_column(comment="平台类型")
    thread_id: Mapped[str] = mapped_column(
        String(100),
        index=True,
        comment="平台原生 Thread/Channel ID"
    )
    source_url: Mapped[str] = mapped_column(String(2048))
    title: Mapped[str | None] = mapped_column(String(500), comment="会话标题/主题")
    message_count: Mapped[int] = mapped_column(default=0)
    first_message_at: Mapped[datetime | None] = mapped_column()
    last_message_at: Mapped[datetime | None] = mapped_column()
    last_sync_at: Mapped[datetime | None] = mapped_column(comment="最后同步时间 (增量)")
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # 关系
    tenant: Mapped["Tenant"] = relationship(back_populates="social_sessions")
    task: Mapped["ScrapingTask | None"] = relationship(back_populates="social_sessions")
    messages: Mapped[list["SocialMessage"]] = relationship(
        back_populates="session",
        order_by="SocialMessage.sent_at"
    )

    # 唯一约束
    __table_args__ = (
        UniqueConstraint("tenant_id", "platform", "thread_id", name="uq_session_thread"),
    )
```

### 8. SocialMessage (社交消息)

```python
class SocialMessage(Base):
    """社交消息实体

    单条 Twitter/Telegram 消息，支持回复和引用关系
    """
    __tablename__ = "social_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("social_sessions.id", ondelete="CASCADE"),
        index=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("social_messages.id", ondelete="SET NULL"),
        comment="回复的父消息 ID"
    )
    quoted_id: Mapped[int | None] = mapped_column(
        ForeignKey("social_messages.id", ondelete="SET NULL"),
        comment="引用的消息 ID"
    )
    platform_message_id: Mapped[str] = mapped_column(
        String(100),
        comment="平台原生消息 ID"
    )
    sender_id: Mapped[str] = mapped_column(String(100), comment="发送者平台 ID")
    sender_name: Mapped[str] = mapped_column(String(100), comment="发送者显示名")
    sender_username: Mapped[str | None] = mapped_column(String(100), comment="发送者用户名")
    content: Mapped[str] = mapped_column(Text, comment="消息内容")
    media_urls: Mapped[list[str]] = mapped_column(JSON, default=[], comment="媒体附件 URL")
    sent_at: Mapped[datetime] = mapped_column(index=True, comment="发送时间")
    raw_data: Mapped[dict] = mapped_column(JSON, default={}, comment="原始 API 响应")
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # 关系
    session: Mapped["SocialSession"] = relationship(back_populates="messages")
    parent: Mapped["SocialMessage | None"] = relationship(
        remote_side=[id],
        foreign_keys=[parent_id]
    )
    quoted: Mapped["SocialMessage | None"] = relationship(
        remote_side=[id],
        foreign_keys=[quoted_id]
    )
    replies: Mapped[list["SocialMessage"]] = relationship(
        foreign_keys=[parent_id],
        back_populates="parent"
    )

    # 索引
    __table_args__ = (
        Index("ix_messages_session_sent", "session_id", "sent_at"),
        UniqueConstraint("session_id", "platform_message_id", name="uq_message_platform"),
    )
```

### 9. AuditLog (审计日志)

```python
class AuditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    CONFIG_CHANGE = "config_change"

class AuditLog(Base):
    """审计日志实体

    记录所有敏感操作
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    action: Mapped[AuditAction] = mapped_column(comment="操作类型")
    resource_type: Mapped[str] = mapped_column(String(50), comment="资源类型")
    resource_id: Mapped[str | None] = mapped_column(String(100), comment="资源 ID")
    ip_address: Mapped[str] = mapped_column(String(45), comment="来源 IP")
    user_agent: Mapped[str | None] = mapped_column(String(500))
    details: Mapped[dict] = mapped_column(JSON, default={}, comment="操作详情")
    created_at: Mapped[datetime] = mapped_column(default=func.now(), index=True)

    # 关系
    user: Mapped["User | None"] = relationship(back_populates="audit_logs")

    # 索引
    __table_args__ = (
        Index("ix_audit_user_created", "user_id", "created_at"),
        Index("ix_audit_action_created", "action", "created_at"),
    )
```

### 10. CaptchaAttempt (验证码尝试)

```python
class CaptchaAttempt(Base):
    """验证码尝试记录

    用于追踪滑块验证码的失败次数和冷却期
    """
    __tablename__ = "captcha_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    identifier: Mapped[str] = mapped_column(
        String(100),
        index=True,
        comment="标识符 (IP 或 email)"
    )
    success: Mapped[bool] = mapped_column()
    ip_address: Mapped[str] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # 清理策略: 保留 24 小时内的记录
```

## 验证规则

### User 验证

```python
from pydantic import BaseModel, EmailStr, validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    captcha_token: str

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("密码至少 8 个字符")
        if not any(c.isupper() for c in v):
            raise ValueError("密码需包含大写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码需包含数字")
        return v
```

### ScrapingTask 验证

```python
class TaskCreate(BaseModel):
    task_type: TaskType
    target_url: str
    config: dict = {}

    @validator("target_url")
    def validate_url(cls, v, values):
        task_type = values.get("task_type")

        if task_type == TaskType.TWITTER:
            if not re.match(r"https?://(twitter\.com|x\.com)/\w+/status/\d+", v):
                raise ValueError("无效的 Twitter Thread URL")

        elif task_type == TaskType.TELEGRAM:
            if not re.match(r"https?://t\.me/\w+", v):
                raise ValueError("无效的 Telegram Channel URL")

        elif task_type == TaskType.NEWS:
            if not v.startswith(("http://", "https://")):
                raise ValueError("URL 必须以 http:// 或 https:// 开头")

        return v
```

## 状态转换

### ScrapingTask 状态机

```text
             ┌──────────────────────────────────────┐
             │                                      │
             ▼                                      │
┌─────────┐     ┌─────────┐     ┌───────────┐     │
│ PENDING │────►│ RUNNING │────►│ COMPLETED │     │
└────┬────┘     └────┬────┘     └───────────┘     │
     │               │                             │
     │               │ 失败                         │
     │               ▼                             │
     │          ┌─────────┐                        │
     │          │ FAILED  │────────────────────────┘
     │          └─────────┘      重试
     │
     │ 用户取消
     ▼
┌───────────┐
│ CANCELLED │
└───────────┘
```

### Quota 重置逻辑

```text
每日 UTC 00:00
     │
     ▼
┌─────────────────┐
│ 遍历所有用户    │
│ 配额记录        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ daily_used = 0  │
│ reset_at = NOW()│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 更新 Meilisearch │
│ 索引 (如需要)   │
└─────────────────┘
```
