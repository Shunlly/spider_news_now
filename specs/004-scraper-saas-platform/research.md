# Research: 全栈爬虫 SaaS 平台

**Branch**: `004-scraper-saas-platform` | **Date**: 2025-12-18

## 概述

本文档整合各角色视角的技术研究与决策，作为实施计划的技术基础。

---

## 1. 系统架构师 (System Architect) 方案

### 1.1 数据库设计 - 多租户隔离 Schema

采用**共享数据库 + 租户ID隔离**模式，所有业务表包含 `tenant_id` 外键。

#### ER 关系图 (核心表)

```text
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Tenant      │     │      User       │     │      Role       │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │◄────│ tenant_id (FK)  │     │ id (PK)         │
│ name            │     │ id (PK)         │◄────│ name            │
│ quota_config    │     │ email           │     │ permissions     │
│ created_at      │     │ password_hash   │     └─────────────────┘
└─────────────────┘     │ role_id (FK)    │────►
                        │ quota_tier      │
                        │ is_active       │
                        └─────────────────┘
                              │
                              │ created_by
                              ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  ScrapingTask   │     │   NewsArticle   │     │  SocialSession  │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │     │ id (PK)         │     │ id (PK)         │
│ tenant_id (FK)  │     │ tenant_id (FK)  │     │ tenant_id (FK)  │
│ user_id (FK)    │────►│ task_id (FK)    │     │ task_id (FK)    │
│ task_type       │     │ title           │     │ platform        │
│ target_url      │     │ content         │     │ thread_id       │
│ status          │     │ url_hash        │     │ message_count   │
│ config (JSON)   │     │ simhash         │     └─────────────────┘
│ created_at      │     │ source          │           │
└─────────────────┘     │ published_at    │           │ 1:N
                        └─────────────────┘           ▼
                                              ┌─────────────────┐
                                              │  SocialMessage  │
                                              ├─────────────────┤
                                              │ id (PK)         │
                                              │ session_id (FK) │
                                              │ parent_id (FK)  │◄─┐
                                              │ sender          │  │ self-ref
                                              │ content         │──┘ (回复关系)
                                              │ sent_at         │
                                              │ quoted_msg_id   │
                                              └─────────────────┘
```

#### 多租户隔离实现

```python
# 所有查询自动注入 tenant_id 过滤
from sqlalchemy.orm import Query

class TenantQuery(Query):
    """租户隔离查询基类"""

    def filter_by_tenant(self, tenant_id: int) -> "TenantQuery":
        # 自动为所有业务表添加租户过滤
        return self.filter(self.column_descriptions[0]['entity'].tenant_id == tenant_id)

# 使用 SQLAlchemy event 自动注入
@event.listens_for(Session, "do_orm_execute")
def _add_tenant_filter(execute_state):
    """在执行 ORM 查询前自动添加租户过滤"""
    if execute_state.is_select:
        tenant_id = get_current_tenant_id()  # 从请求上下文获取
        if tenant_id and hasattr(execute_state.statement, 'whereclause'):
            # 为查询添加 tenant_id 条件
            ...
```

#### 角色权限表 (RBAC)

| 角色 | 权限范围 | 数据访问 |
|-----|---------|---------|
| `super_admin` | 所有租户 | 全局读写，用户管理，系统配置 |
| `tenant_admin` | 单租户 | 租户内用户管理，任务配置 |
| `user` | 单租户 | 仅个人创建的任务和数据 |

### 1.2 存储设计 - StorageProvider 适配器

#### 接口定义

```python
from typing import Protocol
from abc import abstractmethod

class StorageProvider(Protocol):
    """对象存储适配器接口

    通过环境变量 STORAGE_PROVIDER 切换实现:
    - minio: MinIO 本地存储
    - s3: AWS S3
    - oss: 阿里云 OSS
    """

    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """上传文件，返回访问 URL"""
        ...

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """下载文件内容"""
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除文件"""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查文件是否存在"""
        ...

    @abstractmethod
    async def get_presigned_url(self, key: str, expires: int = 3600) -> str:
        """获取预签名 URL"""
        ...
```

#### 环境变量配置

