/**
 * 租户管理页面
 * TenantManagePage
 * T119: Implement TenantManagePage
 *
 * 提供租户的增删改查功能，仅超级管理员可访问。
 */

import { useState, useEffect, useCallback } from 'react';
import { HUDPanel, StoneButton, StoneInput, StoneModal } from '@/components/ui';
import {
  Plus,
  RefreshCw,
  Trash2,
  Edit2,
  Building2,
  Users,
  Check,
  X,
} from 'lucide-react';
import {
  getTenants,
  createTenant,
  updateTenant,
  deleteTenant,
  getSystemStats,
  type Tenant,
  type CreateTenantRequest,
  type SystemStats,
} from '@/services/adminService';

export default function TenantManagePage() {
  // 状态
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const pageSize = 20;

  // 模态框状态
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);

  // 表单状态
  const [formData, setFormData] = useState<CreateTenantRequest>({
    name: '',
    display_name: '',
    quota_config: { daily_limit: 1000, concurrent_limit: 5 },
  });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // 加载租户列表
  const fetchTenants = useCallback(async () => {
    setLoading(true);
    try {
      const response = await getTenants({
        page,
        page_size: pageSize,
        search: search || undefined,
      });
      setTenants(response.tenants);
      setTotal(response.total);
    } catch (error) {
      console.error('Failed to fetch tenants:', error);
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  // 加载统计信息
  const fetchStats = useCallback(async () => {
    try {
      const data = await getSystemStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }, []);

  useEffect(() => {
    fetchTenants();
    fetchStats();
  }, [fetchTenants, fetchStats]);

  // 打开创建模态框
  const handleOpenCreate = () => {
    setFormData({
      name: '',
      display_name: '',
      quota_config: { daily_limit: 1000, concurrent_limit: 5 },
    });
    setFormError('');
    setShowCreateModal(true);
  };

  // 打开编辑模态框
  const handleOpenEdit = async (tenant: Tenant) => {
    setSelectedTenant(tenant);
    setFormData({
      name: tenant.name,
      display_name: tenant.display_name || '',
      quota_config: tenant.quota_config,
    });
    setFormError('');
    setShowEditModal(true);
  };

  // 打开删除确认框
  const handleOpenDelete = (tenant: Tenant) => {
    setSelectedTenant(tenant);
    setShowDeleteModal(true);
  };

  // 创建租户
  const handleCreate = async () => {
    if (!formData.name.trim()) {
      setFormError('请输入租户名称');
      return;
    }

    setSubmitting(true);
    setFormError('');
    try {
      await createTenant(formData);
      setShowCreateModal(false);
      fetchTenants();
      fetchStats();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '创建失败');
    } finally {
      setSubmitting(false);
    }
  };

  // 更新租户
  const handleUpdate = async () => {
    if (!selectedTenant || !formData.name.trim()) {
      setFormError('请输入租户名称');
      return;
    }

    setSubmitting(true);
    setFormError('');
    try {
      await updateTenant(selectedTenant.id, formData);
      setShowEditModal(false);
      fetchTenants();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '更新失败');
    } finally {
      setSubmitting(false);
    }
  };

  // 删除租户
  const handleDelete = async (force: boolean = false) => {
    if (!selectedTenant) return;

    setSubmitting(true);
    try {
      await deleteTenant(selectedTenant.id, force);
      setShowDeleteModal(false);
      fetchTenants();
      fetchStats();
    } catch (error) {
      alert(error instanceof Error ? error.message : '删除失败');
    } finally {
      setSubmitting(false);
    }
  };

  // 切换激活状态
  const handleToggleActive = async (tenant: Tenant) => {
    try {
      await updateTenant(tenant.id, { is_active: !tenant.is_active });
      fetchTenants();
    } catch (error) {
      alert(error instanceof Error ? error.message : '操作失败');
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="min-h-screen bg-slate-900 p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">租户管理</h1>
          <p className="text-sm text-slate-400 mt-1">管理系统中的租户和配额</p>
        </div>
        <div className="flex items-center gap-3">
          <StoneButton onClick={fetchTenants} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </StoneButton>
          <StoneButton onClick={handleOpenCreate} variant="primary">
            <Plus className="w-4 h-4 mr-2" />
            新建租户
          </StoneButton>
        </div>
      </div>

      {/* 统计卡片 */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard
            icon={<Building2 className="w-5 h-5" />}
            label="租户总数"
            value={stats.total_tenants}
            color="cyan"
          />
          <StatCard
            icon={<Check className="w-5 h-5" />}
            label="活跃租户"
            value={stats.active_tenants}
            color="green"
          />
          <StatCard
            icon={<Users className="w-5 h-5" />}
            label="用户总数"
            value={stats.total_users}
            color="purple"
          />
          <StatCard
            icon={<Users className="w-5 h-5" />}
            label="活跃用户"
            value={stats.active_users}
            color="blue"
          />
        </div>
      )}

      {/* 搜索栏 */}
      <HUDPanel title="租户列表" className="p-0">
        <div className="p-4 border-b border-slate-700/50">
          <StoneInput
            placeholder="搜索租户名称..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="max-w-sm"
          />
        </div>

        {/* 租户表格 */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700/50">
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">ID</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">名称</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">显示名</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">用户数</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">配额</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">状态</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">创建时间</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-slate-400">操作</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center">
                    <div className="w-8 h-8 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin mx-auto" />
                  </td>
                </tr>
              ) : tenants.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-slate-400">
                    暂无租户数据
                  </td>
                </tr>
              ) : (
                tenants.map((tenant) => (
                  <tr
                    key={tenant.id}
                    className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"
                  >
                    <td className="px-4 py-3 text-slate-400 font-mono text-sm">{tenant.id}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center">
                          <Building2 className="w-4 h-4 text-cyan-400" />
                        </div>
                        <span className="text-slate-200">{tenant.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {tenant.display_name || '-'}
                    </td>
                    <td className="px-4 py-3 text-slate-300">{tenant.user_count}</td>
                    <td className="px-4 py-3 text-sm text-slate-400">
                      {tenant.quota_config.daily_limit}/日,{' '}
                      {tenant.quota_config.concurrent_limit}并发
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          tenant.is_active
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-red-500/20 text-red-400'
                        }`}
                      >
                        {tenant.is_active ? '正常' : '已禁用'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-400">
                      {new Date(tenant.created_at).toLocaleDateString('zh-CN')}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => handleOpenEdit(tenant)}
                          className="p-1.5 text-slate-400 hover:text-cyan-400 transition-colors"
                          title="编辑"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleToggleActive(tenant)}
                          className={`p-1.5 transition-colors ${
                            tenant.is_active
                              ? 'text-slate-400 hover:text-orange-400'
                              : 'text-slate-400 hover:text-green-400'
                          }`}
                          title={tenant.is_active ? '禁用' : '启用'}
                        >
                          {tenant.is_active ? <X className="w-4 h-4" /> : <Check className="w-4 h-4" />}
                        </button>
                        <button
                          onClick={() => handleOpenDelete(tenant)}
                          className="p-1.5 text-slate-400 hover:text-red-400 transition-colors"
                          title="删除"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

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

      {/* 创建租户模态框 */}
      <StoneModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="新建租户"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">租户名称 *</label>
            <StoneInput
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="唯一标识，如 company-a"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">显示名称</label>
            <StoneInput
              value={formData.display_name}
              onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
              placeholder="用于显示的友好名称"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">每日配额</label>
              <StoneInput
                type="number"
                value={formData.quota_config?.daily_limit || 1000}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    quota_config: {
                      ...formData.quota_config!,
                      daily_limit: parseInt(e.target.value) || 1000,
                    },
                  })
                }
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">并发限制</label>
              <StoneInput
                type="number"
                value={formData.quota_config?.concurrent_limit || 5}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    quota_config: {
                      ...formData.quota_config!,
                      concurrent_limit: parseInt(e.target.value) || 5,
                    },
                  })
                }
              />
            </div>
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

      {/* 编辑租户模态框 */}
      <StoneModal
        open={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="编辑租户"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">租户名称 *</label>
            <StoneInput
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">显示名称</label>
            <StoneInput
              value={formData.display_name}
              onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">每日配额</label>
              <StoneInput
                type="number"
                value={formData.quota_config?.daily_limit || 1000}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    quota_config: {
                      ...formData.quota_config!,
                      daily_limit: parseInt(e.target.value) || 1000,
                    },
                  })
                }
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">并发限制</label>
              <StoneInput
                type="number"
                value={formData.quota_config?.concurrent_limit || 5}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    quota_config: {
                      ...formData.quota_config!,
                      concurrent_limit: parseInt(e.target.value) || 5,
                    },
                  })
                }
              />
            </div>
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
        title="删除租户"
      >
        <div className="space-y-4">
          <p className="text-slate-300">
            确定要删除租户 <strong className="text-red-400">{selectedTenant?.name}</strong> 吗？
          </p>
          {selectedTenant && selectedTenant.user_count > 0 && (
            <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <p className="text-yellow-400 text-sm">
                ⚠️ 该租户下有 {selectedTenant.user_count} 个用户，删除后用户数据也将被删除！
              </p>
            </div>
          )}
          <div className="flex justify-end gap-3 pt-4">
            <StoneButton onClick={() => setShowDeleteModal(false)}>取消</StoneButton>
            <StoneButton
              variant="danger"
              onClick={() => handleDelete(true)}
              disabled={submitting}
            >
              {submitting ? '删除中...' : '确认删除'}
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
  color: 'cyan' | 'green' | 'purple' | 'blue';
}) {
  const colorClasses = {
    cyan: 'text-cyan-400 bg-cyan-500/10',
    green: 'text-green-400 bg-green-500/10',
    purple: 'text-purple-400 bg-purple-500/10',
    blue: 'text-blue-400 bg-blue-500/10',
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
