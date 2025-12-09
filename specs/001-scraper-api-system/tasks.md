# Tasks: Web Scraper API System

**Input**: Design documents from `/specs/001-scraper-api-system/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The constitution mandates TDD with minimum 80% coverage. Tests are included for all user stories.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/` for Python/FastAPI, `frontend/` for Vue.js
- Paths shown below follow web application structure per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create backend project structure (backend/app/, backend/tests/, backend/alembic/)
- [ ] T002 Create frontend project structure (frontend/src/, frontend/public/, frontend/tests/)
- [ ] T003 Initialize Python project with requirements.txt and requirements-dev.txt in backend/
- [ ] T004 Initialize Vue 3 project with Vite in frontend/ using npm create vue@latest
- [ ] T005 [P] Create backend/Dockerfile for Python 3.13 with Playwright
- [ ] T006 [P] Create frontend/Dockerfile with multi-stage build (Node 20 + Nginx)
- [ ] T007 [P] Create frontend/nginx.conf for SPA routing and API proxy
- [ ] T008 Create docker-compose.yml with MySQL, backend, and frontend services
- [ ] T009 [P] Create .env.docker with MySQL and application configuration
- [ ] T010 [P] Create backend/.env.example with all required environment variables
- [ ] T011 [P] Create frontend/.env.example with VITE_API_BASE_URL configuration
- [ ] T012 [P] Configure linting tools (black, flake8, mypy) in backend/
- [ ] T013 [P] Configure ESLint and Prettier in frontend/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Foundation

- [ ] T014 Create backend/alembic.ini for database migrations
- [ ] T015 Initialize Alembic with async template in backend/alembic/
- [ ] T016 Create backend/app/db/__init__.py
- [ ] T017 Create backend/app/db/base.py with SQLAlchemy declarative base
- [ ] T018 Create backend/app/db/session.py with async session management and connection pooling

### Core Configuration

- [ ] T019 Create backend/app/core/__init__.py
- [ ] T020 Create backend/app/core/config.py with Pydantic Settings (DATABASE_URL, LOG_LEVEL, etc.)
- [ ] T021 Create backend/app/core/logging.py with structured logging configuration
- [ ] T022 [P] Create backend/app/core/security.py placeholder for future auth

### FastAPI Application Bootstrap

- [ ] T023 Create backend/app/__init__.py
- [ ] T024 Create backend/app/main.py with FastAPI app initialization, CORS, and health endpoint
- [ ] T025 Create backend/app/api/__init__.py
- [ ] T026 Create backend/app/api/v1/__init__.py for API versioning
- [ ] T027 Create backend/app/api/v1/router.py to aggregate all endpoint routers

### Data Models (All Entities)

- [ ] T028 Create backend/app/models/__init__.py
- [ ] T029 Create backend/app/models/news_source.py with NewsSource SQLAlchemy model and relationships
- [ ] T030 Create backend/app/models/news_article.py with NewsArticle SQLAlchemy model, indexes, and relationships
- [ ] T031 Create backend/app/models/scraper_run.py with ScraperRun SQLAlchemy model and relationships

### Pydantic Schemas (All Entities)

- [ ] T032 Create backend/app/schemas/__init__.py
- [ ] T033 Create backend/app/schemas/news.py with NewsArticle request/response schemas (ArticleResponse, ArticleListResponse, etc.)
- [ ] T034 Create backend/app/schemas/scraper.py with ScraperRun and NewsSource schemas

### Initial Migration

- [ ] T035 Create Alembic migration "001_initial_schema" with news_sources, news_articles, scraper_runs tables and indexes
- [ ] T036 Seed news_sources table with 6 initial sources (sina, qq, wangyi, yicai, huanqiu, ifeng) in migration

### Testing Foundation

