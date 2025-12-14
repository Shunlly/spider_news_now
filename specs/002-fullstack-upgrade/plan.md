# Implementation Plan: 002-fullstack-upgrade

**Branch**: `002-fullstack-upgrade` | **Date**: 2025-12-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-fullstack-upgrade/spec.md`

---

## Summary

本计划实现爬虫系统的全栈升级，包括：
1. **多渠道扩展**: 新增 Twitter/Telegram 社交数据采集
2. **全文检索**: 集成 Meilisearch 实现毫秒级搜索
3. **管理后台**: Vue→React 迁移，实现 Glassmorphism 设计
4. **基础设施**: StorageProvider 适配器、Redis 去重、代理池

---

## Technical Context

**Backend**: Python 3.10+ (FastAPI), Pydantic v2, SQLAlchemy (Async)
**Frontend**: React (TypeScript) + Vite + Tailwind CSS + Arco Design
**Database**: MySQL 8.0+ (utf8mb4_unicode_ci)
**Search**: Meilisearch
**Object Storage**: MinIO / S3-compatible
**Cache**: Redis 7.x (Bloom Filter 去重)
**Testing**: pytest + pytest-asyncio (backend), Vitest + RTL (frontend)
**Project Type**: web (backend + frontend separation)
**Performance Goals**: API < 2s, Search < 500ms, Scraper < 60s per run
**Constraints**: 前端需从 Vue 3 迁移到 React
**Scale/Scope**: 10 万条数据规模，每日 1 万条新增

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Reference: `.specify/memory/constitution.md` v2.0.0 for complete requirements.

### Architecture Compliance (verify now)

- [x] Storage operations use StorageProvider adapter pattern (Section II.A)
- [x] Data models follow heterogeneous modeling rules (News vs Social) (Section II.B)
- [x] Deduplication mechanism planned (URL Hash / SimHash + Redis Bloom Filter) (Section II.C)

### UI/UX Compliance (verify for frontend features)

- [x] UI follows Glassmorphism theme (Section III.A)
- [x] Layout uses Bento Grid pattern (Section III.B)
- [x] Color scheme uses gradient backgrounds (Section III.C)

### Coding Standards (verify during development)

- [ ] Type Hints for all Python functions, TypeScript interfaces for frontend
- [ ] Core logic includes Chinese comments (especially scraper parsing, dedup)
- [ ] Error handling with retry mechanism for external APIs
- [ ] No placeholder code (pass, TODO) - complete implementations only
- [ ] Structured logging with context (scraper_id, article_count, execution_time)

---

## Part 1: Product & Design (产品与设计规划)

### 1.1 用户角色与流程 (User Flow)

#### 核心用户角色

| 角色 | 职责 | 主要操作 |
|------|------|----------|
| 运营人员 | 配置采集任务 | 添加数据源、配置账号、设置调度 |
| 数据分析师 | 检索和导出数据 | 搜索、筛选、导出 Excel/CSV |
| 系统管理员 | 维护系统运行 | 监控状态、配置代理、排查问题 |

#### 全链路用户操作流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           数据采集全链路流程                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. 配置阶段                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                  │
│  │ 添加数据源 │ → │ 配置凭证 │ → │ 设置代理 │ → │ 配置调度 │                  │
│  │ (新闻/社交)│    │ (API Key)│    │ (可选)   │    │ (cron)  │                  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘                  │
│                                                                             │
│  2. 采集阶段                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                  │
│  │ 定时触发 │ → │ 拉取数据 │ → │ 正文提取 │ → │ 去重检查 │                  │
│  │ /手动触发│    │ (爬虫执行)│    │(trafilat)│    │(BloomF) │                  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘                  │
│                                    │                │                       │
│                                    ▼                ▼                       │
│  3. 存储阶段                    ┌─────────┐    ┌─────────┐                  │
│                                 │ 媒体文件 │    │ 数据入库 │                  │
│                                 │ (MinIO) │    │ (MySQL) │                  │
│                                 └─────────┘    └─────────┘                  │
│                                                      │                       │
│  4. 索引阶段                                         ▼                       │
│                                              ┌─────────┐                    │
│                                              │ 索引更新 │                    │
│                                              │(Meilis) │                    │
│                                              └─────────┘                    │
│                                                      │                       │
│  5. 消费阶段                                         ▼                       │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                  │
│  │ 全文搜索 │ ← │ 数据列表 │ ← │ Dashboard│ ← │ 用户访问 │                  │
│  │ (毫秒级) │    │ (分页)   │    │ (统计)  │    │         │                  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘                  │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────┐                                                                │
│  │ 数据导出 │                                                                │
│  │(Excel/CSV)│                                                               │
│  └─────────┘                                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Twitter/TG 会话式渠道配置流程

```
┌─────────────────────────────────────────────────────────────────┐
│               Twitter/TG 配置流程                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: 选择平台                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  [Twitter] [Telegram]                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Step 2: 添加账号凭证                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Twitter: API Key + Secret + Access Token               │   │
│  │  Telegram: Bot Token 或 MTProto Session                 │   │
│  │  [测试连接] [保存]                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Step 3: 配置采集目标                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Twitter: @用户名 / #话题 / 关键词列表                     │   │
│  │  Telegram: 群组 ID / 频道 Username                       │   │
│  │  [添加目标] [移除]                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Step 4: 设置采集规则                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  采集频率: [每 30 分钟 ▼]                                 │   │
│  │  历史深度: [最近 7 天 ▼]                                  │   │
│  │  内容过滤: [包含媒体] [排除转发]                           │   │
│  │  [启用] [禁用]                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 1.2 界面原型定义 (UI Specification)

