# Feature Specification: 爬虫系统全栈升级 (Fullstack Upgrade)

**Feature Branch**: `002-fullstack-upgrade`
**Created**: 2025-12-14
**Status**: Draft
**Input**: User description: "爬虫系统全栈升级需求规格说明书"
**Constitution**: v2.0.0 (Reference: `.specify/memory/constitution.md`)
**Depends On**: `001-scraper-api-system` (基础爬虫 API 系统)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 采集 Twitter/Telegram 社交数据 (Priority: P1)

运营人员需要从 Twitter (X) 和 Telegram 平台采集数据，以扩展信息源覆盖范围。不同于新闻网站的单篇文章模式，社交平台数据需要按会话/话题/群组进行组织。

**Why this priority**: 多渠道扩展是本次升级的核心业务目标，Twitter/TG 是最高价值的社交数据源。没有此功能，升级将缺乏核心价值。

**Independent Test**: 可通过配置 Twitter/TG 账号凭证，执行采集任务，验证数据按会话/群组正确存储，并在前端以话题聚合形式展示。

**Acceptance Scenarios**:

1. **Given** 系统配置了有效的 Twitter API 凭证, **When** 执行 Twitter 采集任务, **Then** 推文数据按会话线程 (Thread) 组织存储
2. **Given** 系统配置了 Telegram Bot Token, **When** 执行 TG 群组采集, **Then** 消息按群组和话题分类存储
3. **Given** 采集了社交数据, **When** 在前端查看, **Then** 数据以会话/话题聚合形式展示，而非单篇文章列表
4. **Given** 同一条推文/消息被多次采集, **When** 入库时, **Then** 系统通过去重机制阻止重复存储

---

### User Story 2 - 全文检索新闻内容 (Priority: P1)

用户需要通过关键词快速搜索新闻标题和正文内容，实现毫秒级检索响应。

**Why this priority**: 全文检索是数据价值变现的关键能力，使海量采集数据可被有效利用。

**Independent Test**: 可通过在搜索框输入关键词，验证搜索结果在 500ms 内返回，且结果包含标题和正文匹配的内容。

**Acceptance Scenarios**:

1. **Given** 系统已索引新闻数据, **When** 用户搜索关键词 "人工智能", **Then** 系统在 500ms 内返回标题或正文包含该关键词的结果
2. **Given** 搜索结果返回, **When** 用户查看结果列表, **Then** 匹配关键词在结果中高亮显示
3. **Given** 数据库包含 100 万条新闻, **When** 执行全文检索, **Then** 响应时间仍保持在 1 秒以内
4. **Given** 新闻刚被采集入库, **When** 立即搜索该新闻关键词, **Then** 新数据在 5 秒内可被检索到

---

### User Story 3 - 可视化管理后台 (Priority: P1)

管理员需要通过现代化的 Web 界面管理爬虫配置、查看数据列表、监控任务状态，界面采用毛玻璃 (Glassmorphism) 风格和便当盒 (Bento Grid) 布局。

**Why this priority**: 管理后台是系统可用性的核心，没有 UI 则系统无法被非技术人员使用。设计规范是宪法 v2.0.0 的强制要求。

**Independent Test**: 可通过访问管理后台 URL，验证界面加载、导航功能、数据列表展示、以及 UI 风格符合设计规范。

**Acceptance Scenarios**:

1. **Given** 用户访问管理后台, **When** 页面加载完成, **Then** 看到符合 Glassmorphism 风格的 Dashboard，使用 Bento Grid 布局
2. **Given** 管理员在配置页面, **When** 添加/修改爬虫规则, **Then** 配置立即生效，无需重启服务
3. **Given** 管理员在数据列表页, **When** 浏览采集数据, **Then** 支持分页、排序、筛选功能
4. **Given** 管理员在任务监控页, **When** 查看任务状态, **Then** 显示实时运行状态、成功率、错误日志

---

### User Story 4 - 多账号凭证轮询 (Priority: P2)

