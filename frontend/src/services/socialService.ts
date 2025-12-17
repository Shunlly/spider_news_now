/**
 * 社交数据服务
 * Social Data Service
 */

import apiClient from './api'

export type Platform = 'twitter' | 'telegram'
export type SessionStatus = 'active' | 'paused' | 'completed' | 'error'

export interface SocialSession {
  id: number
  session_key: string
  platform: Platform
  target_id: string
  target_name: string
  target_username?: string
  description?: string
  status: SessionStatus
  message_count: number
  last_message_at?: string
  fetch_interval: number
  last_fetch_at?: string
  created_at: string
  updated_at: string
}

export interface SocialMessage {
  id: number
  session_id: number
  message_id: string
  author_id: string
  author_name: string
  author_username?: string
  content?: string
  content_html?: string
  media_urls?: string[]
  reply_count: number
  repost_count: number
  like_count: number
  view_count: number
  posted_at: string
  fetched_at: string
}

export interface SessionListResponse {
  data: SocialSession[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface MessageListResponse {
  data: SocialMessage[]
  total: number
  page: number
  page_size: number
  total_pages: number
  session?: SocialSession
}

export interface SocialStatistics {
  total_sessions: number
  total_messages: number
  active_sessions: number
  by_platform: Array<{
    platform: Platform
    session_count: number
    message_count: number
    active_sessions: number
  }>
}

export interface SubscriptionResponse {
  success: boolean
  message?: string
  subscription?: SocialSession
}

export interface FetchAllResponse {
  success: boolean
  message?: string
  results?: Array<{
    session_id: number
    new_count: number
    status: string
  }>
}

export const socialService = {
  // 获取会话列表
  async getSessions(params?: {
    platform?: Platform
    status?: SessionStatus
    page?: number
    page_size?: number
  }): Promise<SessionListResponse> {
    return apiClient.get('/social/sessions', { params })
  },

  // 获取会话详情
  async getSession(
    id: number,
    includeMessages = true,
    messageLimit = 10
  ): Promise<SocialSession & { recent_messages: SocialMessage[] }> {
    return apiClient.get(`/social/sessions/${id}`, {
      params: { include_messages: includeMessages, message_limit: messageLimit },
    })
  },

  // 创建会话
  async createSession(data: {
    platform: Platform
    target_id: string
    target_name: string
    target_username?: string
    description?: string
    fetch_interval?: number
  }) {
    return apiClient.post('/social/sessions', data)
  },

  // 更新会话
  async updateSession(
    id: number,
    data: {
      target_name?: string
      description?: string
      fetch_interval?: number
      status?: SessionStatus
    }
  ) {
    return apiClient.put(`/social/sessions/${id}`, data)
  },

  // 删除会话
  async deleteSession(id: number) {
    return apiClient.delete(`/social/sessions/${id}`)
  },

  // 暂停会话
  async pauseSession(id: number) {
    return apiClient.post(`/social/sessions/${id}/pause`)
  },

  // 恢复会话
  async resumeSession(id: number) {
    return apiClient.post(`/social/sessions/${id}/resume`)
  },

  // 获取会话消息
  async getMessages(
    sessionId: number,
    params?: { page?: number; page_size?: number }
  ): Promise<MessageListResponse> {
    return apiClient.get(`/social/sessions/${sessionId}/messages`, { params })
  },

  // 获取统计数据
  async getStatistics(): Promise<SocialStatistics> {
    return apiClient.get('/social/statistics')
  },

  // 订阅 Twitter 用户
  async subscribeTwitterUser(data: {
    user_id: string
    screen_name: string
    name: string
    description?: string
    fetch_interval?: number
  }): Promise<SubscriptionResponse> {
    return apiClient.post('/social/subscribe/twitter', null, { params: data })
  },

  // 订阅 Telegram 频道
  async subscribeTelegramChannel(data: {
    channel_id: number
    title: string
    username?: string
    target_type?: string
    description?: string
    fetch_interval?: number
  }): Promise<SubscriptionResponse> {
    return apiClient.post('/social/subscribe/telegram', null, { params: data })
  },

  // 手动采集单个订阅
  async fetchSession(sessionId: number): Promise<{ success: boolean; message?: string; new_count?: number }> {
    return apiClient.post(`/social/sessions/${sessionId}/fetch`)
  },

  // 手动采集所有活跃订阅
  async fetchAllActive(): Promise<FetchAllResponse> {
    return apiClient.post('/social/fetch-all')
  },

  // 搜索所有消息
  async searchMessages(params?: {
    platform?: Platform
    keyword?: string
    subscription_id?: number
    page?: number
    page_size?: number
  }): Promise<MessageListResponse> {
    return apiClient.get('/social/messages', { params })
  },
}

export default socialService