- [ ] T037 Create backend/tests/__init__.py
- [ ] T038 Create backend/tests/conftest.py with pytest fixtures (test database, async client, test data factories)
- [ ] T039 [P] Create backend/tests/unit/__init__.py
- [ ] T040 [P] Create backend/tests/integration/__init__.py
- [ ] T041 [P] Create backend/tests/contract/__init__.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 3 - Automated News Collection (Priority: P1) 🎯 MVP

**Goal**: Implement automatic scraper execution on schedule to collect fresh news from all 6 sources

**Independent Test**: Configure a scraper schedule, wait for scheduled time, verify new articles appear in database and are accessible via GET /api/v1/news/articles

**Why US3 before US1**: US1 (viewing news) requires news data to exist. US3 creates that data. This is the logical first implementation step.

### Scraper Base Infrastructure

- [ ] T042 [US3] Create backend/app/scrapers/__init__.py
- [ ] T043 [US3] Create backend/app/scrapers/base.py with BaseScraper abstract class defining scrape(), parse(), validate() methods
- [ ] T044 [US3] Write contract test in backend/tests/contract/test_scraper_schemas.py to verify scraper output format matches NewsArticle schema

### Refactor Existing Scrapers

- [ ] T045 [P] [US3] Refactor news_now/sina_news_crawler.py to backend/app/scrapers/sina_scraper.py inheriting from BaseScraper
- [ ] T046 [P] [US3] Refactor news_now/qq_news_crawler.py to backend/app/scrapers/qq_scraper.py inheriting from BaseScraper
- [ ] T047 [P] [US3] Refactor news_now/wangyi_news_crawler.py to backend/app/scrapers/wangyi_scraper.py inheriting from BaseScraper
- [ ] T048 [P] [US3] Refactor news_now/yicai_news_crawler.py to backend/app/scrapers/yicai_scraper.py inheriting from BaseScraper
- [ ] T049 [P] [US3] Refactor news_now/huanqiu_news_crawler.py to backend/app/scrapers/huanqiu_scraper.py inheriting from BaseScraper
- [ ] T050 [P] [US3] Refactor news_now/ifeng_news_crawler.py to backend/app/scrapers/ifeng_scraper.py inheriting from BaseScraper

### Services Layer

- [ ] T051 [US3] Create backend/app/services/__init__.py
- [ ] T052 [US3] Create backend/app/services/duplicate_service.py with URL hash computation and duplicate detection logic
- [ ] T053 [US3] Create backend/app/services/scraper_service.py with scraper orchestration, error handling, and ScraperRun tracking
- [ ] T054 [US3] Write unit tests in backend/tests/unit/test_services/test_duplicate_service.py for hash computation and duplicate detection
- [ ] T055 [US3] Write unit tests in backend/tests/unit/test_services/test_scraper_service.py for scraper orchestration

### Task Scheduling

- [ ] T056 [US3] Create backend/app/tasks/__init__.py
- [ ] T057 [US3] Create backend/app/tasks/scheduler.py with APScheduler configuration (SQLAlchemy job store, ThreadPoolExecutor)
- [ ] T058 [US3] Create backend/app/tasks/scraper_tasks.py with scheduled jobs for each scraper (30 min intervals, failure handling)
- [ ] T059 [US3] Integrate scheduler startup into backend/app/main.py (start on app startup, shutdown on exit)

### Integration Testing

- [ ] T060 [US3] Write integration test in backend/tests/integration/test_scrapers.py to run one scraper and verify articles saved to database
- [ ] T061 [US3] Write integration test in backend/tests/integration/test_scheduler.py to verify scheduler triggers scraper jobs

### Manual Trigger API (for testing)

- [ ] T062 [US3] Create backend/app/api/v1/endpoints/__init__.py
- [ ] T063 [US3] Create backend/app/api/v1/endpoints/scrapers.py with POST /scrapers/{source_key}/trigger endpoint
- [ ] T064 [US3] Register scrapers router in backend/app/api/v1/router.py
- [ ] T065 [US3] Write integration test in backend/tests/integration/test_scraper_api.py for manual trigger endpoint

