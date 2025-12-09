# Implementation Plan: Web Scraper API System

**Branch**: `001-scraper-api-system` | **Date**: 2025-12-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-scraper-api-system/spec.md`

## Summary

Build a comprehensive news aggregation system that automatically collects articles from 6 existing news sources (Sina, QQ, Wangyi, Yicai, Huanqiu, Ifeng), stores them in MySQL, and provides a RESTful API and Vue.js web interface for querying and viewing news grouped by source.

**Technical Approach**:
- **Backend**: FastAPI (Python 3.13) for async-first REST API with automatic Swagger documentation
- **Database**: MySQL with SQLAlchemy 2.0 ORM providing type-safe async queries and Alembic migrations
- **Scheduling**: APScheduler 4.0 for in-process task scheduling without message broker overhead
- **Frontend**: Vue 3 + Vite with Pinia state management and Element Plus UI components
- **Architecture**: Layered design with clear separation: scrapers → services → API → frontend

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI 0.115.5, SQLAlchemy 2.0.36, Pydantic 2.10.3, APScheduler 4.0+, Vue 3 (latest), Axios
**Storage**: MySQL 8.0+ with aiomysql async driver
**Testing**: pytest 8.3.4, pytest-asyncio 0.24.0, httpx 0.28.1 (backend); Vitest (frontend)
**Target Platform**: Linux/macOS server (backend), modern browsers (frontend)
**Project Type**: Web application (backend + frontend separation)
**Performance Goals**: API response <2s for 1000 articles, scraper completion <60s each, UI load <3s
**Constraints**: 10,000 articles minimum capacity, 95% scraper success rate, <1% duplicate rate
**Scale/Scope**: 6 news sources initially, extensible to dozens; single-instance deployment initially

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Reference: `.specify/memory/constitution.md` for complete quality gates.

### Pre-Implementation Gates (verify now)

- [x] Feature specification approved and unambiguous (no [NEEDS CLARIFICATION])
- [x] Implementation plan includes constitution compliance checks
- [x] Test strategy defined (unit + integration test plan written)
- [x] Performance targets identified and measurable

**Status**: ✅ PASS - All pre-implementation gates satisfied

### Implementation Gates (verify during development)

- [ ] All tests written and passing (Red-Green-Refactor cycle followed)
- [ ] Code coverage meets minimum 80% threshold (100% for critical paths)
- [ ] Linting and formatting checks pass with zero warnings
- [ ] Type checking passes (mypy or equivalent) with no type errors
- [ ] All public APIs/functions have complete docstrings
- [ ] Code review completed with constitutional compliance verified

### Deployment Gates (verify before production)

- [ ] Integration tests pass in staging environment
- [ ] Performance benchmarks meet SLA targets
- [ ] Error handling tested (network failures, timeouts, invalid data)
- [ ] Logging verified (structured logs with appropriate levels)
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured for new functionality

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

```text
# Web application structure (backend + frontend)
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── api/                       # API routes
│   │   ├── __init__.py
│   │   └── v1/                    # API versioning
│   │       ├── __init__.py
│   │       ├── endpoints/
│   │       │   ├── __init__.py
│   │       │   ├── news.py        # News article endpoints
│   │       │   ├── scrapers.py    # Scraper management endpoints
│   │       │   └── health.py      # Health check endpoints
│   │       └── router.py          # Route aggregator
│   ├── core/                      # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py              # Settings (Pydantic Settings)
│   │   ├── security.py            # Authentication/authorization
│   │   └── logging.py             # Logging configuration
│   ├── db/                        # Database layer
│   │   ├── __init__.py
│   │   ├── base.py                # SQLAlchemy base class
│   │   ├── session.py             # Async session management
│   │   └── init_db.py             # Database initialization
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── news_article.py        # News article model
│   │   ├── news_source.py         # News source model
│   │   └── scraper_run.py         # Scraper run model
│   ├── schemas/                   # Pydantic schemas (API contracts)
│   │   ├── __init__.py
│   │   ├── news.py                # News request/response schemas
│   │   └── scraper.py             # Scraper schemas
│   ├── services/                  # Business logic layer
│   │   ├── __init__.py
│   │   ├── news_service.py        # News article operations
│   │   ├── scraper_service.py     # Scraper orchestration
│   │   └── duplicate_service.py   # Duplicate detection logic
│   ├── scrapers/                  # Web scraper modules
│   │   ├── __init__.py
│   │   ├── base.py                # Base scraper class
│   │   ├── sina_scraper.py        # Refactored with async
│   │   ├── qq_scraper.py
│   │   ├── wangyi_scraper.py
│   │   ├── yicai_scraper.py
│   │   ├── huanqiu_scraper.py
│   │   └── ifeng_scraper.py
│   ├── tasks/                     # Background tasks
│   │   ├── __init__.py
│   │   ├── scheduler.py           # APScheduler configuration
│   │   └── scraper_tasks.py       # Scheduled scraping tasks
│   └── utils/                     # Utility functions
│       ├── __init__.py
│       └── helpers.py
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── contract/                  # Scraper output schema tests
│   │   └── test_scraper_schemas.py
│   ├── integration/               # Integration tests
│   │   ├── test_api_endpoints.py
│   │   └── test_database.py
│   └── unit/                      # Unit tests mirroring source structure
│       ├── test_services/
│       └── test_scrapers/
├── alembic/                       # Database migrations
│   ├── versions/
│   └── env.py
├── .env                           # Environment variables
├── .env.example                   # Example environment file
├── alembic.ini                    # Alembic configuration
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
└── README.md

