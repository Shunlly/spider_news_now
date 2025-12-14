/**
 * 爬虫服务
 * Scraper Service
 */

import apiClient from './api'

export interface ScraperStatus {
  source_key: string
  source_name: string
  enabled: boolean
  status: 'idle' | 'running' | 'error'
  last_run: {
    started_at: string
    completed_at: string
    status: string
    articles_scraped: number
    articles_new: number
    articles_duplicate: number
    duration_seconds: number
  } | null
  current_run: {
    started_at: string
    articles_scraped: number
  } | null
  next_run_at: string
  failure_count: number
}

export interface ScraperStatusResponse {
  scrapers: ScraperStatus[]
  total_scrapers: number
  active_runs: number
}

export interface ScraperRunResponse {
  message: string
  source_key: string
  task_id?: string
}

export interface NewsSource {
  id: number
  source_key: string
  display_name: string
  enabled: boolean
  status: string
  schedule_interval: number
  last_run_at: string | null
  last_success_at: string | null
  failure_count: number
}

export interface SourcesResponse {
  sources: NewsSource[]
  total: number
}

export const scraperService = {
  // 获取所有爬虫状态
  async getStatus(): Promise<ScraperStatusResponse> {
    return apiClient.get('/scrapers/status')
  },

  // 获取单个爬虫状态
  async getScraperStatus(sourceKey: string): Promise<ScraperStatus> {
    return apiClient.get(`/scrapers/${sourceKey}/status`)
  },

  // 立即运行指定爬虫
  async runScraper(sourceKey: string): Promise<ScraperRunResponse> {
    return apiClient.post(`/scrapers/${sourceKey}/trigger`)
  },

  // 立即运行所有爬虫（逐个触发）
  async runAllScrapers(): Promise<{ message: string; triggered: number }> {
    // 获取所有爬虫状态
    const status = await this.getStatus()
    const enabledScrapers = status.scrapers.filter(s => s.enabled && s.status !== 'running')

    // 逐个触发
    let triggered = 0
    for (const scraper of enabledScrapers) {
      try {
        await apiClient.post(`/scrapers/${scraper.source_key}/trigger`)
        triggered++
      } catch (error) {
        console.error(`Failed to trigger ${scraper.source_key}:`, error)
      }
    }

    return { message: `成功触发 ${triggered} 个爬虫`, triggered }
  },

  // 获取新闻源列表
  async getSources(enabledOnly = false): Promise<SourcesResponse> {
    return apiClient.get('/news/sources', { params: { enabled_only: enabledOnly } })
  },

  // 启用/禁用爬虫
  async toggleScraper(sourceKey: string, enabled: boolean): Promise<{ message: string }> {
    return apiClient.patch(`/scrapers/${sourceKey}`, { enabled })
  },
}

export default scraperService