**US3 Acceptance Test**:
1. Start backend with `uvicorn app.main:app`
2. Wait 30 minutes or trigger manually via API
3. Query database: `SELECT COUNT(*) FROM news_articles` should return >0
4. Verify articles from all 6 sources exist

---

## Phase 4: User Story 1 - View Aggregated News from All Sources (Priority: P1) 🎯 MVP

**Goal**: Display news articles grouped by source in a web interface

**Independent Test**: Launch web interface, view grouped news display, verify articles from all sources (Sina, QQ, Wangyi, Yicai, Huanqiu, Ifeng) are visible and correctly grouped

**Depends on**: US3 (must have news data to display)

### Backend API Endpoints

- [ ] T066 [US1] Create backend/app/services/news_service.py with get_articles_grouped() method returning articles organized by source
- [ ] T067 [US1] Write unit tests in backend/tests/unit/test_services/test_news_service.py for grouped article retrieval
- [ ] T068 [US1] Create backend/app/api/v1/endpoints/news.py with GET /news/articles/grouped endpoint (returns articles grouped by source)
- [ ] T069 [US1] Create GET /news/sources endpoint in backend/app/api/v1/endpoints/news.py to list all news sources
- [ ] T070 [US1] Register news router in backend/app/api/v1/router.py
- [ ] T071 [US1] Write integration test in backend/tests/integration/test_news_api.py for GET /news/articles/grouped endpoint

### Frontend Infrastructure

- [ ] T072 [P] [US1] Create frontend/src/api/axios.js with centralized Axios instance and interceptors
- [ ] T073 [P] [US1] Create frontend/src/api/endpoints.js with API endpoint constants
- [ ] T074 [P] [US1] Initialize Pinia store in frontend/src/main.js
- [ ] T075 [P] [US1] Install Element Plus and configure in frontend/src/main.js
- [ ] T076 [P] [US1] Create frontend/src/layouts/DefaultLayout.vue with header and main content area

### Pinia Store

- [ ] T077 [US1] Create frontend/src/store/articles.js with Pinia store for articles (state: groupedArticles, actions: fetchGroupedArticles)
- [ ] T078 [US1] Create frontend/src/store/filters.js with Pinia store for filter state (selectedSource, selectedCategory, dateRange)

### API Service Layer

- [ ] T079 [US1] Create frontend/src/services/articleService.js with getGroupedArticles() and getSources() methods using Axios

### Composables

- [ ] T080 [P] [US1] Create frontend/src/composables/useArticles.js with reactive article fetching logic
- [ ] T081 [P] [US1] Create frontend/src/composables/useSources.js with source listing logic

### UI Components

- [ ] T082 [P] [US1] Create frontend/src/components/common/AppHeader.vue with site title and navigation
- [ ] T083 [P] [US1] Create frontend/src/components/news/ArticleCard.vue to display single article (title, URL, category, source, timestamp)
- [ ] T084 [US1] Create frontend/src/components/news/ArticleGroup.vue to display articles from one source with source header and virtual scrolling
- [ ] T085 [US1] Install vue-virtual-scroll-list via npm for rendering 1000+ articles efficiently

### Views

- [ ] T086 [US1] Create frontend/src/views/ArticlesView.vue using ArticleGroup components to render all source groups
- [ ] T087 [US1] Configure Vue Router in frontend/src/router/index.js with route for ArticlesView
- [ ] T088 [US1] Update frontend/src/App.vue to use DefaultLayout and router-view

### Integration & Testing

- [ ] T089 [US1] Write component test in frontend/tests/components/ArticleCard.spec.js
- [ ] T090 [US1] Write integration test in frontend/tests/views/ArticlesView.spec.js to verify grouped display

**US1 Acceptance Test**:
1. Start backend: `docker-compose up backend mysql`
2. Start frontend: `cd frontend && npm run dev`
3. Open http://localhost:5173
4. Verify articles grouped by source (6 groups visible)
5. Verify each group shows source name, article titles, URLs, categories

