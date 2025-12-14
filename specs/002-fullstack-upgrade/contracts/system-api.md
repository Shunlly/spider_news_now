# API Contract: System Management API

**Version**: v1
**Base Path**: `/api/v1`
**Date**: 2025-12-14

---

## 1. 全文检索 (Search)

### 1.1 统一搜索

```http
GET /api/v1/search
```

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 是 | 搜索关键词 |
| type | string | 否 | 内容类型: news, social, all (默认: all) |
| source | string | 否 | 来源筛选 |
| start_date | datetime | 否 | 开始日期 |
| end_date | datetime | 否 | 结束日期 |
| page | int | 否 | 页码 (默认: 1) |
| page_size | int | 否 | 每页数量 (默认: 20, 最大: 100) |

**Response** (200 OK):

```json
{
  "query": "人工智能",
  "results": [
    {
      "type": "news",
      "id": 12345,
      "title": "人工智能发展趋势报告",
      "url": "https://...",
      "source": "sina",
      "category": "tech",
      "summary": "本报告分析了人工智能...",
      "published_at": "2024-12-14T10:00:00Z",
      "highlight": {
        "title": ["<em>人工智能</em>发展趋势报告"],
        "content": ["本报告分析了<em>人工智能</em>..."]
      },
      "score": 0.95
    },
    {
      "type": "social",
      "id": 67890,
      "platform": "twitter",
      "session_id": 1000,
      "sender_name": "TechExpert",
      "content": "人工智能正在改变...",
      "published_at": "2024-12-14T11:00:00Z",
      "highlight": {
        "content": ["<em>人工智能</em>正在改变..."]
      },
      "score": 0.88
    }
  ],
  "total": 156,
  "page": 1,
  "page_size": 20,
  "took_ms": 45,
  "facets": {
    "type": {
      "news": 100,
      "social": 56
    },
    "source": {
      "sina": 30,
      "qq": 25,
      "twitter": 40
    }
  }
}
```

### 1.2 搜索建议 (Autocomplete)

```http
GET /api/v1/search/suggest
```

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 是 | 输入前缀 |
| limit | int | 否 | 建议数量 (默认: 5) |

**Response** (200 OK):

```json
{
  "query": "人工",
  "suggestions": [
    "人工智能",
    "人工智能发展",
    "人工智能应用",
    "人工智能大模型"
  ]
}
```

---

## 2. 账号凭证管理 (Credentials)

### 2.1 获取凭证列表

```http
GET /api/v1/credentials
```

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platform | string | 否 | 平台筛选 |
| status | string | 否 | 状态筛选: active, rate_limited, expired, disabled |

**Response** (200 OK):

```json
{
  "items": [
    {
      "id": 1,
      "platform": "twitter",
      "account_name": "Twitter API Key #1",
      "credential_type": "api_key",
      "status": "active",
      "last_used_at": "2024-12-14T15:00:00Z",
      "request_count": 5000,
      "success_count": 4900,
      "failure_count": 100,
      "priority": 10
    }
  ],
  "total": 5
}
```

### 2.2 添加凭证

```http
POST /api/v1/credentials
```

**Request Body**:

```json
{
  "platform": "twitter",
  "account_name": "Twitter API Key #2",
  "credential_type": "api_key",
  "credential_data": {
    "api_key": "xxx",
    "api_secret": "xxx",
    "access_token": "xxx",
    "access_token_secret": "xxx"
  },
  "priority": 5
}
```

**Response** (201 Created):

```json
{
  "id": 2,
  "platform": "twitter",
  "account_name": "Twitter API Key #2",
  "credential_type": "api_key",
  "status": "active",
  "priority": 5,
  "created_at": "2024-12-14T16:00:00Z"
}
```

### 2.3 更新凭证状态

```http
PATCH /api/v1/credentials/{credential_id}
```

**Request Body**:

```json
{
  "status": "disabled",
  "priority": 0
}
```

### 2.4 删除凭证

```http
DELETE /api/v1/credentials/{credential_id}
```

**Response** (204 No Content)

### 2.5 测试凭证

```http
POST /api/v1/credentials/{credential_id}/test
```

**Response** (200 OK):

```json
{
  "success": true,
  "message": "凭证验证成功",
  "rate_limit": {
    "remaining": 450,
    "reset_at": "2024-12-14T16:15:00Z"
  }
}
```

---

## 3. 代理池管理 (Proxies)

### 3.1 获取代理列表

```http
GET /api/v1/proxies
```

**Response** (200 OK):

