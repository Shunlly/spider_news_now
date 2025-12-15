/**
 * 新闻服务
 * News Service
 */

import apiClient from './api'

export interface NewsArticle {
  id: number
  url_hash: string
  url: string
  title: string
  content_hash?: string
  content_text?: string
  source_key: string
  category?: string
  published_at: string
  scraped_at: string
  created_at: string
  updated_at: string
}

export interface NewsListResponse {
  data: NewsArticle[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface NewsStatistics {
  total_articles: number
  articles_today: number
  sources_active: number
  sources_failed: number
  last_scrape_time?: string
  by_source: Array<{
    source_key: string
    source_name: string
    article_count: number
    last_scraped?: string
  }>
  by_category: Array<{
    category: string
    article_count: number
  }>
}

export const newsService = {
  // 获取文章列表
  async getArticles(params?: {
    source?: string
    category?: string
    start_date?: string
    end_date?: string
    page?: number
    page_size?: number
  }): Promise<NewsListResponse> {
    return apiClient.get('/news/articles', { params })
  },

  // 获取文章详情
  async getArticle(id: number): Promise<NewsArticle> {
    return apiClient.get(`/news/articles/${id}`)
  },

  // 获取分组文章
  async getGroupedArticles(params?: {
    category?: string
    start_date?: string
    limit_per_source?: number
  }) {
    return apiClient.get('/news/articles/grouped', { params })
  },

  // 获取统计数据
  async getStatistics(): Promise<NewsStatistics> {
    return apiClient.get('/news/statistics')
  },

  // 获取新闻来源
  async getSources(enabledOnly = false): Promise<{ sources: Array<{ key: string; name: string }> }> {
    return apiClient.get('/news/sources', { params: { enabled_only: enabledOnly } })
  },
}

export default newsService
