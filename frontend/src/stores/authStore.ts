/**
 * 认证状态管理 Store
 * Auth State Management with Zustand
 *
 * 管理用户认证状态：
 * - 用户信息
 * - 访问令牌
 * - 认证状态
 * - 登录/登出操作
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { LoginRequest, AuthState } from '../types/auth';
import authService from '../services/authService';

// 本地存储的 key
const AUTH_STORAGE_KEY = 'auth-storage';
const TOKEN_KEY = 'access_token';

/**
 * Auth Store 接口
 */
interface AuthStore extends AuthState {
  // Hydration state
  isHydrated: boolean;
  // Actions
  login: (request: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
  fetchCurrentUser: () => Promise<void>;
  setToken: (token: string | null) => void;
  setUser: (user: AuthState['user']) => void;
  clearError: () => void;
  hydrate: () => void;
  setHydrated: (value: boolean) => void;
}

/**
 * 创建 Auth Store
 */
export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial State
      user: null,
      token: null,
      isAuthenticated: false,
      loading: false,
      error: null,
      isHydrated: false,

      // 设置水合状态
      setHydrated: (value: boolean) => {
        set({ isHydrated: value });
      },

      // 登录
      login: async (request: LoginRequest) => {
        set({ loading: true, error: null });
        try {
          const response = await authService.login(request);

          // 存储 token 到 localStorage（供 axios 拦截器使用）
          localStorage.setItem(TOKEN_KEY, response.access_token);

          set({
            user: response.user,
            token: response.access_token,
            isAuthenticated: true,
            isHydrated: true,
            loading: false,
            error: null,
          });
        } catch (err) {
          const message = err instanceof Error ? err.message : '登录失败';
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            loading: false,
            error: message,
          });
          throw err;
        }
      },

      // 登出
      logout: async () => {
        set({ loading: true });
        try {
          await authService.logout();
        } catch {
          // 即使 API 调用失败也清除本地状态
          console.warn('Logout API call failed, clearing local state anyway');
        } finally {
          // 清除本地存储
          localStorage.removeItem(TOKEN_KEY);

          set({
            user: null,
            token: null,
            isAuthenticated: false,
            loading: false,
            error: null,
          });
        }
      },

      // 刷新 Token
      refreshToken: async () => {
        try {
          const response = await authService.refreshToken();

          // 更新 token
          localStorage.setItem(TOKEN_KEY, response.access_token);

          set({
            token: response.access_token,
            isAuthenticated: true,
          });

          return true;
        } catch {
          // 刷新失败，清除认证状态
          localStorage.removeItem(TOKEN_KEY);

          set({
            user: null,
            token: null,
            isAuthenticated: false,
          });

          return false;
        }
      },

      // 获取当前用户信息
      fetchCurrentUser: async () => {
        const token = get().token || localStorage.getItem(TOKEN_KEY);
        if (!token) {
          set({ user: null, isAuthenticated: false });
          return;
        }

        set({ loading: true });
        try {
          const user = await authService.getCurrentUser();
          set({
            user,
            isAuthenticated: true,
            loading: false,
          });
        } catch {
          // 获取用户信息失败，可能是 token 过期
          localStorage.removeItem(TOKEN_KEY);
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            loading: false,
          });
        }
      },

      // 设置 Token（供 axios 拦截器调用）
      setToken: (token: string | null) => {
        if (token) {
          localStorage.setItem(TOKEN_KEY, token);
          set({ token, isAuthenticated: true });
        } else {
          localStorage.removeItem(TOKEN_KEY);
          set({ token: null, isAuthenticated: false, user: null });
        }
      },

      // 设置用户信息
      setUser: (user: AuthState['user']) => {
        set({ user });
      },

      // 清除错误
      clearError: () => {
        set({ error: null });
      },

      // 水合状态（从 localStorage 恢复）
      hydrate: () => {
        const token = localStorage.getItem(TOKEN_KEY);
        if (token) {
          set({ token, isAuthenticated: true });
          // 异步获取用户信息
          get().fetchCurrentUser();
        }
      },
    }),
    {
      name: AUTH_STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      // 只持久化 user 和 token
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      // 水合完成后设置标志
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.setHydrated(true);
        }
      },
    }
  )
);

/**
 * 获取当前 token（供外部使用）
 */
export const getToken = (): string | null => {
  return useAuthStore.getState().token || localStorage.getItem(TOKEN_KEY);
};

/**
 * 检查是否已认证
 */
export const isAuthenticated = (): boolean => {
  return useAuthStore.getState().isAuthenticated;
};

export default useAuthStore;