```json
{
  "items": [
    {
      "id": 1,
      "name": "Proxy #1",
      "protocol": "http",
      "host": "192.168.1.100",
      "port": 8080,
      "status": "active",
      "last_check_at": "2024-12-14T15:55:00Z",
      "response_time_ms": 150,
      "success_count": 1000,
      "failure_count": 5
    }
  ],
  "total": 10
}
```

### 3.2 添加代理

```http
POST /api/v1/proxies
```

**Request Body**:

```json
{
  "name": "Proxy #2",
  "protocol": "socks5",
  "host": "192.168.1.101",
  "port": 1080,
  "username": "user",
  "password": "pass",
  "bound_platforms": ["twitter", "telegram"]
}
```

### 3.3 健康检查

```http
POST /api/v1/proxies/{proxy_id}/check
```

**Response** (200 OK):

```json
{
  "success": true,
  "response_time_ms": 120,
  "external_ip": "1.2.3.4"
}
```

### 3.4 批量健康检查

```http
POST /api/v1/proxies/check-all
```

**Response** (200 OK):

```json
{
  "total": 10,
  "active": 8,
  "failed": 2,
  "results": [
    {"id": 1, "success": true, "response_time_ms": 150},
    {"id": 2, "success": false, "error": "Connection timeout"}
  ]
}
```

---

## 4. 存储管理 (Storage)

### 4.1 上传文件

```http
POST /api/v1/storage/upload
Content-Type: multipart/form-data
```

**Form Data**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 文件内容 |
| path | string | 否 | 存储路径前缀 |
| source_type | string | 否 | 来源类型 |
| source_id | int | 否 | 来源ID |

**Response** (201 Created):

```json
{
  "id": 12345,
  "storage_key": "media/uploads/2024/12/abc123.jpg",
  "url": "https://minio.example.com/bucket/media/uploads/2024/12/abc123.jpg",
  "mime_type": "image/jpeg",
  "file_size": 102400
}
```

### 4.2 获取文件信息

```http
GET /api/v1/storage/files/{file_id}
```

### 4.3 获取预签名 URL

```http
GET /api/v1/storage/files/{file_id}/presigned-url
```

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| expires | int | 否 | 过期时间(秒), 默认 3600 |

**Response** (200 OK):

```json
{
  "url": "https://minio.example.com/bucket/...?X-Amz-Signature=...",
  "expires_at": "2024-12-14T17:00:00Z"
}
```

---

## 5. 数据导出 (Export)

### 5.1 创建导出任务

```http
POST /api/v1/export
```

**Request Body**:

```json
{
  "export_type": "news",
  "export_format": "xlsx",
  "filter_criteria": {
    "source": ["sina", "qq"],
    "start_date": "2024-12-01",
    "end_date": "2024-12-14",
    "category": "tech"
  }
}
```

**Response** (202 Accepted):

```json
{
  "id": 100,
  "status": "pending",
  "export_type": "news",
  "export_format": "xlsx",
  "created_at": "2024-12-14T16:00:00Z"
}
```

### 5.2 获取导出任务状态

```http
GET /api/v1/export/{task_id}
```

**Response** (200 OK):

```json
{
  "id": 100,
  "status": "completed",
  "progress": 100,
  "total_records": 5000,
  "file_path": "/exports/news_20241214_160000.xlsx",
  "file_size": 1048576,
  "download_url": "/api/v1/export/100/download",
  "expires_at": "2024-12-15T16:00:00Z",
  "started_at": "2024-12-14T16:00:10Z",
  "completed_at": "2024-12-14T16:02:30Z"
}
```

### 5.3 下载导出文件

```http
GET /api/v1/export/{task_id}/download
```

**Response** (200 OK):

Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="news_20241214.xlsx"

### 5.4 获取导出历史

```http
GET /api/v1/export
```

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态筛选 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

---

## 6. 错误响应格式

所有 API 使用统一的错误响应格式:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": [
      {
        "field": "q",
        "message": "搜索关键词不能为空"
      }
    ]
  },
  "request_id": "abc123"
}
```

**常见错误码**:

| HTTP Status | Code | 说明 |
|-------------|------|------|
| 400 | VALIDATION_ERROR | 参数验证失败 |
| 401 | UNAUTHORIZED | 未授权 |
| 403 | FORBIDDEN | 禁止访问 |
| 404 | NOT_FOUND | 资源不存在 |
| 409 | CONFLICT | 资源冲突 |
| 429 | RATE_LIMITED | 请求过于频繁 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |
