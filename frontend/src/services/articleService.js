/**
 * Article service for API calls.
 */

import axios from '../api/axios'
import { API_ENDPOINTS } from '../api/endpoints'

export const articleService = {
  /**
   * Get paginated articles with filters
   */
  async getArticles(params = {}) {
    const queryParams = {
      page: params.page || 1,
      page_size: params.pageSize || 50,
      source: params.source,
      category: params.category,
      start_date: params.startDate,
      end_date: params.endDate,
      sort_by: params.sortBy || 'published_at',
      sort_order: params.sortOrder || 'desc'
    }

    // Remove undefined params
    Object.keys(queryParams).forEach((key) => {
      if (queryParams[key] === undefined) {
        delete queryParams[key]
      }
    })

    return await axios.get(API_ENDPOINTS.NEWS_ARTICLES, { params: queryParams })
  },

  /**
   * Get articles grouped by source
   */
  async getGroupedArticles(params = {}) {
    const queryParams = {
      category: params.category,
      start_date: params.startDate,
      limit_per_source: params.limitPerSource || 10
    }

    Object.keys(queryParams).forEach((key) => {
      if (queryParams[key] === undefined) {
        delete queryParams[key]
      }
    })

    return await axios.get(API_ENDPOINTS.NEWS_ARTICLES_GROUPED, { params: queryParams })
  },

  /**
   * Get single article by ID
   */
  async getArticle(id) {
    return await axios.get(API_ENDPOINTS.NEWS_ARTICLE_DETAIL(id))
  },

  /**
   * Get all news sources
   */
  async getSources(enabledOnly = false) {
    return await axios.get(API_ENDPOINTS.NEWS_SOURCES, {
      params: { enabled_only: enabledOnly }
    })
  },

  /**
   * Get statistics
   */
  async getStatistics() {
    return await axios.get(API_ENDPOINTS.NEWS_STATISTICS)
  }
}

export default articleService