```bash
# .env
STORAGE_PROVIDER=minio  # minio | s3 | oss

# MinIO 配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=scraper-data
MINIO_SECURE=false

# S3 配置 (当 STORAGE_PROVIDER=s3)
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=ap-northeast-1
S3_BUCKET=scraper-data

# OSS 配置 (当 STORAGE_PROVIDER=oss)
OSS_ACCESS_KEY_ID=xxx
OSS_ACCESS_KEY_SECRET=xxx
OSS_ENDPOINT=oss-cn-shanghai.aliyuncs.com
OSS_BUCKET=scraper-data
```

#### 工厂模式切换

```python
def get_storage_provider() -> StorageProvider:
    """根据环境变量创建存储提供者"""
    provider_type = settings.STORAGE_PROVIDER

    if provider_type == "minio":
        return MinIOStorageProvider(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            bucket=settings.MINIO_BUCKET,
            secure=settings.MINIO_SECURE,
        )
    elif provider_type == "s3":
        return S3StorageProvider(
            region=settings.AWS_REGION,
            bucket=settings.S3_BUCKET,
        )
    elif provider_type == "oss":
        return OSSStorageProvider(
            endpoint=settings.OSS_ENDPOINT,
            access_key_id=settings.OSS_ACCESS_KEY_ID,
            access_key_secret=settings.OSS_ACCESS_KEY_SECRET,
            bucket=settings.OSS_BUCKET,
        )
    else:
        raise ValueError(f"Unknown storage provider: {provider_type}")
```

### 1.3 高可用设计 - Celery 任务管理

#### 任务失败重试策略

```python
from celery import Celery
from celery.exceptions import MaxRetriesExceededError

app = Celery('scraper')

# Celery 配置
app.conf.update(
    # 任务重试配置
    task_acks_late=True,  # 任务完成后才确认
    task_reject_on_worker_lost=True,  # Worker 失联时拒绝任务

    # 结果后端配置
    result_backend='redis://localhost:6379/1',
    result_expires=3600,  # 结果保留 1 小时

    # 死信队列配置
    task_queues={
        'default': {'exchange': 'default', 'routing_key': 'default'},
        'scraping': {'exchange': 'scraping', 'routing_key': 'scraping'},
        'dlq': {'exchange': 'dlq', 'routing_key': 'dlq'},  # 死信队列
    },
)

@app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 重试间隔 60 秒
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,  # 指数退避
    retry_backoff_max=600,  # 最大退避 10 分钟
    retry_jitter=True,  # 添加随机抖动
)
def scrape_news_task(self, task_id: int, url: str):
    """新闻采集任务

    失败策略:
    1. 自动重试 3 次，指数退避
    2. 超过重试次数后发送到死信队列
    3. 记录失败日志供人工排查
    """
    try:
        # 执行采集逻辑
        result = scrape_news(url)
        return result
    except MaxRetriesExceededError:
        # 超过最大重试次数，发送到死信队列
        send_to_dlq.delay({
            'task_id': task_id,
            'url': url,
            'error': 'Max retries exceeded',
            'timestamp': datetime.utcnow().isoformat(),
        })
        raise

@app.task(queue='dlq')
def send_to_dlq(failed_task_info: dict):
    """死信队列处理

    1. 记录到数据库 (FailedTask 表)
    2. 发送告警通知
    3. 等待人工处理
    """
    # 记录失败任务
    db.add(FailedTask(**failed_task_info))
    db.commit()

    # 发送告警（如果连续失败超过阈值）
    if get_recent_failure_count() > 10:
        send_alert("任务失败率过高", failed_task_info)
```

#### 任务流程图

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   用户触发   │────►│ Celery Task │────►│   执行采集   │
│   采集任务   │     │   入队      │     │             │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                         ┌─────────────────────┼─────────────────────┐
                         │                     │                     │
                         ▼                     ▼                     ▼
                    ┌─────────┐           ┌─────────┐           ┌─────────┐
                    │  成功   │           │ 临时失败 │           │ 永久失败 │
                    └────┬────┘           └────┬────┘           └────┬────┘
                         │                     │                     │
                         ▼                     ▼                     ▼
                    ┌─────────┐           ┌─────────┐           ┌─────────┐
                    │ 存储结果 │           │指数退避  │           │  DLQ    │
                    │ 更新状态 │           │ 重试    │           │ 死信队列│
                    └─────────┘           └─────────┘           └─────────┘
                                               │                     │
                                               │ max_retries         │
                                               └─────────────────────┘
