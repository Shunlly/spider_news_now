# Tasks: 全栈爬虫 SaaS 平台

**Input**: Design documents from `/specs/004-scraper-saas-platform/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/api-v1.yaml

**Tests**: Per QA Engineer strategy in research.md - Pytest for backend (unit/integration), Playwright for frontend E2E

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Per Constitution v3.0.0 Development Standards:

- **Backend**: `backend/app/`, `backend/alembic/`
- **Backend tests**: `backend/tests/unit/`, `backend/tests/integration/`, `backend/tests/contract/`
- **Frontend**: `frontend/src/`
- **Frontend tests**: `frontend/tests/e2e/` (Playwright)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure per plan.md
- [x] T002 [P] Initialize backend Python project with FastAPI dependencies in `backend/requirements.txt`
- [x] T003 [P] Initialize frontend Vite+React+TypeScript project in `frontend/`
- [x] T004 [P] Configure Tailwind CSS with Aura dark theme variables in `frontend/tailwind.config.js`
- [x] T005 [P] Configure ruff linting for backend in `backend/pyproject.toml`
- [x] T006 [P] Configure ESLint/Prettier for frontend in `frontend/.eslintrc.cjs`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & Models

- [x] T007 Setup MySQL database connection and async session in `backend/app/db/session.py`
- [x] T008 [P] Create Tenant model in `backend/app/models/tenant.py`
- [x] T009 [P] Create Role model in `backend/app/models/role.py`
- [x] T010 [P] Create User model in `backend/app/models/user.py`
- [x] T011 [P] Create Quota model in `backend/app/models/quota.py`
- [x] T012 [P] Create AuditLog model in `backend/app/models/audit.py`
- [x] T013 [P] Create CaptchaAttempt model in `backend/app/models/captcha.py`
- [x] T014 Configure Alembic and create initial migration in `backend/alembic/`

### Core Configuration

- [x] T015 [P] Implement configuration management (environment variables) in `backend/app/core/config.py`
- [x] T016 [P] Implement password hashing utilities in `backend/app/core/security.py`
- [x] T017 [P] Implement JWT token creation/validation in `backend/app/core/security.py`
- [x] T018 Setup API router structure in `backend/app/api/v1/__init__.py`

### Storage Adapter

- [x] T019 Define StorageProvider Protocol interface in `backend/app/storage/base.py`
- [x] T020 [P] Implement MinIO storage adapter in `backend/app/storage/minio.py`
- [x] T021 [P] Implement S3 storage adapter in `backend/app/infrastructure/storage/s3.py`
- [x] T022 Create storage factory function in `backend/app/storage/__init__.py`

### Celery & Task Queue

- [x] T023 Configure Celery app with Redis broker in `backend/app/tasks/celery_app.py`
- [x] T024 [P] Implement DLQ (Dead Letter Queue) handler in `backend/app/tasks/dlq.py`
- [x] T025 [P] Implement quota reset scheduled task in `backend/app/tasks/quota_reset.py`

### DevOps

- [x] T026 [P] Create backend Dockerfile (multi-stage build) in `backend/Dockerfile`
- [x] T027 [P] Create frontend Dockerfile (multi-stage build) in `frontend/Dockerfile`
- [x] T028 Create docker-compose.yml for development environment
- [x] T029 Create docker-compose.prod.yml for production environment
- [x] T030 Implement health check endpoint in `backend/app/api/v1/health.py`

### Logging

- [x] T031 Configure Loguru structured logging in `backend/app/core/logging.py`

### Tests - Foundational

- [x] T032 [P] Unit test for JWT token generation in `backend/tests/unit/test_security.py`
- [x] T033 [P] Unit test for password hashing in `backend/tests/unit/test_security.py`
- [x] T034 [P] Unit test for StorageProvider (MinIO) in `backend/tests/unit/test_storage.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 用户注册与安全登录 (Priority: P1) 🎯 MVP

**Goal**: 实现邮箱注册 + 滑块验证码 + JWT 登录，用户能够安全地注册账户并登录系统

