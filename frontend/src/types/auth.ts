/**
 * 认证相关 TypeScript 类型定义
 * Auth TypeScript Interfaces and Types
 *
 * 定义登录、用户、验证码等认证相关的类型。
 * 与后端 Pydantic schemas 保持一致。
 */

// ============== User Types ==============

/**
 * 用户角色枚举
 */
export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
}

/**
 * 用户信息（从后端返回）
 */
export interface User {
  id: number;
  username: string;
  email: string | null;
  role: UserRole;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

/**
 * 创建用户请求
 */
export interface UserCreate {
  username: string;
  email?: string;
  password: string;
  role?: UserRole;
}

/**
 * 更新用户请求
 */
export interface UserUpdate {
  email?: string;
  role?: UserRole;
  is_active?: boolean;
}

/**
 * 更新密码请求
 */
export interface UserPasswordUpdate {
  current_password: string;
  new_password: string;
}

/**
 * 用户列表响应
 */
export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  page_size: number;
}

// ============== Captcha Types ==============

/**
 * 验证码数据（从后端获取）
 */
export interface CaptchaData {
  /** 验证码 Token（UUID） */
  token: string;
  /** 验证码图片 Base64 */
  image: string;
}

/**
 * 验证码验证请求
 */
export interface CaptchaVerifyRequest {
  token: string;
  code: string;
}

/**
 * 验证码验证响应
 */
export interface CaptchaVerifyResponse {
  success: boolean;
  verified_token?: string;
  message?: string;
}

// ============== Login Types ==============

/**
 * 登录请求
 */
export interface LoginRequest {
  username: string;
  password: string;
  captcha_token: string;
}

/**
 * 登录响应
 */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// ============== Token Types ==============

/**
 * Token 刷新响应
 */
export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

/**
 * JWT Token 载荷（解码后）
 */
export interface TokenPayload {
  sub: string;
  exp: number;
  type: 'access' | 'refresh';
}

// ============== Auth State Types ==============

/**
 * 认证状态（用于 store）
 */
export interface AuthState {
  /** 当前登录用户 */
  user: User | null;
  /** Access Token */
  token: string | null;
  /** 是否已认证 */
  isAuthenticated: boolean;
  /** 是否正在加载 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;
}

// ============== Error Types ==============

/**
 * API 错误响应
 */
export interface ErrorResponse {
  detail: string;
  error_code?: string;
}

/**
 * 消息响应
 */
export interface MessageResponse {
  message: string;
}
