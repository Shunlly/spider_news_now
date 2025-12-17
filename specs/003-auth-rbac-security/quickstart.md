# Quickstart: 用户鉴权、数据隔离与安全验证

**Feature**: 003-auth-rbac-security
**Created**: 2025-12-16

## Prerequisites

确保以下服务已运行：

```bash
# 1. MySQL 数据库
docker-compose up -d mysql

# 2. Redis (验证码存储)
docker-compose up -d redis

# 3. Backend API
cd backend && uvicorn app.main:app --reload

# 4. Frontend
cd frontend && pnpm dev
```

## 快速开始

### 1. 运行数据库迁移

```bash
cd backend

# 生成迁移文件
alembic revision --autogenerate -m "add_user_auth_and_rbac"

# 执行迁移
alembic upgrade head
```

### 2. 创建管理员账户

迁移会自动创建默认管理员，也可以手动创建：

```bash
# 使用 CLI 工具 (如果有)
python -m app.cli create-admin --username admin --password admin123

# 或者使用 API
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123!", "role": "admin"}'
```

### 3. 测试登录流程

```bash
# Step 1: 获取验证码
curl http://localhost:8000/api/v1/auth/captcha

# Step 2: 验证滑块 (需要根据返回的图片手动确定 x 坐标)
curl -X POST http://localhost:8000/api/v1/auth/verify-captcha \
  -H "Content-Type: application/json" \
  -d '{"token": "<captcha_token>", "x": 150}'

# Step 3: 登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin123!",
    "captcha_token": "<verified_token>"
  }'
```

### 4. 测试数据隔离

```bash
# 使用管理员 Token (应该看到所有数据)
curl http://localhost:8000/api/v1/scrapers/status \
  -H "Authorization: Bearer <admin_token>"

# 创建普通用户
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "User123!", "role": "user"}'

# 使用普通用户 Token (应该只看到自己的数据)
curl http://localhost:8000/api/v1/scrapers/status \
  -H "Authorization: Bearer <user1_token>"
```

## 开发调试

### 跳过验证码 (仅开发环境)

在 `.env` 中设置：

```env
# 开发环境跳过验证码
SKIP_CAPTCHA=true
```

### 查看 Redis 中的验证码

```bash
# 连接 Redis
redis-cli

# 查看所有验证码 Key
KEYS captcha:*

# 查看具体验证码内容
HGETALL captcha:<token>
```

### 查看登录日志

```bash
# 查看最近的登录尝试
tail -f logs/app.log | grep -E "login|captcha"
```

## 关键文件

| 文件 | 说明 |
|------|------|
| `backend/app/models/user.py` | 用户模型 |
| `backend/app/services/captcha_service.py` | 验证码服务 |
| `backend/app/services/permission_service.py` | 权限过滤服务 |
| `backend/app/api/v1/endpoints/auth.py` | 认证 API |
| `frontend/src/components/SliderCaptcha/` | 滑块验证码组件 |
| `frontend/src/pages/LoginPage.tsx` | 登录页面 |

## 常见问题

### Q: 验证码图片加载失败

检查 Redis 连接和 PIL/Pillow 安装：

```bash
pip install pillow
redis-cli ping  # 应返回 PONG
```

### Q: 登录后无法访问数据

检查 JWT Token 是否正确传递：

```bash
# 确保 Header 格式正确
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Q: 数据隔离不生效

检查 API 端点是否添加了权限过滤依赖：

```python
@router.get("/items")
async def list_items(
    user: User = Depends(get_current_user),  # 必须添加
    db: AsyncSession = Depends(get_db),
):
    user_filter = get_user_filter(user, Item)
    # ...
```

## 测试

```bash
# 运行认证相关测试
cd backend
pytest tests/unit/test_captcha_service.py -v
pytest tests/unit/test_permission_service.py -v
pytest tests/integration/test_auth_api.py -v

# 运行前端测试
cd frontend
pnpm test src/components/SliderCaptcha
```
