<!--
SYNC IMPACT REPORT
==================
Version Change: 1.0.0 → 2.0.0 (MAJOR)
Rationale: Complete architectural redesign with new tech stack (React/TypeScript frontend,
           Arco Design UI), new storage patterns (Adapter Pattern), heterogeneous data
           modeling (News vs Social), and comprehensive UI/UX design system (Glassmorphism).

Modified Principles:
- RENAMED: I. Code Quality Standards → I. Tech Stack Mandate (tech stack now explicit)
- RENAMED: II. Testing Discipline → IV. Coding Standards (merged with new requirements)
- RENAMED: III. Extensibility First → II. Architectural Principles (expanded with patterns)
- RENAMED: IV. Maintainability Requirements → (merged into Coding Standards)
- RENAMED: V. Consistency & Performance → (merged into Architectural Principles)
- NEW: III. UI/UX Design System (Glassmorphism, Bento Grid, color scheme)

Added Sections:
- Tech Stack Mandate (explicit backend/frontend/database/search/storage requirements)
- Adapter Pattern for file storage (StorageProvider interface)
- Heterogeneous Data Modeling (News vs Social Session models)
- Global Deduplication (Redis Bloom Filter, SimHash)
- UI/UX Design System (Glassmorphism, Bento Grid, color guidelines)
- Chinese comment requirement for core logic
- No placeholder code rule (no `pass` or `TODO`)

Removed Sections:
- Detailed Test Categories (unit/integration/contract) - simplified
- Test-First Development detailed rules - simplified
- Quality Gates section - replaced with workflow rules
- Governance section - simplified to workflow

Templates Status:
- ✅ .specify/templates/plan-template.md - Updated Technical Context section with new tech stack
- ✅ .specify/templates/spec-template.md - Compatible (tech-agnostic requirements)
- ✅ .specify/templates/tasks-template.md - Updated Project Structure options
- ⚠ Future: Update existing specs to reference new constitution version

Follow-up TODOs:
- Update existing feature specs in /specs/ to align with new tech stack
- Migrate any Vue.js code to React (if exists)
- Implement StorageProvider adapter pattern in codebase
-->

# Spider News Now 项目宪法 (Project Constitution)

你是一位精通高并发爬虫系统与现代数据可视化的全栈架构师及 UI/UX 设计师。

## Core Principles

### I. 技术栈强制要求 (Tech Stack Mandate)

所有代码必须遵循以下技术栈要求，**严禁擅自替换**：

- **后端**: Python 3.10+ (FastAPI), Pydantic v2, SQLAlchemy (Async/异步)
- **前端**: React (TypeScript) + Vite + Tailwind CSS
- **UI 组件库**: Arco Design (React 版) - *必须配合 Tailwind 进行定制，严禁混用其他组件库*
- **数据库**: MySQL 8.0+ (字符集: utf8mb4_unicode_ci)
- **搜索引擎**: Elasticsearch 或 Meilisearch
- **对象存储**: 兼容 S3 协议 / MinIO

**Rationale**: 统一技术栈确保团队协作效率，避免技术债务积累。前后端分离架构支持
独立部署和扩展。

### II. 核心架构原则 (Architectural Principles)

系统必须遵循以下架构模式和原则：

#### A. 文件存储适配器模式 (Storage Adapter Pattern)

- 文件系统**必须**使用策略模式/适配器模式实现
- 创建一个抽象的 `StorageProvider` 接口
- 具体实现（MinIO, S3, RustFS, OSS）必须通过配置切换，**严禁硬编码**
- 示例接口定义：
  ```python
  class StorageProvider(Protocol):
      async def upload(self, key: str, data: bytes) -> str: ...
      async def download(self, key: str) -> bytes: ...
      async def delete(self, key: str) -> bool: ...
  ```

**Rationale**: 适配器模式解耦业务逻辑与具体存储实现，支持无缝切换云服务商。

#### B. 异构数据建模 (Heterogeneous Data Modeling)

- **新闻 (News)**: 保持标准的 标题/正文/来源/分类 结构
- **社交会话 (Twitter/TG)**: 必须使用**"会话/流式 (Session-based)"**模型
  - 不要把聊天记录强行塞进文章表
  - 支持按"话题"或"群组"聚合
  - 维护消息时间线和回复关系

**Rationale**: 不同数据源有不同的内在结构，强行统一会丢失关键语义信息。

