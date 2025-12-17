/**
 * Twitter 服务
 * Twitter Service
 *
 * 提供 Twitter Cookie 认证、用户信息和推文获取功能
 */

import apiClient from './api'

// 类型定义
export interface TwitterUserInfo {
  id: string
  name?: string
  screen_name?: string
  description?: string
  profile_image_url?: string
  followers_count?: number
  friends_count?: number
  statuses_count?: number
  media_count?: number
  created_at?: string
  verified?: boolean
}

export interface TwitterMediaItem {
  type?: string
  url?: string
  expanded_url?: string
  video_url?: string
}

export interface TwitterTweetUser {
  id?: string
  name?: string
  screen_name?: string
  profile_image_url?: string
}

export interface TwitterTweet {
  id: string
  conversation_id?: string
  text?: string
  created_at?: string
  user?: TwitterTweetUser
  favorite_count: number
  retweet_count: number
  reply_count: number
  views_count?: string
  media: TwitterMediaItem[]
  is_retweet: boolean
  urls: string[]
}

export interface TwitterBaseResponse {
  success: boolean
  message: string
}

export interface TwitterConnectResponse extends TwitterBaseResponse {
  user_info?: TwitterUserInfo
}

export interface TwitterStatusResponse {
  connected: boolean
  user_info?: TwitterUserInfo
}

export interface TwitterUserResponse extends TwitterBaseResponse {
  user?: TwitterUserInfo
}

export interface TwitterTweetsResponse extends TwitterBaseResponse {
  tweets: TwitterTweet[]
  next_cursor?: string
  total: number
}

export const twitterService = {
  // 使用 Cookie 连接
  async connect(data: {
    auth_token: string
    ct0: string
    proxy?: string
  }): Promise<TwitterConnectResponse> {
    return apiClient.post('/twitter/connect', data)
  },

  // 获取连接状态
  async getStatus(): Promise<TwitterStatusResponse> {
    return apiClient.get('/twitter/status')
  },

  // 断开连接
  async disconnect(): Promise<TwitterBaseResponse> {
    return apiClient.post('/twitter/disconnect')
  },

  // 获取用户信息
  async getUser(screen_name: string): Promise<TwitterUserResponse> {
    return apiClient.post('/twitter/user', { screen_name })
  },

  // 获取用户推文
  async getTweets(data: {
    user_id: string
    count?: number
    cursor?: string
    include_retweets?: boolean
  }): Promise<TwitterTweetsResponse> {
    return apiClient.post('/twitter/tweets', data)
  },

  // 搜索推文
  async searchTweets(data: {
    query: string
    count?: number
    cursor?: string
  }): Promise<TwitterTweetsResponse> {
    return apiClient.post('/twitter/search', data)
  },
}

export default twitterService
