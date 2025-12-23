/**
 * 用户管理页面
 * UserManagePage
 * T120: Implement UserManagePage
 *
 * 提供用户的查看和管理功能，支持按租户筛选。
 */

import { useState, useEffect, useCallback } from 'react';
import { HUDPanel, StoneButton, StoneInput, StoneSelect, StoneModal } from '@/components/ui';
import { TenantSelector, UserTable, type User } from '@/components/admin';
import {
  Plus,
  RefreshCw,
  Users,
  Shield,
  UserCheck,
  UserX,
} from 'lucide-react';
import apiClient from '@/services/api';

interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  page_size: number;
}

export default function UserManagePage() {
  // 状态
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [tenantFilter, setTenantFilter] = useState<number | null>(null);
  const pageSize = 20;

  // 模态框状态
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  // 表单状态
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role_id: 3,
    tenant_id: null as number | null,
  });
  const [newPassword, setNewPassword] = useState('');
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // 加载用户列表
  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {
        page,
        page_size: pageSize,
      };
      if (search) params.search = search;

      const response = await apiClient.get<UserListResponse>('/users', { params });
      const data = response as unknown as UserListResponse;
      setUsers(data.users);
      setTotal(data.total);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // 打开创建模态框
  const handleOpenCreate = () => {
    setFormData({
      username: '',
      email: '',
      password: '',
      role_id: 3,
      tenant_id: tenantFilter,
    });
    setFormError('');
    setShowCreateModal(true);
  };

  // 编辑用户
  const handleEdit = (user: User) => {
    setSelectedUser(user);
    setFormData({
      username: user.username,
      email: user.email,
      password: '',
      role_id: user.role_id,
      tenant_id: user.tenant_id,
    });
    setFormError('');
    setShowEditModal(true);
  };

  // 删除用户
  const handleDelete = (user: User) => {
    setSelectedUser(user);
    setShowDeleteModal(true);
  };

  // 切换激活状态
  const handleToggleActive = async (user: User) => {
    try {
      await apiClient.post(`/users/${user.id}/toggle-active`);
      fetchUsers();
    } catch (error) {
      alert(error instanceof Error ? error.message : '操作失败');
    }
  };

  // 重置密码
  const handleResetPassword = (user: User) => {
    setSelectedUser(user);
    setNewPassword('');
    setShowResetPasswordModal(true);
  };

  // 创建用户
  const handleCreate = async () => {
    if (!formData.username.trim() || !formData.email.trim() || !formData.password) {
      setFormError('请填写必填字段');
      return;
    }

    setSubmitting(true);
    setFormError('');
    try {
      await apiClient.post('/users', formData);
      setShowCreateModal(false);
      fetchUsers();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '创建失败');
    } finally {
      setSubmitting(false);
    }
  };

  // 更新用户
  const handleUpdate = async () => {
    if (!selectedUser) return;

    setSubmitting(true);
    setFormError('');
    try {
      await apiClient.put(`/users/${selectedUser.id}`, {
        email: formData.email,
        role_id: formData.role_id,
        tenant_id: formData.tenant_id,
      });
      setShowEditModal(false);
      fetchUsers();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '更新失败');
    } finally {
      setSubmitting(false);
    }
  };

  // 确认删除
  const handleConfirmDelete = async () => {
    if (!selectedUser) return;

    setSubmitting(true);
    try {
      await apiClient.delete(`/users/${selectedUser.id}`);
      setShowDeleteModal(false);
      fetchUsers();
    } catch (error) {
      alert(error instanceof Error ? error.message : '删除失败');
    } finally {
      setSubmitting(false);
    }
  };

  // 确认重置密码
  const handleConfirmResetPassword = async () => {
    if (!selectedUser || !newPassword) return;

    setSubmitting(true);
    try {
      await apiClient.post(`/users/${selectedUser.id}/reset-password`, {
        new_password: newPassword,
      });
      setShowResetPasswordModal(false);
      alert('密码重置成功');
    } catch (error) {
      alert(error instanceof Error ? error.message : '重置失败');
    } finally {
      setSubmitting(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  // 统计
  const activeUsers = users.filter((u) => u.is_active).length;
  const adminUsers = users.filter((u) => u.role_id <= 2).length;

  return (
    <div className="min-h-screen bg-slate-900 p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">用户管理</h1>
          <p className="text-sm text-slate-400 mt-1">管理系统用户和权限</p>
        </div>
        <div className="flex items-center gap-3">
          <TenantSelector
            value={tenantFilter}
            onChange={(id) => {
              setTenantFilter(id);
              setPage(1);
            }}
          />
          <StoneButton onClick={fetchUsers} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </StoneButton>
          <StoneButton onClick={handleOpenCreate} variant="primary">
            <Plus className="w-4 h-4 mr-2" />
            新建用户
          </StoneButton>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          icon={<Users className="w-5 h-5" />}
          label="用户总数"
          value={total}
          color="cyan"
        />
        <StatCard
          icon={<UserCheck className="w-5 h-5" />}
          label="当前页活跃"
          value={activeUsers}
          color="green"
        />
        <StatCard
          icon={<Shield className="w-5 h-5" />}
          label="当前页管理员"
          value={adminUsers}
          color="purple"
        />
        <StatCard
          icon={<UserX className="w-5 h-5" />}
          label="当前页已禁用"
          value={users.length - activeUsers}
          color="red"
        />
      </div>

      {/* 用户列表 */}
      <HUDPanel title="用户列表" className="p-0">
        <div className="p-4 border-b border-slate-700/50">
          <StoneInput
            placeholder="搜索用户名或邮箱..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="max-w-sm"
          />
        </div>

        <UserTable
          users={users}
          loading={loading}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onToggleActive={handleToggleActive}
          onResetPassword={handleResetPassword}
        />

        {/* 分页 */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-slate-700/50 flex items-center justify-between">
            <span className="text-sm text-slate-400">
              共 {total} 条，第 {page}/{totalPages} 页
            </span>
            <div className="flex items-center gap-2">
              <StoneButton
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                上一页
              </StoneButton>
              <StoneButton
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
              >
                下一页
              </StoneButton>
            </div>
          </div>
        )}
      </HUDPanel>

      {/* 创建用户模态框 */}
      <StoneModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="新建用户"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">用户名 *</label>
            <StoneInput
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              placeholder="用户名"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">邮箱 *</label>
            <StoneInput
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="邮箱地址"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">密码 *</label>
            <StoneInput
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="至少 8 位"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">角色</label>
            <StoneSelect
              value={formData.role_id}
              onChange={(e) => setFormData({ ...formData, role_id: parseInt(e.target.value) })}
            >
              <option value={3}>普通用户</option>
              <option value={2}>租户管理员</option>
              <option value={1}>超级管理员</option>
            </StoneSelect>
          </div>
          {formError && <p className="text-sm text-red-400">{formError}</p>}
          <div className="flex justify-end gap-3 pt-4">
            <StoneButton onClick={() => setShowCreateModal(false)}>取消</StoneButton>
            <StoneButton variant="primary" onClick={handleCreate} disabled={submitting}>
              {submitting ? '创建中...' : '创建'}
            </StoneButton>
          </div>
        </div>
      </StoneModal>

      {/* 编辑用户模态框 */}
      <StoneModal
        open={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="编辑用户"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">用户名</label>
            <StoneInput value={formData.username} disabled className="opacity-50" />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">邮箱</label>
            <StoneInput
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">角色</label>
            <StoneSelect
              value={formData.role_id}
              onChange={(e) => setFormData({ ...formData, role_id: parseInt(e.target.value) })}
            >
              <option value={3}>普通用户</option>
              <option value={2}>租户管理员</option>
              <option value={1}>超级管理员</option>
            </StoneSelect>
          </div>
          {formError && <p className="text-sm text-red-400">{formError}</p>}
          <div className="flex justify-end gap-3 pt-4">
            <StoneButton onClick={() => setShowEditModal(false)}>取消</StoneButton>
            <StoneButton variant="primary" onClick={handleUpdate} disabled={submitting}>
              {submitting ? '保存中...' : '保存'}
            </StoneButton>
          </div>
        </div>
      </StoneModal>

      {/* 删除确认模态框 */}
      <StoneModal
        open={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="删除用户"
      >
        <div className="space-y-4">
          <p className="text-slate-300">
            确定要删除用户 <strong className="text-red-400">{selectedUser?.username}</strong> 吗？
          </p>
          <p className="text-sm text-slate-400">此操作不可恢复，用户的所有数据将被删除。</p>
          <div className="flex justify-end gap-3 pt-4">
            <StoneButton onClick={() => setShowDeleteModal(false)}>取消</StoneButton>
            <StoneButton
              variant="danger"
              onClick={handleConfirmDelete}
              disabled={submitting}
            >
              {submitting ? '删除中...' : '确认删除'}
            </StoneButton>
          </div>
        </div>
      </StoneModal>

      {/* 重置密码模态框 */}
      <StoneModal
        open={showResetPasswordModal}
        onClose={() => setShowResetPasswordModal(false)}
        title="重置密码"
      >
        <div className="space-y-4">
          <p className="text-slate-300">
            为用户 <strong className="text-cyan-400">{selectedUser?.username}</strong> 设置新密码：
          </p>
          <div>
            <label className="block text-sm text-slate-400 mb-1">新密码</label>
            <StoneInput
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="至少 8 位"
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <StoneButton onClick={() => setShowResetPasswordModal(false)}>取消</StoneButton>
            <StoneButton
              variant="primary"
              onClick={handleConfirmResetPassword}
              disabled={submitting || newPassword.length < 8}
            >
              {submitting ? '重置中...' : '确认重置'}
            </StoneButton>
          </div>
        </div>
      </StoneModal>
    </div>
  );
}

// 统计卡片子组件
function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: 'cyan' | 'green' | 'purple' | 'red';
}) {
  const colorClasses = {
    cyan: 'text-cyan-400 bg-cyan-500/10',
    green: 'text-green-400 bg-green-500/10',
    purple: 'text-purple-400 bg-purple-500/10',
    red: 'text-red-400 bg-red-500/10',
  };

  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>{icon}</div>
        <div>
          <div className="text-sm text-slate-400">{label}</div>
          <div className="text-2xl font-bold text-slate-200">{value}</div>
        </div>
      </div>
    </div>
  );
}
