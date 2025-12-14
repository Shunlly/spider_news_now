# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  Per Constitution v2.0.0: Tech stack is mandated. Only fill in feature-specific details.
  Reference: .specify/memory/constitution.md Section I. Tech Stack Mandate
-->

**Backend**: Python 3.10+ (FastAPI), Pydantic v2, SQLAlchemy (Async)
**Frontend**: React (TypeScript) + Vite + Tailwind CSS + Arco Design
**Database**: MySQL 8.0+ (utf8mb4_unicode_ci)
**Search**: Elasticsearch / Meilisearch
**Object Storage**: MinIO / S3-compatible
**Testing**: pytest + pytest-asyncio (backend), Vitest + RTL (frontend)
**Project Type**: web (backend + frontend separation)
**Performance Goals**: API < 2s (1000 results), Scraper < 60s per run
**Constraints**: [feature-specific constraints or N/A]
**Scale/Scope**: [feature-specific scale or N/A]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Reference: `.specify/memory/constitution.md` v2.0.0 for complete requirements.

### Architecture Compliance (verify now)

- [ ] Storage operations use StorageProvider adapter pattern (Section II.A)
- [ ] Data models follow heterogeneous modeling rules (News vs Social) (Section II.B)
- [ ] Deduplication mechanism planned (URL Hash / SimHash) (Section II.C)

### UI/UX Compliance (verify for frontend features)

- [ ] UI follows Glassmorphism theme (Section III.A)
- [ ] Layout uses Bento Grid pattern (Section III.B)
- [ ] Color scheme uses gradient backgrounds (Section III.C)

### Coding Standards (verify during development)

- [ ] Type Hints for all Python functions, TypeScript interfaces for frontend
- [ ] Core logic includes Chinese comments (especially scraper parsing, dedup)
- [ ] Error handling with retry mechanism for external APIs
- [ ] No placeholder code (pass, TODO) - complete implementations only
- [ ] Structured logging with context (scraper_id, article_count, execution_time)

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
  Per Constitution v2.0.0 Development Standards: Web application structure is mandated.
  Only adjust paths if feature requires additional directories.
-->

```text
# Web Application Structure (per Constitution v2.0.0)
backend/
├── src/
│   ├── scrapers/       # 爬虫实现（继承基类）
│   ├── models/         # 数据模型 (SQLAlchemy ORM)
│   ├── schemas/        # Pydantic 模型（请求/响应）
│   ├── services/       # 业务逻辑（去重、调度、数据访问）
│   ├── api/            # FastAPI 路由
│   ├── storage/        # StorageProvider 适配器实现
│   └── lib/            # 共享工具（日志、配置）
└── tests/
    ├── unit/           # 单元测试
    ├── integration/    # 集成测试
    └── contract/       # 契约测试

frontend/
├── src/
│   ├── components/     # React 组件
│   │   └── ui/         # 基于 Arco Design 的封装组件
│   ├── pages/          # 页面组件
│   ├── hooks/          # 自定义 Hooks
│   ├── services/       # API 调用服务
│   ├── stores/         # 状态管理
│   └── types/          # TypeScript 类型定义
└── tests/              # 前端测试
```

**Structure Decision**: Web application with backend/frontend separation per Constitution v2.0.0

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
