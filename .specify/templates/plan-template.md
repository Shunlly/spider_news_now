# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  Per Constitution v3.0.0: Tech stack is mandated. Only fill in feature-specific details.
  Reference: .specify/memory/constitution.md Section III. 技术栈强制
-->

**Backend**: Python 3.10+ (FastAPI), SQLAlchemy (Async), Redis, Celery
**Frontend**: React (TypeScript) + Vite + Tailwind CSS + Framer Motion
**UI Library**: Shadcn/UI (recommended) or Arco Design (with Aura customization)
**Database**: MySQL 8.0+ (utf8mb4_unicode_ci)
**Search**: Elasticsearch / Meilisearch
**Object Storage**: MinIO / S3-compatible
**Testing**: Pytest (backend), Playwright (frontend E2E)
**Project Type**: web (backend + frontend separation)
**Performance Goals**: API < 2s (1000 results), Scraper < 60s per run
**Constraints**: [feature-specific constraints or N/A]
**Scale/Scope**: [feature-specific scale or N/A]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Reference: `.specify/memory/constitution.md` v3.0.0 for complete requirements.

### I. 视觉设计规范 (Aura Design System) - verify for frontend features

- [ ] UI follows Aura theme: Immersive Dark + Precision Borders + Subtle Glow (Section I.A)
- [ ] Background uses deep gray/black (`bg-[#09090b]` or `bg-[#0F1117]`) - no pure black (Section I.B)
- [ ] NO glassmorphism (`backdrop-filter: blur()`) or semi-transparent backgrounds (Section I.B)
- [ ] Typography uses Inter (UI) or JetBrains Mono (data display) (Section I.C)

### II. 角色职责 (Roles & Responsibilities) - verify compliance

- [ ] Architect: Storage uses Adapter pattern (StorageProvider interface) (Section II.A)
- [ ] Architect: High-concurrency tasks use Celery (Section II.A)
- [ ] QA: Core business logic has pytest unit tests (Section II.B)
- [ ] QA: API endpoints have integration tests (Section II.B)
- [ ] DevOps: Docker deployment solution provided (Section II.C)
- [ ] DevOps: Health check endpoint (`/health`) provided (Section II.C)

### III. Architecture Compliance (verify now)

- [ ] Storage operations use StorageProvider adapter pattern (Architecture Principles A)
- [ ] Data models follow heterogeneous modeling rules (News vs Social) (Architecture Principles B)
- [ ] Deduplication mechanism planned (URL Hash / SimHash) (Architecture Principles C)

### IV. 编码红线 (Coding Standards) - verify during development

- [ ] No placeholder code (`pass`, `TODO`) - complete implementations only (Section IV.A)
- [ ] Database changes have Alembic Migration scripts (Section IV.B)
- [ ] Type Hints for all Python functions, TypeScript interfaces for frontend (Section IV.C)
- [ ] Core logic includes Chinese comments (especially scraper parsing, dedup) (Section IV.D)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

<!--
  Per Constitution v3.0.0 Development Standards: Web application structure is mandated.
  Only adjust paths if feature requires additional directories.
-->

```text
# Web Application Structure (per Constitution v3.0.0)
backend/
├── src/
│   ├── scrapers/       # 爬虫实现（继承基类）
│   ├── models/         # 数据模型 (SQLAlchemy ORM)
│   ├── schemas/        # Pydantic 模型（请求/响应）
│   ├── services/       # 业务逻辑（去重、调度、数据访问）
│   ├── api/            # FastAPI 路由
│   ├── storage/        # StorageProvider 适配器实现
│   ├── tasks/          # Celery 异步任务
│   └── lib/            # 共享工具（日志、配置）
└── tests/
    ├── unit/           # 单元测试 (pytest)
    ├── integration/    # 集成测试
    └── contract/       # 契约测试

frontend/
├── src/
│   ├── components/     # React 组件
│   │   └── ui/         # 基于 Shadcn/UI 的封装组件
│   ├── pages/          # 页面组件
│   ├── hooks/          # 自定义 Hooks
│   ├── services/       # API 调用服务
│   ├── stores/         # 状态管理
│   └── types/          # TypeScript 类型定义
├── tests/              # 前端测试
│   └── e2e/            # Playwright E2E 测试
└── public/             # 静态资源
```

**Structure Decision**: Web application with backend/frontend separation per Constitution v3.0.0

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