运营人员需要配置多个 Twitter/TG 账号凭证，系统自动轮询使用，以规避单账号的 API 限流。

**Why this priority**: 社交平台 API 限流是实际采集的主要障碍，多账号轮询是保证采集稳定性的必要手段。

**Independent Test**: 可通过配置 3 个 Twitter 账号，执行大批量采集任务，验证系统自动切换账号，且无单账号触发限流。

**Acceptance Scenarios**:

1. **Given** 配置了多个 Twitter 账号凭证, **When** 执行采集任务, **Then** 系统自动轮询使用不同账号
2. **Given** 某账号触发限流, **When** 系统检测到限流响应, **Then** 自动切换到下一个可用账号
3. **Given** 所有账号都被限流, **When** 系统检测到, **Then** 暂停采集并记录告警日志
4. **Given** 账号凭证过期, **When** 系统检测到认证失败, **Then** 标记该账号为失效状态，通知管理员

---

### User Story 5 - 文件存储适配器 (Priority: P2)

系统需要支持将采集的文件（图片、附件等）存储到不同的对象存储服务，通过配置切换存储后端。

**Why this priority**: 存储适配器是宪法 v2.0.0 架构原则的强制要求，支持多云部署和成本优化。

**Independent Test**: 可通过配置切换 MinIO/S3/OSS 存储后端，上传测试文件，验证文件正确存储并可下载。

**Acceptance Scenarios**:

1. **Given** 配置使用 MinIO 存储, **When** 爬虫采集到图片, **Then** 图片上传到 MinIO 并返回访问 URL
2. **Given** 配置切换到 AWS S3, **When** 不修改代码重启服务, **Then** 新采集文件存储到 S3
3. **Given** 存储服务不可用, **When** 上传失败, **Then** 系统记录错误并重试（指数退避）
4. **Given** 需要读取历史文件, **When** 调用下载接口, **Then** 无论使用何种存储后端都能正确返回文件

---

### User Story 6 - 正文智能提取 (Priority: P2)

系统需要从新闻详情页自动提取正文内容，过滤广告和导航噪音，使用 trafilatura 库实现高质量提取。

**Why this priority**: 正文提取是全文检索的前提，也是数据价值提升的关键环节。

**Independent Test**: 可通过提交新闻 URL，验证返回的正文内容完整、无广告噪音、格式清晰。

**Acceptance Scenarios**:

1. **Given** 提供新闻详情页 URL, **When** 调用正文提取服务, **Then** 返回干净的正文内容，不含广告和导航
2. **Given** 新闻页面包含图片, **When** 提取正文, **Then** 保留图片 URL 在内容中
3. **Given** 页面结构异常或无法提取, **When** 提取失败, **Then** 返回空内容并记录错误，不影响其他处理

---

### User Story 7 - 数据导出功能 (Priority: P3)

用户需要将采集数据导出为 Excel (.xlsx) 或 CSV 格式，用于离线分析或报告。

**Why this priority**: 数据导出是常见需求，但不影响核心采集和检索功能。

**Independent Test**: 可通过在数据列表页选择数据范围，点击导出按钮，验证下载的文件格式正确且数据完整。

**Acceptance Scenarios**:

1. **Given** 用户在数据列表页, **When** 点击导出 Excel, **Then** 下载 .xlsx 文件，包含选定范围的所有数据
2. **Given** 用户选择导出 CSV, **When** 点击导出, **Then** 下载 .csv 文件，UTF-8 编码
3. **Given** 导出数据量超过 10 万条, **When** 执行导出, **Then** 系统后台异步处理，完成后通知用户下载

---

### User Story 8 - 代理池管理 (Priority: P3)

运营人员需要配置和管理代理 IP 池，支持在采集任务中动态绑定代理，规避 IP 封禁。

**Why this priority**: 代理池是稳定采集的辅助手段，但非核心功能，可在基础功能稳定后添加。

