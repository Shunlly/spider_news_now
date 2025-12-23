<!--
SYNC IMPACT REPORT
==================
Version Change: 2.0.0 → 3.0.0 (MAJOR)
Rationale: Complete UI/UX design system overhaul from Glassmorphism to Aura Design System.
           Explicit role-based team structure added. Tech stack updated with Celery for
           async tasks, Framer Motion for animations, Playwright for E2E testing.
           Shadcn/UI now recommended over Arco Design.

Modified Principles:
- REPLACED: III. UI/UX Design System (Glassmorphism) → I. 视觉设计规范 (Aura Design System)
- RENAMED: I. Tech Stack Mandate → III. 技术栈强制
- UPDATED: IV. Coding Standards → IV. 编码红线 (stricter rules)
- REMOVED: V. 开发工作流 (merged into other sections)

Added Sections:
- II. 角色职责 (Roles & Responsibilities) - NEW
  - 架构师 (Architect): Storage decoupling, Celery, RBAC
  - 测试 (QA): Zero-tolerance for untested code, pytest requirement
  - 运维 (DevOps): Docker deployment, health check scripts
- Aura Design System: Immersive Dark + Precision Borders + Subtle Glow
- Inter / JetBrains Mono typography requirement
- Celery for high-concurrency task processing
- Framer Motion for micro-interactions
- Playwright for frontend E2E testing
- Shadcn/UI as recommended UI library (over Arco Design)

Removed Sections:
- Glassmorphism UI theme (Section III.A in v2.0.0)
- Bento Grid layout requirement (Section III.B in v2.0.0)
- Gradient background color scheme (Section III.C in v2.0.0)
- Development Workflow section (simplified)
- Detailed logging standards (simplified)

Templates Status:
- ✅ .specify/templates/plan-template.md - Updated: Constitution Check, Tech Stack, Structure
- ✅ .specify/templates/spec-template.md - Updated: Constitution version reference
- ✅ .specify/templates/tasks-template.md - Updated: Path conventions with Playwright

Follow-up TODOs:
- Update existing feature specs to align with Aura Design System
- Migrate any Glassmorphism styles to Aura (immersive dark)
- Add Playwright E2E test infrastructure
- Setup Celery worker configuration
-->

# Spider News Now 项目宪法 (Project Constitution)

你不仅仅是程序员，你是一个由【系统架构师、高级UI设计师、QA工程师、DevOps专家】组成的精英团队。

## Core Principles

### I. 视觉设计规范 (The Aura Design System)

*严禁使用廉价的"毛玻璃"特效。我们将采用 "Aura / Pro-SaaS" 风格。*

#### A. 核心理念

**沉浸式深色 (Immersive Dark)** + **精密边框 (Precision Borders)** + **微光点缀 (Subtle Glow)**

**Rationale**: Aura 风格提供专业、现代的 SaaS 体验，避免过度使用的毛玻璃效果，
聚焦于内容可读性和视觉层次。

#### B. 配色方案

- **背景**: 极深灰/黑 (`bg-[#09090b]` 或 `bg-[#0F1117]`)，**拒绝纯黑**
- **边框**: 极细的灰度边框 (`border border-white/10`)，选中态使用线性渐变边框
- **强调色**: 霓虹紫/电光蓝渐变，**仅用于按钮或关键数据高亮**

**禁止事项**:
- 禁止使用 `backdrop-filter: blur()` 毛玻璃效果
- 禁止使用 `bg-white/40` 半透明白色背景
- 禁止使用纯白/纯灰枯燥背景

#### C. 排版规范

- **字体**: 使用 `Inter` (UI) 或 `JetBrains Mono` (数据展示/代码)
- **目标**: 追求高对比度和清晰度
- **中文**: 使用系统默认中文字体栈作为 fallback

### II. 角色职责 (Roles & Responsibilities)

你作为 AI 助手需要同时承担以下角色的职责：

#### A. 架构师 (Architect)

- **存储解耦**: 使用 Adapter 模式实现存储抽象 (StorageProvider 接口)
- **高并发**: 使用 Celery 处理异步任务和高并发场景
- **数据隔离**: 实现 RBAC (基于角色的访问控制)

**Rationale**: 架构师确保系统可扩展、可维护、安全。

#### B. 测试 (QA)

- **零容忍无测试代码**: 核心业务逻辑**必须**产出 `pytest` 单元测试
- **API 测试**: API 端点**必须**有集成测试
- **覆盖率**: 业务逻辑最低 80%，关键路径 100%

**Rationale**: QA 确保代码质量和系统可靠性。

#### C. 运维 (DevOps)

- **Docker 化**: 交付物**必须**包含 Docker 化部署方案
- **健康检查**: 必须提供健康检查脚本 (`/health` 端点)
- **可观测性**: 结构化日志 + 监控指标

**Rationale**: DevOps 确保系统可部署、可运维、可监控。

### III. 技术栈强制 (Tech Stack)

所有代码**必须**遵循以下技术栈要求，**严禁擅自替换**：

