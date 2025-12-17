# Data Model: 用户鉴权、数据隔离与安全验证

**Feature**: 003-auth-rbac-security
**Created**: 2025-12-16
**Status**: Complete

## Entity Relationship Diagram

```
┌─────────────────┐
│      User       │
├─────────────────┤
│ id (PK)         │───┐
│ username        │   │
│ password_hash   │   │
│ role            │   │
│ is_active       │   │
│ created_at      │   │
│ updated_at      │   │
└─────────────────┘   │
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
    ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  NewsSource   │ │ SocialSession │ │ AccountCred   │
├───────────────┤ ├───────────────┤ ├───────────────┤
│ ...           │ │ ...           │ │ ...           │
│ user_id (FK)  │ │ user_id (FK)  │ │ user_id (FK)  │
└───────────────┘ └───────────────┘ └───────────────┘
        │                 │
        ▼                 ▼
┌───────────────┐ ┌───────────────┐
│ NewsArticle   │ │ SocialMessage │
├───────────────┤ ├───────────────┤
│ ...           │ │ ...           │
│ user_id (FK)  │ │ (通过session) │
└───────────────┘ └───────────────┘
```

---

## New Entities

### User (用户)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK, AUTO_INCREMENT | 用户 ID |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| `email` | VARCHAR(100) | UNIQUE, NULL | 邮箱 (可选) |
| `password_hash` | VARCHAR(255) | NOT NULL | 密码哈希 (bcrypt) |
| `role` | ENUM('admin', 'user') | NOT NULL, DEFAULT 'user' | 角色 |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | 是否激活 |
| `last_login_at` | DATETIME | NULL | 最后登录时间 |
| `login_attempts` | INT | NOT NULL, DEFAULT 0 | 登录失败次数 |
| `locked_until` | DATETIME | NULL | 账号锁定截止时间 |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW() | 创建时间 |
| `updated_at` | DATETIME | NOT NULL, DEFAULT NOW() ON UPDATE | 更新时间 |

**索引**:
- `idx_user_username`: UNIQUE INDEX ON `username`
- `idx_user_email`: UNIQUE INDEX ON `email` (允许 NULL)
- `idx_user_role`: INDEX ON `role`

**SQLAlchemy Model**:

```python
class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"


class User(Base):
    """用户实体"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=UserRole.USER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
```

---

## Modified Entities

### NewsSource (新闻来源)

**新增字段**:

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `user_id` | INT | FK → users.id, DEFAULT 1 | 创建者 ID |

**Migration**:
```python
# 1. 添加字段
op.add_column('news_sources', sa.Column('user_id', sa.Integer(), nullable=True))

# 2. 更新历史数据
op.execute("UPDATE news_sources SET user_id = 1 WHERE user_id IS NULL")

# 3. 设置 NOT NULL 和外键
op.alter_column('news_sources', 'user_id', nullable=False)
op.create_foreign_key('fk_news_sources_user', 'news_sources', 'users', ['user_id'], ['id'])
```

### NewsArticle (新闻文章)

**新增字段**:

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `user_id` | INT | FK → users.id, DEFAULT 1, INDEX | 所属用户 ID |

**索引**: `idx_article_user_date`: INDEX ON `(user_id, published_at)`

### SocialSession (社交会话)

**新增字段**:

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `user_id` | INT | FK → users.id, DEFAULT 1, INDEX | 创建者 ID |

**索引**: `idx_session_user_platform`: INDEX ON `(user_id, platform)`

### ScraperRun (爬虫运行记录)

**新增字段**:

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `user_id` | INT | FK → users.id, DEFAULT 1 | 触发者 ID |

### AccountCredential (账号凭证)

**新增字段**:

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `user_id` | INT | FK → users.id, DEFAULT 1 | 所属用户 ID |

### ProxyConfig (代理配置)

**新增字段**:

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `user_id` | INT | FK → users.id, DEFAULT 1 | 所属用户 ID |

### ExportTask (导出任务)

**新增字段**:

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `user_id` | INT | FK → users.id, DEFAULT 1, NOT NULL | 创建者 ID |

---

## Redis Data Structures

### Captcha Challenge (验证码挑战)

**Key Pattern**: `captcha:{token}`
**Type**: Hash
**TTL**: 300 seconds (5 minutes)

```json
{
  "x": 150,              // 正确的 X 坐标
  "y": 80,               // Y 坐标 (用于前端定位)
  "attempts": 0,         // 已尝试次数
  "created_at": 1702713600
}
```

