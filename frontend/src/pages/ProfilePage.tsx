/**
 * HUD 风格个人信息页面
 * HUD-style Profile Page
 *
 * 深色主题 + 发光效果
 */

import { useState, useCallback, FormEvent } from 'react';
import { User, Mail, Lock, Eye, EyeOff, Save, ArrowLeft, Shield, Activity } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { HUDPanel, StoneButton, toast } from '@/components/ui';
import api from '@/services/api';
import { useAuthStore } from '@/stores/authStore';

// 角色名称映射
const getRoleName = (roleId: number): string => {
  switch (roleId) {
    case 1: return '超级管理员';
    case 2: return '租户管理员';
    case 3: return '普通用户';
    default: return '未知角色';
  }
};

// 角色颜色映射
const getRoleColor = (roleId: number): string => {
  switch (roleId) {
    case 1: return 'bg-red-500/20 text-red-400 border border-red-500/30';
    case 2: return 'bg-purple-500/20 text-purple-400 border border-purple-500/30';
    case 3: return 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30';
    default: return 'bg-slate-500/20 text-slate-400 border border-slate-500/30';
  }
};

interface FormErrors {
  email?: string;
  currentPassword?: string;
  newPassword?: string;
  confirmPassword?: string;
}

/**
 * 个人信息页面组件
 */