---

## Phase 5: User Story 2 - Query and Filter News Data (Priority: P2)

**Goal**: Enable filtering news by source, category, time period via API and UI

**Independent Test**: Make API request filtering by source="sina" and category="ent", verify only matching articles returned. Use UI filter panel and verify results update.

**Depends on**: US1 (builds on display functionality)

### Backend API Enhancement

- [ ] T091 [US2] Add GET /news/articles endpoint in backend/app/api/v1/endpoints/news.py with query parameters (source, category, start_date, end_date, page, page_size)
- [ ] T092 [US2] Implement pagination logic in backend/app/services/news_service.py with get_articles() method supporting filters
- [ ] T093 [US2] Write unit tests in backend/tests/unit/test_services/test_news_service.py for filtered queries (source filter, category filter, date range filter, combined filters)
- [ ] T094 [US2] Write integration test in backend/tests/integration/test_news_api.py for GET /news/articles with various filter combinations

### Frontend Filter UI

- [ ] T095 [US2] Create frontend/src/components/news/FilterPanel.vue with dropdowns for source and category, date range picker (Element Plus components)
- [ ] T096 [US2] Update frontend/src/store/filters.js to include applyFilters() action that calls API with filter params
- [ ] T097 [US2] Create frontend/src/composables/useFilters.js with filter application logic
- [ ] T098 [US2] Update frontend/src/services/articleService.js with getArticles(filters) method
- [ ] T099 [US2] Integrate FilterPanel into frontend/src/views/ArticlesView.vue with reactive filter updates
- [ ] T100 [US2] Write component test in frontend/tests/components/FilterPanel.spec.js

**US2 Acceptance Test**:
1. Open web interface
2. Select source filter: "sina"
3. Verify only Sina articles displayed
4. Add category filter: "ent"
5. Verify only Sina entertainment articles displayed
6. Set date range: last 7 days
7. Verify articles within date range

---

## Phase 6: User Story 4 - Add New News Sources (Priority: P2)

**Goal**: Enable adding new scrapers without modifying core code

**Independent Test**: Create new scraper following BaseScraper pattern, add to database via API, verify it runs on schedule and data appears in queries

**Depends on**: US3 (extends scraper infrastructure)

### Scraper Management API

- [ ] T101 [US4] Add POST /scrapers endpoint in backend/app/api/v1/endpoints/scrapers.py to register new news source (create NewsSource record)
- [ ] T102 [US4] Add PUT /scrapers/{source_key}/enable endpoint in backend/app/api/v1/endpoints/scrapers.py
- [ ] T103 [US4] Add PUT /scrapers/{source_key}/disable endpoint in backend/app/api/v1/endpoints/scrapers.py
- [ ] T104 [US4] Add PUT /scrapers/{source_key}/config endpoint in backend/app/api/v1/endpoints/scrapers.py to update schedule_interval
- [ ] T105 [US4] Implement dynamic scraper loading in backend/app/services/scraper_service.py using importlib to load scraper modules by path
- [ ] T106 [US4] Update backend/app/tasks/scheduler.py to dynamically register jobs based on enabled NewsSource records
- [ ] T107 [US4] Write integration tests in backend/tests/integration/test_scraper_management.py for enable/disable/config endpoints

### Documentation

- [ ] T108 [P] [US4] Create backend/docs/adding_scrapers.md with guide on creating new scraper (inherit BaseScraper, implement required methods, register via API)

**US4 Acceptance Test**:
1. Create new scraper class inheriting from BaseScraper
2. POST to /scrapers with source_key="test_source", scraper_module="app.scrapers.test_scraper"
3. Verify source appears in GET /news/sources
4. Trigger scraper via POST /scrapers/test_source/trigger
5. Verify articles appear with source_key="test_source"

---

## Phase 7: User Story 5 - Monitor Scraper Health and Status (Priority: P3)

**Goal**: Provide visibility into scraper execution history and health