#### Dashboard 仪表盘布局 (Bento Grid)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [Logo] Spider News Now          [Search Bar 🔍]              [⚙️] [👤]    │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌───────┐                                                                   │
│ │ 导航栏 │                                                                   │
│ │──────│  ┌────────────────────────────────────────────────────────────┐  │
│ │ 📊 仪表盘│  │                    Bento Grid 主内容区                      │  │
│ │ 📰 新闻 │  │  ┌────────────────┐  ┌────────────────┐  ┌────────────┐   │  │
│ │ 💬 社交 │  │  │   今日采集量     │  │   数据总量      │  │  成功率    │   │  │
│ │ ⚙️ 配置 │  │  │   ┌─────────┐  │  │   ┌─────────┐  │  │  ┌─────┐  │   │  │
│ │ 📤 导出 │  │  │   │  12,345  │  │  │   │ 1.2M   │  │  │  │ 98% │  │   │  │
│ │ 📋 日志 │  │  │   └─────────┘  │  │   └─────────┘  │  │  └─────┘  │   │  │
│ │       │  │  │   +15% vs 昨日   │  │   新闻 80万    │  │  爬虫健康 │   │  │
│ │       │  │  └────────────────┘  └────────────────┘  └────────────┘   │  │
│ │       │  │                                                            │  │
│ │       │  │  ┌─────────────────────────────────┐  ┌─────────────────┐  │  │
│ │       │  │  │        采集趋势图 (7天)          │  │   来源分布      │  │  │
│ │       │  │  │  ┌──────────────────────────┐  │  │   [Pie Chart]  │  │  │
│ │       │  │  │  │      📈 Line Chart       │  │  │                │  │  │
│ │       │  │  │  │                          │  │  │   新浪 25%     │  │  │
│ │       │  │  │  └──────────────────────────┘  │  │   腾讯 20%     │  │  │
│ │       │  │  └─────────────────────────────────┘  │   Twitter 30% │  │  │
│ │       │  │                                       └─────────────────┘  │  │
│ │       │  │  ┌───────────────────────────────────────────────────────┐ │  │
│ │       │  │  │              实时日志 (最近 10 条)                     │ │  │
│ │       │  │  │  ┌───────────────────────────────────────────────┐   │ │  │
│ │       │  │  │  │ 16:30:01 [INFO] sina_scraper: 采集完成, 150 条  │   │ │  │
│ │       │  │  │  │ 16:25:03 [INFO] twitter_scraper: 采集中...     │   │ │  │
│ │       │  │  │  │ 16:20:00 [WARN] qq_scraper: 超时重试           │   │ │  │
│ │       │  │  │  └───────────────────────────────────────────────┘   │ │  │
│ │       │  │  └───────────────────────────────────────────────────────┘ │  │
│ └───────┘  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Glassmorphism 视觉规范

