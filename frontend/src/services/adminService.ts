/**
 * 管理员 API 服务
 * Admin API Service
 * T118: Create admin API service
 *
 * 提供租户管理、用户管理、审计日志等管理功能 API。
 */

import apiClient from './api';

// =============================================================
// 类型定义
// =============================================================

/**
 * 租户信息
 */
export interface Tenant {
  id: number;
  name: string;
  display_name: string | null;
  quota_config: {
    daily_limit: number;
    concurrent_limit: number;
  };
  settings: Record<string, unknown>;
  is_active: boolean;
  user_count: number;
  created_at: string;
  updated_at: string;
}

/**
 * 创建租户请求
 */
export interface CreateTenantRequest {
  name: string;
  display_name?: string;
  quota_config?: {
    daily_limit: number;
    concurrent_limit: number;
  };
  settings?: Record<string, unknown>;
}

/**
 * 更新租户请求
 */
export interface UpdateTenantRequest {
  name?: string;
  display_name?: string;
  quota_config?: {
    daily_limit: number;
    concurrent_limit: number;
  };
  settings?: Record<string, unknown>;
  is_active?: boolean;
}

/**
 * 租户列表响应
 */
export interface TenantListResponse {
  tenants: Tenant[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * 系统统计
 */
export interface SystemStats {
  total_tenants: number;
  active_tenants: number;
  total_users: number;
  active_users: number;
  timestamp: string;
}

/**
 * 审计日志
 */
export interface AuditLog {
  id: number;
  user_id: string | null;
  username: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

/**
 * 审计日志列表响应
 */
export interface AuditLogListResponse {
  logs: AuditLog[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * 任务队列指标
 */
export interface TaskQueueMetrics {
  pending: number;
  running: number;
  completed: number;
  failed: number;
  total: number;
}

/**
 * 处理速率指标
 */
export interface ProcessingRateMetrics {
  articles_per_minute: number;
  articles_per_hour: number;
  tasks_per_minute: number;
  tasks_per_hour: number;
  avg_task_duration_seconds: number;
}

/**
 * 资源指标
 */
export interface ResourceMetrics {
  active_scrapers: number;
  total_scrapers: number;
  active_connections: number;
  db_connections: number;
  memory_usage_mb: number;
}

/**
 * 系统指标
 */
export interface SystemMetrics {
  timestamp: string;
  uptime_seconds: number;
  task_queue: TaskQueueMetrics;
  processing_rate: ProcessingRateMetrics;
  resources: ResourceMetrics;
}

/**
 * 服务健康详情
 */
export interface ServiceHealth {
  status: 'healthy' | 'unhealthy' | 'degraded';
  latency_ms?: number;
  message?: string;
}

/**
 * 健康状态
 */
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  issues: string[];
  counters: Record<string, number>;
  services: Record<string, ServiceHealth>;
}

// =============================================================
// API 函数
// =============================================================

/**
 * 获取租户列表
 */
export async function getTenants(params?: {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
}): Promise<TenantListResponse> {
  return apiClient.get('/admin/tenants', { params });
}

/**
 * 获取租户详情
 */
export async function getTenant(tenantId: number): Promise<Tenant> {
  return apiClient.get(`/admin/tenants/${tenantId}`);
}

/**
 * 创建租户
 */
export async function createTenant(data: CreateTenantRequest): Promise<Tenant> {
  return apiClient.post('/admin/tenants', data);
}

/**
 * 更新租户
 */
export async function updateTenant(
  tenantId: number,
  data: UpdateTenantRequest
): Promise<Tenant> {
  return apiClient.put(`/admin/tenants/${tenantId}`, data);
}

/**
 * 删除租户
 */
export async function deleteTenant(
  tenantId: number,
  force?: boolean
): Promise<{ message: string }> {
  return apiClient.delete(`/admin/tenants/${tenantId}`, {
    params: { force },
  });
}

/**
 * 获取系统统计
 */
export async function getSystemStats(): Promise<SystemStats> {
  return apiClient.get('/admin/stats');
}

/**
 * 获取审计日志
 */
export async function getAuditLogs(params?: {
  page?: number;
  page_size?: number;
  user_id?: string;
  action?: string;
  resource_type?: string;
}): Promise<AuditLogListResponse> {
  return apiClient.get('/admin/audit-logs', { params });
}

/**
 * 获取系统指标
 */
export async function getSystemMetrics(): Promise<SystemMetrics> {
  return apiClient.get('/admin/metrics');
}

/**
 * 获取系统健康状态
 */
export async function getSystemHealth(): Promise<HealthStatus> {
  return apiClient.get('/admin/health');
}

// 别名
export const getHealthStatus = getSystemHealth;

// 默认导出所有函数
export default {
  getTenants,
  getTenant,
  createTenant,
  updateTenant,
  deleteTenant,
  getSystemStats,
  getAuditLogs,
  getSystemMetrics,
  getSystemHealth,
  getHealthStatus,
};
