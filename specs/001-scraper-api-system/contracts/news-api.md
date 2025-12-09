# API Contracts: News Endpoints

**Feature**: 001-scraper-api-system
**Version**: v1
**Base URL**: `/api/v1`

This document defines the RESTful API contracts for news article operations.

---

## GET /api/v1/news/articles

Retrieve news articles with optional filtering, sorting, and pagination.

### Request

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `source` | string | No | - | Filter by source key (sina, qq, wangyi, etc.) |
| `category` | string | No | - | Filter by category (ent, china, world, finance, etc.) |
| `start_date` | string (ISO 8601) | No | - | Filter articles published after this date |
| `end_date` | string (ISO 8601) | No | - | Filter articles published before this date |
| `search` | string | No | - | Search in article titles (partial match) |
| `page` | integer | No | 1 | Page number (1-indexed) |
| `page_size` | integer | No | 50 | Items per page (max 1000) |
| `sort_by` | string | No | `published_at` | Sort field: `published_at`, `scraped_at`, `title` |
| `sort_order` | string | No | `desc` | Sort order: `asc` or `desc` |

**Example Request**:
```
GET /api/v1/news/articles?source=sina&category=ent&page=1&page_size=50
Host: localhost:8000
Accept: application/json
```

### Response

**Success (200 OK)**:

```json
{
  "data": [
    {
      "id": 12345,
      "url": "https://ent.sina.com.cn/example-article",
      "title": "娱乐新闻标题示例",
      "source_key": "sina",
      "category": "ent",
      "published_at": "2025-12-08T10:30:00Z",
      "scraped_at": "2025-12-08T10:35:12Z"
    },
    {
      "id": 12344,
      "url": "https://ent.sina.com.cn/another-article",
      "title": "另一篇娱乐新闻",
      "source_key": "sina",
      "category": "ent",
      "published_at": "2025-12-08T09:45:00Z",
      "scraped_at": "2025-12-08T10:35:12Z"
    }
  ],
  "pagination": {
    "total": 1234,
    "page": 1,
    "page_size": 50,
    "total_pages": 25
  },
  "filters_applied": {
    "source": "sina",
    "category": "ent"
  }
}
```

**Error Responses**:

| Status Code | Condition | Response Body |
|-------------|-----------|---------------|
| 400 Bad Request | Invalid query parameters | `{"detail": "Invalid page_size: must be between 1 and 1000"}` |
| 422 Unprocessable Entity | Invalid date format | `{"detail": "start_date must be ISO 8601 format"}` |
| 500 Internal Server Error | Database error | `{"detail": "Internal server error"}` |

---

## GET /api/v1/news/articles/{article_id}

Retrieve a single news article by ID.

### Request

**Path Parameters**:
- `article_id` (integer, required): Article unique identifier

**Example Request**:
```
GET /api/v1/news/articles/12345
Host: localhost:8000
Accept: application/json
```

### Response

**Success (200 OK)**:

```json
{
  "id": 12345,
  "url": "https://ent.sina.com.cn/example-article",
  "title": "娱乐新闻标题示例",
  "source_key": "sina",
  "category": "ent",
  "published_at": "2025-12-08T10:30:00Z",
  "scraped_at": "2025-12-08T10:35:12Z",
  "created_at": "2025-12-08T10:35:12Z",
  "url_hash": "abc123...def456"
}
```

**Error Responses**:

| Status Code | Condition | Response Body |
|-------------|-----------|---------------|
| 404 Not Found | Article not found | `{"detail": "Article with id 12345 not found"}` |

---

## GET /api/v1/news/articles/grouped

Retrieve news articles grouped by source for display.

### Request

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `category` | string | No | - | Filter by category |
| `start_date` | string (ISO 8601) | No | 24h ago | Articles published after this date |
| `limit_per_source` | integer | No | 10 | Max articles per source (max 100) |

**Example Request**:
```
GET /api/v1/news/articles/grouped?category=ent&limit_per_source=10
Host: localhost:8000
Accept: application/json
```

### Response

**Success (200 OK)**:

