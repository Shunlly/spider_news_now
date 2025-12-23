# 新闻聚合系统 (News Aggregator)

一个功能完善的新闻爬虫聚合系统，支持自动抓取、存储、全文搜索和监控多个新闻源的实时新闻。

## 功能特性

### 核心功能
- **多源爬取**: 支持新浪、腾讯、网易、第一财经、凤凰网、环球网等主流新闻网站
- **社交媒体**: 支持 Telegram 和 Twitter/X 数据采集
- **定时调度**: 基于 APScheduler 的自动定时爬取（默认 30 分钟）
- **去重机制**: 基于 SimHash 和 Bloom Filter 的智能去重
- **全文搜索**: 基于 Meilisearch 的高性能全文检索（< 500ms SLA）
- **对象存储**: 支持 RustFS/MinIO 存储新闻原文
- **数据持久化**: MySQL 存储，Redis 缓存

### Web 功能
- **响应式 UI**: 基于 React 18 + TailwindCSS 的现代化界面
- **用户认证**: JWT Token 认证，支持多用户和权限管理
- **多租户支持**: 完整的 SaaS 多租户数据隔离
- **RBAC 权限**: 基于角色的访问控制（超级管理员、租户管理员、普通用户）
- **配额管理**: 每日采集配额和并发任务限制
- **高级筛选**: 按新闻源、分类、时间范围多维度筛选
- **监控面板**: 实时查看爬虫运行状态、成功率、抓取统计
- **审计日志**: 完整的操作审计和安全日志
- **执行历史**: 详细的爬虫运行记录和错误追踪
- **手动触发**: 支持一键手动触发爬虫运行
- **数据导出**: 支持 CSV、JSON、Excel 格式导出

### 运维功能
- **Prometheus 监控**: 系统和应用指标采集
- **Grafana 仪表板**: 可视化监控面板
- **健康检查**: 完整的服务健康检查机制
- **CI/CD**: GitHub Actions 自动化部署

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
- **框架**: React 18.3 (Hooks + TypeScript)
- **状态管理**: Zustand 5.0
- **路由**: React Router 6.28
- **UI**: TailwindCSS 3.4 + Lucide Icons
- **图表**: Recharts 2.14
- **构建工具**: Vite 7.3
- **HTTP 客户端**: Axios 1.7

### 监控技术栈
- **指标采集**: Prometheus 2.51
- **可视化**: Grafana 10.4
- **系统监控**: Node Exporter, MySQL Exporter, Redis Exporter

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
├── frontend/               # 前端应用 (React)
│   ├── src/
│   │   ├── api/           # API 配置
│   │   ├── components/    # React 组件
│   │   ├── hooks/         # 自定义 Hooks
│   │   ├── pages/         # 页面组件
│   │   ├── services/      # API 服务
│   │   └── stores/        # Zustand 状态
│   └── public/            # 静态资源
├── docker/                 # Docker 配置
│   ├── prometheus/        # Prometheus 配置
│   └── grafana/           # Grafana 配置
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
- API 文档: http://localhost:8001/api/v1/docs
- ReDoc: http://localhost:8001/api/v1/redoc
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

### GitHub Actions 自动部署

项目支持通过 GitHub Actions 自动部署到服务器：

1. 在 GitHub 仓库设置中配置 Secrets：
   - `SERVER_HOST`: 服务器地址
   - `SERVER_USER`: SSH 用户名
   - `SERVER_SSH_KEY`: SSH 私钥
   - `GHCR_TOKEN`: GitHub Container Registry Token
   - 其他环境变量（数据库密码等）

2. 推送到 `main` 分支自动触发部署

3. 支持清洁部署（删除所有数据重新部署）：
   - 在 Actions 页面手动触发，勾选 "Clean deploy"

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 8080 | 前端界面 |
| Backend | 8001 | 后端 API |
| MySQL | 33060 | 数据库 |
| Redis | 63790 | 缓存 |
| Meilisearch | 7701 | 搜索引擎 |
| RustFS API | 9010 | 对象存储 API |
| RustFS Console | 9011 | 对象存储控制台 |
| Prometheus | 9090 | 监控指标 |
| Grafana | 3000 | 监控面板 |

## 认证说明

### 默认管理员账户
首次部署时会自动创建管理员账户：
- 用户名: `admin`
- 密码: 通过环境变量 `ADMIN_PASSWORD` 设置（默认: `admin123`）

### JWT Token 认证
所有 API 接口（除健康检查和验证码外）需要 JWT Token 认证。

#### 登录流程
```bash
# 步骤 1: 获取图形验证码
CAPTCHA_RESPONSE=$(curl -s http://localhost:8001/api/v1/auth/captcha)
CAPTCHA_TOKEN=$(echo $CAPTCHA_RESPONSE | jq -r '.token')
CAPTCHA_CODE=$(echo $CAPTCHA_RESPONSE | jq -r '.code')  # 测试环境返回验证码

# 步骤 2: 使用验证码登录
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"admin\",
    \"password\": \"your_password\",
    \"captcha_token\": \"$CAPTCHA_TOKEN\",
    \"captcha_code\": \"$CAPTCHA_CODE\"
  }"

# 响应示例
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### 使用 Token 访问 API
```bash
# 设置 Token 变量
TOKEN="your_access_token"

# 访问需要认证的 API
curl http://localhost:8001/api/v1/news/articles \
  -H "Authorization: Bearer $TOKEN"