**Independent Test**: Check status endpoint or admin interface, verify last execution time, success/failure status, article counts for each scraper

**Depends on**: US3 (monitors scraper system)

### Status API Endpoints

- [ ] T109 [US5] Create GET /scrapers/status endpoint in backend/app/api/v1/endpoints/scrapers.py returning all scrapers with last run, status, next run time
- [ ] T110 [US5] Create GET /scrapers/{source_key}/runs endpoint in backend/app/api/v1/endpoints/scrapers.py with pagination for execution history
- [ ] T111 [US5] Create GET /news/statistics endpoint in backend/app/api/v1/endpoints/news.py returning aggregated stats (total articles, articles by source, articles by category)
- [ ] T112 [US5] Implement scraper health check logic in backend/app/services/scraper_service.py (check failure_count, last_run_at)
- [ ] T113 [US5] Write integration tests in backend/tests/integration/test_scraper_status.py for status and runs endpoints

### Health Dashboard UI

- [ ] T114 [P] [US5] Create frontend/src/views/DashboardView.vue to display scraper status grid (source, last run, status, article count)
- [ ] T115 [P] [US5] Create frontend/src/components/dashboard/ScraperStatusCard.vue showing individual scraper health with status icons
- [ ] T116 [P] [US5] Create frontend/src/components/dashboard/StatisticsPanel.vue showing total articles, source breakdown, category breakdown
- [ ] T117 [US5] Create frontend/src/services/scraperService.js with getScraperStatus() and getStatistics() methods
- [ ] T118 [US5] Create frontend/src/store/scrapers.js Pinia store for scraper status data
- [ ] T119 [US5] Add /dashboard route in frontend/src/router/index.js
- [ ] T120 [US5] Add dashboard link in frontend/src/components/common/AppHeader.vue navigation

**US5 Acceptance Test**:
1. Navigate to /dashboard
2. Verify 6 scraper status cards displayed
3. Verify each card shows: source name, last run time, status (idle/running/failed), article count
4. Verify statistics panel shows: total articles, breakdown by source, breakdown by category
5. Click on failed scraper (if any) to see error details

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final touches, optimization, deployment readiness

### Error Handling & Logging

- [ ] T121 [P] Create backend/app/utils/__init__.py
- [ ] T122 [P] Create backend/app/utils/helpers.py with utility functions (date formatting, URL normalization for hashing)
- [ ] T123 [P] Add global exception handler in backend/app/main.py for structured error responses
- [ ] T124 [P] Verify structured logging in all services (scraper_service, news_service) with context (source_key, article_count, duration)

### Performance Optimization

- [ ] T125 Verify database indexes exist (run migration, check MySQL with SHOW INDEX FROM news_articles)
- [ ] T126 Add query optimization: use SELECT specific columns instead of SELECT * in backend/app/services/news_service.py
- [ ] T127 Verify pagination implemented correctly (LIMIT/OFFSET or cursor-based) in news article queries

### Security & Configuration

- [ ] T128 Validate environment variables on startup in backend/app/core/config.py (DATABASE_URL, required settings)
- [ ] T129 Add input validation for all API endpoints using Pydantic models (already done via FastAPI, verify completeness)
- [ ] T130 Configure CORS properly in backend/app/main.py (restrict origins in production)

### Deployment Readiness

- [ ] T131 Build Docker images: `docker-compose build`
- [ ] T132 Run database migrations in Docker: `docker-compose exec backend alembic upgrade head`
- [ ] T133 Test full stack with Docker Compose: `docker-compose up -d`
- [ ] T134 Verify health checks: `curl http://localhost:8000/api/v1/health` and `curl http://localhost/`
- [ ] T135 Run full test suite: `docker-compose exec backend pytest` and `docker-compose exec frontend npm run test`

### Documentation

