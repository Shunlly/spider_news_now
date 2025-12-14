# Technical Research: 002-fullstack-upgrade

**Date**: 2025-12-14
**Author**: System Architect
**Status**: Completed

## 1. 现有系统分析

### 1.1 代码库结构

```text
spider_news_now/
├── backend/                    # FastAPI 后端 ✅ 已实现
│   ├── app/
│   │   ├── api/v1/endpoints/   # news.py, scrapers.py
│   │   ├── models/             # NewsArticle, NewsSource, ScraperRun
│   │   ├── schemas/            # Pydantic 验证模型
│   │   ├── scrapers/           # 6 个新闻爬虫 (Playwright)
│   │   ├── services/           # news_service, scraper_service, duplicate_service
│   │   └── tasks/              # APScheduler 调度
│   ├── alembic/                # 数据库迁移
│   └── tests/                  # 测试套件
│
├── frontend/                   # ⚠️ Vue 3 + Element Plus (需迁移到 React)
│   └── src/                    # Vue 组件、路由、状态管理
│
└── docker-compose.yml          # MySQL 8.0 + 应用容器
```

### 1.2 现有数据模型

| 模型 | 状态 | 说明 |
|------|------|------|
| NewsArticle | ✅ | 新闻文章 (url_hash 去重) |
| NewsSource | ✅ | 新闻源配置 |
| ScraperRun | ✅ | 爬虫执行记录 |
| SocialSession | ❌ | 需新增 (Twitter Thread / TG 话题) |
| SocialMessage | ❌ | 需新增 (推文 / TG 消息) |
| AccountCredential | ❌ | 需新增 (多账号凭证) |
| ProxyConfig | ❌ | 需新增 (代理池) |
| StorageFile | ❌ | 需新增 (对象存储记录) |
| ExportTask | ❌ | 需新增 (导出任务) |

### 1.3 现有技术栈

| 组件 | 现状 | 目标 | 变更 |
|------|------|------|------|
| 后端框架 | FastAPI 0.115 | FastAPI 0.115 | 保持 |
| ORM | SQLAlchemy 2.0 (Async) | SQLAlchemy 2.0 (Async) | 保持 |
| 数据库 | MySQL 8.0 | MySQL 8.0 | 保持 |
| 前端框架 | **Vue 3** | **React + TypeScript** | 🔴 迁移 |
| UI 组件库 | **Element Plus** | **Arco Design** | 🔴 迁移 |
| 构建工具 | Vite | Vite | 保持 |
| 搜索引擎 | 无 | Meilisearch | 🟡 新增 |
| 对象存储 | 无 | MinIO (S3) | 🟡 新增 |
| 缓存/去重 | 数据库唯一索引 | Redis Bloom Filter | 🟡 升级 |

---

## 2. 技术选型决策

### 2.1 搜索引擎: Meilisearch vs Elasticsearch

| 维度 | Meilisearch | Elasticsearch |
|------|-------------|---------------|
| 安装复杂度 | ⭐⭐⭐⭐⭐ (单二进制) | ⭐⭐ (JVM + 配置) |
| 资源占用 | ~50MB RAM | ~2GB+ RAM |
| 中文支持 | ✅ 内置分词 | ✅ 需配置 IK |
| 实时索引 | ✅ < 50ms | ⚠️ 1s (refresh) |
| 查询性能 | ✅ 10ms p99 | ✅ 20ms p99 |
| 生态系统 | 较新 | 成熟稳定 |
| 运维成本 | 低 | 中高 |

**决策**: 选择 **Meilisearch**
- 轻量级，适合单机部署
- 中文支持开箱即用
- 实时索引满足 5 秒内可检索要求
- Docker 部署简单

### 2.2 去重方案: Bloom Filter + SimHash

#### URL 去重 (Bloom Filter)
```python
# 使用 Redis Bloom Filter (RedisBloom 模块)
# 预估容量: 1000 万条 URL
# 误判率: 0.1%
# 内存占用: ~12MB

BF.RESERVE url_dedup 0.001 10000000
BF.ADD url_dedup <sha256_hash>
BF.EXISTS url_dedup <sha256_hash>
```

#### 内容去重 (SimHash)
```python
# 使用 simhash 库计算内容指纹
# 汉明距离阈值: 3 (可配置)

from simhash import Simhash

def get_content_fingerprint(text: str) -> int:
    return Simhash(text).value

def is_similar(fp1: int, fp2: int, threshold: int = 3) -> bool:
    return bin(fp1 ^ fp2).count('1') <= threshold
```

### 2.3 文件存储适配器

```python
# backend/src/storage/provider.py (Protocol 接口)
from typing import Protocol

class StorageProvider(Protocol):
    """存储提供者接口 - 遵循宪法 II.A 适配器模式"""

    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        """上传文件，返回访问 URL"""
        ...

    async def download(self, key: str) -> bytes:
        """下载文件"""
        ...

    async def delete(self, key: str) -> bool:
        """删除文件"""
        ...

    async def exists(self, key: str) -> bool:
        """检查文件是否存在"""
        ...

    async def get_url(self, key: str, expires: int = 3600) -> str:
        """获取预签名 URL"""
        ...
```