# 刷新 Token
curl -X POST http://localhost:8001/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your_refresh_token"}'
```

## API 接口

### 认证接口
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户登出
- `POST /api/v1/auth/refresh` - 刷新 Token
- `GET /api/v1/auth/captcha` - 获取图形验证码

### 新闻接口
- `GET /api/v1/news/articles` - 获取新闻列表（分页）
- `GET /api/v1/news/articles/{id}` - 获取新闻详情
- `GET /api/v1/news/sources` - 获取新闻源列表
- `GET /api/v1/news/statistics` - 获取统计数据

### 搜索接口
- `GET /api/v1/search` - 全文搜索
- `GET /api/v1/search/facets` - 分面搜索
- `GET /api/v1/search/stats` - 搜索统计

### 爬虫管理接口
- `GET /api/v1/scrapers/status` - 获取所有爬虫状态
- `GET /api/v1/scrapers/{source_key}/runs` - 获取爬虫执行历史
- `POST /api/v1/scrapers/{source_key}/trigger` - 手动触发爬虫
- `POST /api/v1/scrapers/{source_key}/enable` - 启用爬虫
- `POST /api/v1/scrapers/{source_key}/disable` - 禁用爬虫

### 社交媒体接口
- `GET /api/v1/social/sessions` - 获取社交会话列表
- `GET /api/v1/social/messages` - 获取社交消息
- `POST /api/v1/telegram/sessions` - 创建 Telegram 会话
- `POST /api/v1/twitter/sessions` - 创建 Twitter 会话

### 导出接口
- `POST /api/v1/exports` - 创建导出任务
- `GET /api/v1/exports` - 获取导出任务列表
- `GET /api/v1/exports/{id}/download` - 下载导出文件

### 管理接口（需要管理员权限）
- `GET /api/v1/admin/users` - 获取用户列表
- `POST /api/v1/admin/users` - 创建用户
- `PUT /api/v1/admin/users/{id}` - 更新用户
- `DELETE /api/v1/admin/users/{id}` - 删除用户
- `GET /api/v1/admin/tenants` - 获取租户列表
- `POST /api/v1/admin/tenants` - 创建租户
- `GET /api/v1/admin/audit-logs` - 获取审计日志
- `GET /api/v1/admin/health` - 系统健康状态

### 配额接口
- `GET /api/v1/quota` - 获取当前配额使用情况
- `GET /api/v1/quota/history` - 获取配额历史

### 健康检查
- `GET /api/v1/health` - 服务健康检查

## 配置说明

### 环境变量

#### 必要配置
```bash
# 数据库
MYSQL_ROOT_PASSWORD=your_strong_password
MYSQL_DATABASE=news_scraper
MYSQL_USER=news_user
MYSQL_PASSWORD=your_password

# Redis
REDIS_URL=redis://redis:6379/0

# Meilisearch
MEILI_MASTER_KEY=your_32_char_key_here

# RustFS（S3 兼容对象存储）
RUSTFS_ACCESS_KEY=rustfsadmin
RUSTFS_SECRET_KEY=your_password

# 应用安全（必须配置）
SECRET_KEY=your_jwt_secret_key_min_32_chars
FERNET_KEY=your_fernet_key_for_encryption

# 管理员账户
ADMIN_PASSWORD=your_admin_password
```

#### 生成安全密钥
```bash
# 生成 SECRET_KEY（用于 JWT）
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成 FERNET_KEY（用于加密敏感数据）
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 生成 MEILI_MASTER_KEY
python -c "import secrets; print(secrets.token_hex(16))"
```

#### 可选配置
```bash
# 应用
LOG_LEVEL=INFO
ALLOWED_ORIGINS=*

# 监控
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_password

# Twitter API（可选，用于 Twitter 数据采集）
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=

# Telegram（可选，用于 Telegram 数据采集）
TELEGRAM_BOT_TOKEN=
```

### 添加新的新闻源

1. 在 `backend/app/scrapers/` 创建爬虫类
2. 继承 `BaseScraper` 并实现 `scrape()` 方法
3. 在数据库中添加新闻源配置
4. 重启服务即可自动调度

## 开发指南

### 本地开发

#### 后端
```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 复制环境配置
cp .env.example .env
# 编辑 .env 配置数据库连接等

# 启动开发服务器
uvicorn app.main:app --reload --port 8001
```

#### 前端
```bash
cd frontend

# 安装依赖
npm install

# 复制环境配置
cp .env.example .env.local

# 启动开发服务器
npm run dev
```

### 运行测试
```bash
cd backend

# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试（需要 Docker 环境）
pytest tests/integration/ -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

### 代码检查
```bash
# 后端代码检查
cd backend
ruff check .
ruff format .

# 前端代码检查
cd frontend
npm run lint
npm run build  # 类型检查
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

## 监控

### Prometheus
访问 http://localhost:9090 查看 Prometheus 监控指标。

预配置的监控目标：
- Backend API 应用指标
- MySQL 数据库指标
- Redis 缓存指标
- Node 系统指标

### Grafana
访问 http://localhost:3000 查看 Grafana 仪表板。

默认账户：`admin` / `admin`（生产环境请修改）

预配置的仪表板：
- 系统概览（CPU、内存、磁盘、网络）
- 数据库状态（连接数、查询性能）
- Redis 状态（内存、连接、命中率）

## 常见问题

### 1. 前端无法连接后端 API
检查 nginx 配置中的后端地址是否正确指向 `news_scraper_backend:8000`

### 2. 爬虫无法运行
- 检查网络连接
- 查看 `backend/logs/` 日志文件
- 确认目标网站是否可访问

### 3. 搜索功能不工作
确认 Meilisearch 服务正常运行，检查索引是否创建成功

### 4. 登录失败
- 检查验证码是否正确
- 确认用户名密码是否正确
- 查看后端日志了解详细错误

## License

本项目采用 MIT 许可证

## 作者

- [@Shunlly](https://github.com/Shunlly)
