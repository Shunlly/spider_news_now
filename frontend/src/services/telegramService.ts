/**
 * Telegram 服务
 * Telegram Service
 *
 * 提供 Telegram 认证、频道管理和消息获取功能
 */

import apiClient from './api'

// 类型定义
export interface TelegramUserInfo {
  id: number
  first_name?: string
  last_name?: string
  username?: string
  phone?: string
}

export interface TelegramDialog {
  id: number
  title: string
  username?: string
  type?: 'channel' | 'group' | 'user'
  participant_count?: number
  unread_count: number
  last_message_date?: string
  is_pinned: boolean
}

export interface TelegramEntity {
  id: number
  title: string
  username?: string
  type?: string
  participant_count?: number
  description?: string
}

export interface TelegramMessage {
  id: number
  date?: string
  text?: string
  html?: string
  views?: number
  forwards?: number
  reply_to_id?: number
  media_type?: string
  urls: string[]
  sender_id?: number
}

export interface TelegramBaseResponse {
  success: boolean
  message: string
}

export interface TelegramInitResponse extends TelegramBaseResponse {}

export interface TelegramSendCodeResponse extends TelegramBaseResponse {
  phone_code_hash?: string
}

export interface TelegramSignInResponse extends TelegramBaseResponse {
  string_session?: string
  user_info?: TelegramUserInfo
  need_password?: boolean
}

export interface TelegramConnectResponse extends TelegramBaseResponse {
  user_info?: TelegramUserInfo
}

export interface TelegramDialogsResponse extends TelegramBaseResponse {
  dialogs: TelegramDialog[]
  total: number
}

export interface TelegramSearchResponse extends TelegramBaseResponse {
  entity?: TelegramEntity
}

export interface TelegramSearchPublicResponse extends TelegramBaseResponse {
  entities: TelegramEntity[]
}

export interface TelegramMessagesResponse extends TelegramBaseResponse {
  messages: TelegramMessage[]
  total: number
}

export interface TelegramStatusResponse {
  connected: boolean
  user_info?: TelegramUserInfo
}

export const telegramService = {
  // 初始化客户端
  async initClient(data: {
    api_id: number
    api_hash: string
    string_session?: string
    proxy?: Record<string, unknown>
  }): Promise<TelegramInitResponse> {
    return apiClient.post('/telegram/init', data)
  },

  // 发送验证码
  async sendCode(phone: string): Promise<TelegramSendCodeResponse> {
    return apiClient.post('/telegram/send-code', { phone })
  },

  // 验证登录
  async signIn(data: {
    phone: string
    code: string
    phone_code_hash: string
    password?: string
  }): Promise<TelegramSignInResponse> {
    return apiClient.post('/telegram/sign-in', data)
  },

  // 使用 StringSession 连接
  async connectWithSession(data: {
    api_id: number
    api_hash: string
    string_session: string
    proxy?: Record<string, unknown>
  }): Promise<TelegramConnectResponse> {
    return apiClient.post('/telegram/connect', data)
  },

  // 获取连接状态
  async getStatus(): Promise<TelegramStatusResponse> {
    return apiClient.get('/telegram/status')
  },

  // 断开连接
  async disconnect(): Promise<TelegramBaseResponse> {
    return apiClient.post('/telegram/disconnect')
  },

  // 获取对话列表
  async getDialogs(params?: {
    limit?: number
    offset?: number
    filter_type?: 'channel' | 'group' | 'user'
  }): Promise<TelegramDialogsResponse> {
    return apiClient.get('/telegram/dialogs', { params })
  },

  // 搜索频道（精确匹配用户名）
  async searchChannel(username: string): Promise<TelegramSearchResponse> {
    return apiClient.post('/telegram/search', { username })
  },

  // 关键词搜索频道（支持中文）
  async searchPublic(query: string, limit: number = 20): Promise<TelegramSearchPublicResponse> {
    return apiClient.post('/telegram/search-public', { query, limit })
  },

  // 加入频道
  async joinChannel(channel: string): Promise<TelegramBaseResponse> {
    return apiClient.post('/telegram/join', { channel })
  },

  // 退出频道
  async leaveChannel(channel_id: number): Promise<TelegramBaseResponse> {
    return apiClient.post('/telegram/leave', { channel_id })
  },

  // 获取频道消息
  async getMessages(
    channel_id: number,
    params?: {
      limit?: number
      offset_id?: number
      min_date?: string
      max_date?: string
    }
  ): Promise<TelegramMessagesResponse> {
    return apiClient.get(`/telegram/messages/${channel_id}`, { params })
  },
}

export default telegramService
