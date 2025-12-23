/**
 * HUD 风格路由保护组件
 * HUD-style Protected Route Component
 *
 * 功能：
 * - 检查用户是否已登录
 * - 未登录时重定向到登录页
 * - 支持 role_id 权限检查
 */

import { Navigate, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { isAdmin, isSuperAdmin } from '../types/auth';

interface ProtectedRouteProps {
  /**
   * 子组件
   */
  children: React.ReactNode;
  /**
   * 允许的角色 ID 列表（可选）
   * - 1: super_admin
   * - 2: tenant_admin
   * - 3: user
   */
  allowedRoleIds?: number[];
  /**
   * 是否需要管理员权限（简化写法）
   */
  requireAdmin?: boolean;
  /**
   * 是否需要超级管理员权限
   */
  requireSuperAdmin?: boolean;
}

/**
 * 路由保护组件
 *
 * 用法：
 * ```tsx
 * // 任何已登录用户
 * <Route
 *   path="/dashboard"
 *   element={
 *     <ProtectedRoute>
 *       <DashboardPage />
 *     </ProtectedRoute>
 *   }
 * />
 *
 * // 仅管理员
 * <Route
 *   path="/admin"
 *   element={
 *     <ProtectedRoute requireAdmin>
 *       <AdminPage />
 *     </ProtectedRoute>
 *   }
 * />
 *
 * // 指定角色 ID
 * <Route
 *   path="/settings"
 *   element={
 *     <ProtectedRoute allowedRoleIds={[1, 2]}>
 *       <SettingsPage />
 *     </ProtectedRoute>
 *   }
 * />
 * ```
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoleIds,
  requireAdmin,
  requireSuperAdmin,
}) => {
  const location = useLocation();
  const { isAuthenticated, user, loading, isHydrated } = useAuthStore();

  // 等待 Zustand 水合完成或正在加载 - HUD 风格
  if (!isHydrated || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
      </div>
    );
  }

  // 未登录，重定向到登录页
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  // 检查超级管理员权限
  if (requireSuperAdmin && !isSuperAdmin(user)) {
    return <Navigate to="/" replace />;
  }

  // 检查管理员权限
  if (requireAdmin && !isAdmin(user)) {
    return <Navigate to="/" replace />;
  }

  // 检查角色 ID 权限
  if (allowedRoleIds && allowedRoleIds.length > 0 && user) {
    if (!allowedRoleIds.includes(user.role_id)) {
      return <Navigate to="/" replace />;
    }
  }

  // 已登录且有权限，渲染子组件
  return <>{children}</>;
};

export default ProtectedRoute;
