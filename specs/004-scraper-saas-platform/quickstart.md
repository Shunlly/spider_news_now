# Quickstart: 全栈爬虫 SaaS 平台

**Branch**: `004-scraper-saas-platform` | **Date**: 2025-12-18

## 快速启动指南

本文档帮助开发者快速搭建开发环境并运行项目。

---

## 1. 前置要求

### 系统要求

- **操作系统**: macOS / Linux / Windows (WSL2)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Node.js**: 20.x LTS (前端开发)
- **Python**: 3.11+ (后端开发)
- **pnpm**: 8.x (推荐的包管理器)

### 检查环境

```bash
# 检查 Docker
docker --version
docker-compose --version

# 检查 Node.js
node --version
pnpm --version

# 检查 Python
python3 --version
```

---

## 2. 项目结构

```text
spider_news_now/
├── backend/                  # 后端服务
│   ├── app/                  # 应用代码
│   │   ├── api/v1/          # API 端点
│   │   ├── core/            # 核心配置
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic 模型
│   │   ├── services/        # 业务逻辑
│   │   ├── scrapers/        # 爬虫实现
│   │   ├── storage/         # 存储适配器
│   │   └── tasks/           # Celery 任务
│   ├── alembic/             # 数据库迁移
│   ├── tests/               # 测试用例
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # 前端应用
│   ├── src/
│   │   ├── components/      # React 组件
│   │   ├── pages/           # 页面
│   │   ├── hooks/           # 自定义 Hooks
│   │   ├── services/        # API 服务
│   │   ├── stores/          # 状态管理
│   │   └── types/           # TypeScript 类型
│   ├── tests/e2e/           # E2E 测试
│   └── Dockerfile
├── specs/                    # 功能规格文档
├── docker-compose.yml        # 开发环境
└── docker-compose.prod.yml   # 生产环境
```

---

## 3. 开发环境启动

### 3.1 克隆项目

```bash
git clone https://github.com/Shunlly/spider_news_now.git
cd spider_news_now
git checkout 004-scraper-saas-platform
```

### 3.2 启动依赖服务

```bash
# 启动 MySQL, Redis, MinIO, Meilisearch
docker-compose up -d mysql redis minio meilisearch
```

### 3.3 后端开发

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 复制环境变量
cp .env.example .env
# 编辑 .env 配置数据库等信息

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

### 3.4 启动 Celery Worker

```bash
# 新开一个终端
cd backend
source venv/bin/activate

# 启动 Worker
celery -A app.tasks.celery_app worker --loglevel=info

# (可选) 启动 Beat 调度器
celery -A app.tasks.celery_app beat --loglevel=info
```

### 3.5 前端开发

```bash
cd frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

---

## 4. 访问服务

| 服务 | URL | 说明 |
|-----|-----|------|
| 前端 | http://localhost:5173 | Vite 开发服务器 |
| 后端 API | http://localhost:8000 | FastAPI |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| MinIO 控制台 | http://localhost:9001 | 对象存储管理 |
| Meilisearch | http://localhost:7700 | 搜索引擎 |

---

## 5. 开发工作流

### 5.1 后端开发

```bash
# 创建新的数据库迁移
alembic revision --autogenerate -m "add new table"

# 运行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 运行测试
pytest tests/ -v

# 运行特定测试
pytest tests/unit/test_dedup.py -v

# 代码检查
ruff check app/
```

### 5.2 前端开发

```bash
# 运行开发服务器
pnpm dev

# 构建生产版本
pnpm build

# 运行 E2E 测试
pnpm test:e2e

# 代码检查
pnpm lint
```

### 5.3 Git 工作流

```bash
# 创建功能分支
git checkout -b feature/add-new-scraper

# 提交代码 (Conventional Commits)
git commit -m "feat(scraper): add twitter thread scraper"

# 推送分支
git push origin feature/add-new-scraper
```

---

## 6. 环境变量

### 后端 (.env)

```bash
# 数据库
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/scraper_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=120

# 存储
STORAGE_PROVIDER=minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=scraper-data
MINIO_SECURE=false

# Meilisearch
MEILI_URL=http://localhost:7700
MEILI_MASTER_KEY=your-master-key

# 日志
LOG_LEVEL=DEBUG
LOG_TO_CONSOLE=true
LOG_TO_FILE=false
```

### 前端 (.env.local)

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/api/v1/dashboard/ws
```

---

## 7. 常见问题

### Q: 数据库连接失败

```bash
# 检查 MySQL 是否运行
docker-compose ps mysql

# 查看日志
docker-compose logs mysql
```

### Q: Celery Worker 无法连接 Redis

```bash
# 检查 Redis 是否运行
docker-compose ps redis

# 测试连接
redis-cli ping
```

### Q: MinIO 上传失败

```bash
# 检查 MinIO 状态
docker-compose logs minio

# 确保 bucket 已创建
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/scraper-data
```

### Q: 前端 API 请求 CORS 错误

确保后端 CORS 配置正确:

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 8. 下一步

1. 阅读 [spec.md](./spec.md) 了解功能需求
2. 阅读 [data-model.md](./data-model.md) 了解数据结构
3. 阅读 [research.md](./research.md) 了解技术决策
4. 查看 [contracts/api-v1.yaml](./contracts/api-v1.yaml) 了解 API 规范

---

## 9. 联系方式

- **项目仓库**: https://github.com/Shunlly/spider_news_now
- **Issue 反馈**: https://github.com/Shunlly/spider_news_now/issues
