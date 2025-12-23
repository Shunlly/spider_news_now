# Quickstart Guide: 新闻爬虫 SaaS 平台

**Date**: 2025-12-22
**Audience**: 开发者

---

## 1. 环境准备

### 1.1 系统要求

| 组件 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Python | 3.10 | 3.12 |
| Node.js | 18.x | 20.x |
| npm | 9.x | 10.x |
| Docker | 24.x | 25.x |
| MySQL | 8.0 | 8.0 |
| Redis | 7.x | 7.2 |

### 1.2 克隆项目

```bash
git clone https://github.com/Shunlly/spider_news_now.git
cd spider_news_now
```

---

## 2. Docker 一键启动 (推荐)

### 2.1 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置（必须修改密码等敏感信息）
vim .env
```

**必须配置的变量**：
```bash
MYSQL_ROOT_PASSWORD=your_strong_password
MYSQL_PASSWORD=your_password
SECRET_KEY=your_jwt_secret_key_min_32_chars
FERNET_KEY=your_fernet_key_for_encryption
MEILI_MASTER_KEY=your_32_char_key
ADMIN_PASSWORD=your_admin_password
```

### 2.2 启动所有服务

```bash
# 构建并启动所有容器
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

**服务列表**:

| 服务 | 端口映射 | 说明 |
|------|----------|------|
| frontend | 8080:80 | React 前端 (Nginx) |
| backend | 8001:8000 | FastAPI 后端 |
| mysql | 33060:3306 | MySQL 数据库 |
| redis | 63790:6379 | Redis 缓存 |
| meilisearch | 7701:7700 | 全文检索 |
| rustfs | 9010:9000, 9011:9001 | S3 兼容对象存储 |

### 2.3 访问服务

```
# 管理后台
http://localhost:8080

# API 文档
http://localhost:8001/api/v1/docs

# Meilisearch 控制台
http://localhost:7701

# RustFS 控制台
http://localhost:9011
```

### 2.4 停止服务

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

# 安装 Playwright 浏览器（用于爬虫）
playwright install chromium

# 复制环境配置
cp .env.example .env
# 编辑 .env 配置数据库等信息
```

### 3.2 数据库迁移

```bash
# 确保 MySQL 已启动（可用 Docker）
docker-compose up -d mysql redis meilisearch rustfs

# 执行迁移
alembic upgrade head
```

### 3.3 启动后端

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3.4 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 复制环境配置
cp .env.example .env.local

# 启动开发服务器
npm run dev
```

**访问**: http://localhost:5173

---

## 4. 功能验证

### 4.1 检查服务健康

```bash
# API 健康检查（无需认证）
curl http://localhost:8001/api/v1/health

# 期望响应
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected",
    "meilisearch": "connected",
    "storage": "connected"
  }
}
```

### 4.2 登录获取 Token

```bash
# 步骤 1: 获取图形验证码
CAPTCHA_RESPONSE=$(curl -s http://localhost:8001/api/v1/auth/captcha)
echo $CAPTCHA_RESPONSE

# 提取 token 和 code（测试环境会返回验证码）
CAPTCHA_TOKEN=$(echo $CAPTCHA_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
CAPTCHA_CODE=$(echo $CAPTCHA_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['code'])")

# 步骤 2: 登录
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"admin\",
    \"password\": \"admin123\",
    \"captcha_token\": \"$CAPTCHA_TOKEN\",
    \"captcha_code\": \"$CAPTCHA_CODE\"
  }")
echo $LOGIN_RESPONSE

# 提取 access_token
TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token: $TOKEN"
```

### 4.3 测试 API 接口

```bash
# 获取新闻统计（需要认证）
curl -s http://localhost:8001/api/v1/news/statistics \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 获取爬虫状态
curl -s http://localhost:8001/api/v1/scrapers/status \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 触发爬虫（手动运行）
curl -s -X POST http://localhost:8001/api/v1/scrapers/sina/trigger \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### 4.4 全文检索测试

```bash
# 搜索新闻（需要认证）
curl -s "http://localhost:8001/api/v1/search?q=人工智能" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 5. 生产环境部署

### 5.1 使用生产配置

```bash
# 复制生产环境变量
cp .env.example .env
# 编辑 .env，设置强密码

# 启动生产服务
docker-compose -f docker-compose.prod.yml up -d

# 查看状态
docker-compose -f docker-compose.prod.yml ps
```

### 5.2 GitHub Actions 自动部署

1. 在 GitHub 仓库设置 Secrets：
   - `SERVER_HOST`: 服务器地址
   - `SERVER_USER`: SSH 用户名
   - `SERVER_SSH_KEY`: SSH 私钥
   - `GHCR_TOKEN`: GitHub Container Registry Token
   - 其他环境变量

2. 推送到 `main` 分支自动触发部署

---

## 6. 常见问题

### Q1: 数据库连接失败

```
Error: Can't connect to MySQL server
```

**解决**: 确保 MySQL 服务已启动，检查 .env 中的数据库配置

### Q2: 登录失败 - 验证码错误

```
Error: Invalid captcha
```

**解决**: 验证码有效期 5 分钟，获取后需尽快使用

### Q3: API 返回 401 Unauthorized

```
Error: Could not validate credentials
```

**解决**: Token 已过期，需要重新登录或使用 refresh_token 刷新

### Q4: Meilisearch 索引错误

```
Error: Index not found
```

**解决**: 系统会自动创建索引，首次启动可能需要等待几秒

### Q5: 前端无法访问后端 API

**解决**:
- 开发环境: 确保 Vite 代理配置正确（`vite.config.ts`）
- 生产环境: 检查 Nginx 配置中的 proxy_pass 地址

---

## 7. 运行测试

```bash
# 后端测试
cd backend
pytest tests/ -v

# 单元测试
pytest tests/unit/ -v

# 集成测试（需要 Docker 环境）
pytest tests/integration/ -v

# 覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 前端 E2E 测试
cd frontend
npx playwright test
```

---

## 8. 开发工作流

### 8.1 添加新的爬虫

1. 创建爬虫类 `backend/app/scrapers/new_scraper.py`
2. 继承 `BaseScraper` 基类
3. 实现 `run()` 方法
4. 在数据库注册新的 NewsSource

### 8.2 添加 API 端点

1. 路由定义在 `backend/app/api/v1/endpoints/`
2. 创建 Pydantic Schema 在 `backend/app/schemas/`
3. 业务逻辑在 `backend/app/services/`

### 8.3 前端开发

1. 组件位于 `frontend/src/components/`
2. 使用 Stone 色系深色主题
3. 使用 TailwindCSS + 自定义 UI 组件

---

## 9. 有用的命令

```bash
# 查看后端日志
docker-compose logs -f backend

# 进入后端容器
docker-compose exec backend bash

# 执行数据库迁移
docker-compose exec backend alembic upgrade head

# 重建索引
curl -X POST http://localhost:8001/api/v1/search/index/rebuild \
  -H "Authorization: Bearer $TOKEN"

# 清理 Docker 资源
docker system prune -a
```
