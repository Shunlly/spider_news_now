# 📰 新闻聚合系统 (News Aggregator)

一个功能完善的新闻爬虫聚合系统，支持自动抓取、存储、展示和监控多个新闻源的实时新闻。

## ✨ 功能特性

### 核心功能
- 🕷️ **多源爬取**: 支持新浪、腾讯、网易、第一财经、凤凰网、环球网等主流新闻网站
- ⏰ **定时调度**: 基于 APScheduler 的自动定时爬取（默认 30 分钟）
- 🔄 **去重机制**: 基于内容哈希的智能去重，避免重复抓取
- 💾 **数据持久化**: PostgreSQL 存储，支持高效查询和分页
- 🎯 **分类管理**: 支持娱乐、国内、国际、军事、财经、科技、体育等多个分类

### Web 功能
- 📱 **响应式 UI**: 基于 Vue 3 + Element Plus 的现代化界面
- 🔍 **高级筛选**: 按新闻源、分类、时间范围多维度筛选
- 📊 **监控面板**: 实时查看爬虫运行状态、成功率、抓取统计
- 📈 **执行历史**: 详细的爬虫运行记录和错误追踪
- 🚀 **手动触发**: 支持一键手动触发爬虫运行

### API 功能
- 🔌 **RESTful API**: 完整的 REST API 接口
- 📖 **自动文档**: Swagger/OpenAPI 自动生成接口文档
- 🔐 **CORS 支持**: 跨域资源共享配置
- ⚡ **异步处理**: 基于 FastAPI 的高性能异步处理

## 🏗️ 技术架构

### 后端技术栈
- **框架**: FastAPI 0.115.6
- **数据库**: PostgreSQL (通过 asyncpg)
- **ORM**: SQLAlchemy 2.0 (异步模式)
- **调度器**: APScheduler 4.0
- **HTTP 客户端**: httpx (异步)
- **日志**: 结构化 JSON 日志

### 前端技术栈
- **框架**: Vue 3.5.13 (Composition API)
- **UI 组件**: Element Plus 2.9.1
- **状态管理**: Pinia 2.3.0
- **路由**: Vue Router 4.5.0
- **构建工具**: Vite 6.4.1
- **HTTP 客户端**: Axios 1.7.9

### 项目结构
```
spider_news_now/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API 路由
│   │   │   └── v1/
│   │   │       └── endpoints/  # API 端点
│   │   ├── core/           # 核心配置
│   │   ├── db/             # 数据库配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic 模式
│   │   ├── scrapers/       # 爬虫实现
│   │   ├── services/       # 业务逻辑
│   │   └── tasks/          # 定时任务
│   ├── alembic/            # 数据库迁移
│   └── tests/              # 测试用例
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── api/           # API 配置
│   │   ├── components/    # Vue 组件
│   │   ├── layouts/       # 布局组件
│   │   ├── router/        # 路由配置
│   │   ├── services/      # API 服务
│   │   ├── store/         # Pinia 状态
│   │   └── views/         # 页面视图
│   └── public/            # 静态资源
└── README.md
```

## 🚀 快速开始

### 环境要求
- Python 3.12+
- Node.js 18+ & npm
- PostgreSQL 14+

### 1. 克隆项目
```bash
git clone https://github.com/yourusername/spider_news_now.git
cd spider_news_now
```

### 2. 后端设置

#### 安装依赖
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 配置数据库
创建 `.env` 文件（参考 `.env.example`）:
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/news_scraper
LOG_LEVEL=INFO
```

#### 初始化数据库
```bash
# 运行迁移
alembic upgrade head

