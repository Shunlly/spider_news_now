# Tasks: 用户鉴权、数据隔离与安全验证 (Auth & RBAC & Security)

**Input**: Design documents from `/specs/003-auth-rbac-security/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/auth-api.yaml

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Per Constitution v2.0.0 Development Standards:

- **Backend**: `backend/app/` (models, schemas, services, api, core)
- **Frontend**: `frontend/src/` (components, pages, services, stores, types)
- **Backend tests**: `backend/tests/unit/`, `backend/tests/integration/`
- **Frontend tests**: `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [x] T001 Install backend dependencies: `passlib[bcrypt]`, `python-jose[cryptography]`, `redis`, `pillow` in backend/requirements.txt
- [ ] T002 [P] Install frontend dependencies: Add slider captcha related packages (if needed) via pnpm
- [x] T003 [P] Add JWT and captcha related environment variables to backend/.env.example and backend/app/core/config.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### 2.1 Database Model & Migration

- [ ] T004 Create User model with role field (admin/user) in backend/app/models/user.py
- [ ] T005 Create Pydantic schemas for User (UserCreate, UserResponse, UserUpdate) in backend/app/schemas/user.py
- [ ] T006 [P] Create Pydantic schemas for Auth (LoginRequest, LoginResponse, CaptchaResponse) in backend/app/schemas/auth.py
- [ ] T007 Generate Alembic migration: Create users table with default admin account in backend/alembic/versions/

### 2.2 Security Utilities

- [ ] T008 Implement password hashing utilities (bcrypt hash/verify) in backend/app/core/security.py
- [ ] T009 Implement JWT token creation and validation logic in backend/app/core/security.py
- [ ] T010 [P] Create get_current_user dependency for route protection in backend/app/core/deps.py

### 2.3 Frontend Types

- [ ] T011 [P] Define TypeScript interfaces for auth types (User, LoginRequest, LoginResponse, CaptchaData) in frontend/src/types/auth.ts

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 安全登录验证 (Priority: P1) 🎯 MVP

**Goal**: 实现带滑块验证码的安全登录功能

**Independent Test**: 可以通过尝试登录流程并完成滑块验证来独立测试，成功完成验证后才能提交登录请求

### 3.1 Backend - Captcha Service

- [ ] T012 [US1] Implement captcha image generation (background + slider) using PIL in backend/app/services/captcha_service.py
- [ ] T013 [US1] Implement captcha storage/retrieval in Redis with TTL in backend/app/services/captcha_service.py
- [ ] T014 [US1] Implement captcha verification logic (tolerance ±5px) in backend/app/services/captcha_service.py

### 3.2 Backend - Auth Service

- [ ] T015 [US1] Implement user authentication service (login, verify credentials) in backend/app/services/auth_service.py
- [ ] T016 [US1] Add login attempt tracking and account lockout logic in backend/app/services/auth_service.py

### 3.3 Backend - API Routes

- [ ] T017 [US1] Implement GET /auth/captcha endpoint in backend/app/api/v1/endpoints/auth.py
- [ ] T018 [US1] Implement POST /auth/verify-captcha endpoint in backend/app/api/v1/endpoints/auth.py
- [ ] T019 [US1] Implement POST /auth/login endpoint in backend/app/api/v1/endpoints/auth.py
- [ ] T020 [US1] Implement POST /auth/logout endpoint in backend/app/api/v1/endpoints/auth.py
- [ ] T021 [US1] Implement POST /auth/refresh endpoint in backend/app/api/v1/endpoints/auth.py
- [ ] T022 [US1] Implement GET /auth/me endpoint in backend/app/api/v1/endpoints/auth.py
- [ ] T023 [US1] Register auth router in backend/app/api/v1/router.py

### 3.4 Frontend - Auth Service & Store

- [ ] T024 [US1] Implement authService API calls (getCaptcha, verifyCaptcha, login, logout, refresh) in frontend/src/services/authService.ts
- [ ] T025 [US1] Create authStore for state management (user, token, isAuthenticated) in frontend/src/stores/authStore.ts
- [ ] T026 [US1] Implement Axios interceptors for token injection and refresh logic in frontend/src/services/api.ts

### 3.5 Frontend - Slider Captcha Component

- [ ] T027 [US1] Create SliderCaptcha component structure in frontend/src/components/SliderCaptcha/index.tsx
- [ ] T028 [US1] Implement slider drag interaction logic in frontend/src/components/SliderCaptcha/index.tsx
- [ ] T029 [US1] Add Glassmorphism styling to SliderCaptcha in frontend/src/components/SliderCaptcha/styles.css

### 3.6 Frontend - Login Page

- [ ] T030 [US1] Create LoginPage with username/password form in frontend/src/pages/LoginPage.tsx
- [ ] T031 [US1] Integrate SliderCaptcha component into LoginPage in frontend/src/pages/LoginPage.tsx
- [ ] T032 [US1] Apply Glassmorphism card styling to LoginPage in frontend/src/pages/LoginPage.tsx

### 3.7 Frontend - Route Guard