```tsx
// 卡片组件样式规范
const glassCardStyles = {
  // 毛玻璃核心效果
  backdropFilter: "blur(12px)",

  // 半透明背景
  background: "rgba(255, 255, 255, 0.4)", // 亮色模式
  // dark: "rgba(15, 23, 42, 0.4)",       // 暗色模式

  // 边框
  border: "1px solid rgba(255, 255, 255, 0.2)",

  // 阴影
  boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",

  // 圆角
  borderRadius: "1rem", // rounded-2xl
};

// Tailwind 类名
// bg-white/40 dark:bg-slate-900/40
// backdrop-blur-xl
// border border-white/20
// shadow-xl
// rounded-2xl
```

#### 页面背景规范

```css
/* 渐变背景 - 深蓝紫色调 */
.app-background {
  background: linear-gradient(
    to bottom right,
    #0f172a,      /* slate-900 */
    #581c87,      /* purple-900 */
    #0f172a       /* slate-900 */
  );
  min-height: 100vh;
}

/* Tailwind: bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 */
```

#### 核心页面组件清单

| 页面 | Arco Design 组件 | Tailwind 样式 |
|------|------------------|---------------|
| Dashboard | Card, Statistic, Progress | rounded-2xl, backdrop-blur-xl |
| 数据列表 | Table, Pagination, Input.Search | hover:bg-white/10 |
| 配置页 | Form, Input, Select, Switch | glass-card |
| 搜索结果 | List, Tag, Highlight | text-purple-400 |
| 导出页 | Steps, Progress, Button | btn-gradient |

---

### 1.3 功能验收标准 (Acceptance Criteria)

#### 全文搜索交互预期

| 场景 | 预期行为 | 响应时间 |
|------|----------|----------|
| 输入关键词 | 实时显示搜索建议 (Autocomplete) | < 100ms |
| 按下回车 | 执行搜索并显示结果 | < 500ms |
| 结果展示 | 关键词高亮 (`<em>` 标签) | - |
| 无结果 | 显示空状态提示 | - |
| 筛选切换 | 支持按来源/时间/类型筛选 | < 200ms |
| 分页 | 滚动加载更多 (Infinite Scroll) | < 300ms |

#### 数据导出性能预期

| 数据量 | 导出方式 | 预期时间 |
|--------|----------|----------|
| < 1万条 | 同步下载 | < 10秒 |
| 1万-10万条 | 异步任务 | < 2分钟 |
| > 10万条 | 分片导出 | < 5分钟 |

---

## Part 2: Technical Architecture (技术架构规划)

### 2.1 数据模型设计

详见 [data-model.md](./data-model.md)

**核心模型关系**:

```
NewsSource 1:N NewsArticle
SocialSession 1:N SocialMessage
SocialMessage N:1 SocialMessage (reply_to)
```

**新增表**:
- `social_sessions` - 社交会话
- `social_messages` - 社交消息
- `account_credentials` - 账号凭证
- `proxy_configs` - 代理配置
- `storage_files` - 存储文件
- `export_tasks` - 导出任务

### 2.2 去重与检索引擎

#### 去重架构

