/**
 * 根应用组件
 * Root Application Component
 *
 * 特性：
 * - 路由懒加载（代码分割）
 * - Toast 通知系统
 * - 认证状态管理
 * - 空闲时预加载常用路由
 */

import { useEffect, Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import MainLayout from './layouts/MainLayout';
import ProtectedRoute from './components/ProtectedRoute';
import { ToastProvider, useToast, setGlobalToast } from '@/components/ui';
import ErrorBoundary from '@/components/ErrorBoundary';
import { useAuthStore } from './stores/authStore';
import { preloadOnIdle } from '@/utils/preload';

// 路由懒加载 - 代码分割
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const NewsPage = lazy(() => import('./pages/NewsPage'));
const DataPoolPage = lazy(() => import('./pages/DataPoolPage'));
const SocialPage = lazy(() => import('./pages/SocialPage'));
const TelegramPage = lazy(() => import('./pages/TelegramPage'));
const TwitterPage = lazy(() => import('./pages/TwitterPage'));
const SearchPage = lazy(() => import('./pages/SearchPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

// 管理页面懒加载
const TenantManagePage = lazy(() => import('./pages/admin/TenantManagePage'));
const UserManagePage = lazy(() => import('./pages/admin/UserManagePage'));
const AuditLogPage = lazy(() => import('./pages/admin/AuditLogPage'));
const SystemMonitorPage = lazy(() => import('./pages/admin/SystemMonitorPage'));

// 页面加载 Loading 组件
function PageLoading() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
    </div>
  );
}

// Toast 初始化组件
function ToastInitializer() {
  const toast = useToast();
  useEffect(() => {
    setGlobalToast(toast);
  }, [toast]);
  return null;
}

function AppContent() {
  const { hydrate, logout } = useAuthStore();

  // 应用启动时恢复认证状态
  useEffect(() => {
    hydrate();
  }, [hydrate]);

  // 空闲时预加载常用路由
  useEffect(() => {
    preloadOnIdle();
  }, []);

  // 监听全局登出事件（由 axios 拦截器触发）
  useEffect(() => {
    const handleLogout = () => {
      logout();
    };

    window.addEventListener('auth:logout', handleLogout);
    return () => {
      window.removeEventListener('auth:logout', handleLogout);
    };
  }, [logout]);

  return (
    <Suspense fallback={<PageLoading />}>
      <Routes>
        {/* 登录和注册页面（公开） */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* 受保护的路由 */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="data-pool" element={<DataPoolPage />} />
          <Route path="news" element={<NewsPage />} />
          <Route path="social" element={<SocialPage />} />
          <Route path="telegram" element={<TelegramPage />} />
          <Route path="twitter" element={<TwitterPage />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="profile" element={<ProfilePage />} />

          {/* 管理页面 */}
          <Route path="admin" element={<Navigate to="/admin/system" replace />} />
          <Route path="admin/tenants" element={<TenantManagePage />} />
          <Route path="admin/users" element={<UserManagePage />} />
          <Route path="admin/audit-logs" element={<AuditLogPage />} />
          <Route path="admin/system" element={<SystemMonitorPage />} />
        </Route>

        {/* 404 页面 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <ToastInitializer />
        <AppContent />
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