### User Session (用户会话 - 可选)

**Key Pattern**: `session:{user_id}`
**Type**: Hash
**TTL**: 86400 seconds (24 hours)

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "last_active": 1702713600,
  "ip": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

### Login Rate Limit (登录速率限制)

**Key Pattern**: `login_rate:{ip}`
**Type**: String (counter)
**TTL**: 60 seconds

---

## Validation Rules

### User

| 字段 | 规则 |
|------|------|
| `username` | 3-50 字符，仅字母/数字/下划线 |
| `email` | 有效邮箱格式 (可选) |
| `password` | 最少 8 字符，包含大小写字母和数字 |
| `role` | 只能是 'admin' 或 'user' |

### Captcha

| 字段 | 规则 |
|------|------|
| `token` | 非空，有效的 UUID 格式 |
| `x` | 0-280 范围内的整数 (图片宽度 - 滑块宽度) |
| `tolerance` | ±5 像素 |

---

## State Transitions

### User Account States

```
┌──────────┐
│  ACTIVE  │◄──────────────────┐
└────┬─────┘                   │
     │ 5次失败                 │ 15分钟后自动解锁
     ▼                         │ 或管理员手动解锁
┌──────────┐                   │
│  LOCKED  │───────────────────┘
└──────────┘
```

### Captcha Verification States

```
┌──────────┐
│ PENDING  │  (生成后等待验证)
└────┬─────┘
     │ 用户提交
     ▼
┌──────────────────┐
│ VERIFY_ATTEMPT   │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
SUCCESS    FAILED
(删除Key)  (attempts++)
              │
              │ attempts >= 3
              ▼
           EXPIRED
           (删除Key)
```

---

## Migration Plan

### Phase 1: Create Users Table

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at DATETIME,
    login_attempts INT NOT NULL DEFAULT 0,
    locked_until DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建默认管理员账户 (密码: admin123)
INSERT INTO users (id, username, password_hash, role)
VALUES (1, 'admin', '$2b$12$...', 'admin');
```

### Phase 2: Add user_id to Existing Tables

```sql
-- 为每张表添加 user_id 字段
ALTER TABLE news_sources ADD COLUMN user_id INT;
ALTER TABLE news_articles ADD COLUMN user_id INT;
ALTER TABLE social_sessions ADD COLUMN user_id INT;
ALTER TABLE scraper_runs ADD COLUMN user_id INT;
ALTER TABLE account_credentials ADD COLUMN user_id INT;
ALTER TABLE proxy_configs ADD COLUMN user_id INT;
ALTER TABLE export_tasks ADD COLUMN user_id INT;

-- 更新历史数据归属到管理员
UPDATE news_sources SET user_id = 1 WHERE user_id IS NULL;
UPDATE news_articles SET user_id = 1 WHERE user_id IS NULL;
UPDATE social_sessions SET user_id = 1 WHERE user_id IS NULL;
UPDATE scraper_runs SET user_id = 1 WHERE user_id IS NULL;
UPDATE account_credentials SET user_id = 1 WHERE user_id IS NULL;
UPDATE proxy_configs SET user_id = 1 WHERE user_id IS NULL;
UPDATE export_tasks SET user_id = 1 WHERE user_id IS NULL;

-- 设置 NOT NULL 约束
ALTER TABLE news_sources MODIFY user_id INT NOT NULL;
ALTER TABLE news_articles MODIFY user_id INT NOT NULL;
-- ... 其他表类似
```

### Phase 3: Add Foreign Keys and Indexes

```sql
-- 添加外键约束
ALTER TABLE news_sources
    ADD CONSTRAINT fk_news_sources_user FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE news_articles
    ADD CONSTRAINT fk_news_articles_user FOREIGN KEY (user_id) REFERENCES users(id);
-- ... 其他表类似

-- 添加索引优化查询
CREATE INDEX idx_article_user_date ON news_articles (user_id, published_at);
CREATE INDEX idx_session_user_platform ON social_sessions (user_id, platform);
```

---

## Rollback Plan

如需回滚，按相反顺序执行：

```sql
-- 1. 删除外键
ALTER TABLE news_sources DROP FOREIGN KEY fk_news_sources_user;
-- ...

-- 2. 删除 user_id 列
ALTER TABLE news_sources DROP COLUMN user_id;
-- ...

-- 3. 删除 users 表
DROP TABLE users;
```
