/**
 * 代理配置服务
 * Proxy Configuration Service
 */

import apiClient from './api'

export type ProxyProtocol = 'http' | 'https' | 'socks5'
export type ProxyStatus = 'active' | 'failed' | 'unknown'

export interface ProxyConfig {
  id: number
  name: string
  protocol: ProxyProtocol
  host: string
  port: number
  username?: string
  status: ProxyStatus
  enabled: boolean
  weight: number
  priority: number
  request_count: number
  success_count: number
  failure_count: number
  avg_response_time?: number
  last_response_time?: number
  last_check_at?: string
  last_success_at?: string
  last_failure_at?: string
  last_error_message?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface ProxyListResponse {
  data: ProxyConfig[]
  total: number
}

export interface ProxyActionResponse {
  success: boolean
  message: string
  proxy_id?: number
  proxy?: ProxyConfig
}

export const proxiesService = {
  // 获取代理列表
  async getProxies(params?: {
    protocol?: ProxyProtocol
    status?: ProxyStatus
    enabled?: boolean
  }): Promise<ProxyListResponse> {
    return apiClient.get('/proxies', { params })
  },

  // 获取代理详情
  async getProxy(id: number): Promise<ProxyConfig> {
    return apiClient.get(`/proxies/${id}`)
  },

  // 创建代理
  async createProxy(data: {
    name: string
    protocol: ProxyProtocol
    host: string
    port: number
    username?: string
    password?: string
    weight?: number
    priority?: number
    notes?: string
  }): Promise<ProxyActionResponse> {
    return apiClient.post('/proxies', data)
  },

  // 更新代理
  async updateProxy(
    id: number,
    data: {
      name?: string
      protocol?: ProxyProtocol
      host?: string
      port?: number
      username?: string
      password?: string
      status?: ProxyStatus
      enabled?: boolean
      weight?: number
      priority?: number
      notes?: string
    }
  ): Promise<ProxyActionResponse> {
    return apiClient.put(`/proxies/${id}`, data)
  },

  // 删除代理
  async deleteProxy(id: number): Promise<ProxyActionResponse> {
    return apiClient.delete(`/proxies/${id}`)
  },

  // 测试代理
  async testProxy(id: number): Promise<ProxyActionResponse> {
    return apiClient.post(`/proxies/${id}/test`)
  },

  // 启用代理
  async enableProxy(id: number): Promise<ProxyActionResponse> {
    return apiClient.post(`/proxies/${id}/enable`)
  },

  // 禁用代理
  async disableProxy(id: number): Promise<ProxyActionResponse> {
    return apiClient.post(`/proxies/${id}/disable`)
  },

  // 测试所有代理
  async testAllProxies(): Promise<ProxyListResponse> {
    return apiClient.post('/proxies/test-all')
  },
}

export default proxiesService
