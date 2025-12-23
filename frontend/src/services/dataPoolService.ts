/**
 * 数据池服务
 * Data Pool Service
 */

import apiClient from './api'

// ============ Types ============

export type DataVisibility = 'private' | 'tenant_shared' | 'public'
export type PlatformType = 'news' | 'twitter' | 'telegram' | 'weibo'

export interface DataPointer {
  id: string
  domain: string
  domain_table: string
  domain_id: string
  visibility: DataVisibility
  created_by: string | null
  tenant_id: number | null
  title: string | null
  url: string | null
  platform: string | null
  has_content: boolean
  has_analysis: boolean
  extra_metadata: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface ArticleContent {
  id: string
  pointer_id: string
  title: string | null
  content_text: string | null
  summary: string | null
  word_count: number
  extraction_method: string | null
  version: number
  is_primary: boolean
  created_at: string
}

export interface ArticleAnalysis {
  id: string
  pointer_id: string
  analysis_type: string
  result: Record<string, unknown> | null
  model_name: string | null
  confidence: number | null
  created_at: string
}

export interface DataPointerDetail extends DataPointer {
  content: ArticleContent | null
  analyses: ArticleAnalysis[]
}

export interface DataPointerListResponse {
  data: DataPointer[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface UserDataRelation {
  id: string
  user_id: string
  pointer_id: string
  is_favorited: boolean
  is_bookmarked: boolean
  is_read: boolean
  user_tags: string[] | null
  user_notes: string | null
  rating: number | null
  read_at: string | null
  created_at: string
  updated_at: string
}

export interface DomainStats {
  domain: string
  count: number
  has_content_count: number
  has_analysis_count: number
}

export interface DataPoolStatistics {
  total_pointers: number
  by_domain: DomainStats[]
  by_visibility: Record<string, number>
  user_favorites_count: number
  user_bookmarks_count: number
}

// ============ Service ============

export const dataPoolService = {
  // 获取数据指针列表
  async getDataPointers(params?: {
    domain?: string
    page?: number
    page_size?: number
  }): Promise<DataPointerListResponse> {
    return apiClient.get('/data-pool', { params })
  },

  // 获取统计数据
  async getStatistics(): Promise<DataPoolStatistics> {
    return apiClient.get('/data-pool/statistics')
  },

  // 获取收藏列表
  async getFavorites(params?: {
    page?: number
    page_size?: number
  }): Promise<DataPointerListResponse> {
    return apiClient.get('/data-pool/favorites', { params })
  },

  // 获取书签列表
  async getBookmarks(params?: {
    page?: number
    page_size?: number
  }): Promise<DataPointerListResponse> {
    return apiClient.get('/data-pool/bookmarks', { params })
  },

  // 获取单个数据指针详情
  async getDataPointer(pointerId: string): Promise<DataPointerDetail> {
    return apiClient.get(`/data-pool/${pointerId}`)
  },

  // 获取用户与数据的关系
  async getRelation(pointerId: string): Promise<UserDataRelation | null> {
    return apiClient.get(`/data-pool/${pointerId}/relation`)
  },

  // 切换收藏状态
  async toggleFavorite(pointerId: string): Promise<{ pointer_id: string; is_favorited: boolean }> {
    return apiClient.post(`/data-pool/${pointerId}/favorite`)
  },

  // 切换书签状态
  async toggleBookmark(pointerId: string): Promise<{ pointer_id: string; is_bookmarked: boolean }> {
    return apiClient.post(`/data-pool/${pointerId}/bookmark`)
  },

  // 标记为已读
  async markAsRead(pointerId: string): Promise<{ pointer_id: string; is_read: boolean }> {
    return apiClient.post(`/data-pool/${pointerId}/read`)
  },

  // 添加标签
  async addTag(pointerId: string, tag: string): Promise<{ pointer_id: string; tags: string[] }> {
    return apiClient.post(`/data-pool/${pointerId}/tags`, { tag })
  },

  // 移除标签
  async removeTag(pointerId: string, tag: string): Promise<{ pointer_id: string; tags: string[] }> {
    return apiClient.delete(`/data-pool/${pointerId}/tags/${encodeURIComponent(tag)}`)
  },

  // 更新笔记
  async updateNotes(pointerId: string, notes: string): Promise<{ pointer_id: string; notes: string | null }> {
    return apiClient.put(`/data-pool/${pointerId}/notes`, { notes })
  },

  // 更新可见性 (Admin)
  async updateVisibility(pointerId: string, visibility: DataVisibility): Promise<DataPointer> {
    return apiClient.patch(`/data-pool/${pointerId}/visibility`, { visibility })
  },

  // 批量更新可见性 (Admin)
  async batchUpdateVisibility(
    pointerIds: string[],
    visibility: DataVisibility
  ): Promise<{ updated_count: number; pointer_ids: string[] }> {
    return apiClient.post('/data-pool/batch-visibility', { pointer_ids: pointerIds, visibility })
  },
}

export default dataPoolService