实现类:
- `MinioStorage` - MinIO / S3 兼容存储
- `AliyunOSSStorage` - 阿里云 OSS
- `LocalStorage` - 本地文件系统 (开发/测试)

### 2.4 Twitter / Telegram 采集方案

#### Twitter (X) 采集
| 方案 | 优点 | 缺点 |
|------|------|------|
| 官方 API v2 | 稳定、合规 | 免费额度有限 (1500 推/月) |
| Nitter 实例 | 免费、无限制 | 不稳定、可能被封 |
| Playwright 爬虫 | 灵活 | 需登录、风控风险 |

**决策**: 优先官方 API v2 + Nitter 备用

#### Telegram 采集
| 方案 | 优点 | 缺点 |
|------|------|------|
| Bot API | 简单稳定 | 仅能访问 Bot 所在群组 |
| MTProto (Telethon) | 功能完整 | 需要个人账号 |

**决策**: Bot API 为主 (配置简单)，MTProto 作为高级选项

---

## 3. 前端迁移策略

### 3.1 Vue → React 迁移清单

| Vue 组件 | React 等价物 | 优先级 |
|----------|-------------|--------|
| App.vue | App.tsx | P1 |
| DefaultLayout.vue | Layout.tsx | P1 |
| ArticleCard.vue | ArticleCard.tsx | P1 |
| ArticleGroup.vue | ArticleGroup.tsx | P1 |
| FilterPanel.vue | FilterPanel.tsx | P1 |
| ScraperStatusCard.vue | ScraperStatusCard.tsx | P2 |
| StatisticsPanel.vue | StatisticsPanel.tsx | P2 |
| Pinia store | Zustand/Jotai | P1 |
| Vue Router | React Router | P1 |

### 3.2 UI 组件映射 (Element Plus → Arco Design)

| Element Plus | Arco Design | 用途 |
|--------------|-------------|------|
| ElTable | Table | 数据表格 |
| ElPagination | Pagination | 分页 |
| ElInput | Input | 输入框 |
| ElSelect | Select | 下拉选择 |
| ElButton | Button | 按钮 |
| ElCard | Card | 卡片 |
| ElTag | Tag | 标签 |
| ElMessage | Message | 消息提示 |
| ElLoading | Spin | 加载状态 |

### 3.3 Glassmorphism 组件封装

```tsx
// frontend/src/components/ui/GlassCard.tsx
interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
}

export const GlassCard: React.FC<GlassCardProps> = ({ children, className }) => (
  <div className={cn(
    // 毛玻璃核心样式 (宪法 III.A)
    "backdrop-blur-xl",
    "bg-white/40 dark:bg-slate-900/40",
    "border border-white/20",
    "shadow-xl",
    // Bento Grid 圆角 (宪法 III.B)
    "rounded-2xl",
    "p-6",
    className
  )}>
    {children}
  </div>
);
```

---

## 4. 依赖清单

### 4.1 后端新增依赖

```text
# requirements.txt 新增
meilisearch==0.31.0          # 全文检索
redis>=5.0.0                 # Redis 客户端
simhash>=2.1.0               # 内容指纹
trafilatura>=1.8.0           # 正文提取
tweepy>=4.14.0               # Twitter API v2
telethon>=1.34.0             # Telegram MTProto
python-telegram-bot>=20.7    # Telegram Bot API
boto3>=1.34.0                # S3/MinIO 客户端
openpyxl>=3.1.0              # Excel 导出
```

### 4.2 前端新增依赖

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.22.0",
    "@arco-design/web-react": "^2.60.0",
    "tailwindcss": "^3.4.0",
    "zustand": "^4.5.0",
    "axios": "^1.7.0",
    "@tanstack/react-query": "^5.28.0",
    "clsx": "^2.1.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "@types/react": "^18.3.0",
    "vitest": "^1.4.0",
    "@testing-library/react": "^14.2.0"
  }
}
```

---

## 5. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 前端 Vue→React 迁移工作量大 | 高 | 分阶段迁移，优先核心页面 |
| Twitter API 限流 | 中 | 多账号轮询 + Nitter 备用 |
| Meilisearch 中文分词质量 | 中 | 配置 jieba 分词器 |
| Redis Bloom Filter 内存 | 低 | 预估 12MB，可接受 |
| MinIO 部署复杂度 | 低 | Docker 一键部署 |

---

## 6. 技术验证清单

- [x] Meilisearch 中文检索性能验证
- [x] Redis Bloom Filter 误判率测试
- [x] SimHash 相似度检测准确性
- [x] MinIO S3 兼容性验证
- [x] Arco Design + Tailwind 兼容性
- [x] Twitter API v2 额度验证
- [x] Telegram Bot API 群组权限验证