```
┌──────────────────────────────────────────────────────────────┐
│                      去重检查流程                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   新数据                                                      │
│     │                                                        │
│     ▼                                                        │
│   ┌────────────────┐     ┌────────────────┐                 │
│   │ URL Hash 计算   │────▶│ Bloom Filter   │                 │
│   │ SHA256(url)    │     │ (Redis)        │                 │
│   └────────────────┘     └───────┬────────┘                 │
│                                  │                           │
│                          存在?   │                           │
│                    ┌─────────────┼─────────────┐             │
│                    │ Yes         │ No          │             │
│                    ▼             ▼             │             │
│             ┌──────────┐   ┌──────────┐       │             │
│             │ 可能重复  │   │ 一定新增  │       │             │
│             │ (需确认)  │   │ 直接入库  │       │             │
│             └────┬─────┘   └──────────┘       │             │
│                  │                             │             │
│                  ▼                             │             │
│            ┌──────────┐                        │             │
│            │ DB 查询   │                        │             │
│            │ 二次确认  │                        │             │
│            └────┬─────┘                        │             │
│                 │                              │             │
│         ┌──────┴──────┐                        │             │
│         │ 真重复      │ 假阳性                  │             │
│         ▼             ▼                        │             │
│     [丢弃]        [入库]                       │             │
│                                                │             │
│   ┌────────────────────────────────────────────┘             │
│   │ 内容相似检测 (可选)                                       │
│   ▼                                                          │
│   ┌────────────────┐     ┌────────────────┐                 │
│   │ SimHash 计算   │────▶│ 汉明距离检测    │                 │
│   │ Simhash(text)  │     │ threshold=3   │                 │
│   └────────────────┘     └────────────────┘                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

#### 全文检索架构 (Meilisearch)

```
┌──────────────────────────────────────────────────────────────┐
│                     Meilisearch 索引架构                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   索引: news_articles                                        │
│   ┌────────────────────────────────────────────────────────┐ │
│   │ Primary Key: id                                        │ │
│   │                                                        │ │
│   │ Searchable:                                            │ │
│   │   - title (权重 1.0)                                   │ │
│   │   - content_text (权重 0.8)                            │ │
│   │   - summary (权重 0.6)                                 │ │
│   │                                                        │ │
│   │ Filterable:                                            │ │
│   │   - source_key                                         │ │
│   │   - category                                           │ │
│   │   - published_at (timestamp)                           │ │
│   │                                                        │ │
│   │ Sortable:                                              │ │
│   │   - published_at                                       │ │
│   │   - scraped_at                                         │ │
│   └────────────────────────────────────────────────────────┘ │
│                                                              │
│   索引: social_messages                                       │
│   ┌────────────────────────────────────────────────────────┐ │
│   │ Primary Key: id                                        │ │
│   │                                                        │ │
│   │ Searchable:                                            │ │
│   │   - content                                            │ │
│   │   - sender_name                                        │ │
│   │                                                        │ │
│   │ Filterable:                                            │ │
│   │   - platform                                           │ │
│   │   - session_id                                         │ │
│   │   - sender_id                                          │ │
│   │   - published_at                                       │ │
│   └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 2.3 存储适配器设计

```python
# backend/app/storage/provider.py

from typing import Protocol, Optional
from abc import ABC, abstractmethod

class StorageProvider(Protocol):
    """存储提供者接口 - 遵循宪法 II.A 适配器模式"""

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream"
    ) -> str:
        """上传文件，返回访问 URL"""
        ...

    async def download(self, key: str) -> bytes:
        """下载文件"""
        ...

    async def delete(self, key: str) -> bool:
        """删除文件"""
        ...

    async def exists(self, key: str) -> bool:
        """检查文件是否存在"""
        ...

    async def get_presigned_url(
        self,
        key: str,
        expires: int = 3600,
        method: str = "GET"
    ) -> str:
        """获取预签名 URL"""
        ...


# 实现类
class MinioStorage(StorageProvider):
    """MinIO / S3 兼容存储"""
    ...

class AliyunOSSStorage(StorageProvider):
    """阿里云 OSS 存储"""
    ...

class LocalStorage(StorageProvider):
    """本地文件存储 (开发/测试)"""
    ...


# 工厂函数
def get_storage_provider() -> StorageProvider:
    """根据配置返回对应的存储提供者"""
    backend = settings.STORAGE_BACKEND  # minio, s3, oss, local
    if backend == "minio":
        return MinioStorage(...)
    elif backend == "oss":
        return AliyunOSSStorage(...)
    else:
        return LocalStorage(...)
```