**Independent Test**: 通过注册新账户、完成滑块验证、登录系统来完整测试，成功后用户能看到个人 Dashboard

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T035 [P] [US1] Integration test for register endpoint in `backend/tests/integration/test_auth_api.py`
- [x] T036 [P] [US1] Integration test for login endpoint in `backend/tests/integration/test_auth_api.py`
- [x] T037 [P] [US1] Integration test for captcha verify endpoint in `backend/tests/integration/test_auth_api.py`
- [x] T038 [P] [US1] Integration test for token refresh in `backend/tests/integration/test_auth_api.py`

### Backend Implementation for User Story 1

- [x] T039 [P] [US1] Create auth Pydantic schemas in `backend/app/schemas/auth.py`
- [x] T040 [P] [US1] Create user Pydantic schemas in `backend/app/schemas/user.py`
- [x] T041 [US1] Implement captcha generation logic in `backend/app/core/captcha.py`
- [x] T042 [US1] Implement captcha verification with cooldown in `backend/app/core/captcha.py`
- [x] T043 [US1] Implement user registration service in `backend/app/services/user.py`
- [x] T044 [US1] Implement email verification token generation in `backend/app/services/user.py`
- [x] T045 [US1] Implement auth endpoints (register/login/refresh/captcha) in `backend/app/api/v1/auth.py`
- [x] T046 [US1] Implement /users/me endpoint in `backend/app/api/v1/users.py`
- [x] T047 [US1] Add RBAC dependency injection for route protection in `backend/app/core/deps.py`
- [x] T048 [US1] Create Alembic migration for User/Role/CaptchaAttempt tables

### Frontend Implementation for User Story 1

- [x] T049 [P] [US1] Create Aura Button component in `frontend/src/components/ui/Button.tsx`
- [x] T050 [P] [US1] Create Aura Input component in `frontend/src/components/ui/Input.tsx`
- [x] T051 [P] [US1] Create Aura Card component in `frontend/src/components/ui/Card.tsx`
- [x] T052 [US1] Create SliderCaptcha component in `frontend/src/components/ui/SliderCaptcha.tsx`
- [x] T053 [US1] Create auth API service in `frontend/src/services/api.ts`
- [x] T054 [US1] Create auth Zustand store in `frontend/src/stores/auth.ts`
- [x] T055 [US1] Implement Login page in `frontend/src/pages/auth/LoginPage.tsx`
- [x] T056 [US1] Implement Register page in `frontend/src/pages/auth/RegisterPage.tsx`
- [x] T057 [US1] Implement route protection (PrivateRoute) in `frontend/src/components/PrivateRoute.tsx`
- [x] T058 [US1] Setup React Router with auth routes in `frontend/src/App.tsx`

### E2E Tests for User Story 1

- [x] T059 [US1] E2E test for user registration flow in `frontend/e2e/auth.spec.ts`
- [x] T060 [US1] E2E test for user login flow in `frontend/e2e/auth.spec.ts`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 新闻站点内容采集 (Priority: P1) 🎯 MVP

**Goal**: 用户能够创建新闻站点采集任务，系统自动提取正文并去重存储

**Independent Test**: 创建一个新闻采集任务、运行采集、查看采集结果

### Tests for User Story 2 ⚠️

- [x] T061 [P] [US2] Unit test for news parser (trafilatura) in `backend/tests/unit/test_parsers.py`
- [x] T062 [P] [US2] Unit test for SimHash dedup algorithm in `backend/tests/unit/test_dedup.py`
- [x] T063 [P] [US2] Unit test for URL Bloom Filter dedup in `backend/tests/unit/test_dedup.py`
- [x] T064 [P] [US2] Integration test for task CRUD endpoints in `backend/tests/integration/test_tasks_api.py`
- [x] T065 [P] [US2] Integration test for news list endpoint in `backend/tests/integration/test_news_api.py`

### Backend Implementation for User Story 2