frontend/
├── src/
│   ├── api/                       # Axios instance, endpoints
│   │   ├── axios.js
│   │   └── endpoints.js
│   ├── assets/                    # Static assets
│   │   ├── styles/
│   │   └── images/
│   ├── components/
│   │   ├── common/                # Reusable components
│   │   │   ├── AppHeader.vue
│   │   │   └── AppFooter.vue
│   │   └── news/                  # Feature-specific components
│   │       ├── ArticleCard.vue
│   │       ├── ArticleList.vue
│   │       ├── ArticleGroup.vue   # Source grouping component
│   │       └── FilterPanel.vue
│   ├── composables/               # Reusable composition logic
│   │   ├── useArticles.js
│   │   ├── useFilters.js
│   │   └── useDateRange.js
│   ├── layouts/                   # Layout wrappers
│   │   └── DefaultLayout.vue
│   ├── router/
│   │   └── index.js               # Vue Router configuration
│   ├── services/                  # API calls
│   │   ├── articleService.js
│   │   └── filterService.js
│   ├── store/                     # Pinia stores
│   │   ├── articles.js
│   │   └── filters.js
│   ├── utils/                     # Helper functions
│   │   ├── dateUtils.js
│   │   └── formatters.js
│   ├── views/                     # Page components
│   │   ├── HomeView.vue
│   │   └── ArticlesView.vue
│   ├── App.vue
│   └── main.js
├── public/                        # Public static files
├── tests/                         # Frontend tests
├── .env                           # Environment variables
├── vite.config.js                 # Vite configuration
├── package.json
└── README.md