# 初始化新闻源数据
python -m app.db.init_db
```

#### 启动后端服务
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端服务将运行在: http://localhost:8000
API 文档: http://localhost:8000/docs

### 3. 前端设置

#### 安装依赖
```bash
cd frontend
npm install
```

#### 配置环境
创建 `.env` 文件:
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

#### 启动前端服务
```bash
npm run dev
```

前端应用将运行在: http://localhost:5173

### 4. 访问应用

- **新闻列表页**: http://localhost:5173/
- **监控面板**: http://localhost:5173/dashboard
- **API 文档**: http://localhost:8000/docs

## 📡 API 接口

### 新闻接口
- `GET /api/v1/news/articles` - 获取新闻列表（分页）
- `GET /api/v1/news/articles/grouped` - 按来源分组获取新闻
- `GET /api/v1/news/articles/{id}` - 获取新闻详情
- `GET /api/v1/news/sources` - 获取新闻源列表
- `GET /api/v1/news/statistics` - 获取统计数据

### 爬虫管理接口
- `GET /api/v1/scrapers/status` - 获取所有爬虫状态
- `GET /api/v1/scrapers/{source_key}/runs` - 获取爬虫执行历史
- `POST /api/v1/scrapers/{source_key}/trigger` - 手动触发爬虫

### 健康检查
- `GET /api/v1/health` - 服务健康检查

完整的 API 文档请访问: http://localhost:8000/docs

## 🎨 使用示例

### 查询新闻（带筛选）
```bash
# 获取新浪的国内新闻，按发布时间倒序
curl "http://localhost:8000/api/v1/news/articles?source=sina&category=china&sort_by=published_at&sort_order=desc&page_size=10"
```

### 手动触发爬虫
```bash
# 触发新浪新闻爬虫
curl -X POST "http://localhost:8000/api/v1/scrapers/sina/trigger"
```

### 查看爬虫状态
```bash
# 获取所有爬虫当前状态
curl "http://localhost:8000/api/v1/scrapers/status"
```

## 🔧 配置说明

### 新闻源配置
在数据库 `news_sources` 表中配置新闻源:
- `source_key`: 唯一标识符（如 sina, qq, wangyi）
- `display_name`: 显示名称
- `scraper_module`: 爬虫模块路径
- `enabled`: 是否启用
- `schedule_interval`: 调度间隔（秒）

### 添加新的新闻源
1. 在 `backend/app/scrapers/` 创建爬虫类
2. 继承 `BaseScraper` 并实现 `scrape()` 方法
3. 在数据库中添加新闻源配置
4. 重启服务即可自动调度

## 📊 监控面板功能

### 系统统计
- 爬虫总数
- 运行中的爬虫数
- 已启用的爬虫数
- 失败的爬虫数
- 新闻总量统计

### 爬虫状态卡片
- 实时状态（空闲/运行中/失败）
- 最近运行信息
- 下次运行时间
- 失败次数统计
- 一键触发运行
- 查看执行历史

### 执行历史
- 分页展示历史记录
- 运行时长统计
- 抓取文章数量
- 新增/重复统计
- 错误信息追踪

## 🐛 常见问题

### 1. 页面显示空白
**原因**: 系统代理配置问题
**解决**: 在浏览器代理设置中将 `localhost` 和 `127.0.0.1` 添加到例外列表

### 2. 数据库连接失败
**原因**: PostgreSQL 未启动或连接配置错误
**解决**:
```bash
# macOS
brew services start postgresql

# Linux
sudo systemctl start postgresql

# 检查 .env 中的 DATABASE_URL 配置
```

### 3. 爬虫无法运行
**原因**: 网络连接问题或目标网站反爬
**解决**:
- 检查网络连接
- 查看 `backend/logs/` 日志文件
- 调整爬虫请求头和延迟

### 4. 前端无法连接后端
**原因**: CORS 配置或 API 地址错误
**解决**:
- 检查 `frontend/.env` 中的 `VITE_API_BASE_URL`
- 确认后端服务正常运行在 8000 端口

## 🔒 安全建议

- 生产环境请修改数据库密码
- 配置防火墙规则限制访问
- 使用 HTTPS 加密传输
- 定期备份数据库
- 启用 API 访问频率限制
- 配置日志轮转避免磁盘占满

## 📈 性能优化

- 数据库索引优化（已在迁移中配置）
- 爬虫并发控制（避免被封禁）
- 前端组件懒加载
- API 响应缓存
- 数据库连接池配置

## 🛠️ 开发指南

### 运行测试
```bash
# 后端测试
cd backend
pytest tests/ -v

# 前端测试（如已配置）
cd frontend
npm run test
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

### 代码风格
- 后端: PEP 8 (使用 black 格式化)
- 前端: ESLint + Prettier

## 📝 待办事项

- [ ] 添加用户认证系统
- [ ] 实现评论和收藏功能
- [ ] 添加更多新闻源
- [ ] 实现关键词搜索
- [ ] 添加邮件通知功能
- [ ] Docker 容器化部署
- [ ] CI/CD 自动化部署
- [ ] 性能监控和告警

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 License

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👥 作者

- 项目维护者: [@chenshuhang](https://github.com/chenshuhang)

## 🙏 致谢

- FastAPI 框架
- Vue.js 团队
- Element Plus 组件库
- 所有开源贡献者

## 📧 联系方式

如有问题或建议，请通过以下方式联系:
- 提交 GitHub Issue
- 发送邮件至: your.email@example.com

---

⭐ 如果觉得这个项目有帮助，欢迎 Star！