```

---

## 2. UI/UX 设计师 (Designer) 方案

### 2.1 布局规划 - AppLayout 结构

```text
┌──────────────────────────────────────────────────────────────────┐
│  TopBar (h-14)                                                    │
│  ┌────────────┬────────────────────────────────┬───────────────┐ │
│  │  Logo      │        Search Bar              │  User Menu    │ │
│  └────────────┴────────────────────────────────┴───────────────┘ │
├──────────────────────────────────────────────────────────────────┤
│ ┌──────────┐                                                     │
│ │ Sidebar  │  Main Content Area (flex-1)                         │
│ │ (w-64)   │  ┌──────────────────────────────────────────────┐   │
│ │          │  │                                              │   │
│ │ ┌──────┐ │  │   Page Content                               │   │
│ │ │ Nav  │ │  │   (Outlet / Children)                        │   │
│ │ │ Items│ │  │                                              │   │
│ │ └──────┘ │  │                                              │   │
│ │          │  │                                              │   │
│ │ ┌──────┐ │  │                                              │   │
│ │ │Quota │ │  │                                              │   │
│ │ │ Card │ │  │                                              │   │
│ │ └──────┘ │  │                                              │   │
│ └──────────┘  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘

背景色: bg-[#0F1117]
边框色: border-white/10
```

#### React 组件结构

```tsx
// AppLayout.tsx
export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0F1117] text-white font-inter">
      {/* 顶部栏 */}
      <TopBar />

      <div className="flex">
        {/* 侧边栏 */}
        <Sidebar />

        {/* 主内容区 */}
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}

// TopBar.tsx
export function TopBar() {
  return (
    <header className="h-14 border-b border-white/10 bg-[#0F1117] flex items-center px-4">
      <div className="flex items-center gap-4">
        <Logo />
      </div>

      <div className="flex-1 max-w-xl mx-auto">
        <SearchInput />
      </div>

      <div className="flex items-center gap-4">
        <NotificationBell />
        <UserMenu />
      </div>
    </header>
  );
}

// Sidebar.tsx
export function Sidebar() {
  return (
    <aside className="w-64 border-r border-white/10 min-h-[calc(100vh-3.5rem)] p-4">
      <nav className="space-y-2">
        <NavItem icon={LayoutDashboard} label="Dashboard" href="/dashboard" />
        <NavItem icon={Play} label="采集任务" href="/tasks" />
        <NavItem icon={Database} label="数据中心" href="/data" />
        <NavItem icon={Search} label="全文检索" href="/search" />
        <NavItem icon={Settings} label="设置" href="/settings" />
      </nav>

      {/* 配额卡片 */}
      <div className="mt-auto pt-4">
        <QuotaCard />
      </div>
    </aside>
  );
}
```

### 2.2 组件规范 - Aura 风格基础组件

#### Card 组件

```tsx
// ui/Card.tsx
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hoverable?: boolean;
  glowColor?: "purple" | "blue" | "green" | "warning";
}

const glowColors = {
  purple: "hover:shadow-[0_0_20px_rgba(168,85,247,0.15)]",
  blue: "hover:shadow-[0_0_20px_rgba(59,130,246,0.15)]",
  green: "hover:shadow-[0_0_20px_rgba(34,197,94,0.15)]",
  warning: "hover:shadow-[0_0_20px_rgba(234,179,8,0.15)]",
};

export function Card({
  children,
  className,
  hoverable = false,
  glowColor = "purple"
}: CardProps) {
  return (
    <motion.div
      className={cn(
        // 基础样式
        "rounded-xl bg-[#0F1117] border border-white/10",
        // 可交互态
        hoverable && [
          "transition-all duration-300",
          "hover:border-white/20",
          glowColors[glowColor],
        ],
        className
      )}
      whileHover={hoverable ? { scale: 1.01 } : undefined}
    >
      {children}
    </motion.div>
  );
}

// 子组件
Card.Header = function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("px-6 py-4 border-b border-white/10", className)}>
      {children}
    </div>
  );
};