```json
{
  "groups": [
    {
      "source_key": "sina",
      "source_name": "新浪新闻",
      "article_count": 10,
      "articles": [
        {
          "id": 12345,
          "url": "https://ent.sina.com.cn/example",
          "title": "娱乐新闻标题",
          "category": "ent",
          "published_at": "2025-12-08T10:30:00Z"
        }
        // ... 9 more articles
      ]
    },
    {
      "source_key": "qq",
      "source_name": "腾讯新闻",
      "article_count": 10,
      "articles": [
        // ... articles from QQ
      ]
    }
    // ... more sources
  ],
  "total_sources": 6,
  "filters_applied": {
    "category": "ent"
  }
}
```

---

## GET /api/v1/news/sources

Retrieve list of all news sources.

### Request

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `enabled_only` | boolean | No | false | Return only enabled sources |

**Example Request**:
```
GET /api/v1/news/sources?enabled_only=true
Host: localhost:8000
Accept: application/json
```

### Response

**Success (200 OK)**:

```json
{
  "sources": [
    {
      "id": 1,
      "source_key": "sina",
      "display_name": "新浪新闻",
      "enabled": true,
      "status": "idle",
      "last_run_at": "2025-12-08T10:00:00Z",
      "last_success_at": "2025-12-08T10:00:00Z",
      "failure_count": 0,
      "schedule_interval": 1800
    },
    {
      "id": 2,
      "source_key": "qq",
      "display_name": "腾讯新闻",
      "enabled": true,
      "status": "running",
      "last_run_at": "2025-12-08T10:30:00Z",
      "last_success_at": "2025-12-08T10:00:00Z",
      "failure_count": 0,
      "schedule_interval": 1800
    }
  ],
  "total": 6
}
```

---

## GET /api/v1/news/statistics

Retrieve aggregated statistics about news collection.

### Request

**Example Request**:
```
GET /api/v1/news/statistics
Host: localhost:8000
Accept: application/json
```

### Response

**Success (200 OK)**:

```json
{
  "total_articles": 12450,
  "articles_today": 345,
  "sources_active": 6,
  "sources_failed": 0,
  "last_scrape_time": "2025-12-08T10:30:00Z",
  "by_source": [
    {
      "source_key": "sina",
      "source_name": "新浪新闻",
      "article_count": 2100,
      "last_scraped": "2025-12-08T10:30:00Z"
    }
    // ... more sources
  ],
  "by_category": [
    {
      "category": "ent",
      "article_count": 3200
    },
    {
      "category": "china",
      "article_count": 2800
    }
    // ... more categories
  ]
}
```

---

## Response Models

### ArticleResponse

```json
{
  "id": "integer",
  "url": "string (URL)",
  "title": "string (1-255 chars)",
  "source_key": "string (lowercase alphanumeric)",
  "category": "string | null",
  "published_at": "string (ISO 8601 datetime)",
  "scraped_at": "string (ISO 8601 datetime)"
}
```

### ArticleDetailResponse

Extends `ArticleResponse` with:

```json
{
  "created_at": "string (ISO 8601 datetime)",
  "url_hash": "string (64 char hex)"
}
```

### SourceResponse

```json
{
  "id": "integer",
  "source_key": "string",
  "display_name": "string",
  "enabled": "boolean",
  "status": "string (idle|running|failed|disabled)",
  "last_run_at": "string (ISO 8601 datetime) | null",
  "last_success_at": "string (ISO 8601 datetime) | null",
  "failure_count": "integer",
  "schedule_interval": "integer (seconds)"
}
```

---

## Error Response Format

All error responses follow this format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "timestamp": "2025-12-08T10:35:12Z"
}
```

**Common Error Codes**:
- `VALIDATION_ERROR`: Invalid request parameters
- `NOT_FOUND`: Resource not found
- `INTERNAL_ERROR`: Server error
- `DATABASE_ERROR`: Database operation failed

---

## Rate Limiting

- **Rate Limit**: 100 requests per minute per IP
- **Headers**:
  - `X-RateLimit-Limit`: Maximum requests per window
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Unix timestamp when window resets

**Rate Limit Exceeded Response (429 Too Many Requests)**:

```json
{
  "detail": "Rate limit exceeded. Try again in 30 seconds.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 30
}
```

---

## CORS Configuration

- **Allowed Origins**: Configurable via environment variable
- **Allowed Methods**: GET, POST, PUT, DELETE, OPTIONS
- **Allowed Headers**: Content-Type, Authorization
- **Exposed Headers**: X-RateLimit-*, X-Total-Count