---

## Development Milestones (开发里程碑)

### Phase 0: 基础设施 (Infrastructure)

**目标**: 搭建升级所需的基础服务

| 任务 | 优先级 | 依赖 |
|------|--------|------|
| 更新 docker-compose.yml (添加 Redis, Meilisearch, MinIO) | P0 | 无 |
| 实现 StorageProvider 接口和 MinIO 适配器 | P0 | 无 |
| 实现 Redis Bloom Filter 去重服务 | P0 | 无 |
| 集成 Meilisearch 搜索服务 | P0 | 无 |
| 数据库迁移 (新增表) | P0 | 无 |

### Phase 1: 后端核心功能

**目标**: 实现社交数据采集和全文检索

| 任务 | 优先级 | 依赖 |
|------|--------|------|
| Twitter 爬虫实现 (API v2) | P1-US1 | Phase 0 |
| Telegram 爬虫实现 (Bot API) | P1-US1 | Phase 0 |
| 社交数据 API 端点 | P1-US1 | Twitter/TG 爬虫 |
| 全文检索 API 端点 | P1-US2 | Meilisearch |
| SimHash 内容指纹服务 | P1-US1 | 无 |
| 正文提取服务 (trafilatura) | P2-US6 | 无 |
| 账号凭证管理 API | P2-US4 | 无 |
| 代理池管理 API | P3-US8 | 无 |
| 数据导出服务 | P3-US7 | 无 |

### Phase 2: 前端重构 (Vue → React)

**目标**: 迁移前端框架并实现 Glassmorphism 设计

| 任务 | 优先级 | 依赖 |
|------|--------|------|
| 初始化 React + Vite 项目 | P1-US3 | 无 |
| Tailwind CSS + Arco Design 配置 | P1-US3 | React 项目 |
| Glassmorphism 组件库封装 | P1-US3 | Tailwind |
| Dashboard 页面 | P1-US3 | 组件库 |
| 数据列表页面 | P1-US3 | 组件库 |
| 搜索结果页面 | P1-US2 | 全文检索 API |
| 配置管理页面 | P2-US4/5 | 账号/代理 API |
| 导出功能页面 | P3-US7 | 导出 API |

### Phase 3: 集成测试与部署

**目标**: 确保系统稳定运行

| 任务 | 优先级 | 依赖 |
|------|--------|------|
| 后端单元测试补充 | P1 | Phase 1 |
| 前端组件测试 | P1 | Phase 2 |
| 集成测试 | P1 | Phase 1 + 2 |
| 性能测试 (搜索响应时间) | P1 | 全功能完成 |
| Dockerfile 优化 | P3-US9 | 全功能完成 |
| docker-compose 生产配置 | P3-US9 | Dockerfile |

---

## Project Structure

### Documentation (this feature)

```text
specs/002-fullstack-upgrade/
├── spec.md              # 功能规格
├── plan.md              # 本文件 - 实施计划
├── research.md          # 技术研究
├── data-model.md        # 数据模型设计
├── quickstart.md        # 快速启动指南
├── contracts/           # API 契约
│   ├── social-api.md    # 社交数据 API
│   └── system-api.md    # 系统管理 API
└── tasks.md             # 任务列表 (/speckit.tasks 生成)
```

### Source Code (repository root)

