/**
 * 搜索服务
 * Search Service
 */

import apiClient from './api'

export interface SearchHit {
  id: number
  title: string
  url: string
  source_key: string
  category?: string
  published_at: string
  title_highlighted?: string
  content_highlighted?: string
  _formatted?: {
    title?: string
    content?: string
  }
}

export interface SearchResponse {
  hits: SearchHit[]
  query: string
  total_hits: number
  page: number
  hits_per_page: number
  total_pages: number
  processing_time_ms: number
  facets?: {
    source_key?: Record<string, number>
    category?: Record<string, number>
  }
}

export interface IndexStats {
  index_name: string
  number_of_documents: number
  is_indexing: boolean
  field_distribution: Record<string, number>
}

export const searchService = {
  // 执行搜索
  async search(params: {
    q: string
    page?: number
    hits_per_page?: number
    source_key?: string
    category?: string
    start_date?: string
    end_date?: string
    highlight?: boolean
  }): Promise<SearchResponse> {
    return apiClient.get('/search', { params })
  },

  // 带分面统计的搜索
  async searchWithFacets(params: {
    q: string
    page?: number
    hits_per_page?: number
    source_key?: string
    category?: string
  }): Promise<SearchResponse> {
    return apiClient.get('/search/facets', { params })
  },

  // 获取索引统计
  async getIndexStats(): Promise<IndexStats> {
    return apiClient.get('/search/index/stats')
  },
}

export default searchService
