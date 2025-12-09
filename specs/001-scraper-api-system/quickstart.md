# Quickstart Guide: Web Scraper API System

**Feature**: 001-scraper-api-system
**Date**: 2025-12-08

This guide helps developers set up the development environment and run the news scraper system locally.

---

## Prerequisites

### Required Software

- **Python 3.13+**: [Download](https://www.python.org/downloads/)
- **Node.js 20+ & npm**: [Download](https://nodejs.org/)
- **MySQL 8.0+**: [Download](https://dev.mysql.com/downloads/mysql/)
- **Git**: [Download](https://git-scm.com/downloads)

### Recommended Tools

- **VS Code** with Python and Vue extensions
- **Postman** or **Insomnia** for API testing
- **MySQL Workbench** for database management

---

## Backend Setup (Python/FastAPI)

### 1. Create Python Virtual Environment

```bash
cd backend
python3.13 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

### 3. Configure MySQL Database

```bash
# Create database
mysql -u root -p
```

```sql
CREATE DATABASE news_scraper CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'news_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON news_scraper.* TO 'news_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. Configure Environment Variables

Create `.env` file in `backend/` directory:

```bash
# Database Configuration
DATABASE_URL=mysql+aiomysql://news_user:your_secure_password@localhost:3306/news_scraper

# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME="News Scraper API"
VERSION=1.0.0

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Logging
LOG_LEVEL=INFO

# APScheduler
SCHEDULER_TIMEZONE=Asia/Shanghai
SCHEDULER_JOBSTORE_URL=mysql+pymysql://news_user:your_secure_password@localhost:3306/news_scraper

# Scraper Configuration
SCRAPER_TIMEOUT=60
SCRAPER_MAX_CONCURRENT=6
SCRAPER_DEFAULT_INTERVAL=1800  # 30 minutes
```

### 5. Run Database Migrations

```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### 6. Start Backend Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the run script
python -m app.main
```

**Verify backend is running**:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

---

## Frontend Setup (Vue.js)

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment Variables

Create `.env` file in `frontend/` directory:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/api/v1

# App Configuration
VITE_APP_TITLE=News Scraper
VITE_DEFAULT_PAGE_SIZE=50
VITE_MAX_PAGE_SIZE=1000
```

### 3. Start Development Server

```bash
npm run dev
```

**Verify frontend is running**:
- Frontend: http://localhost:5173

---

## Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/contract/      # Contract tests only

# Run with verbose output
pytest -v
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm run test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

---

## Development Workflow

### 1. Start All Services

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: MySQL (if not running as service)
mysql.server start  # macOS
# Or: sudo systemctl start mysql  # Linux
```

### 2. Access Application

- **Frontend UI**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 3. Manual Scraper Testing

```bash
# Trigger a single scraper via API
curl -X POST http://localhost:8000/api/v1/scrapers/sina/trigger

# Or use Python script
cd backend
python -m app.scrapers.sina_scraper
```

### 4. View Logs

```bash
# Backend logs (console)
tail -f logs/app.log

# Database logs
# Check MySQL logs location:
# macOS: /usr/local/var/mysql/*.log
# Linux: /var/log/mysql/error.log
```

---

## Database Management

### View Tables

```sql
USE news_scraper;
SHOW TABLES;

-- View news articles
SELECT * FROM news_articles ORDER BY published_at DESC LIMIT 10;

-- View scraper runs
SELECT * FROM scraper_runs ORDER BY started_at DESC LIMIT 10;

-- View sources
SELECT * FROM news_sources;
```

### Common Queries

```sql
-- Article count by source
SELECT source_key, COUNT(*) as count
FROM news_articles
GROUP BY source_key;

-- Recent scraper failures
SELECT * FROM scraper_runs
WHERE status = 'failed'
ORDER BY started_at DESC
LIMIT 10;

-- Duplicate rate
SELECT
    COUNT(*) as total_runs,
    AVG(articles_duplicate * 100.0 / NULLIF(articles_scraped, 0)) as avg_duplicate_rate
FROM scraper_runs
WHERE status = 'success';
```

### Reset Database

```bash
# Drop all tables and recreate
alembic downgrade base
alembic upgrade head
```

---

## Docker Deployment (Recommended for Production)

### Prerequisites

- **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: [Install Docker Compose](https://docs.docker.com/compose/install/)

### Project Structure for Docker

```
├── backend/
│   ├── Dockerfile
│   ├── app/
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── .env
├── docker-compose.yml
└── .env.docker
```

### 1. Backend Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build for production
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files to nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

### 3. Frontend Nginx Configuration

Create `frontend/nginx.conf`:

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy to backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket proxy
    location /api/v1/scrapers/ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 4. Docker Compose Configuration

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: news_scraper_mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-root_password}
      MYSQL_DATABASE: ${MYSQL_DATABASE:-news_scraper}
      MYSQL_USER: ${MYSQL_USER:-news_user}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD:-news_password}
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./mysql/init:/docker-entrypoint-initdb.d  # Optional: init scripts
    networks:
      - news_scraper_network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p$$MYSQL_ROOT_PASSWORD"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: news_scraper_backend
    restart: unless-stopped
    depends_on:
      mysql:
        condition: service_healthy
    environment:
      DATABASE_URL: mysql+aiomysql://${MYSQL_USER:-news_user}:${MYSQL_PASSWORD:-news_password}@mysql:3306/${MYSQL_DATABASE:-news_scraper}
      SCHEDULER_JOBSTORE_URL: mysql+pymysql://${MYSQL_USER:-news_user}:${MYSQL_PASSWORD:-news_password}@mysql:3306/${MYSQL_DATABASE:-news_scraper}
      API_V1_PREFIX: /api/v1
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      ALLOWED_ORIGINS: http://localhost,http://localhost:3000,http://frontend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/logs:/app/logs
    networks:
      - news_scraper_network
    command: >
      sh -c "
        alembic upgrade head &&
        uvicorn app.main:app --host 0.0.0.0 --port 8000
      "

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: news_scraper_frontend
    restart: unless-stopped
    depends_on:
      - backend
    ports:
      - "80:80"
    networks:
      - news_scraper_network

volumes:
  mysql_data:
    driver: local

networks:
  news_scraper_network:
    driver: bridge
```

### 5. Docker Environment Configuration

Create `.env.docker` in project root:

```bash
# MySQL Configuration
MYSQL_ROOT_PASSWORD=strong_root_password_change_me
MYSQL_DATABASE=news_scraper
MYSQL_USER=news_user
MYSQL_PASSWORD=strong_password_change_me

# Application Configuration
LOG_LEVEL=INFO
SCHEDULER_TIMEZONE=Asia/Shanghai

# Security (change in production)
SECRET_KEY=your-secret-key-change-in-production
```

### 6. Deploy with Docker Compose

```bash
# Build and start all services
docker-compose --env-file .env.docker up -d --build

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql

# Check service status
docker-compose ps

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### 7. Production Deployment Commands

```bash
# Build images without starting
docker-compose build

# Start services in detached mode
docker-compose up -d

# Scale backend (if needed)
docker-compose up -d --scale backend=3

# View resource usage
docker stats

# Execute commands in running container
docker-compose exec backend bash
docker-compose exec mysql mysql -u news_user -p

# Restart specific service
docker-compose restart backend

# Update and restart
docker-compose pull
docker-compose up -d --build
```

### 8. Database Backup and Restore

```bash
# Backup database
docker-compose exec mysql mysqldump -u news_user -p news_scraper > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T mysql mysql -u news_user -p news_scraper < backup_20251208.sql

# Automated backup script (add to cron)
#!/bin/bash
BACKUP_DIR=/path/to/backups
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T mysql mysqldump -u news_user -pnews_password news_scraper | gzip > $BACKUP_DIR/backup_$DATE.sql.gz
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete  # Keep 7 days
```

### 9. Monitoring and Health Checks

```bash
# Check service health
docker-compose ps

# Backend health check
curl http://localhost:8000/api/v1/health

# Frontend health check
curl http://localhost/

# View container logs
docker-compose logs --tail=100 -f backend

# Monitor resource usage
docker stats news_scraper_backend news_scraper_frontend news_scraper_mysql
```

### 10. Production Best Practices

**Security**:
- Change default passwords in `.env.docker`
- Use secrets management (Docker secrets, vault)
- Enable HTTPS with Let's Encrypt (add nginx-proxy/traefik)
- Restrict MySQL port exposure (remove `ports:` in production)

**Performance**:
- Use volume mounts for logs and data persistence
- Configure resource limits in docker-compose.yml:
  ```yaml
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        memory: 2G
  ```

**Reliability**:
- Configure restart policies: `restart: unless-stopped`
- Use health checks for all services
- Implement log rotation
- Set up monitoring (Prometheus + Grafana)

**Backup**:
- Automate database backups (cron job)
- Store backups offsite (S3, Google Cloud Storage)
- Test restore procedures regularly

### 11. Troubleshooting Docker Deployment

**Issue**: `Cannot connect to MySQL`
**Solution**:
```bash
# Check MySQL is healthy
docker-compose ps mysql
# View MySQL logs
docker-compose logs mysql
# Verify network connectivity
docker-compose exec backend ping mysql
```

**Issue**: `Playwright browser not found`
**Solution**:
```bash
# Rebuild with --no-cache
docker-compose build --no-cache backend
# Or add to Dockerfile:
# RUN playwright install chromium
# RUN playwright install-deps chromium
```

**Issue**: `Port already in use`
**Solution**:
```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Instead of 8000:8000
```

---

## Troubleshooting

### Backend Issues

**Issue**: `ImportError: No module named 'app'`
**Solution**:
```bash
# Ensure you're in backend directory and venv is activated
cd backend
source venv/bin/activate
pip install -e .
```

**Issue**: `sqlalchemy.exc.OperationalError: (2003, "Can't connect to MySQL server")`
**Solution**:
- Verify MySQL is running: `mysql.server status` (macOS) or `sudo systemctl status mysql` (Linux)
- Check DATABASE_URL in `.env` file
- Test connection: `mysql -u news_user -p -h localhost`

**Issue**: `alembic.util.exc.CommandError: Target database is not up to date`
**Solution**:
```bash
alembic upgrade head
```

### Frontend Issues

**Issue**: `Failed to fetch` or CORS errors
**Solution**:
- Ensure backend is running on http://localhost:8000
- Check `ALLOWED_ORIGINS` in backend `.env`
- Verify `VITE_API_BASE_URL` in frontend `.env`

**Issue**: `npm ERR! code ELIFECYCLE`
**Solution**:
```bash
# Clear npm cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### Scraper Issues

**Issue**: `playwright._impl._api_types.Error: Executable doesn't exist`
**Solution**:
```bash
# Install Playwright browsers
playwright install chromium
```

**Issue**: Scraper timeout after 60 seconds
**Solution**:
- Increase `SCRAPER_TIMEOUT` in backend `.env`
- Check network connectivity
- Verify target website is accessible

---

## Development Best Practices

### Code Quality

```bash
# Backend: Run linters
cd backend
black .  # Code formatting
flake8 .  # Linting
mypy app/  # Type checking

# Frontend: Run linters
cd frontend
npm run lint
npm run format
```

### Pre-commit Checks

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash

echo "Running pre-commit checks..."

# Backend checks
cd backend
source venv/bin/activate
black --check .
mypy app/
pytest tests/unit/

# Frontend checks
cd ../frontend
npm run lint
npm run test:unit

echo "All checks passed!"
```

### Debugging

**Backend (VS Code)**:

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

**Frontend (VS Code)**:

Install Vue DevTools browser extension for debugging Vue components.

---

## Next Steps

1. Review [data-model.md](./data-model.md) for entity relationships
2. Check [contracts/](./contracts/) for API specifications
3. Read [research.md](./research.md) for technology decisions
4. Review constitution at `.specify/memory/constitution.md` for coding standards
5. Generate tasks with `/speckit.tasks` command

---

## Useful Commands

```bash
# Backend
uvicorn app.main:app --reload  # Start dev server
alembic upgrade head           # Run migrations
pytest --cov                   # Run tests with coverage
black .                        # Format code
mypy app/                      # Type check

# Frontend
npm run dev                    # Start dev server
npm run build                  # Production build
npm run test                   # Run tests
npm run lint                   # Lint code

# Database
mysql -u news_user -p          # Connect to MySQL
alembic revision --autogenerate -m "message"  # Create migration
alembic downgrade -1           # Rollback last migration

# Docker (optional future enhancement)
docker-compose up              # Start all services
docker-compose down            # Stop all services
```

---

## Support

- **Documentation**: See `specs/001-scraper-api-system/` directory
- **API Docs**: http://localhost:8000/docs
- **Issues**: Create GitHub issues for bugs/features