- [ ] T033 [US1] Implement ProtectedRoute component for authentication check in frontend/src/components/ProtectedRoute.tsx
- [ ] T034 [US1] Configure route guards in App.tsx for protected routes in frontend/src/App.tsx
- [ ] T035 [US1] Add login/logout routes to router configuration in frontend/src/App.tsx

**Checkpoint**: At this point, User Story 1 (安全登录验证) should be fully functional and testable independently

---

## Phase 4: User Story 2 & 3 - 管理员全局数据访问 & 普通用户数据隔离 (Priority: P2)

**Goal**: 实现基于角色的数据访问控制，管理员可查看所有数据，普通用户仅能查看自己的数据

**Independent Test**: 可以通过管理员和普通用户账户分别登录，验证数据访问范围的差异

### 4.1 Database Migration - Add user_id to Existing Tables

- [ ] T036 [US2/US3] Generate Alembic migration: Add user_id column to news_sources table in backend/alembic/versions/
- [ ] T037 [P] [US2/US3] Generate Alembic migration: Add user_id column to news_articles table in backend/alembic/versions/
- [ ] T038 [P] [US2/US3] Generate Alembic migration: Add user_id column to social_sessions table in backend/alembic/versions/
- [ ] T039 [P] [US2/US3] Generate Alembic migration: Add user_id column to scraper_runs table in backend/alembic/versions/
- [ ] T040 [P] [US2/US3] Generate Alembic migration: Add user_id column to account_credentials table in backend/alembic/versions/
- [ ] T041 [P] [US2/US3] Generate Alembic migration: Add user_id column to proxy_configs table in backend/alembic/versions/
- [ ] T042 [P] [US2/US3] Generate Alembic migration: Add user_id column to export_tasks table in backend/alembic/versions/

### 4.2 Update Existing Models

- [ ] T043 [US2/US3] Add user_id field and relationship to NewsSource model in backend/app/models/news_source.py
- [ ] T044 [P] [US2/US3] Add user_id field and relationship to NewsArticle model in backend/app/models/news_article.py
- [ ] T045 [P] [US2/US3] Add user_id field and relationship to SocialSession model in backend/app/models/social_session.py
- [ ] T046 [P] [US2/US3] Add user_id field to ScraperRun model in backend/app/models/scraper_run.py
- [ ] T047 [P] [US2/US3] Add user_id field to AccountCredential model in backend/app/models/account_credential.py
- [ ] T048 [P] [US2/US3] Add user_id field to ProxyConfig model in backend/app/models/proxy_config.py
- [ ] T049 [P] [US2/US3] Add user_id field to ExportTask model in backend/app/models/export_task.py

### 4.3 Permission Service

- [ ] T050 [US2/US3] Create get_user_filter dependency injection function in backend/app/services/permission_service.py
- [ ] T051 [US2/US3] Create require_admin dependency for admin-only routes in backend/app/services/permission_service.py

### 4.4 Update Existing API Endpoints

- [ ] T052 [US2/US3] Add permission filtering to scrapers endpoints in backend/app/api/v1/endpoints/scrapers.py
- [ ] T053 [P] [US2/US3] Add permission filtering to news endpoints in backend/app/api/v1/endpoints/news.py
- [ ] T054 [P] [US2/US3] Add permission filtering to social endpoints in backend/app/api/v1/endpoints/social.py
- [ ] T055 [P] [US2/US3] Add permission filtering to credentials endpoints in backend/app/api/v1/endpoints/credentials.py
- [ ] T056 [P] [US2/US3] Add permission filtering to proxies endpoints in backend/app/api/v1/endpoints/proxies.py
- [ ] T057 [P] [US2/US3] Add permission filtering to exports endpoints in backend/app/api/v1/endpoints/exports.py
- [ ] T058 [P] [US2/US3] Add permission filtering to telegram endpoints in backend/app/api/v1/endpoints/telegram.py
- [ ] T059 [P] [US2/US3] Add permission filtering to search endpoints in backend/app/api/v1/endpoints/search.py

### 4.5 User Management API (Admin Only)

- [ ] T060 [US2] Implement GET /users endpoint (list users) in backend/app/api/v1/endpoints/users.py
- [ ] T061 [P] [US2] Implement POST /users endpoint (create user) in backend/app/api/v1/endpoints/users.py
- [ ] T062 [P] [US2] Implement GET /users/{id} endpoint in backend/app/api/v1/endpoints/users.py
- [ ] T063 [P] [US2] Implement PUT /users/{id} endpoint in backend/app/api/v1/endpoints/users.py
- [ ] T064 [P] [US2] Implement DELETE /users/{id} endpoint in backend/app/api/v1/endpoints/users.py
- [ ] T065 [US2] Implement POST /users/{id}/unlock endpoint in backend/app/api/v1/endpoints/users.py
- [ ] T066 [US2] Register users router in backend/app/api/v1/router.py

### 4.6 Frontend - Display User Info

- [ ] T067 [US2/US3] Display current user info and role in header/navbar in frontend/src/layouts/MainLayout.tsx
- [ ] T068 [P] [US2/US3] Add creator info display to task list items (for admin view) in frontend/src/pages/DashboardPage.tsx

