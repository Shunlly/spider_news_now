/**
 * 凭证管理服务
 * Credentials Management Service
 */

import apiClient from './api'

export type Platform = 'twitter' | 'telegram'
export type CredentialStatus = 'active' | 'inactive' | 'revoked' | 'rate_limited'

export interface Credential {
  id: number
  name: string
  platform: Platform
  status: CredentialStatus
  is_default: boolean
  request_count: number
  error_count: number
  last_used_at?: string
  last_error_at?: string
  last_error_message?: string
  rate_limit_reset_at?: string
  created_at: string
  updated_at: string
}

export interface CredentialListResponse {
  data: Credential[]
  total: number
}

export interface CredentialActionResponse {
  success: boolean
  message: string
  credential_id?: number
  credential?: Credential
}

export const credentialsService = {
  // 获取凭证列表
  async getCredentials(params?: {
    platform?: Platform
    status?: CredentialStatus
  }): Promise<CredentialListResponse> {
    return apiClient.get('/credentials', { params })
  },

  // 获取凭证详情
  async getCredential(id: number): Promise<Credential> {
    return apiClient.get(`/credentials/${id}`)
  },

  // 创建凭证
  async createCredential(data: {
    name: string
    platform: Platform
    credentials: Record<string, string>
    is_default?: boolean
  }): Promise<CredentialActionResponse> {
    return apiClient.post('/credentials', data)
  },

  // 更新凭证
  async updateCredential(
    id: number,
    data: {
      name?: string
      credentials?: Record<string, string>
      status?: CredentialStatus
      is_default?: boolean
    }
  ): Promise<CredentialActionResponse> {
    return apiClient.put(`/credentials/${id}`, data)
  },

  // 删除凭证
  async deleteCredential(id: number): Promise<CredentialActionResponse> {
    return apiClient.delete(`/credentials/${id}`)
  },

  // 测试凭证
  async testCredential(id: number): Promise<CredentialActionResponse> {
    return apiClient.post(`/credentials/${id}/test`)
  },

  // 设置默认凭证
  async setDefaultCredential(id: number): Promise<CredentialActionResponse> {
    return apiClient.post(`/credentials/${id}/set-default`)
  },
}

export default credentialsService
