# Implementation Plan: 全栈爬虫 SaaS 平台

**Branch**: `004-scraper-saas-platform` | **Date**: 2025-12-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-scraper-saas-platform/spec.md`

## Summary

构建一个多租户爬虫 SaaS 平台，支持新闻站点和社交媒体（Twitter/Telegram）的内容采集。核心功能包括：
- **用户认证**: 邮箱注册 + 滑块验证码（Aura 深色主题适配）
- **多租户隔离**: RBAC 权限模型，租户间数据完全隔离
- **配额管理**: 按用户等级限制每日采集量和并发任务数
- **数据采集**: 新闻站点（trafilatura）+ 社交媒体会话流（Thread/Session 结构）
- **数据治理**: URL Hash + SimHash 双重去重，Meilisearch 全文检索
- **HUD Dashboard**: Aura 风格实时监控面板，WebSocket 推送
- **可观测性**: Celery 任务监控、审计日志、结构化日志

## Technical Context

<!--
  Per Constitution v3.0.0: Tech stack is mandated. Only fill in feature-specific details.
  Reference: .specify/memory/constitution.md Section III. 技术栈强制
-->

**Backend**: Python 3.10+ (FastAPI), SQLAlchemy (Async), Redis, Celery
**Frontend**: React (TypeScript) + Vite + Tailwind CSS + Framer Motion
**UI Library**: Shadcn/UI (recommended) with Aura dark theme customization
**Database**: MySQL 8.0+ (utf8mb4_unicode_ci)
**Search**: Meilisearch (轻量级全文检索)
**Object Storage**: MinIO / S3-compatible (通过 StorageProvider 适配器)
**Message Queue**: Redis (Celery broker) + RabbitMQ (可选 DLQ)
**Testing**: Pytest (backend), Playwright (frontend E2E)
**Project Type**: web (backend + frontend separation)
**Performance Goals**: API < 2s (1000 results), Scraper < 60s per run
**Constraints**: 多租户数据隔离，配额限制，滑块验证码防护
**Scale/Scope**: 1000 并发采集任务，10万+ 数据量全文检索

### Feature-Specific Technologies

| 功能模块 | 技术选型 | 说明 |
|---------|---------|------|
| 新闻正文提取 | trafilatura | 高准确率正文提取库 |
| 内容去重 | Redis Bloom Filter + SimHash | URL 去重 + 内容相似度检测 |
| 滑块验证码 | 自研前端组件 | Aura 深色主题适配 |
| 实时推送 | WebSocket (FastAPI) | Dashboard 数据实时更新 |
| 图表渲染 | Recharts | 深色系数据可视化 |
| 日志系统 | Loguru | 结构化日志输出 |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Reference: `.specify/memory/constitution.md` v3.0.0 for complete requirements.

### I. 视觉设计规范 (Aura Design System) - verify for frontend features

- [x] UI follows Aura theme: Immersive Dark + Precision Borders + Subtle Glow (Section I.A)
- [x] Background uses deep gray/black (`bg-[#09090b]` or `bg-[#0F1117]`) - no pure black (Section I.B)
- [x] NO glassmorphism (`backdrop-filter: blur()`) or semi-transparent backgrounds (Section I.B)
- [x] Typography uses Inter (UI) or JetBrains Mono (data display) (Section I.C)

**设计决策**:
- HUD Dashboard 采用 `bg-[#0F1117]` 极深灰背景
- 卡片边框使用 `border border-white/10`，hover 态渐变边框
- 图表使用霓虹紫/电光蓝渐变强调色
- 数据展示区域使用 JetBrains Mono 字体

### II. 角色职责 (Roles & Responsibilities) - verify compliance

- [x] Architect: Storage uses Adapter pattern (StorageProvider interface) (Section II.A)
- [x] Architect: High-concurrency tasks use Celery (Section II.A)
- [x] QA: Core business logic has pytest unit tests (Section II.B)
- [x] QA: API endpoints have integration tests (Section II.B)
- [x] DevOps: Docker deployment solution provided (Section II.C)
- [x] DevOps: Health check endpoint (`/health`) provided (Section II.C)

### III. Architecture Compliance (verify now)

- [x] Storage operations use StorageProvider adapter pattern (Architecture Principles A)
- [x] Data models follow heterogeneous modeling rules (News vs Social) (Architecture Principles B)
- [x] Deduplication mechanism planned (URL Hash / SimHash) (Architecture Principles C)

### IV. 编码红线 (Coding Standards) - verify during development

- [x] No placeholder code (`pass`, `TODO`) - complete implementations only (Section IV.A)
- [x] Database changes have Alembic Migration scripts (Section IV.B)
- [x] Type Hints for all Python functions, TypeScript interfaces for frontend (Section IV.C)
- [x] Core logic includes Chinese comments (especially scraper parsing, dedup) (Section IV.D)

## Project Structure

### Documentation (this feature)

```text
specs/004-scraper-saas-platform/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── api-v1.yaml      # OpenAPI 3.0 规范
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Web Application Structure (per Constitution v3.0.0)
backend/
├── app/
│   ├── api/v1/
│   │   ├── auth.py          # 认证端点（登录/注册/验证码）
│   │   ├── users.py         # 用户管理
│   │   ├── tenants.py       # 租户管理
│   │   ├── tasks.py         # 采集任务 CRUD
│   │   ├── news.py          # 新闻数据查询/导出
│   │   ├── social.py        # 社交媒体数据查询
│   │   ├── search.py        # 全文检索
│   │   ├── dashboard.py     # Dashboard 统计数据
│   │   ├── audit.py         # 审计日志
│   │   └── health.py        # 健康检查
│   ├── core/
│   │   ├── config.py        # 配置管理（环境变量）
│   │   ├── security.py      # JWT/密码哈希/RBAC
│   │   └── captcha.py       # 滑块验证码逻辑
│   ├── db/
│   │   └── session.py       # 异步数据库会话
│   ├── models/
│   │   ├── user.py          # User, Role, Tenant
│   │   ├── task.py          # ScrapingTask
│   │   ├── news.py          # NewsArticle
│   │   ├── social.py        # SocialSession, SocialMessage
│   │   ├── quota.py         # Quota
│   │   └── audit.py         # AuditLog
│   ├── schemas/
│   │   └── ...              # Pydantic 请求/响应模型
│   ├── services/
│   │   ├── dedup.py         # 去重服务（Bloom Filter + SimHash）
│   │   ├── quota.py         # 配额检查与消耗
│   │   ├── search.py        # Meilisearch 索引与查询
│   │   └── export.py        # 数据导出（CSV/JSON/Excel）
│   ├── scrapers/
│   │   ├── base.py          # 爬虫基类
│   │   ├── news/            # 新闻站点爬虫（trafilatura）
│   │   └── social/          # 社交媒体爬虫（Twitter/Telegram）
│   ├── storage/
│   │   ├── base.py          # StorageProvider Protocol
│   │   ├── minio.py         # MinIO 实现
│   │   └── s3.py            # S3 实现
│   └── tasks/
│       ├── celery_app.py    # Celery 配置
│       ├── scraping.py      # 采集任务
│       └── quota_reset.py   # 配额重置定时任务
├── alembic/                  # 数据库迁移
└── tests/
    ├── unit/                 # 单元测试
    ├── integration/          # 集成测试
    └── fixtures/             # 测试数据

frontend/
├── src/
│   ├── components/
│   │   └── ui/              # Aura 风格基础组件
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Input.tsx
│   │       └── SliderCaptcha.tsx
│   ├── pages/
│   │   ├── auth/            # 登录/注册页
│   │   ├── dashboard/       # HUD Dashboard
│   │   ├── tasks/           # 任务管理
│   │   ├── data/            # 数据查看/导出
│   │   └── admin/           # 管理后台
│   ├── hooks/
│   │   └── useWebSocket.ts  # WebSocket 实时推送
│   ├── services/
│   │   └── api.ts           # API 调用封装
│   ├── stores/
│   │   └── auth.ts          # 认证状态（Zustand）
│   └── types/
│       └── ...              # TypeScript 类型定义
├── tests/e2e/               # Playwright E2E 测试
└── public/
```

**Structure Decision**: Web application with backend/frontend separation per Constitution v3.0.0

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | All Constitution requirements satisfied | - |