- [x] T066 [P] [US2] Create ScrapingTask model in `backend/app/models/task.py`
- [x] T067 [P] [US2] Create NewsArticle model in `backend/app/models/news.py`
- [x] T068 [P] [US2] Create task Pydantic schemas in `backend/app/schemas/task.py`
- [x] T069 [P] [US2] Create news Pydantic schemas in `backend/app/schemas/news.py`
- [x] T070 [US2] Create Alembic migration for ScrapingTask/NewsArticle tables
- [x] T071 [US2] Implement news scraper base class in `backend/app/scrapers/base.py`
- [x] T072 [US2] Implement trafilatura news parser in `backend/app/scrapers/news/parser.py`
- [x] T073 [US2] Implement news scraper task handler in `backend/app/scrapers/news/scraper.py`
- [x] T074 [US2] Implement Bloom Filter URL dedup in `backend/app/services/dedup.py`
- [x] T075 [US2] Implement SimHash content fingerprint in `backend/app/services/dedup.py`
- [x] T076 [US2] Implement DedupService (combined) in `backend/app/services/dedup.py`
- [x] T077 [US2] Implement Celery task for news scraping in `backend/app/tasks/scraping.py`
- [x] T078 [US2] Implement task CRUD service in `backend/app/services/task.py`
- [x] T079 [US2] Implement task endpoints (list/create/get/delete/run/cancel) in `backend/app/api/v1/tasks.py`
- [x] T080 [US2] Implement news endpoints (list/get/export) in `backend/app/api/v1/news.py`

### Frontend Implementation for User Story 2

- [x] T081 [P] [US2] Create TaskCard component in `frontend/src/components/tasks/TaskCard.tsx`
- [x] T082 [P] [US2] Create TaskProgress component in `frontend/src/components/tasks/TaskProgress.tsx`
- [x] T083 [P] [US2] Create NewsCard component in `frontend/src/components/news/NewsCard.tsx`
- [x] T084 [US2] Create tasks API service in `frontend/src/services/tasks.ts`
- [x] T085 [US2] Create news API service in `frontend/src/services/news.ts`
- [x] T086 [US2] Implement TaskListPage in `frontend/src/pages/tasks/TaskListPage.tsx`
- [x] T087 [US2] Implement TaskCreatePage in `frontend/src/pages/tasks/TaskCreatePage.tsx`
- [x] T088 [US2] Implement TaskDetailPage in `frontend/src/pages/tasks/TaskDetailPage.tsx`
- [x] T089 [US2] Implement NewsListPage in `frontend/src/pages/data/NewsListPage.tsx`
- [x] T090 [US2] Implement NewsDetailPage in `frontend/src/pages/data/NewsDetailPage.tsx`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - 社交媒体会话流采集 (Priority: P2)

**Goal**: 用户能够采集 Twitter Thread 和 Telegram 频道的会话流，保持消息时间线和回复关系

**Independent Test**: 配置 Twitter Thread 或 Telegram 频道采集任务、运行采集、查看会话结构

### Tests for User Story 3 ⚠️

- [x] T091 [P] [US3] Unit test for Twitter thread parser in `backend/tests/unit/test_social_parsers.py`
- [x] T092 [P] [US3] Unit test for Telegram message parser in `backend/tests/unit/test_social_parsers.py`
- [x] T093 [P] [US3] Integration test for social sessions endpoint in `backend/tests/integration/test_social_integration.py`

### Backend Implementation for User Story 3

- [x] T094 [P] [US3] Create SocialSession model in `backend/app/models/social_session.py`
- [x] T095 [P] [US3] Create SocialMessage model in `backend/app/models/social_message.py`
- [x] T096 [P] [US3] Create social Pydantic schemas in `backend/app/schemas/social.py`
- [x] T097 [US3] Create Alembic migration for SocialSession/SocialMessage tables
- [x] T098 [US3] Implement Twitter thread scraper in `backend/app/scrapers/twitter_scraper.py`
- [x] T099 [US3] Implement Telegram channel scraper in `backend/app/scrapers/telegram_scraper.py`
- [x] T100 [US3] Implement Celery task for social scraping in `backend/app/tasks/social_tasks.py`
- [x] T101 [US3] Implement social session service in `backend/app/services/social_service.py`
- [x] T102 [US3] Implement social endpoints (sessions/messages) in `backend/app/api/v1/endpoints/social.py`

### Frontend Implementation for User Story 3

