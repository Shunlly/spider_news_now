/**
 * 路由保护组件
 * Protected Route Component
 *
 * 功能：
 * - 检查用户是否已登录
 * - 未登录时重定向到登录页
 * - 可选的角色检查
 */

import { Navigate, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { UserRole } from '../types/auth';

interface ProtectedRouteProps {
  /**
   * 子组件
   */
  children: React.ReactNode;
  /**
   * 允许的角色（可选），不指定则任何已登录用户都可访问
   */
  allowedRoles?: UserRole[];
}

/**
 * 路由保护组件
 *
 * 用法：
 * ```tsx
 * <Route
 *   path="/admin"
 *   element={
 *     <ProtectedRoute allowedRoles={[UserRole.ADMIN]}>
 *       <AdminPage />
 *     </ProtectedRoute>
 *   }
 * />
 * ```
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles,
}) => {
  const location = useLocation();
  const { isAuthenticated, user, loading, isHydrated } = useAuthStore();

  // 等待 Zustand 水合完成或正在加载
  if (!isHydrated || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-stone-200">
        <Loader2 className="w-8 h-8 animate-spin text-stone-600" />
      </div>
    );
  }

  // 未登录，重定向到登录页
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  // 检查角色权限
  if (allowedRoles && allowedRoles.length > 0 && user) {
    if (!allowedRoles.includes(user.role)) {
      // 无权限，显示 403 或重定向到首页
      return <Navigate to="/" replace />;
    }
  }

  // 已登录且有权限，渲染子组件
  return <>{children}</>;
};

export default ProtectedRoute;