**Independent Test**: 可通过在配置界面添加代理 IP，执行采集任务，验证请求通过配置的代理发出。

**Acceptance Scenarios**:

1. **Given** 配置了代理 IP 列表, **When** 执行采集任务, **Then** 请求通过代理池中的 IP 轮询发出
2. **Given** 某代理 IP 不可用, **When** 连接超时, **Then** 自动剔除该 IP 并切换下一个
3. **Given** 管理员在代理配置界面, **When** 添加/删除代理, **Then** 实时生效，无需重启

---

### User Story 9 - Docker 一键部署 (Priority: P3)

运维人员需要通过 Docker Compose 一键启动所有服务（应用、数据库、Redis、搜索引擎），简化部署流程。

**Why this priority**: 容器化部署是现代化交付的标准，但开发阶段可暂时使用本地环境。

**Independent Test**: 可通过执行 `docker-compose up`，验证所有服务正常启动并可访问。

**Acceptance Scenarios**:

1. **Given** 已安装 Docker 和 Docker Compose, **When** 执行 `docker-compose up -d`, **Then** 所有服务（app, mysql, redis, meilisearch）启动成功
2. **Given** 服务启动完成, **When** 访问管理后台 URL, **Then** 页面正常加载
3. **Given** 需要停止服务, **When** 执行 `docker-compose down`, **Then** 所有容器停止，数据卷保留

---

### Edge Cases

- 当 Twitter/TG API 凭证全部失效时，系统如何告警并暂停相关任务？
- 当搜索引擎服务不可用时，系统如何降级（fallback 到数据库查询）？
- 当存储后端配置错误时，如何防止采集数据丢失？
- 当单个采集任务产生超大数据量（10 万+消息）时，如何分批处理？
- 当前端导出超大数据集时，如何避免浏览器内存溢出？
- 当多个采集任务同时运行时，如何避免账号凭证冲突？
- 当新闻页面使用 JavaScript 渲染时，trafilatura 如何处理？

## Requirements *(mandatory)*

### Functional Requirements

#### 核心采集业务

- **FR-001**: 系统必须支持 Twitter (X) 数据采集，使用官方 API 或爬虫方式
- **FR-002**: 系统必须支持 Telegram 群组/频道数据采集，使用 Bot API 或 MTProto
- **FR-003**: Twitter 数据必须按会话线程 (Thread) 模型存储，保留回复关系
- **FR-004**: Telegram 数据必须按群组/话题模型存储，支持话题分类聚合
- **FR-005**: 系统必须支持多账号凭证配置，实现自动轮询切换
- **FR-006**: 系统必须集成 trafilatura 库进行新闻正文智能提取
- **FR-007**: 系统必须实现全局去重机制，支持 URL 指纹 (SHA256) 和内容指纹 (SimHash)
- **FR-008**: 去重检查必须在数据入库前执行，基于 Redis Bloom Filter 或数据库唯一索引

#### 全文检索

- **FR-009**: 系统必须集成 Elasticsearch 或 Meilisearch 搜索引擎
- **FR-010**: 系统必须支持对新闻标题和正文内容的全文检索
- **FR-011**: 搜索响应时间必须在 500ms 以内（10 万条数据规模）
- **FR-012**: 新入库数据必须在 5 秒内可被检索到

#### 基础设施

- **FR-013**: 系统必须实现 StorageProvider 抽象接口，遵循适配器模式
- **FR-014**: StorageProvider 必须支持 MinIO、AWS S3、Aliyun OSS 实现
- **FR-015**: 存储后端必须通过配置切换，严禁硬编码
- **FR-016**: 系统必须支持代理池配置，支持 HTTP/HTTPS/SOCKS5 代理
- **FR-017**: 代理池必须支持健康检查和自动剔除失效代理

#### 管理后台 UI