- [x] T103 [P] [US3] Create SessionCard component (integrated in SocialPage)
- [x] T104 [P] [US3] Create MessageThread component (integrated in SocialPage)
- [x] T105 [US3] Create social API service in `frontend/src/services/socialService.ts`
- [x] T106 [US3] Implement SocialSessionListPage in `frontend/src/pages/SocialPage.tsx`
- [x] T107 [US3] Implement SocialSessionDetailPage (integrated in SocialPage)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - 多租户数据隔离与权限管理 (Priority: P2)

**Goal**: 实现多租户数据隔离，租户间数据完全不可见，超级管理员可查看所有数据

**Independent Test**: 创建多个租户用户、各自运行采集任务、验证数据隔离、超级管理员查看全部数据

### Tests for User Story 4 ⚠️

- [x] T108 [P] [US4] Integration test for tenant isolation in `backend/tests/integration/test_tenant_isolation.py`
- [x] T109 [P] [US4] Integration test for super admin access in `backend/tests/integration/test_tenant_isolation.py`
- [x] T110 [P] [US4] Integration test for permission denied cases in `backend/tests/integration/test_tenant_isolation.py`

### Backend Implementation for User Story 4

- [x] T111 [US4] Implement tenant filter middleware in `backend/app/core/middleware.py`
- [x] T112 [US4] Add tenant_id filter to all business queries (SQLAlchemy event listener)
- [x] T113 [US4] Implement tenant admin endpoints in `backend/app/api/v1/admin.py`
- [x] T114 [US4] Implement user management endpoints in `backend/app/api/v1/admin.py`
- [x] T115 [US4] Implement X-Tenant-ID header handling for super admin

### Frontend Implementation for User Story 4

- [x] T116 [P] [US4] Create TenantSelector component in `frontend/src/components/admin/TenantSelector.tsx`
- [x] T117 [P] [US4] Create UserTable component in `frontend/src/components/admin/UserTable.tsx`
- [x] T118 [US4] Create admin API service in `frontend/src/services/admin.ts`
- [x] T119 [US4] Implement TenantManagePage in `frontend/src/pages/admin/TenantManagePage.tsx`
- [x] T120 [US4] Implement UserManagePage in `frontend/src/pages/admin/UserManagePage.tsx`

**Checkpoint**: Multi-tenant isolation fully functional

---

## Phase 7: User Story 5 - 配额管理与使用量控制 (Priority: P2)

**Goal**: 为不同等级用户设置每日采集配额和并发任务限制，防止资源滥用

**Independent Test**: 设置用户配额、用户运行任务直到达到配额、验证限制生效

### Tests for User Story 5 ⚠️

- [x] T121 [P] [US5] Unit test for quota calculation in `backend/tests/unit/test_services/test_quota_service.py`
- [x] T122 [P] [US5] Unit test for quota reset logic in `backend/tests/unit/test_services/test_quota_service.py`
- [x] T123 [P] [US5] Integration test for quota enforcement in `backend/tests/integration/test_quota_integration.py`

### Backend Implementation for User Story 5

- [x] T124 [US5] Implement quota check service in `backend/app/services/quota_service.py`
- [x] T125 [US5] Implement quota consumption on task start in `backend/app/services/quota_service.py`
- [x] T126 [US5] Implement concurrent task limit check in `backend/app/services/quota_service.py`
- [x] T127 [US5] Implement /quota endpoint in `backend/app/api/v1/endpoints/quota.py`
- [x] T128 [US5] Add quota check middleware to task creation endpoint
- [x] T129 [US5] Verify Celery Beat quota reset task (T025)

### Frontend Implementation for User Story 5

- [x] T130 [P] [US5] Create QuotaCard component in `frontend/src/components/QuotaDisplay.tsx`
- [x] T131 [P] [US5] Create QuotaWarning component in `frontend/src/components/ui/QuotaWarning.tsx`
- [x] T132 [US5] Add quota display to DashboardPage
- [x] T133 [US5] Add quota warning to DashboardPage (integrated with task trigger)

**Checkpoint**: Quota management fully functional

---

## Phase 8: User Story 6 - HUD 风格实时监控 Dashboard (Priority: P3)

**Goal**: 实现科幻电影 HUD 风格的实时监控面板，展示系统状态、采集统计、资源使用情况

**Independent Test**: 登录后查看 Dashboard、观察数据实时更新、验证图表交互