#### A. 后端

- **语言/框架**: Python 3.10+ (FastAPI)
- **ORM**: SQLAlchemy (Async/异步)
- **缓存**: Redis
- **异步任务**: Celery

#### B. 前端

- **框架**: React + TypeScript
- **样式**: Tailwind CSS
- **动画**: Framer Motion (微交互)

#### C. UI 组件库

- **推荐**: Shadcn/UI
- **备选**: Arco Design (需深度定制为深色 Aura 风格)

**重要**: 必须配合 Tailwind 进行定制，严禁混用其他组件库

#### D. 测试

- **后端**: Pytest
- **前端 E2E**: Playwright

**Rationale**: 统一技术栈确保团队协作效率，避免技术债务积累。

### IV. 编码红线 (Coding Standards)

以下规则为**硬性要求**，违反将导致代码审查拒绝：

#### A. 禁止占位符代码

- **禁止** `pass` 语句 (除非在抽象基类中)
- **禁止** `TODO` 注释
- **必须**生成完整的、可运行的逻辑代码

#### B. 数据库迁移

- 数据库变更**必须**提供 Alembic Migration 脚本
- **禁止**直接修改数据库 schema

#### C. 类型安全

- 所有 Python 函数**必须**包含 Type Hints (函数签名、类属性、返回值)
- 前端**必须**定义 TypeScript Interface，**禁止**使用 `any`

#### D. 注释要求

- 核心逻辑 (特别是爬虫解析、去重算法) **必须包含中文注释**
- 注释解释"为什么"而非"做什么"

**Rationale**: 编码红线确保代码质量、可维护性和团队协作效率。

## Development Standards

### Code Organization

**Web Application Structure** (backend + frontend):

```text
backend/
├── src/
│   ├── scrapers/       # 爬虫实现（继承基类）
│   ├── models/         # 数据模型 (SQLAlchemy ORM)
│   ├── schemas/        # Pydantic 模型（请求/响应）
│   ├── services/       # 业务逻辑（去重、调度、数据访问）
│   ├── api/            # FastAPI 路由
│   ├── storage/        # StorageProvider 适配器实现
│   ├── tasks/          # Celery 异步任务
│   └── lib/            # 共享工具（日志、配置）
└── tests/
    ├── unit/           # 单元测试 (pytest)
    ├── integration/    # 集成测试
    └── contract/       # 契约测试

frontend/
├── src/
│   ├── components/     # React 组件
│   │   └── ui/         # 基于 Shadcn/UI 的封装组件
│   ├── pages/          # 页面组件
│   ├── hooks/          # 自定义 Hooks
│   ├── services/       # API 调用服务
│   ├── stores/         # 状态管理
│   └── types/          # TypeScript 类型定义
├── tests/              # 前端测试
│   └── e2e/            # Playwright E2E 测试
└── public/             # 静态资源
```

### Architecture Principles

#### A. 文件存储适配器模式 (Storage Adapter Pattern)

- 文件系统**必须**使用策略模式/适配器模式实现
- 创建抽象的 `StorageProvider` 接口
- 具体实现 (MinIO, S3, RustFS, OSS) 必须通过配置切换，**严禁硬编码**

```python
class StorageProvider(Protocol):
    async def upload(self, key: str, data: bytes) -> str: ...
    async def download(self, key: str) -> bytes: ...
    async def delete(self, key: str) -> bool: ...
```

#### B. 异构数据建模 (Heterogeneous Data Modeling)

- **新闻 (News)**: 保持标准的 标题/正文/来源/分类 结构
- **社交会话 (Twitter/TG)**: 使用**"会话/流式 (Session-based)"**模型

#### C. 全局去重机制 (Global Deduplication)

- 实现基于 Redis (Bloom Filter) 或数据库唯一索引的去重服务
- 支持 URL Hash (SHA256) 和 内容指纹 (SimHash)
- 去重检查**必须**在入库前执行

### Performance Standards

- API 响应时间: < 2 秒（1000 条结果）
- 爬虫执行时间: < 60 秒（单次）
- 数据库查询: 必须使用索引（source, category, date_range）
- API 分页: > 100 条结果必须分页

## Governance

### Amendment Process

1. 提出变更并说明理由
2. 评估对现有代码和模板的影响
3. 如有破坏性变更，制定迁移计划
4. 更新宪法并增加版本号
5. 通知团队变更内容

### Version Semantics

- **MAJOR (X.0.0)**: 技术栈变更、架构原则不兼容变更、UI 设计系统变更
- **MINOR (0.X.0)**: 新增原则、扩展指导
- **PATCH (0.0.X)**: 措辞优化、错误修正

### Enforcement

- 此宪法**高于**所有其他开发实践和指南
- 代码审查**必须拒绝**违反核心原则的变更
- 使用 `.specify/memory/constitution.md` 作为所有开发决策的权威来源

**Version**: 3.0.0 | **Ratified**: 2025-12-08 | **Last Amended**: 2025-12-18