- **FR-018**: 前端必须使用 React + TypeScript + Tailwind CSS + Arco Design
- **FR-019**: UI 必须遵循 Glassmorphism (毛玻璃) 设计风格
- **FR-020**: Dashboard 必须使用 Bento Grid (便当盒) 布局
- **FR-021**: 系统必须提供爬虫配置管理界面（规则配置、任务调度、账号管理）
- **FR-022**: 系统必须提供数据列表展示界面，支持分页、排序、筛选
- **FR-023**: 系统必须提供搜索结果预览界面，支持关键词高亮
- **FR-024**: 系统必须支持数据导出为 Excel (.xlsx) 和 CSV 格式

#### 部署交付

- **FR-025**: 系统必须提供完整的 Dockerfile 和 docker-compose.yml
- **FR-026**: docker-compose 必须包含所有服务：应用、MySQL、Redis、搜索引擎
- **FR-027**: 必须支持一键启动所有服务，无需额外配置

### Key Entities

- **SocialSession (社交会话)**: 表示一个 Twitter Thread 或 TG 话题，属性包括：会话 ID、平台类型 (twitter/telegram)、话题标题、创建时间、消息数量、参与者列表
- **SocialMessage (社交消息)**: 表示单条推文或 TG 消息，属性包括：消息 ID、所属会话 ID、发送者、内容、媒体附件列表、发布时间、回复目标 ID（可选）
- **AccountCredential (账号凭证)**: 表示平台账号凭证，属性包括：凭证 ID、平台类型、凭证内容（Token/Cookie）、状态（有效/限流/失效）、最后使用时间
- **ProxyConfig (代理配置)**: 表示代理 IP 配置，属性包括：代理 ID、协议类型 (HTTP/SOCKS5)、地址、端口、认证信息（可选）、状态、最后检查时间
- **StorageFile (存储文件)**: 表示存储的文件，属性包括：文件 ID、存储 Key、原始文件名、MIME 类型、大小、存储后端类型、创建时间
- **ExportTask (导出任务)**: 表示数据导出任务，属性包括：任务 ID、导出格式、筛选条件、状态（等待/处理中/完成/失败）、文件路径、创建时间

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 系统成功采集 Twitter/TG 数据，每日采集量达到 1 万条消息
- **SC-002**: 全文检索响应时间在 500ms 以内（10 万条数据规模）
- **SC-003**: 新数据入库后 5 秒内可被检索到
- **SC-004**: 管理后台页面加载时间在 2 秒以内
- **SC-005**: UI 符合 Glassmorphism 设计规范，Lighthouse 可访问性评分 > 90
- **SC-006**: 存储适配器支持无代码切换 MinIO/S3/OSS，切换时间 < 5 分钟
- **SC-007**: 多账号轮询机制使单账号限流率降低 80%
- **SC-008**: 正文提取准确率 > 95%（基于人工抽样验证）
- **SC-009**: 去重机制将重复数据率控制在 < 0.5%
- **SC-010**: Docker Compose 一键部署成功率 100%，首次启动时间 < 5 分钟

## Assumptions

- Twitter API 或爬虫方式可获取所需数据（遵守平台 ToS）
- Telegram Bot API 可满足群组数据采集需求
- 现有 001 基础系统已稳定运行
- 用户有有效的 Twitter/TG 账号凭证
- 部署环境支持 Docker 和 Docker Compose
- 网络环境允许访问 Twitter/TG（或提供代理）

## Dependencies

- 依赖 001-scraper-api-system 的基础架构（数据库、API 框架、爬虫基类）
- 需要 Redis 服务支持 Bloom Filter 去重
- 需要 Elasticsearch 或 Meilisearch 服务支持全文检索
- 需要对象存储服务（MinIO 本地部署或云服务）
- 需要有效的 Twitter/TG API 凭证

## Out of Scope

- AI 内容分析（情感分析、自动摘要等）
- 多语言国际化支持
- 移动端原生应用
- 用户权限管理系统（单用户/管理员模式）
- 实时推送通知（WebSocket/SSE）
- 数据归档和冷热分离存储
- 第三方 Webhook 集成
