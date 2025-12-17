# Research: 用户鉴权、数据隔离与安全验证

**Feature**: 003-auth-rbac-security
**Created**: 2025-12-16
**Status**: Complete

## 1. 滑块验证码技术选型

### Decision: 使用 PIL/Pillow 自行生成滑块验证码

### Rationale
1. **完全控制**：可自定义缺口形状、大小、位置
2. **无第三方依赖**：不依赖外部 API 服务
3. **性能可控**：本地生成，无网络延迟
4. **样式自由**：可适配 Glassmorphism 风格

### Alternatives Considered

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| 第三方服务 (reCAPTCHA) | 成熟、安全 | 依赖外网、样式不可控 | 不适合 |
| captcha 库 | 简单易用 | 只支持图形验证码 | 不适合 |
| py-captcha | 支持滑块 | 样式固定、依赖老旧 | 不适合 |
| PIL/Pillow 自实现 | 完全可控 | 需自行实现算法 | **采用** |

### Implementation Details

```python
# 滑块验证码生成流程
1. 加载背景图片 (预置多张风景图)
2. 在随机位置生成拼图形状 (凸起 + 凹槽)
3. 裁剪出滑块图片
4. 背景图对应位置变暗/模糊
5. 返回: background_base64, slider_base64, encrypted_position
```

### 验证码存储方案

**Decision**: Redis with TTL

```python
# Redis Key 结构
captcha:{token} = {
    "x": 150,           # 正确的 x 坐标
    "created_at": timestamp,
    "attempts": 0       # 尝试次数
}
TTL = 300  # 5 分钟
```

### 验证算法

```python
def verify_captcha(token: str, user_x: int, tolerance: int = 5) -> bool:
    """
    验证滑块位置

    Args:
        token: 验证码 Token
        user_x: 用户提交的 x 坐标
        tolerance: 容差范围 (默认 ±5 像素)

    Returns:
        True if |user_x - correct_x| <= tolerance
    """
    correct_x = redis.get(f"captcha:{token}")["x"]
    return abs(user_x - correct_x) <= tolerance
```

---

## 2. 数据隔离实现方案

### Decision: FastAPI 依赖注入 + Service 层统一过滤

### Rationale
1. **代码复用**：权限逻辑集中在一处
2. **低侵入性**：现有 API 只需添加依赖参数
3. **易于测试**：权限逻辑可独立测试
4. **易于扩展**：未来可添加更多角色

### Implementation Design

```python
# backend/app/services/permission_service.py

from typing import Optional, Any
from sqlalchemy import and_, ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole

def get_user_filter(
    user: User,
    model_class: Any,
    user_id_column: str = "user_id"
) -> Optional[ColumnElement[bool]]:
    """
    获取基于用户角色的数据过滤条件

    - Admin: 返回 None (无过滤，查看所有数据)
    - User: 返回 model.user_id == user.id

    Args:
        user: 当前登录用户
        model_class: SQLAlchemy 模型类
        user_id_column: user_id 字段名

    Returns:
        SQLAlchemy 过滤条件，或 None (无过滤)
    """
    if user.role == UserRole.ADMIN:
        return None  # 管理员无限制

    column = getattr(model_class, user_id_column)
    return column == user.id


# 使用示例 - API Endpoint
@router.get("/tasks")
async def list_tasks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(CrawlerTask)

    # 应用权限过滤
    user_filter = get_user_filter(user, CrawlerTask)
    if user_filter is not None:
        query = query.where(user_filter)

    result = await db.execute(query)
    return result.scalars().all()
```

### Database Migration Strategy

```sql
-- 迁移脚本示例 (Alembic)

-- 1. 创建用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 插入默认管理员
INSERT INTO users (id, username, password_hash, role)
VALUES (1, 'admin', '<hashed_password>', 'admin');

-- 3. 为现有表添加 user_id 字段
ALTER TABLE news_sources ADD COLUMN user_id INT DEFAULT 1;
ALTER TABLE news_articles ADD COLUMN user_id INT DEFAULT 1;
ALTER TABLE social_sessions ADD COLUMN user_id INT DEFAULT 1;
ALTER TABLE social_messages ADD COLUMN user_id INT DEFAULT 1;

-- 4. 添加外键约束
ALTER TABLE news_sources
    ADD CONSTRAINT fk_news_sources_user
    FOREIGN KEY (user_id) REFERENCES users(id);
-- ... 其他表类似
```