### Backend Implementation for User Story 6

- [x] T134 [US6] Implement dashboard stats service in `backend/app/services/dashboard_service.py`
- [x] T135 [US6] Implement /dashboard/stats endpoint in `backend/app/api/v1/endpoints/dashboard.py`
- [x] T136 [US6] Implement WebSocket endpoint for real-time updates in `backend/app/api/v1/endpoints/dashboard.py`
- [x] T137 [US6] Implement WebSocket message types (stats update, alert) in `backend/app/schemas/websocket.py`

### Frontend Implementation for User Story 6

- [x] T138 [P] [US6] Create StatsCard component (HUDStatCard) in `frontend/src/components/ui/HUDStatCard.tsx`
- [x] T139 [P] [US6] Create TrendChart component (SourcePieChart) in `frontend/src/components/charts/SourcePieChart.tsx`
- [x] T140 [P] [US6] Create ActivityFeed component (HUDActivityList) in `frontend/src/components/ui/HUDActivityList.tsx`
- [x] T141 [P] [US6] Create AlertBanner component in `frontend/src/components/dashboard/AlertBanner.tsx`
- [x] T142 [US6] Create useWebSocket hook in `frontend/src/hooks/useWebSocket.ts`
- [x] T143 [US6] Create dashboard API service (integrated in scraperService)
- [x] T144 [US6] Implement DashboardPage in `frontend/src/pages/DashboardPage.tsx`
- [x] T145 [US6] Create AppLayout with TopBar and Sidebar in `frontend/src/components/layout/`

**Checkpoint**: Dashboard with real-time updates functional

---

## Phase 9: User Story 7 - 全文检索与数据导出 (Priority: P3)

**Goal**: 用户能够对采集内容进行全文检索，并将结果导出为常用格式

**Independent Test**: 输入关键词搜索、验证结果准确性、导出数据文件

### Tests for User Story 7 ⚠️

- [x] T146 [P] [US7] Integration test for search endpoint in `backend/tests/integration/test_search_integration.py`
- [x] T147 [P] [US7] Unit test for export service in `backend/tests/unit/test_services/test_export_service.py`

### Backend Implementation for User Story 7

- [x] T148 [US7] Configure Meilisearch client in `backend/app/services/search_service.py`
- [x] T149 [US7] Implement search index sync service in `backend/app/services/search_service.py`
- [x] T150 [US7] Implement full-text search endpoint in `backend/app/api/v1/endpoints/search.py`
- [x] T151 [US7] Implement export service (CSV/JSON/Excel) in `backend/app/services/export_service.py`
- [x] T152 [US7] Implement export endpoint in `backend/app/api/v1/endpoints/exports.py`

### Frontend Implementation for User Story 7

- [x] T153 [P] [US7] Create SearchInput component (integrated in SearchPage)
- [x] T154 [P] [US7] Create SearchResultCard component (integrated in SearchPage)
- [x] T155 [P] [US7] Create ExportDialog component in `frontend/src/components/ui/ExportDialog.tsx`
- [x] T156 [US7] Create search API service in `frontend/src/services/searchService.ts`
- [x] T157 [US7] Implement SearchPage in `frontend/src/pages/SearchPage.tsx`
- [x] T158 [US7] Add export functionality to NewsPage

**Checkpoint**: Full-text search and export fully functional

---

## Phase 10: User Story 8 - 运维监控与审计日志 (Priority: P3)

**Goal**: 系统管理员能够监控系统资源使用情况并查看操作审计日志

**Independent Test**: 查看系统监控面板、执行敏感操作后验证审计日志记录

### Tests for User Story 8 ⚠️

- [x] T159 [P] [US8] Integration test for audit log endpoint in `backend/tests/integration/test_audit_api.py`
- [x] T160 [P] [US8] Unit test for audit log service in `backend/tests/unit/test_services/test_audit_service.py`

### Backend Implementation for User Story 8

- [x] T161 [US8] Implement audit log service in `backend/app/services/audit_service.py`
- [x] T162 [US8] Add audit log decorator for sensitive endpoints in `backend/app/core/audit.py`
- [x] T163 [US8] Implement /admin/audit-logs endpoint in `backend/app/api/v1/admin.py`
- [x] T164 [US8] Add system metrics collection (task queue, processing rate)
- [x] T165 [US8] Implement alerting service for threshold breach in `backend/app/services/alerting.py`