const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { user, setUser } = useAuthStore();

  // 表单状态
  const [email, setEmail] = useState(user?.email || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);

  // 是否有修改
  const hasEmailChange = email !== user?.email;
  const hasPasswordChange = newPassword.length > 0;

  /**
   * 验证表单
   */
  const validateForm = useCallback((): boolean => {
    const errors: FormErrors = {};

    // 验证邮箱
    if (hasEmailChange) {
      if (!email.trim()) {
        errors.email = '请输入邮箱';
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        errors.email = '请输入有效的邮箱地址';
      }
    }

    // 验证密码修改
    if (hasPasswordChange) {
      if (!currentPassword) {
        errors.currentPassword = '请输入当前密码';
      }

      if (newPassword.length < 8) {
        errors.newPassword = '新密码至少8位';
      }

      if (newPassword !== confirmPassword) {
        errors.confirmPassword = '两次密码输入不一致';
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }, [hasEmailChange, hasPasswordChange, email, currentPassword, newPassword, confirmPassword]);

  /**
   * 处理表单提交
   */
  const handleSubmit = useCallback(async (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    // 检查是否有修改
    if (!hasEmailChange && !hasPasswordChange) {
      toast.info('没有需要保存的修改');
      return;
    }

    setLoading(true);
    try {
      const updateData: {
        email?: string;
        current_password?: string;
        new_password?: string;
      } = {};

      if (hasEmailChange) {
        updateData.email = email.trim();
      }

      if (hasPasswordChange) {
        updateData.current_password = currentPassword;
        updateData.new_password = newPassword;
      }

      const response = await api.put('/auth/me', updateData);

      // 更新本地用户信息
      setUser(response.data);

      // 清空密码字段
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');

      toast.success('个人信息更新成功');
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '更新失败';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [email, currentPassword, newPassword, hasEmailChange, hasPasswordChange, setUser, validateForm]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-2xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-8">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-slate-500 hover:text-cyan-400 transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            返回
          </button>
          <h1 className="text-2xl font-bold text-cyan-400 tracking-wide">个人信息</h1>
          <p className="text-slate-500 mt-1 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <span>管理您的账户信息和安全设置</span>
          </p>
        </div>

        {/* 用户基本信息卡片 */}
        <HUDPanel title="账户信息" color="cyan" className="mb-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-slate-700/50">
              <span className="text-slate-500 flex items-center gap-2">
                <User className="w-4 h-4" />
                用户名
              </span>
              <span className="text-slate-200 font-mono">{user?.username}</span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-slate-700/50">
              <span className="text-slate-500 flex items-center gap-2">
                <Shield className="w-4 h-4" />
                角色
              </span>
              <span className={`px-2 py-1 rounded text-sm ${getRoleColor(user?.role_id || 3)}`}>
                {getRoleName(user?.role_id || 3)}
              </span>
            </div>
            <div className="flex items-center justify-between py-3">
              <span className="text-slate-500">账户状态</span>
              <span className={`px-2 py-1 rounded text-sm ${
                user?.is_active
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-red-500/20 text-red-400 border border-red-500/30'
              }`}>
                {user?.is_active ? 'ACTIVE' : 'DISABLED'}
              </span>
            </div>
          </div>
        </HUDPanel>

        {/* 编辑表单 */}
        <form onSubmit={handleSubmit}>
          {/* 修改邮箱 */}
          <HUDPanel title="修改邮箱" color="purple" className="mb-6">
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setFormErrors((prev) => ({ ...prev, email: undefined }));
                }}
                placeholder="邮箱地址"
                className={`w-full bg-slate-800/50 border rounded-lg pl-12 pr-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none transition-colors ${
                  formErrors.email
                    ? 'border-red-500/50 focus:border-red-500'
                    : 'border-slate-700/50 focus:border-purple-500/50'
                }`}
              />
            </div>
            {formErrors.email && (
              <p className="text-red-400 text-xs mt-2">{formErrors.email}</p>
            )}
          </HUDPanel>

          {/* 修改密码 */}
          <HUDPanel title="修改密码" subtitle="如需修改密码，请填写以下信息" color="green" className="mb-6">
            <div className="space-y-4">
              {/* 当前密码 */}
              <div>
                <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">当前密码</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={currentPassword}
                    onChange={(e) => {
                      setCurrentPassword(e.target.value);
                      setFormErrors((prev) => ({ ...prev, currentPassword: undefined }));
                    }}
                    placeholder="请输入当前密码"
                    className={`w-full bg-slate-800/50 border rounded-lg pl-12 pr-12 py-3 text-slate-200 placeholder-slate-500 focus:outline-none transition-colors ${
                      formErrors.currentPassword
                        ? 'border-red-500/50 focus:border-red-500'
                        : 'border-slate-700/50 focus:border-emerald-500/50'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {formErrors.currentPassword && (
                  <p className="text-red-400 text-xs mt-1">{formErrors.currentPassword}</p>
                )}
              </div>

              {/* 新密码 */}
              <div>
                <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">新密码</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => {
                      setNewPassword(e.target.value);
                      setFormErrors((prev) => ({ ...prev, newPassword: undefined }));
                    }}
                    placeholder="请输入新密码（至少8位）"
                    className={`w-full bg-slate-800/50 border rounded-lg pl-12 pr-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none transition-colors ${
                      formErrors.newPassword
                        ? 'border-red-500/50 focus:border-red-500'
                        : 'border-slate-700/50 focus:border-emerald-500/50'
                    }`}
                  />
                </div>
                {formErrors.newPassword && (
                  <p className="text-red-400 text-xs mt-1">{formErrors.newPassword}</p>
                )}
              </div>

              {/* 确认新密码 */}
              <div>
                <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">确认新密码</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      setFormErrors((prev) => ({ ...prev, confirmPassword: undefined }));
                    }}
                    placeholder="请再次输入新密码"
                    className={`w-full bg-slate-800/50 border rounded-lg pl-12 pr-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none transition-colors ${
                      formErrors.confirmPassword
                        ? 'border-red-500/50 focus:border-red-500'
                        : 'border-slate-700/50 focus:border-emerald-500/50'
                    }`}
                  />
                </div>
                {formErrors.confirmPassword && (
                  <p className="text-red-400 text-xs mt-1">{formErrors.confirmPassword}</p>
                )}
              </div>
            </div>
          </HUDPanel>

          {/* 保存按钮 */}
          <div className="flex justify-end">
            <StoneButton
              type="submit"
              className="px-8 h-12"
              loading={loading}
              disabled={!hasEmailChange && !hasPasswordChange}
            >
              <Save className="w-4 h-4 mr-2" />
              保存修改
            </StoneButton>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfilePage;