### Affected Tables

| 表名 | 说明 | 迁移策略 |
|------|------|----------|
| `news_sources` | 新闻来源配置 | 添加 user_id，默认值 1 |
| `news_articles` | 新闻文章 | 添加 user_id，默认值 1 |
| `social_sessions` | 社交会话 | 添加 user_id，默认值 1 |
| `social_messages` | 社交消息 | 通过 session 关联，无需单独添加 |
| `scraper_runs` | 爬虫运行记录 | 添加 user_id，默认值 1 |
| `account_credentials` | 账号凭证 | 添加 user_id，默认值 1 |
| `proxy_configs` | 代理配置 | 添加 user_id，默认值 1 |
| `export_tasks` | 导出任务 | 添加 user_id，默认值 1 |

---

## 3. 前端滑块组件设计

### Decision: 自定义 React 组件 + Glassmorphism 样式

### Component Interface

```typescript
// SliderCaptcha/types.ts
interface SliderCaptchaProps {
  onSuccess: (token: string) => void;  // 验证成功回调
  onFail: () => void;                  // 验证失败回调
  onRefresh: () => void;               // 刷新验证码
  className?: string;                   // 额外样式类
}

interface CaptchaData {
  token: string;           // 验证码 Token
  background: string;      // 背景图 Base64
  slider: string;          // 滑块图 Base64
  sliderY: number;         // 滑块 Y 坐标
}
```

### Glassmorphism Styling

```css
/* SliderCaptcha/styles.css */
.captcha-container {
  /* 毛玻璃效果 */
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.captcha-slider-track {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  height: 40px;
}

.captcha-slider-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  cursor: grab;
  transition: transform 0.2s;
}

.captcha-slider-thumb:hover {
  transform: scale(1.05);
}
```

### Interaction Flow

```
1. 组件挂载 → 调用 GET /auth/captcha 获取验证码
2. 渲染背景图和滑块图
3. 用户拖动滑块 → 实时更新滑块位置
4. 用户释放滑块 → 调用 POST /auth/verify-captcha
5. 验证成功 → onSuccess(token)，登录按钮可用
6. 验证失败 → onFail()，自动刷新验证码
```

---

## 4. 认证流程设计

### JWT Token Strategy

**Decision**: Access Token + Refresh Token

```
Access Token: 短期有效 (15 分钟)，存储在内存/Redux
Refresh Token: 长期有效 (7 天)，存储在 HttpOnly Cookie
```

### Login Flow

```
1. 用户打开登录页
2. 获取验证码 (GET /auth/captcha)
3. 用户输入用户名/密码
4. 用户完成滑块验证
5. 提交登录 (POST /auth/login)
   - 包含: username, password, captcha_token, captcha_x
6. 后端验证:
   a. 验证 captcha_token 和 captcha_x
   b. 验证用户名密码
   c. 生成 JWT Token
7. 返回 Access Token，设置 Refresh Token Cookie
8. 前端存储 Access Token，跳转到首页
```

---

## 5. 安全考量

### 防暴力破解

| 措施 | 实现 |
|------|------|
| 验证码 | 登录必须完成滑块验证 |
| 速率限制 | 同一 IP 每分钟最多 10 次登录尝试 |
| 账号锁定 | 连续 5 次失败后锁定账号 15 分钟 |
| 日志记录 | 记录所有登录尝试 (成功/失败) |

### 验证码安全

| 措施 | 实现 |
|------|------|
| Token 加密 | 使用 Fernet 加密正确坐标 |
| 一次性使用 | 验证后立即从 Redis 删除 |
| 尝试限制 | 每个 Token 最多尝试 3 次 |
| 时效限制 | Token 5 分钟后自动过期 |

---

## 6. 性能考量

### 验证码生成优化

| 优化点 | 措施 |
|--------|------|
| 图片缓存 | 预生成 100 张背景图缓存 |
| 异步生成 | 使用 asyncio 不阻塞主线程 |
| 图片压缩 | JPEG 质量 80%，减少传输大小 |
| CDN 缓存 | 静态背景图可使用 CDN |

### 预期性能指标

| 指标 | 目标值 |
|------|--------|
| 验证码生成时间 | < 100ms |
| 验证响应时间 | < 50ms |
| 登录响应时间 | < 200ms |
| Redis 操作延迟 | < 5ms |