- [ ] T136 [P] Update README.md with project overview, architecture diagram, quick start (link to quickstart.md)
- [ ] T137 [P] Verify quickstart.md has accurate setup instructions (already created in plan phase)
- [ ] T138 [P] Generate API documentation: verify FastAPI Swagger UI at http://localhost:8000/docs

---

## Dependencies Between User Stories

```
US3 (Automated Collection) - FOUNDATIONAL
  ↓
US1 (View Aggregated News) - Depends on US3 (needs data)
  ↓
US2 (Query/Filter) - Depends on US1 (extends display)
  ↓
US4 (Add Sources) - Depends on US3 (extends scrapers)
  ↓
US5 (Monitor Health) - Depends on US3 (monitors scrapers)
```

**Critical Path**: Setup → Foundation → US3 → US1 → US2

**Parallel Opportunities**:
- After US3 completes: US4 and US5 can be developed in parallel
- Within US1: Frontend component development is highly parallelizable (T082-T085 can be done simultaneously)
- Within US3: Scraper refactoring (T045-T050) is fully parallel

---

## Parallel Execution Examples

### After Foundation Phase (T001-T041), these can run in parallel:

**Team A - Backend**:
- T042-T065 (US3: Scrapers and scheduling)

**Team B - Planning**:
- Review data model, prepare test data

### After US3 Completes (T042-T065), these can run in parallel:

**Team A - Backend**:
- T066-T071 (US1: News API endpoints)
- T091-T094 (US2: Filter API)
- T101-T107 (US4: Scraper management API)

**Team B - Frontend**:
- T072-T090 (US1: Frontend display)
- T095-T100 (US2: Filter UI)
- T114-T120 (US5: Dashboard UI)

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Include**:
- ✅ US3: Automated News Collection (collect data)
- ✅ US1: View Aggregated News (display data)

**MVP delivers**: A working news aggregation system that automatically collects news and displays it grouped by source.

**Exclude from MVP** (add later):
- US2: Query/Filter (nice-to-have)
- US4: Add Sources (extensibility)
- US5: Monitor Health (operational convenience)

### Incremental Delivery

1. **Sprint 1**: Setup + Foundation (T001-T041) - ~1 week
2. **Sprint 2**: US3 Automated Collection (T042-T065) - ~2 weeks
3. **Sprint 3**: US1 View Aggregated News (T066-T090) - ~1.5 weeks
4. **Sprint 4**: US2 Query/Filter (T091-T100) - ~1 week
5. **Sprint 5**: US4 + US5 (T101-T120) - ~1.5 weeks
6. **Sprint 6**: Polish & Deployment (T121-T138) - ~1 week

**Total Estimate**: ~8-9 weeks for full implementation

### Test-Driven Development (TDD) Workflow

For each user story:
1. Write contract/integration tests first (define expected behavior)
2. Run tests (they fail - RED)
3. Implement minimal code to pass tests (GREEN)
4. Refactor for quality while keeping tests passing (REFACTOR)
5. Verify 80% code coverage minimum (100% for scrapers, models, services)

---

## Task Summary

- **Total Tasks**: 138
- **Setup Phase**: 13 tasks (T001-T013)
- **Foundational Phase**: 28 tasks (T014-T041)
- **US3 (P1)**: 24 tasks (T042-T065)
- **US1 (P1)**: 25 tasks (T066-T090)
- **US2 (P2)**: 10 tasks (T091-T100)
- **US4 (P2)**: 8 tasks (T101-T108)
- **US5 (P3)**: 12 tasks (T109-T120)
- **Polish**: 18 tasks (T121-T138)

**Parallel Opportunities**: 45 tasks marked with [P] can run in parallel
**MVP Tasks**: 80 tasks (Setup + Foundation + US3 + US1)

---

## Next Steps

1. Review this task breakdown with team
2. Assign tasks to developers
3. Begin with Phase 1: Setup
4. Follow TDD workflow for each task
5. Track progress in project management tool
6. Run constitution checks at each phase gate
7. Use quickstart.md for development environment setup

**Ready to implement** ✅
