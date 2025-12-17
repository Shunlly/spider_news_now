/**
 * 认证 API 服务
 * Auth API Service
 *
 * 提供认证相关的 API 调用：
 * - getCaptcha: 获取验证码
 * - verifyCaptcha: 验证滑块位置
 * - login: 用户登录
 * - logout: 用户登出
 * - refresh: 刷新令牌
 * - getCurrentUser: 获取当前用户信息
 */

import apiClient from './api';
import type {
  CaptchaData,
  CaptchaVerifyRequest,
  CaptchaVerifyResponse,
  LoginRequest,
  LoginResponse,
  TokenResponse,
  User,
  MessageResponse,
} from '../types/auth';

/**
 * 获取滑块验证码
 */
export const getCaptcha = async (): Promise<CaptchaData> => {
  return apiClient.get('/auth/captcha');
};

/**
 * 验证滑块位置
 */
export const verifyCaptcha = async (
  data: CaptchaVerifyRequest
): Promise<CaptchaVerifyResponse> => {
  return apiClient.post('/auth/verify-captcha', data);
};

/**
 * 用户登录
 */
export const login = async (data: LoginRequest): Promise<LoginResponse> => {
  return apiClient.post('/auth/login', data);
};

/**
 * 用户登出
 */
export const logout = async (): Promise<MessageResponse> => {
  return apiClient.post('/auth/logout');
};

/**
 * 刷新访问令牌
 */
export const refreshToken = async (
  refreshToken?: string
): Promise<TokenResponse> => {
  return apiClient.post('/auth/refresh', { refresh_token: refreshToken });
};

/**
 * 获取当前用户信息
 */
export const getCurrentUser = async (): Promise<User> => {
  return apiClient.get('/auth/me');
};

/**
 * 认证服务对象（便于统一导入）
 */
const authService = {
  getCaptcha,
  verifyCaptcha,
  login,
  logout,
  refreshToken,
  getCurrentUser,
};

export default authService;
