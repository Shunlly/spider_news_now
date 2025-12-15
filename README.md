# 新闻聚合系统 (News Aggregator)

一个功能完善的新闻爬虫聚合系统，支持自动抓取、存储、全文搜索和监控多个新闻源的实时新闻。

## 功能特性

### 核心功能
- **多源爬取**: 支持新浪、腾讯、网易、第一财经、凤凰网、环球网等主流新闻网站
- **定时调度**: 基于 APScheduler 的自动定时爬取（默认 30 分钟）
- **去重机制**: 基于 SimHash 和 Bloom Filter 的智能去重
- **全文搜索**: 基于 Meilisearch 的高性能全文检索
- **对象存储**: 支持 RustFS/MinIO 存储新闻原文
- **数据持久化**: MySQL 存储，Redis 缓存

### Web 功能
- **响应式 UI**: 基于 Vue 3 + Element Plus 的现代化界面
- **高级筛选**: 按新闻源、分类、时间范围多维度筛选
- **监控面板**: 实时查看爬虫运行状态、成功率、抓取统计
- **执行历史**: 详细的爬虫运行记录和错误追踪
- **手动触发**: 支持一键手动触发爬虫运行

### API 功能
- **RESTful API**: 完整的 REST API 接口
- **自动文档**: Swagger/OpenAPI 自动生成接口文档
- **数据导出**: 支持 JSON、CSV、Excel 格式导出

## 技术架构

### 后端技术栈
- **框架**: FastAPI 0.115.5
- **数据库**: MySQL 8.0 (异步 aiomysql)
- **ORM**: SQLAlchemy 2.0 (异步模式)
- **缓存**: Redis 7.2
- **搜索引擎**: Meilisearch 1.11
- **对象存储**: RustFS (S3 兼容)
- **调度器**: APScheduler 4.0
- **爬虫**: Playwright + httpx

### 前端技术栈
- **框架**: Vue 3.5 (Composition API)
- **UI 组件**: Element Plus 2.9
- **状态管理**: Pinia 2.3
- **路由**: Vue Router 4.5
- **构建工具**: Vite 6.4
- **HTTP 客户端**: Axios 1.7

### 项目结构
```
spider_news_now/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/v1/         # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── db/             # 数据库配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic 模式
│   │   ├── scrapers/       # 爬虫实现
│   │   ├── services/       # 业务逻辑
│   │   ├── storage/        # 存储服务
│   │   └── tasks/          # 定时任务
│   ├── alembic/            # 数据库迁移
│   └── tests/              # 测试用例
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── api/           # API 配置
│   │   ├── components/    # Vue 组件
│   │   ├── router/        # 路由配置
│   │   ├── services/      # API 服务
│   │   ├── store/         # Pinia 状态
│   │   └── views/         # 页面视图
│   └── public/            # 静态资源
├── scripts/               # 部署脚本
├── docker-compose.yml     # 开发环境
└── docker-compose.prod.yml # 生产环境
```

## 快速开始

### Docker Compose 部署（推荐）

#### 1. 克隆项目
```bash
git clone https://github.com/Shunlly/spider_news_now.git
cd spider_news_now
```

#### 2. 启动服务
```bash
docker-compose up -d
```

#### 3. 访问应用
- 前端界面: http://localhost:8080
- API 文档: http://localhost:8001/docs
- RustFS 控制台: http://localhost:9011

### 生产环境部署

#### 1. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库密码等
```

#### 2. 启动生产服务
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 服务器部署（1Panel）

项目支持自动化部署，详见 `scripts/deploy.sh`:

```bash
# 部署最新版本（自动备份+清理）
./scripts/deploy.sh deploy

# 回滚到上一个版本
./scripts/deploy.sh rollback

# 查看当前状态
./scripts/deploy.sh status

# 手动清理旧镜像
./scripts/deploy.sh cleanup
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 8080 | 前端界面 |
| Backend | 8000 | 后端 API |
| MySQL | 33060 | 数据库 |
| Redis | 63790 | 缓存 |
| Meilisearch | 7701 | 搜索引擎 |
| RustFS API | 9010 | 对象存储 API |
| RustFS Console | 9011 | 对象存储控制台 |

## API 接口

### 新闻接口
- `GET /api/v1/news/articles` - 获取新闻列表（分页）
- `GET /api/v1/news/articles/{id}` - 获取新闻详情
- `GET /api/v1/news/sources` - 获取新闻源列表
- `GET /api/v1/news/statistics` - 获取统计数据
- `GET /api/v1/news/search` - 全文搜索

### 爬虫管理接口
- `GET /api/v1/scrapers/status` - 获取所有爬虫状态
- `GET /api/v1/scrapers/{source_key}/runs` - 获取爬虫执行历史
- `POST /api/v1/scrapers/{source_key}/trigger` - 手动触发爬虫
- `POST /api/v1/scrapers/{source_key}/enable` - 启用爬虫
- `POST /api/v1/scrapers/{source_key}/disable` - 禁用爬虫

### 导出接口
- `POST /api/v1/export/news` - 导出新闻数据

### 健康检查
- `GET /api/v1/health` - 服务健康检查

## 配置说明

### 环境变量

```bash
# 数据库
MYSQL_ROOT_PASSWORD=your_password
MYSQL_DATABASE=news_scraper
MYSQL_USER=news_user
MYSQL_PASSWORD=your_password

# Redis
REDIS_URL=redis://redis:6379/0

# Meilisearch
MEILI_MASTER_KEY=your_key

# RustFS
RUSTFS_ACCESS_KEY=rustfsadmin
RUSTFS_SECRET_KEY=your_password

# 应用
LOG_LEVEL=INFO
ALLOWED_ORIGINS=*
```

### 添加新的新闻源

1. 在 `backend/app/scrapers/` 创建爬虫类
2. 继承 `BaseScraper` 并实现 `scrape()` 方法
3. 在数据库中添加新闻源配置
4. 重启服务即可自动调度

## 开发指南

### 本地开发

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

### 运行测试
```bash
cd backend
pytest tests/ -v
```

### 数据库迁移
```bash
# 创建新迁移
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 常见问题

### 1. 前端无法连接后端 API
检查 nginx 配置中的后端地址是否正确指向 `news_scraper_backend:8000`

### 2. 爬虫无法运行
- 检查网络连接
- 查看 `backend/logs/` 日志文件
- 确认目标网站是否可访问

### 3. 搜索功能不工作
确认 Meilisearch 服务正常运行，检查索引是否创建成功

## License

本项目采用 MIT 许可证

## 作者

- [@Shunlly](https://github.com/Shunlly)
