# Data Model Design: 002-fullstack-upgrade

**Date**: 2025-12-14
**Status**: Final
**Constitution**: v2.0.0 (异构数据建模要求)

---

## 1. 数据模型概览

### 1.1 模型分类

```
┌─────────────────────────────────────────────────────────────────┐
│                      数据模型架构                                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  新闻模型    │    │  社交模型    │    │  系统模型    │         │
│  │  (News)     │    │  (Social)   │    │  (System)   │         │
│  ├─────────────┤    ├─────────────┤    ├─────────────┤         │
│  │ NewsArticle │    │SocialSession│    │ AccountCred │         │
│  │ NewsSource  │    │SocialMessage│    │ ProxyConfig │         │
│  │ ScraperRun  │    │             │    │ StorageFile │         │
│  │ (已存在)     │    │ (新增)       │    │ ExportTask  │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 社交数据模型 (新增)

### 2.1 SocialSession (社交会话)

表示一个 Twitter Thread 或 Telegram 话题/群组讨论。

```sql
CREATE TABLE social_sessions (
    -- 主键
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 业务标识
    platform        VARCHAR(20) NOT NULL COMMENT '平台: twitter, telegram',
    external_id     VARCHAR(100) NOT NULL COMMENT '外部平台ID (thread_id/topic_id)',

    -- 会话元数据
    title           VARCHAR(500) COMMENT '话题标题 (Twitter首推/TG话题名)',
    description     TEXT COMMENT '话题描述',
    session_type    VARCHAR(30) NOT NULL COMMENT '类型: thread, topic, group_chat',

    -- 来源信息
    source_group_id VARCHAR(100) COMMENT 'TG群组ID / Twitter用户ID',
    source_group_name VARCHAR(200) COMMENT '群组/用户显示名',

    -- 统计
    message_count   INT UNSIGNED DEFAULT 0 COMMENT '消息数量',
    participant_count INT UNSIGNED DEFAULT 0 COMMENT '参与者数量',

    -- 时间
    first_message_at DATETIME COMMENT '首条消息时间',
    last_message_at  DATETIME COMMENT '最后消息时间',

    -- 去重指纹
    content_hash    CHAR(64) COMMENT 'SimHash内容指纹',

    -- 审计
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- 索引
    UNIQUE KEY uk_platform_external (platform, external_id),
    INDEX idx_platform_type (platform, session_type),
    INDEX idx_source_group (source_group_id),
    INDEX idx_last_message (last_message_at),
    INDEX idx_content_hash (content_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='社交会话表 - Twitter Thread / Telegram 话题';
```

### 2.2 SocialMessage (社交消息)

表示单条推文或 Telegram 消息。

```sql
CREATE TABLE social_messages (
    -- 主键
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 关联会话
    session_id      BIGINT UNSIGNED NOT NULL COMMENT '所属会话ID',

    -- 业务标识
    platform        VARCHAR(20) NOT NULL COMMENT '平台: twitter, telegram',
    external_id     VARCHAR(100) NOT NULL COMMENT '外部消息ID',

    -- 发送者
    sender_id       VARCHAR(100) NOT NULL COMMENT '发送者外部ID',
    sender_name     VARCHAR(200) COMMENT '发送者显示名',
    sender_handle   VARCHAR(100) COMMENT '发送者用户名 (@handle)',

    -- 消息内容
    content         TEXT COMMENT '消息正文',
    content_type    VARCHAR(30) DEFAULT 'text' COMMENT '内容类型: text, media, reply',

    -- 回复关系
    reply_to_id     BIGINT UNSIGNED COMMENT '回复目标消息ID (本表)',
    reply_to_external VARCHAR(100) COMMENT '回复目标外部ID',

    -- 媒体附件 (JSON)
    media_attachments JSON COMMENT '媒体附件列表 [{type, url, storage_key}]',

    -- 交互数据
    like_count      INT UNSIGNED DEFAULT 0,
    repost_count    INT UNSIGNED DEFAULT 0,
    reply_count     INT UNSIGNED DEFAULT 0,

    -- 时间
    published_at    DATETIME NOT NULL COMMENT '发布时间',
    scraped_at      DATETIME NOT NULL COMMENT '采集时间',

    -- 去重
    url_hash        CHAR(64) NOT NULL COMMENT 'SHA256(platform+external_id)',
    content_hash    CHAR(64) COMMENT 'SimHash内容指纹',

    -- 审计
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 外键
    FOREIGN KEY (session_id) REFERENCES social_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (reply_to_id) REFERENCES social_messages(id) ON DELETE SET NULL,

    -- 索引
    UNIQUE KEY uk_url_hash (url_hash),
    UNIQUE KEY uk_platform_external (platform, external_id),
    INDEX idx_session_published (session_id, published_at),
    INDEX idx_sender (sender_id),
    INDEX idx_reply_to (reply_to_id),
    INDEX idx_published (published_at),
    INDEX idx_content_hash (content_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='社交消息表 - 推文 / TG消息';
```

### 2.3 消息媒体附件 JSON 结构

```json
{
  "media_attachments": [
    {
      "type": "image",
      "url": "https://pbs.twimg.com/media/xxx.jpg",
      "storage_key": "media/twitter/2024/12/xxx.jpg",
      "width": 1200,
      "height": 800
    },
    {
      "type": "video",
      "url": "https://video.twimg.com/xxx.mp4",
      "storage_key": "media/twitter/2024/12/xxx.mp4",
      "duration": 120
    }
  ]
}
```

---

## 3. 系统配置模型 (新增)

### 3.1 AccountCredential (账号凭证)

```sql
CREATE TABLE account_credentials (
    -- 主键
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 平台信息
    platform        VARCHAR(20) NOT NULL COMMENT '平台: twitter, telegram',
    account_name    VARCHAR(100) NOT NULL COMMENT '账号标识/显示名',

    -- 凭证内容 (加密存储)
    credential_type VARCHAR(30) NOT NULL COMMENT '凭证类型: api_key, oauth_token, cookie, bot_token',
    credential_data TEXT NOT NULL COMMENT '加密后的凭证JSON',

    -- 状态管理
    status          VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态: active, rate_limited, expired, disabled',
    rate_limit_until DATETIME COMMENT '限流解除时间',
    last_used_at    DATETIME COMMENT '最后使用时间',
    last_error      TEXT COMMENT '最后错误信息',

    -- 统计
    request_count   INT UNSIGNED DEFAULT 0 COMMENT '总请求数',
    success_count   INT UNSIGNED DEFAULT 0 COMMENT '成功请求数',
    failure_count   INT UNSIGNED DEFAULT 0 COMMENT '失败请求数',

    -- 优先级 (轮询权重)
    priority        INT DEFAULT 0 COMMENT '优先级 (越大越优先)',

    -- 审计
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_platform_status (platform, status),
    INDEX idx_rate_limit (rate_limit_until)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='平台账号凭证表';
```

### 3.2 ProxyConfig (代理配置)

```sql
CREATE TABLE proxy_configs (
    -- 主键
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 代理信息
    name            VARCHAR(100) COMMENT '代理名称/备注',
    protocol        VARCHAR(10) NOT NULL COMMENT '协议: http, https, socks5',
    host            VARCHAR(255) NOT NULL COMMENT '代理地址',
    port            INT UNSIGNED NOT NULL COMMENT '代理端口',

    -- 认证 (可选)
    username        VARCHAR(100) COMMENT '认证用户名',
    password        VARCHAR(255) COMMENT '认证密码 (加密)',

    -- 状态
    status          VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态: active, failed, disabled',
    last_check_at   DATETIME COMMENT '最后健康检查时间',
    last_success_at DATETIME COMMENT '最后成功时间',
    response_time_ms INT COMMENT '最后响应时间(ms)',

    -- 统计
    success_count   INT UNSIGNED DEFAULT 0,
    failure_count   INT UNSIGNED DEFAULT 0,

    -- 绑定 (可选)
    bound_platforms JSON COMMENT '绑定的平台列表 ["twitter", "telegram"]',

    -- 审计
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_status (status),
    INDEX idx_protocol_status (protocol, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='代理配置表';
```

### 3.3 StorageFile (存储文件)

```sql
CREATE TABLE storage_files (
    -- 主键
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 存储信息
    storage_key     VARCHAR(500) NOT NULL COMMENT '存储键 (路径)',
    storage_backend VARCHAR(30) NOT NULL COMMENT '存储后端: minio, s3, oss, local',
    bucket          VARCHAR(100) COMMENT '存储桶名称',

    -- 文件元数据
    original_name   VARCHAR(255) COMMENT '原始文件名',
    mime_type       VARCHAR(100) COMMENT 'MIME类型',
    file_size       BIGINT UNSIGNED COMMENT '文件大小(bytes)',
    file_hash       CHAR(64) COMMENT '文件SHA256',

    -- 来源关联
    source_type     VARCHAR(30) COMMENT '来源类型: news_article, social_message',
    source_id       BIGINT UNSIGNED COMMENT '来源记录ID',

    -- 审计
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    UNIQUE KEY uk_storage_key (storage_key),
    INDEX idx_file_hash (file_hash),
    INDEX idx_source (source_type, source_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='存储文件记录表';
```

### 3.4 ExportTask (导出任务)

```sql
CREATE TABLE export_tasks (
    -- 主键
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 导出配置
    export_type     VARCHAR(20) NOT NULL COMMENT '导出类型: news, social',
    export_format   VARCHAR(10) NOT NULL COMMENT '格式: xlsx, csv',

    -- 筛选条件 (JSON)
    filter_criteria JSON NOT NULL COMMENT '筛选条件',

    -- 状态
    status          VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态: pending, processing, completed, failed',
    progress        INT UNSIGNED DEFAULT 0 COMMENT '进度百分比 0-100',

    -- 结果
    total_records   INT UNSIGNED COMMENT '总记录数',
    file_path       VARCHAR(500) COMMENT '生成的文件路径',
    file_size       BIGINT UNSIGNED COMMENT '文件大小',
    error_message   TEXT COMMENT '错误信息',

    -- 时间
    started_at      DATETIME COMMENT '开始时间',
    completed_at    DATETIME COMMENT '完成时间',
    expires_at      DATETIME COMMENT '文件过期时间',

    -- 审计
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_status (status),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='数据导出任务表';
```

---

## 4. 现有模型扩展

### 4.1 NewsArticle 扩展

```sql
-- 新增字段
ALTER TABLE news_articles
ADD COLUMN content_text TEXT COMMENT '正文内容 (trafilatura提取)',
ADD COLUMN content_html TEXT COMMENT '正文HTML',
ADD COLUMN summary VARCHAR(500) COMMENT '摘要',
ADD COLUMN word_count INT UNSIGNED COMMENT '字数',
ADD COLUMN simhash CHAR(64) COMMENT 'SimHash内容指纹',
ADD INDEX idx_simhash (simhash);
```

### 4.2 Meilisearch 索引结构

```json
{
  "index": "news_articles",
  "primaryKey": "id",
  "searchableAttributes": [
    "title",
    "content_text",
    "summary"
  ],
  "filterableAttributes": [
    "source_key",
    "category",
    "published_at"
  ],
  "sortableAttributes": [
    "published_at",
    "scraped_at"
  ],
  "displayedAttributes": [
    "id",
    "title",
    "url",
    "source_key",
    "category",
    "summary",
    "published_at"
  ]
}
```

---

## 5. ER 关系图

```
┌──────────────────┐     ┌──────────────────┐
│   NewsSource     │────<│   NewsArticle    │
│   (新闻源)        │     │   (新闻文章)      │
└──────────────────┘     └──────────────────┘
         │
         │ 1:N
         ▼
┌──────────────────┐
│   ScraperRun     │
│   (爬虫执行)      │
└──────────────────┘

┌──────────────────┐     ┌──────────────────┐
│  SocialSession   │────<│  SocialMessage   │
│  (社交会话)       │ 1:N │  (社交消息)       │
└──────────────────┘     └──────────────────┘
                                  │
                                  │ self-ref
                                  ▼ (reply_to)

┌──────────────────┐     ┌──────────────────┐
│AccountCredential │     │   ProxyConfig    │
│   (账号凭证)      │     │   (代理配置)      │
└──────────────────┘     └──────────────────┘

┌──────────────────┐     ┌──────────────────┐
│   StorageFile    │     │   ExportTask     │
│   (存储文件)      │     │   (导出任务)      │
└──────────────────┘     └──────────────────┘
```

---

## 6. Alembic 迁移脚本

```python
# alembic/versions/20241214_002_social_models.py
"""Add social data models and system tables

Revision ID: 20241214_002
Revises: 20251208_001
Create Date: 2024-12-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '20241214_002'
down_revision = '20251208_001'

def upgrade() -> None:
    # 1. 创建 social_sessions 表
    op.create_table('social_sessions', ...)

    # 2. 创建 social_messages 表
    op.create_table('social_messages', ...)

    # 3. 创建 account_credentials 表
    op.create_table('account_credentials', ...)

    # 4. 创建 proxy_configs 表
    op.create_table('proxy_configs', ...)

    # 5. 创建 storage_files 表
    op.create_table('storage_files', ...)

    # 6. 创建 export_tasks 表
    op.create_table('export_tasks', ...)

    # 7. 扩展 news_articles 表
    op.add_column('news_articles', sa.Column('content_text', sa.Text))
    op.add_column('news_articles', sa.Column('simhash', sa.String(64)))
    op.create_index('idx_simhash', 'news_articles', ['simhash'])

def downgrade() -> None:
    op.drop_index('idx_simhash', 'news_articles')
    op.drop_column('news_articles', 'simhash')
    op.drop_column('news_articles', 'content_text')
    op.drop_table('export_tasks')
    op.drop_table('storage_files')
    op.drop_table('proxy_configs')
    op.drop_table('account_credentials')
    op.drop_table('social_messages')
    op.drop_table('social_sessions')
```