Card.Body = function CardBody({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("px-6 py-4", className)}>
      {children}
    </div>
  );
};
```

#### Input 组件

```tsx
// ui/Input.tsx
import { cn } from "@/lib/utils";
import { forwardRef, InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, icon, ...props }, ref) => {
    return (
      <div className="space-y-1.5">
        {label && (
          <label className="text-sm text-white/70 font-medium">
            {label}
          </label>
        )}

        <div className="relative">
          {icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40">
              {icon}
            </div>
          )}

          <input
            ref={ref}
            className={cn(
              // 基础样式
              "w-full h-10 px-3 rounded-lg",
              "bg-white/5 border border-white/10",
              "text-white placeholder:text-white/30",
              "font-inter text-sm",

              // Focus 态 - 紫色微光边框
              "focus:outline-none focus:ring-2 focus:ring-purple-500/50",
              "focus:border-purple-500/50",
              "transition-all duration-200",

              // 错误态
              error && "border-red-500/50 focus:ring-red-500/50",

              // 有图标时的 padding
              icon && "pl-10",

              className
            )}
            {...props}
          />
        </div>

        {error && (
          <p className="text-sm text-red-400">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
```

#### Button 组件

```tsx
// ui/Button.tsx
import { cn } from "@/lib/utils";
import { motion, HTMLMotionProps } from "framer-motion";
import { Loader2 } from "lucide-react";

interface ButtonProps extends HTMLMotionProps<"button"> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  icon?: React.ReactNode;
}

const variants = {
  primary: [
    "bg-gradient-to-r from-purple-600 to-blue-600",
    "hover:from-purple-500 hover:to-blue-500",
    "text-white font-medium",
    "shadow-[0_0_20px_rgba(168,85,247,0.3)]",
    "hover:shadow-[0_0_30px_rgba(168,85,247,0.4)]",
  ],
  secondary: [
    "bg-white/5 border border-white/10",
    "hover:bg-white/10 hover:border-white/20",
    "text-white",
  ],
  ghost: [
    "bg-transparent",
    "hover:bg-white/5",
    "text-white/70 hover:text-white",
  ],
  danger: [
    "bg-red-600/20 border border-red-500/30",
    "hover:bg-red-600/30",
    "text-red-400",
  ],
};

const sizes = {
  sm: "h-8 px-3 text-sm rounded-md",
  md: "h-10 px-4 text-sm rounded-lg",
  lg: "h-12 px-6 text-base rounded-lg",
};

export function Button({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <motion.button
      className={cn(
        // 基础样式
        "inline-flex items-center justify-center gap-2",
        "font-inter transition-all duration-200",
        "disabled:opacity-50 disabled:cursor-not-allowed",

        // 变体样式
        variants[variant],
        sizes[size],

        className
      )}
      disabled={disabled || loading}
      whileHover={{ scale: disabled ? 1 : 1.02 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      {...props}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : icon ? (
        icon
      ) : null}
      {children}
    </motion.button>
  );
}
```

#### 滑块验证码组件

```tsx
// ui/SliderCaptcha.tsx
import { useState, useRef } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { CheckCircle } from "lucide-react";

interface SliderCaptchaProps {
  onSuccess: () => void;
  onFail: () => void;
  disabled?: boolean;
}

export function SliderCaptcha({ onSuccess, onFail, disabled }: SliderCaptchaProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState(0);
  const [verified, setVerified] = useState(false);
  const trackRef = useRef<HTMLDivElement>(null);

  // 目标位置 (随机生成)
  const targetPosition = useRef(Math.random() * 60 + 20); // 20% - 80%
  const tolerance = 3; // 允许误差

  const handleDrag = (e: MouseEvent | TouchEvent) => {
    if (!trackRef.current || disabled) return;

    const rect = trackRef.current.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const newPosition = ((clientX - rect.left) / rect.width) * 100;

    setPosition(Math.max(0, Math.min(100, newPosition)));
  };

  const handleDragEnd = () => {
    setIsDragging(false);

    // 验证位置
    if (Math.abs(position - targetPosition.current) <= tolerance) {
      setVerified(true);
      onSuccess();
    } else {
      setPosition(0);
      onFail();
    }
  };

  return (
    <div className={cn(
      "space-y-3",
      disabled && "opacity-50 pointer-events-none"
    )}>
      {/* 拼图区域 */}
      <div className="relative h-32 rounded-lg overflow-hidden bg-white/5 border border-white/10">
        {/* 背景图 (可替换为实际验证图) */}
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/30 to-blue-900/30" />

        {/* 目标缺口 */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-12 h-12 rounded border-2 border-dashed border-purple-500/50"
          style={{ left: `${targetPosition.current}%`, marginLeft: -24 }}
        />

        {/* 滑块拼图块 */}
        <motion.div
          className={cn(
            "absolute top-1/2 -translate-y-1/2 w-12 h-12 rounded",
            "bg-gradient-to-br from-purple-500 to-blue-500",
            "shadow-[0_0_15px_rgba(168,85,247,0.5)]",
            verified && "bg-green-500"
          )}
          style={{ left: `${position}%`, marginLeft: -24 }}
        />
      </div>

      {/* 滑动轨道 */}
      <div
        ref={trackRef}
        className="relative h-12 rounded-lg bg-white/5 border border-white/10 overflow-hidden"
      >
        {/* 填充进度 */}
        <div
          className={cn(
            "absolute inset-y-0 left-0 bg-gradient-to-r",
            verified
              ? "from-green-600/30 to-green-500/30"
              : "from-purple-600/30 to-blue-600/30"
          )}
          style={{ width: `${position}%` }}
        />

        {/* 提示文字 */}
        <div className="absolute inset-0 flex items-center justify-center text-sm text-white/50">
          {verified ? (
            <span className="flex items-center gap-2 text-green-400">
              <CheckCircle className="w-4 h-4" />
              验证成功
            </span>
          ) : (
            "向右拖动滑块完成验证"
          )}
        </div>

        {/* 滑块 */}
        <motion.div
          className={cn(
            "absolute top-1 bottom-1 w-12 rounded-md",
            "bg-gradient-to-r from-purple-500 to-blue-500",
            "flex items-center justify-center cursor-grab",
            "shadow-[0_0_10px_rgba(168,85,247,0.5)]",
            isDragging && "cursor-grabbing",
            verified && "from-green-500 to-green-400"
          )}
          style={{ left: `calc(${position}% - 24px)` }}
          drag="x"
          dragConstraints={trackRef}
          dragElastic={0}
          onDragStart={() => setIsDragging(true)}
          onDrag={(_, info) => {
            if (trackRef.current) {
              const rect = trackRef.current.getBoundingClientRect();
              const newPos = (info.point.x - rect.left) / rect.width * 100;
              setPosition(Math.max(0, Math.min(100, newPos)));
            }
          }}
          onDragEnd={handleDragEnd}
        >
          <div className="w-1 h-4 bg-white/50 rounded-full" />
        </motion.div>
      </div>
    </div>
  );
}
```

---

## 3. QA 工程师 (Test Engineer) 策略

### 3.1 测试金字塔结构

```text
                    ┌─────────────┐
                   /│   E2E      │\
                  / │ (Playwright)│ \      <- 少量关键用户流程
                 /  └─────────────┘  \
                /   ┌─────────────────┐\
               /    │  Integration    │ \   <- API 端点、服务集成
              /     │   (pytest)      │  \
             /      └─────────────────┘   \
            /       ┌─────────────────────┐\
           /        │      Unit           │ \  <- 核心逻辑、解析器、算法
          /         │     (pytest)        │  \
         /          └─────────────────────┘   \
        ────────────────────────────────────────
```

### 3.2 测试分类与覆盖范围

| 测试类型 | 覆盖目标 | 测试框架 | 文件位置 |
|---------|---------|---------|---------|
| **Unit** | 解析器、去重算法、配额计算、工具函数 | pytest | `backend/tests/unit/` |
| **Integration** | API 端点、服务层、数据库操作 | pytest + httpx | `backend/tests/integration/` |
| **Contract** | 爬虫输出 Schema、API 响应格式 | pytest + pydantic | `backend/tests/contract/` |
| **E2E** | 用户登录流程、任务创建流程 | Playwright | `frontend/tests/e2e/` |

### 3.3 具体测试用例规划

#### Unit Tests (单元测试)

```python
# tests/unit/test_parsers.py
"""新闻解析器单元测试"""

import pytest
from app.scrapers.news.parser import NewsParser

class TestNewsParser:
    """测试 trafilatura 新闻解析器"""

    @pytest.fixture
    def parser(self):
        return NewsParser()

    def test_extract_title_from_html(self, parser, sample_html):
        """测试标题提取"""
        result = parser.parse(sample_html)
        assert result.title is not None
        assert len(result.title) > 0

    def test_extract_publish_date(self, parser, sample_html):
        """测试发布时间提取"""
        result = parser.parse(sample_html)
        assert result.published_at is not None

    def test_handle_malformed_html(self, parser):
        """测试畸形 HTML 处理"""
        malformed = "<html><body><p>Unclosed tag"
        result = parser.parse(malformed)
        assert result.content is not None  # 不应崩溃

# tests/unit/test_dedup.py
"""去重算法单元测试"""

import pytest
from app.services.dedup import DedupService, simhash

class TestSimHash:
    """测试 SimHash 内容指纹算法"""

    def test_identical_content_same_hash(self):
        """相同内容应产生相同指纹"""
        content = "这是一段测试文本"
        hash1 = simhash(content)
        hash2 = simhash(content)
        assert hash1 == hash2

    def test_similar_content_close_hash(self):
        """相似内容应产生接近指纹（汉明距离小）"""
        content1 = "这是一段测试文本，用于验证去重算法"
        content2 = "这是一段测试文本，用于验证去重功能"

        hash1 = simhash(content1)
        hash2 = simhash(content2)

        # 汉明距离应小于阈值
        distance = bin(hash1 ^ hash2).count('1')
        assert distance < 10

    def test_different_content_different_hash(self):
        """完全不同内容应产生不同指纹"""
        content1 = "新闻标题A：今日天气晴朗"
        content2 = "科技新闻：人工智能最新突破"

        hash1 = simhash(content1)
        hash2 = simhash(content2)

        distance = bin(hash1 ^ hash2).count('1')
        assert distance > 10

class TestDedupService:
    """测试去重服务"""

    @pytest.fixture
    async def dedup_service(self, redis_client):
        return DedupService(redis_client)

    async def test_url_dedup_with_bloom_filter(self, dedup_service):
        """测试 URL Bloom Filter 去重"""
        url = "https://example.com/news/12345"

        # 首次检查应返回 False (不存在)
        assert await dedup_service.url_exists(url) is False

        # 添加后应返回 True
        await dedup_service.add_url(url)
        assert await dedup_service.url_exists(url) is True

    async def test_content_dedup_threshold(self, dedup_service):
        """测试内容相似度阈值"""
        content1 = "这是原始新闻内容"
        content2 = "这是原始新闻内容（略有修改）"

        await dedup_service.add_content(content1)

        # 相似内容应被识别为重复
        is_dup = await dedup_service.is_content_duplicate(content2, threshold=0.9)
        assert is_dup is True
```

#### Integration Tests (集成测试)

```python
# tests/integration/test_auth_api.py
"""认证 API 集成测试"""

import pytest
from httpx import AsyncClient

class TestAuthAPI:
    """测试认证相关 API"""

    @pytest.fixture
    async def client(self, app):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    async def test_register_new_user(self, client):
        """测试用户注册"""
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "captcha_token": "valid_token",
        })
        assert response.status_code == 201
        assert "id" in response.json()

    async def test_register_duplicate_email(self, client, existing_user):
        """测试重复邮箱注册"""
        response = await client.post("/api/v1/auth/register", json={
            "email": existing_user.email,
            "password": "AnotherPass123!",
            "captcha_token": "valid_token",
        })
        assert response.status_code == 409

    async def test_login_with_valid_credentials(self, client, existing_user):
        """测试正确凭证登录"""
        response = await client.post("/api/v1/auth/login", json={
            "email": existing_user.email,
            "password": "CorrectPassword123!",
            "captcha_token": "valid_token",
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_login_captcha_cooldown(self, client, failed_captcha_user):
        """测试验证码冷却期"""
        response = await client.post("/api/v1/auth/login", json={
            "email": failed_captcha_user.email,
            "password": "Password123!",
            "captcha_token": "valid_token",
        })
        assert response.status_code == 429
        assert "cooldown" in response.json()

# tests/integration/test_tenant_isolation.py
"""多租户数据隔离集成测试"""

class TestTenantIsolation:
    """测试租户数据隔离"""

    async def test_user_cannot_see_other_tenant_data(
        self, client, tenant_a_user, tenant_b_task
    ):
        """租户 A 用户不能看到租户 B 的任务"""
        response = await client.get(
            f"/api/v1/tasks/{tenant_b_task.id}",
            headers={"Authorization": f"Bearer {tenant_a_user.token}"},
        )
        assert response.status_code == 403

    async def test_super_admin_can_see_all_tenants(
        self, client, super_admin, tenant_a_task, tenant_b_task
    ):
        """超级管理员可以看到所有租户数据"""
        response = await client.get(
            "/api/v1/admin/tasks",
            headers={"Authorization": f"Bearer {super_admin.token}"},
        )
        assert response.status_code == 200
        task_ids = [t["id"] for t in response.json()["items"]]
        assert tenant_a_task.id in task_ids
        assert tenant_b_task.id in task_ids
```

### 3.4 测试数据 (Fixtures) 生成策略

```python
# tests/fixtures/factories.py
"""测试数据工厂"""

import factory
from factory.alchemy import SQLAlchemyModelFactory
from app.models import User, Tenant, ScrapingTask, NewsArticle

class TenantFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Tenant
        sqlalchemy_session_persistence = "commit"

    name = factory.Sequence(lambda n: f"Tenant {n}")
    quota_config = {"daily_limit": 1000, "concurrent_limit": 5}

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password_hash = factory.LazyAttribute(lambda _: hash_password("TestPass123!"))
    tenant = factory.SubFactory(TenantFactory)
    role_id = 3  # 普通用户
    quota_tier = "basic"

class ScrapingTaskFactory(SQLAlchemyModelFactory):
    class Meta:
        model = ScrapingTask
        sqlalchemy_session_persistence = "commit"

    tenant = factory.SubFactory(TenantFactory)
    user = factory.SubFactory(UserFactory)
    task_type = "news"
    target_url = factory.Sequence(lambda n: f"https://example.com/page/{n}")
    status = "pending"

# tests/conftest.py
"""Pytest fixtures"""

@pytest.fixture
def tenant_a():
    return TenantFactory(name="Tenant A")

@pytest.fixture
def tenant_b():
    return TenantFactory(name="Tenant B")

@pytest.fixture
def tenant_a_user(tenant_a):
    return UserFactory(tenant=tenant_a)

@pytest.fixture
def super_admin():
    return UserFactory(role_id=1, email="admin@example.com")

@pytest.fixture
def sample_html():
    """示例 HTML 用于解析器测试"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>测试新闻标题</title></head>
    <body>
        <article>
            <h1>测试新闻标题</h1>
            <time datetime="2025-12-18">2025年12月18日</time>
            <p>这是新闻正文内容...</p>
        </article>
    </body>
    </html>
    """
```

---

## 4. 运维工程师 (DevOps) 方案

### 4.1 Docker 镜像分层构建策略

#### 后端 Dockerfile (多阶段构建)

```dockerfile
# backend/Dockerfile

# ==================== 阶段 1: 构建依赖 ====================
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# ==================== 阶段 2: 运行时镜像 ====================
FROM python:3.11-slim as runtime

WORKDIR /app

# 只安装运行时必需的系统包
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 前端 Dockerfile (多阶段构建)

```dockerfile
# frontend/Dockerfile

# ==================== 阶段 1: 构建 ====================
FROM node:20-alpine as builder

WORKDIR /app

# 复制包管理文件
COPY package.json pnpm-lock.yaml ./

# 安装 pnpm 并安装依赖
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# 复制源代码
COPY . .

# 构建生产版本
RUN pnpm build

# ==================== 阶段 2: Nginx 运行时 ====================
FROM nginx:alpine as runtime

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### 镜像体积优化对比

| 镜像 | 未优化 | 多阶段构建后 | 优化比例 |
|-----|-------|------------|---------|
| Backend | ~1.2GB | ~350MB | 70% ↓ |
| Frontend | ~500MB | ~25MB | 95% ↓ |

### 4.2 日志收集方案 (Loguru)

#### 日志配置

```python
# app/core/logging.py
"""结构化日志配置"""

import sys
from loguru import logger
from app.core.config import settings

def setup_logging():
    """配置 Loguru 日志系统"""

    # 移除默认 handler
    logger.remove()

    # 控制台输出 (开发环境)
    if settings.LOG_TO_CONSOLE:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level=settings.LOG_LEVEL,
            colorize=True,
        )

    # 文件输出 (JSON 格式，便于 ELK 采集)
    if settings.LOG_TO_FILE:
        logger.add(
            settings.LOG_FILE_PATH,
            format="{message}",
            level=settings.LOG_LEVEL,
            rotation="100 MB",  # 文件大小轮转
            retention="7 days",  # 保留 7 天
            compression="gz",    # 压缩旧日志
            serialize=True,      # JSON 序列化
        )

    # 错误日志单独文件
    logger.add(
        settings.ERROR_LOG_PATH,
        format="{message}",
        level="ERROR",
        rotation="50 MB",
        retention="30 days",
        compression="gz",
        serialize=True,
    )

    return logger

# 使用示例
logger = setup_logging()

# 结构化日志输出
logger.info(
    "采集任务开始",
    extra={
        "task_id": task.id,
        "tenant_id": task.tenant_id,
        "target_url": task.target_url,
        "task_type": task.task_type,
    }
)

logger.bind(
    task_id=task.id,
    scraper="news",
    execution_time_ms=elapsed,
).info("采集任务完成", article_count=len(articles))
```

#### 日志输出示例 (JSON 格式)

```json
{
  "text": "采集任务完成",
  "record": {
    "elapsed": {"repr": "0:00:05.234", "seconds": 5.234},
    "level": {"icon": "ℹ️", "name": "INFO", "no": 20},
    "message": "采集任务完成",
    "name": "app.scrapers.news",
    "time": {"repr": "2025-12-18 10:30:45.123456+08:00", "timestamp": 1734489045.123456}
  },
  "extra": {
    "task_id": 12345,
    "scraper": "news",
    "execution_time_ms": 5234,
    "article_count": 25
  }
}
```

### 4.3 Docker Compose 生产配置

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    environment:
      - DATABASE_URL=mysql+aiomysql://${MYSQL_USER}:${MYSQL_PASSWORD}@mysql:3306/${MYSQL_DATABASE}
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - STORAGE_PROVIDER=${STORAGE_PROVIDER:-minio}
      - MINIO_ENDPOINT=minio:9000
      - LOG_LEVEL=INFO
      - LOG_TO_FILE=true
      - LOG_FILE_PATH=/app/logs/app.log
    volumes:
      - ./logs/backend:/app/logs
    depends_on:
      - mysql
      - redis
      - minio
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
    restart: always
    environment:
      - DATABASE_URL=mysql+aiomysql://${MYSQL_USER}:${MYSQL_PASSWORD}@mysql:3306/${MYSQL_DATABASE}
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    volumes:
      - ./logs/celery:/app/logs
    depends_on:
      - mysql
      - redis
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.tasks.celery_app beat --loglevel=info
    restart: always
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: always
    ports:
      - "80:80"
    depends_on:
      - backend

  mysql:
    image: mysql:8.0
    restart: always
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DATABASE}
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  minio:
    image: minio/minio
    restart: always
    environment:
      - MINIO_ROOT_USER=${MINIO_ACCESS_KEY}
      - MINIO_ROOT_PASSWORD=${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

  meilisearch:
    image: getmeili/meilisearch:v1.6
    restart: always
    environment:
      - MEILI_MASTER_KEY=${MEILI_MASTER_KEY}
    volumes:
      - meilisearch_data:/meili_data

volumes:
  mysql_data:
  redis_data:
  minio_data:
  meilisearch_data:
```

---

## 技术决策总结

| 决策项 | 选择 | 理由 | 备选方案 |
|-------|-----|------|---------|
| 多租户模式 | 共享数据库 + tenant_id | 简单高效，适合 SaaS 初期 | 独立数据库（复杂度高） |
| 对象存储 | MinIO (S3 兼容) | 自托管、S3 API 兼容 | 直接用 S3（成本高） |
| 任务队列 | Celery + Redis | 成熟稳定，社区活跃 | RabbitMQ（重量级） |
| 全文检索 | Meilisearch | 轻量、易部署、中文支持好 | Elasticsearch（重量级） |
| 内容去重 | Bloom Filter + SimHash | URL 精确 + 内容模糊 | 纯数据库去重（性能差） |
| 前端状态 | Zustand | 轻量、TypeScript 友好 | Redux（复杂度高） |
| 图表库 | Recharts | React 生态、深色主题支持 | ECharts（API 复杂） |
| 日志系统 | Loguru | 简洁 API、结构化输出 | logging（配置繁琐） |
