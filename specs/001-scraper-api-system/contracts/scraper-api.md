# API Contracts: Scraper Management Endpoints

**Feature**: 001-scraper-api-system
**Version**: v1
**Base URL**: `/api/v1`

This document defines the RESTful API contracts for scraper management and monitoring operations.

---

## GET /api/v1/scrapers/status

Retrieve status of all scrapers.

### Request

**Example Request**:
```
GET /api/v1/scrapers/status
Host: localhost:8000
Accept: application/json
```

### Response

**Success (200 OK)**:

```json
{
  "scrapers": [
    {
      "source_key": "sina",
      "source_name": "新浪新闻",
      "enabled": true,
      "status": "idle",
      "last_run": {
        "started_at": "2025-12-08T10:00:00Z",
        "completed_at": "2025-12-08T10:00:45Z",
        "status": "success",
        "articles_scraped": 120,
        "articles_new": 85,
        "articles_duplicate": 35,
        "duration_seconds": 45
      },
      "next_run_at": "2025-12-08T10:30:00Z",
      "failure_count": 0
    },
    {
      "source_key": "qq",
      "source_name": "腾讯新闻",
      "enabled": true,
      "status": "running",
      "current_run": {
        "started_at": "2025-12-08T10:30:00Z",
        "status": "running",
        "duration_seconds": 15
      },
      "next_run_at": null,
      "failure_count": 0
    }
  ],
  "total_scrapers": 6,
  "active_runs": 1
}
```

---

## GET /api/v1/scrapers/{source_key}/runs

Retrieve execution history for a specific scraper.

### Request

**Path Parameters**:
- `source_key` (string, required): Source identifier (sina, qq, etc.)

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | string | No | - | Filter by status (success, failed, timeout) |
| `limit` | integer | No | 50 | Number of runs to return (max 500) |
| `offset` | integer | No | 0 | Pagination offset |

**Example Request**:
```
GET /api/v1/scrapers/sina/runs?status=failed&limit=10
Host: localhost:8000
Accept: application/json
```

### Response

**Success (200 OK)**:

```json
{
  "runs": [
    {
      "id": 9876,
      "source_key": "sina",
      "started_at": "2025-12-08T09:30:00Z",
      "completed_at": "2025-12-08T09:30:50Z",
      "status": "failed",
      "articles_scraped": 0,
      "articles_new": 0,
      "articles_duplicate": 0,
      "duration_seconds": 50,
      "error_message": "Connection timeout after 3 retries",
      "error_type": "HTTPTimeoutError"
    },
    {
      "id": 9875,
      "source_key": "sina",
      "started_at": "2025-12-08T09:00:00Z",
      "completed_at": "2025-12-08T09:00:45Z",
      "status": "success",
      "articles_scraped": 120,
      "articles_new": 85,
      "articles_duplicate": 35,
      "duration_seconds": 45,
      "error_message": null
    }
  ],
  "total": 250,
  "page": 1,
  "page_size": 10
}
```

---

## POST /api/v1/scrapers/{source_key}/trigger

Manually trigger a scraper execution (for testing/admin use).

### Request

**Path Parameters**:
- `source_key` (string, required): Source identifier

**Request Body**: None required

**Example Request**:
```
POST /api/v1/scrapers/sina/trigger
Host: localhost:8000
Content-Type: application/json
```

### Response

**Success (202 Accepted)**:

```json
{
  "message": "Scraper triggered successfully",
  "run_id": 9877,
  "source_key": "sina",
  "started_at": "2025-12-08T10:35:12Z",
  "status": "running"
}
```

**Error Responses**:

| Status Code | Condition | Response Body |
|-------------|-----------|---------------|
| 404 Not Found | Source not found | `{"detail": "Source 'invalid_source' not found"}` |
| 409 Conflict | Scraper already running | `{"detail": "Scraper for 'sina' is already running"}` |
| 503 Service Unavailable | Too many scrapers running | `{"detail": "Maximum concurrent scrapers reached (6/6)"}` |

---

## PUT /api/v1/scrapers/{source_key}/enable

Enable a disabled scraper.

### Request

**Path Parameters**:
- `source_key` (string, required): Source identifier

**Example Request**:
```
PUT /api/v1/scrapers/sina/enable
Host: localhost:8000
```

### Response

**Success (200 OK)**:

```json
{
  "message": "Scraper enabled successfully",
  "source_key": "sina",
  "enabled": true,
  "next_run_at": "2025-12-08T11:00:00Z"
}
```

---

## PUT /api/v1/scrapers/{source_key}/disable

Disable a scraper (stops future scheduled runs, does not stop current run).

### Request

**Path Parameters**:
- `source_key` (string, required): Source identifier

**Example Request**:
```
PUT /api/v1/scrapers/sina/disable
Host: localhost:8000
```

### Response

**Success (200 OK)**:

```json
{
  "message": "Scraper disabled successfully",
  "source_key": "sina",
  "enabled": false,
  "current_run_status": "running (will complete, future runs cancelled)"
}
```

---

## PUT /api/v1/scrapers/{source_key}/config

Update scraper configuration (schedule interval).

### Request

**Path Parameters**:
- `source_key` (string, required): Source identifier

**Request Body**:

```json
{
  "schedule_interval": 3600
}
```

**Validation**:
- `schedule_interval`: Must be >= 60 seconds (minimum 1 minute)