#### C. 全局去重机制 (Global Deduplication)

- 实现基于 Redis (Bloom Filter) 或 数据库唯一索引的去重服务
- 去重依据需支持：
  - **URL Hash**: 对规范化 URL 进行 SHA256 哈希
  - **内容指纹 (SimHash)**: 用于相似内容检测（阈值可配置）
- 去重检查必须在入库前执行

**Rationale**: 爬虫系统的核心挑战之一是数据重复，早期去重减少存储成本和用户干扰。

### III. UI/UX 设计规范 (Design System)

前端界面必须遵循以下设计规范：

#### A. 视觉风格: Glassmorphism (毛玻璃)

毛玻璃是核心设计主题，实现要点：
- 使用 `backdrop-filter: blur(12px)` 或更高
- 半透明背景: `bg-white/40 dark:bg-slate-900/40`
- 细微亮色边框: `border border-white/20`
- 柔和阴影: `shadow-xl`

#### B. 布局结构: Bento Grid (便当盒布局)

- Dashboard 的卡片必须是模块化、网格状的
- 统一使用大圆角: `rounded-xl` 或 `rounded-2xl`
- 卡片间距统一: `gap-4` 或 `gap-6`
- 支持响应式布局: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`

#### C. 配色方案 (Color Scheme)

- 使用现代、充满活力的配色（如深蓝/紫渐变背景）
- 背景示例: `bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900`
- **避免**使用枯燥的纯白/纯灰背景
- 强调色: 使用 Arco Design 的主题色或自定义渐变

**Rationale**: 统一的视觉语言提升用户体验，毛玻璃效果现代且专业。

### IV. 编码标准 (Coding Standards)

所有代码必须遵循以下编码规范：

- **类型安全**:
  - Python 代码必须加 Type Hints（函数签名、类属性、返回值）
  - 前端必须定义 TypeScript Interface，禁止使用 `any`
- **注释要求**:
  - 核心逻辑（特别是爬虫解析、去重算法）**必须包含中文注释**
  - 注释解释"为什么"而非"做什么"
- **错误处理**:
  - 严禁静默失败
  - 对外部 API (Twitter/TG) 的调用必须包含重试机制（指数退避）
  - 所有异常必须记录日志
- **拒绝占位符**:
  - 禁止输出 `pass` 或 `TODO`
  - 必须生成完整的、可运行的逻辑代码
- **日志规范**:
  - 使用结构化日志（JSON 格式）
  - 日志级别: DEBUG(追踪), INFO(生命周期), WARNING(可恢复), ERROR(失败)
  - 包含上下文（scraper_id, article_count, execution_time）

**Rationale**: 类型安全减少运行时错误，中文注释便于团队协作，完整代码避免技术债务。

### V. 开发工作流 (Development Workflow)

- 设计 API 时优先遵循 RESTful 规范
- 前端包管理默认使用 `pnpm`
- 数据库变更使用 Alembic 迁移管理
- Git 提交信息使用 Conventional Commits 规范

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
│   └── lib/            # 共享工具（日志、配置）
└── tests/
    ├── unit/           # 单元测试
    ├── integration/    # 集成测试
    └── contract/       # 契约测试

frontend/
├── src/
│   ├── components/     # React 组件
│   │   └── ui/         # 基于 Arco Design 的封装组件
│   ├── pages/          # 页面组件
│   ├── hooks/          # 自定义 Hooks
│   ├── services/       # API 调用服务
│   ├── stores/         # 状态管理
│   └── types/          # TypeScript 类型定义
└── tests/              # 前端测试
```

### Testing Requirements

- 后端: pytest + pytest-asyncio
- 前端: Vitest + React Testing Library
- 最低覆盖率: 80%（业务逻辑），100%（关键路径）
- 爬虫必须包含契约测试（验证输出 Schema）

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

- **MAJOR (X.0.0)**: 技术栈变更、架构原则不兼容变更
- **MINOR (0.X.0)**: 新增原则、扩展指导
- **PATCH (0.0.X)**: 措辞优化、错误修正

### Enforcement

- 此宪法高于所有其他开发实践和指南
- 代码审查必须拒绝违反核心原则的变更
- 使用 `.specify/memory/constitution.md` 作为所有开发决策的权威来源

**Version**: 2.0.0 | **Ratified**: 2025-12-08 | **Last Amended**: 2025-12-14