```text
# Web Application Structure (per Constitution v2.0.0)
backend/
├── app/
│   ├── api/v1/endpoints/
│   │   ├── news.py          # 已有
│   │   ├── scrapers.py      # 已有
│   │   ├── social.py        # 新增: 社交数据 API
│   │   ├── search.py        # 新增: 全文检索 API
│   │   ├── credentials.py   # 新增: 账号凭证 API
│   │   ├── proxies.py       # 新增: 代理池 API
│   │   ├── storage.py       # 新增: 存储管理 API
│   │   └── export.py        # 新增: 数据导出 API
│   ├── models/
│   │   ├── news_article.py  # 已有 (扩展)
│   │   ├── social.py        # 新增: SocialSession, SocialMessage
│   │   ├── credential.py    # 新增: AccountCredential
│   │   ├── proxy.py         # 新增: ProxyConfig
│   │   ├── storage.py       # 新增: StorageFile
│   │   └── export.py        # 新增: ExportTask
│   ├── schemas/
│   │   ├── social.py        # 新增
│   │   ├── search.py        # 新增
│   │   └── system.py        # 新增
│   ├── scrapers/
│   │   ├── base.py          # 已有
│   │   ├── twitter_scraper.py   # 新增
│   │   └── telegram_scraper.py  # 新增
│   ├── services/
│   │   ├── news_service.py      # 已有
│   │   ├── social_service.py    # 新增
│   │   ├── search_service.py    # 新增
│   │   ├── dedup_service.py     # 重构: 升级为 Bloom Filter + SimHash
│   │   ├── storage_service.py   # 新增
│   │   ├── credential_service.py # 新增
│   │   └── export_service.py    # 新增
│   └── storage/
│       ├── provider.py      # 新增: StorageProvider 接口
│       ├── minio.py         # 新增: MinIO 实现
│       ├── oss.py           # 新增: OSS 实现
│       └── local.py         # 新增: 本地存储
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

frontend/                    # 全新 React 项目
├── src/
│   ├── components/
│   │   ├── ui/              # Glassmorphism 组件库
│   │   │   ├── GlassCard.tsx
│   │   │   ├── GlassButton.tsx
│   │   │   └── GlassInput.tsx
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Header.tsx
│   │   ├── dashboard/
│   │   │   ├── StatsCard.tsx
│   │   │   ├── TrendChart.tsx
│   │   │   └── RealtimeLog.tsx
│   │   ├── news/
│   │   │   ├── ArticleCard.tsx
│   │   │   └── ArticleList.tsx
│   │   ├── social/
│   │   │   ├── SessionCard.tsx
│   │   │   ├── MessageList.tsx
│   │   │   └── ThreadView.tsx
│   │   └── search/
│   │       ├── SearchBar.tsx
│   │       ├── SearchResults.tsx
│   │       └── Highlight.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── NewsList.tsx
│   │   ├── SocialList.tsx
│   │   ├── Search.tsx
│   │   ├── Settings.tsx
│   │   └── Export.tsx
│   ├── hooks/
│   │   ├── useSearch.ts
│   │   ├── useSocial.ts
│   │   └── useExport.ts
│   ├── services/
│   │   └── api.ts
│   ├── stores/
│   │   └── index.ts
│   └── types/
│       └── index.ts
└── tests/
```

**Structure Decision**: Web application with backend/frontend separation per Constitution v2.0.0. 前端从 Vue 3 完全迁移到 React + TypeScript。

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 前端框架迁移 (Vue→React) | 宪法 v2.0.0 强制要求 React + Arco Design | 保留 Vue 违反宪法技术栈要求 |
| Redis 服务新增 | Bloom Filter 去重需要 Redis 支持 | 数据库去重性能不足 (O(n) vs O(1)) |
| Meilisearch 服务新增 | 全文检索需要专用搜索引擎 | MySQL LIKE 无法满足 500ms SLA |