**Example Request**:
```
PUT /api/v1/scrapers/sina/config
Host: localhost:8000
Content-Type: application/json

{
  "schedule_interval": 3600
}
```

### Response

**Success (200 OK)**:

```json
{
  "message": "Configuration updated successfully",
  "source_key": "sina",
  "schedule_interval": 3600,
  "next_run_at": "2025-12-08T11:35:12Z"
}
```

**Error Responses**:

| Status Code | Condition | Response Body |
|-------------|-----------|---------------|
| 400 Bad Request | Invalid interval | `{"detail": "schedule_interval must be >= 60 seconds"}` |

---

## GET /api/v1/scrapers/{source_key}/logs

Retrieve recent log entries for a specific scraper run.

### Request

**Path Parameters**:
- `source_key` (string, required): Source identifier

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `run_id` | integer | No | Latest | Specific run ID to get logs for |
| `level` | string | No | - | Filter by log level (DEBUG, INFO, WARNING, ERROR) |
| `limit` | integer | No | 100 | Number of log entries (max 1000) |

**Example Request**:
```
GET /api/v1/scrapers/sina/logs?run_id=9876&level=ERROR
Host: localhost:8000
Accept: application/json
```

### Response

**Success (200 OK)**:

```json
{
  "run_id": 9876,
  "source_key": "sina",
  "logs": [
    {
      "timestamp": "2025-12-08T09:30:15Z",
      "level": "ERROR",
      "message": "Failed to fetch articles from https://news.sina.com.cn",
      "context": {
        "url": "https://news.sina.com.cn",
        "attempt": 3,
        "error_type": "HTTPTimeoutError"
      }
    },
    {
      "timestamp": "2025-12-08T09:30:10Z",
      "level": "WARNING",
      "message": "Retry attempt 2 of 3 after timeout",
      "context": {
        "backoff_seconds": 4
      }
    }
  ],
  "total_logs": 25
}
```

---

## GET /api/v1/health

Health check endpoint for monitoring.

### Request

**Example Request**:
```
GET /api/v1/health
Host: localhost:8000
Accept: application/json
```

### Response

**Success (200 OK)**:

```json
{
  "status": "healthy",
  "timestamp": "2025-12-08T10:35:12Z",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "up",
      "response_time_ms": 5
    },
    "scheduler": {
      "status": "up",
      "active_jobs": 6
    },
    "scrapers": {
      "total": 6,
      "running": 1,
      "failed": 0
    }
  }
}
```

**Degraded (200 OK with warnings)**:

```json
{
  "status": "degraded",
  "timestamp": "2025-12-08T10:35:12Z",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "up",
      "response_time_ms": 5
    },
    "scheduler": {
      "status": "up",
      "active_jobs": 6
    },
    "scrapers": {
      "total": 6,
      "running": 0,
      "failed": 2,
      "warnings": ["sina: 3 consecutive failures", "qq: last run failed"]
    }
  }
}
```

**Unhealthy (503 Service Unavailable)**:

```json
{
  "status": "unhealthy",
  "timestamp": "2025-12-08T10:35:12Z",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "down",
      "error": "Connection refused"
    },
    "scheduler": {
      "status": "unknown"
    },
    "scrapers": {
      "status": "unknown"
    }
  }
}
```

---

## Response Models

### ScraperStatusResponse

```json
{
  "source_key": "string",
  "source_name": "string",
  "enabled": "boolean",
  "status": "string (idle|running|failed|disabled)",
  "last_run": "RunSummary | null",
  "current_run": "RunSummary | null",
  "next_run_at": "string (ISO 8601) | null",
  "failure_count": "integer"
}
```

### RunSummary

```json
{
  "started_at": "string (ISO 8601)",
  "completed_at": "string (ISO 8601) | null",
  "status": "string (running|success|failed|timeout)",
  "articles_scraped": "integer",
  "articles_new": "integer",
  "articles_duplicate": "integer",
  "duration_seconds": "integer | null"
}
```

### ScraperRunResponse

Extends `RunSummary` with:

```json
{
  "id": "integer",
  "source_key": "string",
  "error_message": "string | null",
  "error_type": "string | null"
}
```

---

## WebSocket: Real-time Scraper Updates

### Connection

```
WS /api/v1/scrapers/ws
Host: localhost:8000
```

### Messages

**Server → Client (scraper status updates)**:

```json
{
  "event": "scraper_started",
  "timestamp": "2025-12-08T10:35:12Z",
  "data": {
    "source_key": "sina",
    "run_id": 9877
  }
}
```

```json
{
  "event": "scraper_completed",
  "timestamp": "2025-12-08T10:36:00Z",
  "data": {
    "source_key": "sina",
    "run_id": 9877,
    "status": "success",
    "articles_scraped": 120,
    "articles_new": 85,
    "duration_seconds": 48
  }
}
```

```json
{
  "event": "scraper_failed",
  "timestamp": "2025-12-08T10:36:00Z",
  "data": {
    "source_key": "qq",
    "run_id": 9878,
    "error_message": "Connection timeout",
    "error_type": "HTTPTimeoutError"
  }
}
```

**Client → Server (subscribe to specific sources)**:

```json
{
  "action": "subscribe",
  "sources": ["sina", "qq"]
}
```

**Client → Server (unsubscribe)**:

```json
{
  "action": "unsubscribe",
  "sources": ["sina"]
}
```
