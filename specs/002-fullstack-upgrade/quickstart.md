# Quickstart Guide: 002-fullstack-upgrade

**Date**: 2025-12-14
**Audience**: 开发者

---

## 1. 环境准备

### 1.1 系统要求

| 组件 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Python | 3.10 | 3.12 |
| Node.js | 18.x | 20.x |
| pnpm | 8.x | 9.x |
| Docker | 24.x | 25.x |
| MySQL | 8.0 | 8.0 |
| Redis | 7.x | 7.2 |

### 1.2 克隆项目

```bash
git clone https://github.com/your-org/spider_news_now.git
cd spider_news_now
git checkout 002-fullstack-upgrade
```

---

## 2. Docker 一键启动 (推荐)

### 2.1 启动所有服务

```bash
# 构建并启动所有容器
docker-compose up -d

# 查看服务状态
docker-compose ps
```

**服务列表**:

| 服务 | 端口 | 说明 |
|------|------|------|
| backend | 8000 | FastAPI 后端 |
| frontend | 3000 | React 前端 |
| mysql | 3306 | MySQL 数据库 |
| redis | 6379 | Redis 缓存 |
| meilisearch | 7700 | 全文检索 |
| minio | 9000/9001 | 对象存储 |

### 2.2 访问服务

```
# 管理后台
http://localhost:3000

# API 文档
http://localhost:8000/docs

# Meilisearch 控制台
http://localhost:7700

# MinIO 控制台
http://localhost:9001
```

### 2.3 停止服务

```bash
docker-compose down
# 保留数据卷: docker-compose down
# 删除数据卷: docker-compose down -v
```

---

## 3. 本地开发环境

### 3.1 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 安装 Playwright 浏览器
playwright install chromium

# 复制环境配置
cp .env.example .env
# 编辑 .env 配置数据库等信息
```

### 3.2 数据库迁移

```bash
# 确保 MySQL 已启动
# 执行迁移
alembic upgrade head
```

### 3.3 启动后端

```bash
# 开发模式 (热重载)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用脚本
python -m app.main
```

### 3.4 前端设置

```bash
cd frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

**访问**: http://localhost:5173

---

## 4. 配置说明

### 4.1 后端配置 (.env)

```ini
# 数据库
DATABASE_URL=mysql+aiomysql://user:pass@localhost:3306/spider_news

# Redis
REDIS_URL=redis://localhost:6379/0

# Meilisearch
MEILISEARCH_URL=http://localhost:7700
MEILISEARCH_API_KEY=your_master_key

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=spider-news

# Twitter API (可选)
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=

# Telegram (可选)
TELEGRAM_BOT_TOKEN=
```

### 4.2 前端配置 (.env)

```ini
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 5. 功能验证

### 5.1 检查服务健康

```bash
# API 健康检查
curl http://localhost:8000/api/v1/health

# 期望响应
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected",
    "meilisearch": "connected",
    "minio": "connected"
  }
}
```

### 5.2 触发爬虫测试

```bash
# 触发新浪爬虫
curl -X POST http://localhost:8000/api/v1/scrapers/sina/trigger

# 查看爬虫状态
curl http://localhost:8000/api/v1/scrapers/status
```

### 5.3 全文检索测试

```bash
# 搜索新闻
curl "http://localhost:8000/api/v1/search?q=人工智能&type=news"
```

---

## 6. 常见问题

### Q1: 数据库连接失败

```
Error: Can't connect to MySQL server
```

**解决**: 确保 MySQL 服务已启动，检查 .env 中的 DATABASE_URL 配置

### Q2: Redis 连接失败

```
Error: Connection refused (redis://localhost:6379)
```

**解决**: 启动 Redis 服务 `docker-compose up -d redis`

### Q3: Meilisearch 索引错误

```
Error: Index not found
```

**解决**: 系统会自动创建索引，首次启动可能需要等待几秒

### Q4: 前端构建失败

```
Error: Cannot find module '@arco-design/web-react'
```

**解决**: 删除 node_modules 并重新安装 `rm -rf node_modules && pnpm install`

---

## 7. 开发工作流

### 7.1 添加新的社交平台爬虫

1. 创建爬虫类 `backend/app/scrapers/new_platform_scraper.py`
2. 继承 `BaseScraper` 基类
3. 实现 `scrape()`, `parse()`, `validate()` 方法
4. 在数据库注册新的 source

### 7.2 修改前端组件

1. 组件位于 `frontend/src/components/`
2. 遵循 Glassmorphism 设计规范
3. 使用 Arco Design + Tailwind CSS

### 7.3 添加 API 端点

1. 路由定义在 `backend/app/api/v1/endpoints/`
2. 创建 Pydantic Schema 在 `backend/app/schemas/`
3. 业务逻辑在 `backend/app/services/`

---

## 8. 运行测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
pnpm test

# 覆盖率报告
pytest --cov=app --cov-report=html
```
