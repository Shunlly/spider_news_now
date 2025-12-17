/**
 * API 客户端配置
 * API Client Configuration with Auth Interceptors
 *
 * 功能：
 * - 自动注入 Authorization 头
 * - Token 过期自动刷新
 * - 统一错误处理
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

// Token 存储 key
const TOKEN_KEY = 'access_token';

// 标记是否正在刷新 token
let isRefreshing = false;
// 等待 token 刷新的请求队列
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: Error) => void;
}> = [];

/**
 * 处理等待队列
 */
const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else if (token) {
      promise.resolve(token);
    }
  });
  failedQueue = [];
};

// 创建 Axios 实例
const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  // 允许发送 Cookie（用于 refresh_token）
  withCredentials: true,
});

// 请求拦截器 - 自动注入 Token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem(TOKEN_KEY);

    // 如果有 token，添加到请求头
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理 401 和 Token 刷新
apiClient.interceptors.response.use(
  (response) => {
    // 成功响应直接返回数据
    return response.data;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // 如果是 401 错误且不是重试请求
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 如果是登录、刷新或登出请求本身失败，不要尝试刷新
      if (
        originalRequest.url?.includes('/auth/login') ||
        originalRequest.url?.includes('/auth/refresh') ||
        originalRequest.url?.includes('/auth/logout')
      ) {
        return Promise.reject(error);
      }

      // 如果正在刷新 token，将请求加入队列等待
      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      // 标记为重试请求
      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // 尝试刷新 token
        const response = await apiClient.post<{ access_token: string }>('/auth/refresh');
        const newToken = (response as unknown as { access_token: string }).access_token;

        // 存储新 token
        localStorage.setItem(TOKEN_KEY, newToken);

        // 处理等待队列
        processQueue(null, newToken);

        // 重试原始请求
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        }
        return apiClient(originalRequest);
      } catch (refreshError) {
        // 刷新失败，清除 token 并处理队列
        localStorage.removeItem(TOKEN_KEY);
        processQueue(new Error('Token 刷新失败'));

        // 触发登出事件（可以通过 window event 通知 store）
        window.dispatchEvent(new CustomEvent('auth:logout'));

        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // 统一错误处理
    const message =
      (error.response?.data as { detail?: string })?.detail ||
      error.message ||
      '请求失败';
    console.error('API Error:', message);
    return Promise.reject(new Error(message));
  }
);

/**
 * 手动设置 Token（用于登录后）
 */
export const setAuthToken = (token: string | null) => {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
};

/**
 * 获取当前 Token
 */
export const getAuthToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * 清除 Token
 */
export const clearAuthToken = () => {
  localStorage.removeItem(TOKEN_KEY);
};

export default apiClient;