news_now/                          # Existing scrapers (to be refactored)
├── sina_news_crawler.py
├── qq_news_crawler.py
├── wangyi_news_crawler.py
├── yicai_news_crawler.py
├── huanqiu_news_crawler.py
├── ifeng_news_crawler.py
└── news_now_client.py
```

**Structure Decision**: Selected **Web Application** structure (Option 2) with backend/frontend separation. This provides:
- Clear separation of concerns between API and UI
- Independent deployment and scaling of backend/frontend
- Technology-appropriate organization (Python backend, JavaScript frontend)
- Easy integration with existing scrapers in `news_now/` folder

## Complexity Tracking

**No constitutional violations identified.** The chosen architecture aligns with constitution principles:
- ✅ Extensibility First: Plugin architecture for scrapers, clear base class pattern
- ✅ Testing Discipline: Clear test structure (unit/integration/contract)
- ✅ Code Quality: Type-safe ORM, Pydantic validation, mypy support
- ✅ Maintainability: Layered architecture, clear separation of concerns
- ✅ Consistency & Performance: Async-first design, indexed database queries

---

## Phase 0: Research (Completed)

See [research.md](./research.md) for comprehensive technology evaluation and decisions.

## Phase 1: Design & Contracts (Completed)

### Deliverables

1. **data-model.md**: Complete entity definitions with SQLAlchemy models and Pydantic schemas
   - NewsArticle: 12 fields with composite indexes for query optimization
   - NewsSource: Source management with scraper configuration  
   - ScraperRun: Execution history tracking
   - Entity relationships and validation rules defined

2. **contracts/news-api.md**: RESTful API contracts for news operations
   - GET /api/v1/news/articles: Paginated article retrieval with filtering
   - GET /api/v1/news/articles/{id}: Single article retrieval
   - GET /api/v1/news/articles/grouped: Source-grouped article display
   - GET /api/v1/news/sources: Source listing
   - GET /api/v1/news/statistics: Aggregated statistics

3. **contracts/scraper-api.md**: Scraper management endpoints
   - GET /api/v1/scrapers/status: All scraper status
   - GET /api/v1/scrapers/{source_key}/runs: Execution history
   - POST /api/v1/scrapers/{source_key}/trigger: Manual triggering
   - PUT /api/v1/scrapers/{source_key}/enable|disable: Source control
   - GET /api/v1/health: Health check endpoint
   - WebSocket /api/v1/scrapers/ws: Real-time updates

4. **quickstart.md**: Developer setup guide
   - Prerequisites and installation steps
   - Backend and frontend configuration
   - Database setup and migrations
   - Docker deployment (production)
   - Testing instructions
   - Troubleshooting guide

5. **CLAUDE.md**: Updated agent context with technology stack

### Design Decisions

- **API Versioning**: `/api/v1/` prefix for future compatibility
- **Pagination**: Default 50 items, max 1000 per page
- **Rate Limiting**: 100 requests/minute per IP
- **Duplicate Detection**: SHA-256 hash-based with URL and content comparison
- **Indexing Strategy**: Composite index on (source, category, date) for common queries
- **Error Format**: Consistent JSON structure with error codes
- **Deployment**: Docker Compose with separate containers for backend, frontend, MySQL
- **Nginx Proxy**: Frontend serves as reverse proxy to backend API

---

## Constitution Check (Post-Design Re-evaluation)

### Pre-Implementation Gates

- [x] Feature specification approved and unambiguous
- [x] Implementation plan includes constitution compliance checks
- [x] Test strategy defined (pytest, httpx, Vitest)
- [x] Performance targets identified (API <2s, scraper <60s, UI <3s)

**Status**: ✅ PASS

### Design Compliance

- [x] **Extensibility First**: Plugin architecture for scrapers with base class, config-driven scheduling
- [x] **Testing Discipline**: Three-tier testing (unit/integration/contract), pytest+httpx+Vitest
- [x] **Code Quality**: Type-safe models (SQLAlchemy + Pydantic), mypy enforcement
- [x] **Maintainability**: Layered architecture (scrapers → services → API → UI), clear separation
- [x] **Consistency & Performance**: Async-first, indexed queries, pagination, duplicate detection

**Violations**: None identified

### Deployment Compliance

- [x] **Containerization**: Docker + Docker Compose for consistent environments
- [x] **Health Checks**: Implemented for all services (MySQL, backend, frontend)
- [x] **Observability**: Structured logging, health endpoints, resource monitoring
- [x] **Backup Strategy**: Automated MySQL backups with retention policy
- [x] **Security**: Environment-based secrets, nginx proxy, resource limits

**Status**: ✅ READY FOR IMPLEMENTATION

---

## Next Steps

1. **Run `/speckit.tasks`** to generate actionable task breakdown from this plan
2. **Review generated tasks.md** for dependency-ordered implementation steps
3. **Begin Phase 2: Implementation** following TDD cycle (tests → code → refactor)
4. **Reference quickstart.md** for local development setup
5. **Use docker-compose.yml** for production-like testing environment

---

## Summary

The implementation plan is complete with:
- ✅ Technology stack selected and researched (Phase 0)
- ✅ Data models designed with relationships and validations (Phase 1)
- ✅ API contracts defined with versioning and error handling (Phase 1)
- ✅ Development and deployment guides created (Phase 1)
- ✅ Constitutional compliance verified (no violations)
- ✅ Ready for task generation and implementation

**Branch**: `001-scraper-api-system`
**Spec**: [spec.md](./spec.md)
**Research**: [research.md](./research.md)
**Data Model**: [data-model.md](./data-model.md)
**Contracts**: [contracts/](./contracts/)
**Quickstart**: [quickstart.md](./quickstart.md)