### Frontend Implementation for User Story 8

- [x] T166 [P] [US8] Create AuditLogTable component in `frontend/src/components/admin/AuditLogTable.tsx`
- [x] T167 [P] [US8] Create SystemMetricsCard component in `frontend/src/components/admin/SystemMetricsCard.tsx`
- [x] T168 [US8] Implement AuditLogPage in `frontend/src/pages/admin/AuditLogPage.tsx`
- [x] T169 [US8] Implement SystemMonitorPage in `frontend/src/pages/admin/SystemMonitorPage.tsx`

**Checkpoint**: All user stories implemented

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### E2E Tests

- [x] T170 [P] E2E test for complete task creation and viewing flow in `frontend/e2e/tasks.spec.ts`
- [x] T171 [P] E2E test for search and export flow in `frontend/e2e/search.spec.ts`
- [x] T172 [P] E2E test for admin user management in `frontend/e2e/admin.spec.ts`

### Documentation & DevOps

- [x] T173 [P] Create .env.example for backend
- [x] T174 [P] Create .env.example for frontend
- [x] T175 Update README.md with setup instructions
- [x] T176 Run and verify quickstart.md steps
- [x] T177 Configure GitHub Actions CI pipeline for tests

### Code Quality

- [x] T178 [P] Code cleanup and remove debug logs
- [x] T179 [P] Add Chinese comments to complex scraper parsing logic
- [x] T180 [P] Verify all Type Hints are complete (Python + TypeScript)
- [x] T181 Security audit - check for SQL injection, XSS vulnerabilities
- [x] T182 Performance optimization for Meilisearch queries

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Story 1 (Phase 3)**: Depends on Foundational - MVP core
- **User Story 2 (Phase 4)**: Depends on Foundational - MVP core
- **User Stories 3-8 (Phases 5-10)**: Depend on Foundational, can proceed in priority order
- **Polish (Phase 11)**: Depends on all desired user stories being complete

### MVP Strategy

Complete in this order for earliest working product:

1. Phase 1: Setup
2. Phase 2: Foundational (CRITICAL)
3. Phase 3: User Story 1 (认证系统) - **MVP Checkpoint 1**
4. Phase 4: User Story 2 (新闻采集) - **MVP Checkpoint 2**

### User Story Priority Order

| Phase | User Story | Priority | Can Start After |
|-------|-----------|----------|-----------------|
| 3 | US1 - 用户注册与安全登录 | P1 | Phase 2 |
| 4 | US2 - 新闻站点内容采集 | P1 | Phase 2 |
| 5 | US3 - 社交媒体会话流采集 | P2 | Phase 2 |
| 6 | US4 - 多租户数据隔离 | P2 | Phase 2 |
| 7 | US5 - 配额管理 | P2 | Phase 2 |
| 8 | US6 - HUD Dashboard | P3 | Phase 2 |
| 9 | US7 - 全文检索与导出 | P3 | Phase 2 |
| 10 | US8 - 运维监控与审计 | P3 | Phase 2 |

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes:
  - US1 and US2 (P1 stories) can start in parallel
  - After P1 complete, US3-US5 (P2 stories) can start in parallel
  - After P2 complete, US6-US8 (P3 stories) can start in parallel
- Within each user story, all tests marked [P] can run in parallel
- Within each user story, all models marked [P] can run in parallel

---

## Task Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | T001-T006 | Setup |
| 2 | T007-T034 | Foundational |
| 3 | T035-T060 | US1 - 认证系统 |
| 4 | T061-T090 | US2 - 新闻采集 |
| 5 | T091-T107 | US3 - 社交采集 |
| 6 | T108-T120 | US4 - 多租户 |
| 7 | T121-T133 | US5 - 配额管理 |
| 8 | T134-T145 | US6 - Dashboard |
| 9 | T146-T158 | US7 - 检索导出 |
| 10 | T159-T169 | US8 - 运维审计 |
| 11 | T170-T182 | Polish |

**Total Tasks**: 182

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
