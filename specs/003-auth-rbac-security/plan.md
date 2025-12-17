# Implementation Plan: 用户鉴权、数据隔离与安全验证 (Auth & RBAC & Security)

**Branch**: `003-auth-rbac-security` | **Date**: 2025-12-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-auth-rbac-security/spec.md`

## Summary

本功能实现用户权限控制和数据隔离，包含三个核心部分：
1. **滑块验证码**：登录时的人机验证，防止暴力破解
2. **RBAC 角色权限**：Admin（管理员）和 User（普通用户）两种角色
3. **数据隔离**：普通用户只能访问自己的数据，管理员可访问所有数据

技术方案：
- 后端使用 FastAPI 依赖注入实现统一权限过滤
- 滑块验证码使用 Python PIL/Pillow 生成，Redis 暂存验证状态
- 数据库通过 Alembic 迁移添加 `user_id` 外键
- 前端自定义滑块组件适配 Glassmorphism 风格

## Technical Context

**Backend**: Python 3.10+ (FastAPI), Pydantic v2, SQLAlchemy (Async)
**Frontend**: React (TypeScript) + Vite + Tailwind CSS + Arco Design
**Database**: MySQL 8.0+ (utf8mb4_unicode_ci)
**Cache**: Redis (验证码状态暂存，5 分钟过期)
**Testing**: pytest + pytest-asyncio (backend), Vitest + RTL (frontend)
**Project Type**: web (backend + frontend separation)
**Constraints**:
- 验证码图片生成需在 100ms 内完成
- 验证码 Token 有效期 5 分钟
- 滑块位置容差 ±5 像素
**Scale/Scope**:
- 支持 1000 并发用户同时进行验证码验证
- 数据隔离需覆盖 4 张核心业务表

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Reference: `.specify/memory/constitution.md` v2.0.0 for complete requirements.

### Architecture Compliance (verify now)

- [x] Storage operations use StorageProvider adapter pattern (Section II.A)
  - N/A: 本功能不涉及文件存储操作
- [x] Data models follow heterogeneous modeling rules (News vs Social) (Section II.B)
  - 符合：仅添加 user_id 外键，不改变现有数据结构
- [x] Deduplication mechanism planned (URL Hash / SimHash) (Section II.C)
  - N/A: 本功能不涉及去重逻辑

### UI/UX Compliance (verify for frontend features)

- [x] UI follows Glassmorphism theme (Section III.A)
  - 滑块验证码组件使用 `backdrop-filter: blur(12px)`, `bg-white/40`
- [x] Layout uses Bento Grid pattern (Section III.B)
  - 登录页面保持现有布局，验证码组件嵌入登录卡片
- [x] Color scheme uses gradient backgrounds (Section III.C)
  - 使用现有登录页渐变背景

### Coding Standards (verify during development)

- [x] Type Hints for all Python functions, TypeScript interfaces for frontend
- [x] Core logic includes Chinese comments (especially captcha generation, permission filter)
- [x] Error handling with retry mechanism for external APIs
  - N/A: 本功能不调用外部 API
- [x] No placeholder code (pass, TODO) - complete implementations only
- [x] Structured logging with context (user_id, captcha_token, verification_result)

## Project Structure

### Documentation (this feature)

```text
specs/003-auth-rbac-security/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI schemas)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/app/
├── models/
│   ├── user.py              # NEW: 用户模型（角色字段）
│   └── *.py                 # MODIFY: 添加 user_id 外键
├── schemas/
│   ├── auth.py              # NEW: 登录/验证码请求响应
│   └── user.py              # NEW: 用户相关 schema
├── services/
│   ├── captcha_service.py   # NEW: 滑块验证码生成和验证
│   ├── auth_service.py      # NEW: 用户认证服务
│   └── permission_service.py # NEW: 权限过滤依赖注入
├── api/v1/endpoints/
│   └── auth.py              # NEW: 登录/验证码 API
└── core/
    └── security.py          # NEW: JWT/Session 安全相关

frontend/src/
├── components/
│   └── SliderCaptcha/       # NEW: 滑块验证码组件
│       ├── index.tsx
│       └── styles.css
├── pages/
│   └── LoginPage.tsx        # NEW: 登录页面
├── services/
│   └── authService.ts       # NEW: 认证 API 调用
├── stores/
│   └── authStore.ts         # NEW: 认证状态管理
└── types/
    └── auth.ts              # NEW: 认证相关类型
```

## Complexity Tracking

> **No violations - all requirements align with Constitution v2.0.0**

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| 验证码存储 | Redis with TTL | 比数据库更适合短期状态存储，5 分钟自动过期 |
| 权限过滤 | 依赖注入函数 | 避免在每个 API 重复编写 if/else 逻辑 |
| 数据迁移 | 历史数据归 admin | 保证数据完整性，管理员可后续重新分配 |
