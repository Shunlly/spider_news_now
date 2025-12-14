# API Contract: Social Data API

**Version**: v1
**Base Path**: `/api/v1/social`
**Date**: 2025-12-14

---

## 1. 会话管理 (Sessions)

### 1.1 获取会话列表

```http
GET /api/v1/social/sessions
```

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platform | string | 否 | 平台筛选: twitter, telegram |
| session_type | string | 否 | 类型筛选: thread, topic, group_chat |
| source_group_id | string | 否 | 群组/用户ID筛选 |
| start_date | datetime | 否 | 开始日期 |
| end_date | datetime | 否 | 结束日期 |
| page | int | 否 | 页码 (默认: 1) |
| page_size | int | 否 | 每页数量 (默认: 20, 最大: 100) |
| sort_by | string | 否 | 排序字段: last_message_at, message_count, created_at |
| sort_order | string | 否 | 排序方向: asc, desc |

**Response** (200 OK):

```json
{
  "items": [
    {
      "id": 12345,
      "platform": "twitter",
      "external_id": "1234567890",
      "title": "关于 AI 发展趋势的讨论",
      "session_type": "thread",
      "source_group_id": "elonmusk",
      "source_group_name": "Elon Musk",
      "message_count": 42,
      "participant_count": 15,
      "first_message_at": "2024-12-14T10:00:00Z",
      "last_message_at": "2024-12-14T15:30:00Z",
      "created_at": "2024-12-14T10:05:00Z"
    }
  ],
  "total": 156,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### 1.2 获取会话详情

```http
GET /api/v1/social/sessions/{session_id}
```

**Response** (200 OK):

```json
{
  "id": 12345,
  "platform": "twitter",
  "external_id": "1234567890",
  "title": "关于 AI 发展趋势的讨论",
  "description": "...",
  "session_type": "thread",
  "source_group_id": "elonmusk",
  "source_group_name": "Elon Musk",
  "message_count": 42,
  "participant_count": 15,
  "participants": ["user1", "user2", "user3"],
  "first_message_at": "2024-12-14T10:00:00Z",
  "last_message_at": "2024-12-14T15:30:00Z",
  "created_at": "2024-12-14T10:05:00Z",
  "updated_at": "2024-12-14T15:35:00Z"
}
```

### 1.3 获取会话消息列表

```http
GET /api/v1/social/sessions/{session_id}/messages
```

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 (默认: 1) |
| page_size | int | 否 | 每页数量 (默认: 50) |
| sort_order | string | 否 | 时间排序: asc (旧→新), desc (新→旧) |

**Response** (200 OK):

```json
{
  "session_id": 12345,
  "items": [
    {
      "id": 100001,
      "external_id": "tweet_123",
      "sender_id": "elonmusk",
      "sender_name": "Elon Musk",
      "sender_handle": "@elonmusk",
      "content": "AI 正在改变一切...",
      "content_type": "text",
      "reply_to_id": null,
      "media_attachments": [
        {
          "type": "image",
          "url": "https://...",
          "storage_key": "media/twitter/..."
        }
      ],
      "like_count": 50000,
      "repost_count": 10000,
      "reply_count": 5000,
      "published_at": "2024-12-14T10:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 50
}
```

---

## 2. 消息管理 (Messages)

### 2.1 搜索消息

```http
GET /api/v1/social/messages/search
```

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 是 | 搜索关键词 |
| platform | string | 否 | 平台筛选 |
| sender_id | string | 否 | 发送者筛选 |
| start_date | datetime | 否 | 开始日期 |
| end_date | datetime | 否 | 结束日期 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**Response** (200 OK):

```json
{
  "query": "AI",
  "items": [
    {
      "id": 100001,
      "session_id": 12345,
      "platform": "twitter",
      "sender_name": "Elon Musk",
      "content": "AI 正在改变一切...",
      "published_at": "2024-12-14T10:00:00Z",
      "highlight": {
        "content": ["<em>AI</em> 正在改变一切..."]
      }
    }
  ],
  "total": 100,
  "took_ms": 15
}
```

### 2.2 获取消息详情

```http
GET /api/v1/social/messages/{message_id}
```

**Response** (200 OK):

```json
{
  "id": 100001,
  "session_id": 12345,
  "platform": "twitter",
  "external_id": "tweet_123",
  "sender_id": "elonmusk",
  "sender_name": "Elon Musk",
  "sender_handle": "@elonmusk",
  "content": "AI 正在改变一切...",
  "content_type": "text",
  "reply_to_id": null,
  "reply_to_external": null,
  "media_attachments": [],
  "like_count": 50000,
  "repost_count": 10000,
  "reply_count": 5000,
  "published_at": "2024-12-14T10:00:00Z",
  "scraped_at": "2024-12-14T10:05:00Z",
  "replies": [
    {
      "id": 100002,
      "sender_name": "User1",
      "content": "完全同意!",
      "published_at": "2024-12-14T10:01:00Z"
    }
  ]
}
```

---

## 3. 统计接口

### 3.1 获取社交数据统计

```http
GET /api/v1/social/statistics
```

**Response** (200 OK):

```json
{
  "total_sessions": 1560,
  "total_messages": 45000,
  "by_platform": {
    "twitter": {
      "sessions": 800,
      "messages": 25000
    },
    "telegram": {
      "sessions": 760,
      "messages": 20000
    }
  },
  "today": {
    "new_sessions": 50,
    "new_messages": 1200
  },
  "last_updated_at": "2024-12-14T16:00:00Z"
}
```

---

## 4. Pydantic Schemas

```python
# backend/app/schemas/social.py

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class MediaAttachment(BaseModel):
    type: str  # image, video, document
    url: str
    storage_key: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None  # 视频时长(秒)

class SocialMessageBase(BaseModel):
    platform: str
    external_id: str
    sender_id: str
    sender_name: Optional[str] = None
    sender_handle: Optional[str] = None
    content: Optional[str] = None
    content_type: str = "text"
    media_attachments: List[MediaAttachment] = []
    like_count: int = 0
    repost_count: int = 0
    reply_count: int = 0
    published_at: datetime

class SocialMessageResponse(SocialMessageBase):
    id: int
    session_id: int
    reply_to_id: Optional[int] = None
    scraped_at: datetime

    class Config:
        from_attributes = True

class SocialSessionBase(BaseModel):
    platform: str
    external_id: str
    title: Optional[str] = None
    session_type: str
    source_group_id: Optional[str] = None
    source_group_name: Optional[str] = None

class SocialSessionResponse(SocialSessionBase):
    id: int
    message_count: int = 0
    participant_count: int = 0
    first_message_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SocialSessionDetail(SocialSessionResponse):
    description: Optional[str] = None
    participants: List[str] = []
    updated_at: datetime

class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int
```
