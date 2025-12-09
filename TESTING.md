# MVP System Testing Guide

## 测试时间：2025-12-08

本指南用于测试新闻聚合系统的MVP功能。

## 系统要求

- Python 3.13+
- Node.js 20+
- MySQL 8.0+

## 测试步骤

### 1. 数据库设置

```bash
# 创建数据库
mysql -u root -p
```

```sql
CREATE DATABASE news_scraper CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'news_user'@'localhost' IDENTIFIED BY 'news_password';
GRANT ALL PRIVILEGES ON news_scraper.* TO 'news_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境（如果还没有）
python3.13 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 运行数据库迁移
alembic upgrade head

# 验证数据已正确初始化
mysql -u news_user -p news_scraper -e "SELECT * FROM news_sources;"
# 应该看到6个新闻源：sina, qq, wangyi, yicai, huanqiu, ifeng
```

### 3. 运行后端测试

```bash
# 单元测试
pytest tests/unit/ -v

# 集成测试（需要测试数据库）
pytest tests/integration/ -v

# 契约测试
pytest tests/contract/ -v

# 完整测试套件
pytest --cov=app --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html  # macOS
# 或 start htmlcov/index.html  # Windows
```

### 4. 启动后端服务

```bash
# 在 backend 目录下
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**验证后端启动成功：**
- API文档: http://localhost:8000/docs
- Health检查: http://localhost:8000/api/v1/health

### 5. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

**验证前端启动成功：**
- 前端界面: http://localhost:5173

### 6. 功能测试清单

#### 6.1 后端API测试

使用浏览器访问 http://localhost:8000/docs 进行交互式测试：

- [ ] **GET /api/v1/health** - 健康检查
  - 期望结果：返回 `{"status": "healthy"}`

- [ ] **POST /api/v1/scrapers/sina/trigger** - 手动触发爬虫
  - 期望结果：返回 202 状态码，爬虫开始运行
  - 等待约30-60秒让爬虫完成

- [ ] **GET /api/v1/news/articles** - 获取文章列表
  - 期望结果：返回文章数据（如果爬虫已运行）
  - 检查分页：`?page=1&page_size=10`

- [ ] **GET /api/v1/news/articles/grouped** - 获取分组文章
  - 期望结果：按来源分组的文章列表

- [ ] **GET /api/v1/news/sources** - 获取新闻源列表
  - 期望结果：6个新闻源信息

- [ ] **GET /api/v1/news/statistics** - 获取统计信息
  - 期望结果：文章总数、来源统计等

#### 6.2 前端UI测试

访问 http://localhost:5173：

- [ ] **页面加载**
  - 看到 "📰 新闻聚合系统" 标题
  - 页面正确加载（无JavaScript错误）

- [ ] **新闻显示**
  - 如果已有数据，看到按来源分组的新闻
  - 每个来源显示来源名称和文章数量
  - 文章卡片显示标题、分类、时间

- [ ] **文章交互**
  - 点击文章标题可以在新标签页打开原文
  - 悬停在卡片上有视觉反馈

- [ ] **刷新功能**
  - 点击右下角"刷新新闻"按钮
  - 看到加载状态
  - 数据更新

#### 6.3 自动化调度测试

- [ ] **验证调度器启动**
  - 后端日志中看到 "Scraper scheduler initialized"
  - 日志显示已注册6个爬虫任务

- [ ] **等待自动执行**（可选，需要等待30分钟）
  - 等待30分钟后检查数据库
  - 应该看到新的 scraper_runs 记录
  - 文章数量增加

### 7. 数据库验证

```bash
mysql -u news_user -p news_scraper
```

```sql
-- 查看文章数量
SELECT source_key, COUNT(*) as count
FROM news_articles
GROUP BY source_key;

-- 查看最新文章
SELECT title, source_key, published_at
FROM news_articles
ORDER BY scraped_at DESC
LIMIT 10;

-- 查看爬虫运行历史
SELECT source_key, started_at, status, articles_scraped, articles_new
FROM scraper_runs
ORDER BY started_at DESC
LIMIT 10;

-- 查看新闻源状态
SELECT source_key, display_name, enabled, status, last_run_at
FROM news_sources;
```

### 8. 性能测试

#### 8.1 API响应时间

```bash
# 测试文章列表API
time curl -s http://localhost:8000/api/v1/news/articles?page_size=100 > /dev/null

# 期望：< 2秒
```

#### 8.2 前端加载时间

- 打开浏览器开发者工具 (F12)
- Network 标签
- 刷新页面
- 检查加载时间应 < 3秒

### 9. 故障排查

#### 后端无法启动

```bash
# 检查Python版本
python --version  # 应该是 3.13+

# 检查依赖
pip list | grep -E "fastapi|sqlalchemy|playwright"

# 检查数据库连接
python -c "from app.core.config import settings; print(settings.DATABASE_URL)"
```

#### 数据库连接失败

```bash
# 验证MySQL运行
mysql.server status  # macOS
# 或 sudo systemctl status mysql  # Linux

# 测试连接
mysql -u news_user -p -h localhost news_scraper
```

#### 前端API调用失败

- 检查后端是否在运行（http://localhost:8000/docs）
- 检查浏览器控制台是否有CORS错误
- 验证 `.env` 文件中的 `VITE_API_BASE_URL`

#### 爬虫失败

```bash
# 检查Playwright浏览器
playwright install chromium

# 手动测试单个爬虫
cd backend
python -c "
import asyncio
from app.scrapers.sina_scraper import SinaScraper
scraper = SinaScraper()
articles = asyncio.run(scraper.run())
print(f'Scraped {len(articles)} articles')
"
```

### 10. 成功标准

系统测试通过的标准：

- [x] 后端服务成功启动，API文档可访问
- [x] 数据库迁移成功，6个新闻源已创建
- [ ] 至少一个爬虫成功运行并保存文章
- [ ] 前端界面正确显示文章（分组显示）
- [ ] API响应时间 < 2秒
- [ ] 前端加载时间 < 3秒
- [ ] 无JavaScript错误
- [ ] 爬虫调度器正常运行

### 11. 下一步

测试通过后，可以：

1. **继续开发** - 实现Phase 5-8的剩余功能
2. **Docker部署** - 使用已创建的Docker配置进行部署
3. **生产环境配置** - 修改环境变量、配置安全设置

---

## 快速测试命令

```bash
# 终端1: 启动后端
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# 终端2: 启动前端
cd frontend
npm run dev

# 终端3: 手动触发爬虫
curl -X POST http://localhost:8000/api/v1/scrapers/sina/trigger

# 终端4: 查看数据
curl http://localhost:8000/api/v1/news/articles/grouped | python -m json.tool
```

## 测试记录

测试日期：__________
测试人员：__________

| 测试项 | 结果 | 备注 |
|--------|------|------|
| 后端启动 | ☐ 通过 ☐ 失败 | |
| 前端启动 | ☐ 通过 ☐ 失败 | |
| 爬虫执行 | ☐ 通过 ☐ 失败 | |
| 文章显示 | ☐ 通过 ☐ 失败 | |
| API性能 | ☐ 通过 ☐ 失败 | |

问题记录：
