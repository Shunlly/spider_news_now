# spider_news_now Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-20

## Active Technologies

- Python 3.12+ + FastAPI 0.115.5, SQLAlchemy 2.0.36, Pydantic 2.10.3, APScheduler 4.0+, Vue 3, Axios
- Authentication: JWT + Slider Captcha (RBAC with admin/user roles)
- Database: MySQL 8.0 with UUID primary keys for users

## Project Structure

```text
backend/
  app/
    api/v1/endpoints/    # API routes
    core/                # Config, security, dependencies
    models/              # SQLAlchemy models
    schemas/             # Pydantic schemas
    services/            # Business logic
    tasks/               # Scheduled tasks (APScheduler)
  alembic/versions/      # Database migrations
  tests/                 # Unit and integration tests
frontend/
  src/
    api/                 # API service layer
    components/          # Vue components
    pages/               # Page components
    stores/              # Zustand state management
```

## Commands

```bash
# Backend
cd backend && ./venv/bin/python -m pytest tests/ -v
cd backend && ./venv/bin/ruff check .

# Docker development
docker-compose up -d
docker-compose logs backend --tail 50

# Database migrations
docker-compose exec backend alembic upgrade head
docker-compose exec backend python scripts/verify_migration.py
```

## Code Style

- Python: Follow PEP 8, use type hints, Chinese comments for core logic
- All business tables include `user_id` foreign key for data isolation
- Use `get_current_user` dependency for authenticated endpoints
- Use `require_admin` dependency for admin-only endpoints

## Recent Changes

- 003-auth-rbac-security: JWT authentication, slider captcha, RBAC (admin/user), data isolation, rate limiting
- 001-scraper-api-system: FastAPI backend, news scrapers, APScheduler tasks

## Auth Endpoints

- `POST /api/v1/auth/captcha` - Generate slider captcha
- `POST /api/v1/auth/login` - User login with captcha verification
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user info

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