**Checkpoint**: At this point, User Stories 2 AND 3 should both work - admin sees all data, user sees only their own

---

## Phase 5: User Story 4 - 历史数据迁移归属 (Priority: P3)

**Goal**: 确保历史数据正确归属到管理员账户

**Independent Test**: 可以通过检查数据库迁移后历史记录的 user_id 字段值来验证

### 5.1 Migration Script

- [ ] T069 [US4] Create consolidated migration script to update all NULL user_id to admin (id=1) in backend/alembic/versions/
- [ ] T070 [US4] Add foreign key constraints after data migration in backend/alembic/versions/
- [ ] T071 [US4] Add indexes for user_id columns (idx_article_user_date, idx_session_user_platform) in backend/alembic/versions/

### 5.2 Verification

- [ ] T072 [US4] Add migration verification query to check no NULL user_id remains in backend/scripts/verify_migration.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Integration & Polish

**Purpose**: 前后端联调与整体优化

### 6.1 End-to-End Integration

- [ ] T073 Perform frontend-backend login flow integration test (manual)
- [ ] T074 Test captcha generation and verification across different browsers
- [ ] T075 Verify permission filtering works correctly for admin vs user roles
- [ ] T076 Test token refresh mechanism when access token expires

### 6.2 Security Hardening

- [ ] T077 Add rate limiting to login and captcha endpoints in backend/app/api/v1/endpoints/auth.py
- [ ] T078 [P] Add CORS configuration for authentication cookies in backend/app/main.py
- [ ] T079 [P] Ensure sensitive data is not logged (passwords, tokens) in backend/app/core/logging.py

### 6.3 Documentation & Cleanup

- [ ] T080 Update API documentation with new auth endpoints
- [ ] T081 Run quickstart.md validation to ensure setup instructions work
- [ ] T082 Code review and cleanup

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
     │
     ▼
Phase 2 (Foundational) ─────────── BLOCKS ALL USER STORIES
     │
     ├─────────────────┬─────────────────┬─────────────────┐
     ▼                 ▼                 ▼                 ▼
Phase 3 (US1)    Phase 4 (US2/3)   Phase 5 (US4)    (Can parallel)
     │                 │                 │
     └─────────────────┴─────────────────┘
                       │
                       ▼
               Phase 6 (Polish)
```

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|------------|-------------------|
| US1 (安全登录验证) | Phase 2 | - |
| US2 (管理员全局访问) | Phase 2 + US1 | US3 |
| US3 (用户数据隔离) | Phase 2 + US1 | US2 |
| US4 (历史数据迁移) | Phase 2 | US1, US2, US3 |

### Within Each User Story

1. Backend models/schemas → Services → API endpoints
2. Frontend types → Services → Components → Pages
3. Backend and frontend can develop in parallel within a story

### Parallel Opportunities

**Phase 2 (Foundational)**:
- T005, T006, T011 can run in parallel (different schema files)
- T008, T009 must be sequential (same file)

**Phase 3 (US1)**:
- T027-T029 (SliderCaptcha) can parallel with T024-T026 (Auth Service)
- T030-T032 (LoginPage) depends on T027-T029

**Phase 4 (US2/US3)**:
- All model updates (T043-T049) can run in parallel (different files)
- All API endpoint updates (T052-T059) can run in parallel
- All user management endpoints (T060-T065) can run in parallel

---

## Parallel Example: Phase 3 (User Story 1)

```bash
# Launch backend captcha service tasks:
Task: "T012 [US1] Implement captcha image generation"
Task: "T013 [US1] Implement captcha storage/retrieval in Redis"

# In parallel, launch frontend service tasks:
Task: "T024 [US1] Implement authService API calls"
Task: "T025 [US1] Create authStore for state management"

# After models ready, launch API endpoints:
Task: "T017-T023 [US1] Implement auth API endpoints"

# After API ready, launch frontend pages:
Task: "T030-T032 [US1] Create LoginPage"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T011)
3. Complete Phase 3: User Story 1 (T012-T035)
4. **STOP and VALIDATE**: Test login flow end-to-end
5. Deploy/demo if ready

### Incremental Delivery

| Increment | Stories | Value Delivered |
|-----------|---------|-----------------|
| MVP | US1 | 安全登录验证，防暴力破解 |
| +RBAC | US2 + US3 | 管理员/用户角色区分，数据隔离 |
| +Migration | US4 | 历史数据正确归属 |
| Complete | All | 完整的鉴权和数据隔离系统 |

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Tasks** | 82 |
| **Phase 1 (Setup)** | 3 |
| **Phase 2 (Foundational)** | 8 |
| **Phase 3 (US1 - 安全登录验证)** | 24 |
| **Phase 4 (US2/US3 - 数据隔离)** | 33 |
| **Phase 5 (US4 - 数据迁移)** | 4 |
| **Phase 6 (Integration & Polish)** | 10 |
| **Parallel Opportunities** | ~40% of tasks can run in parallel |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- 所有核心逻辑必须包含中文注释 (per Constitution v2.0.0)
