/**
 * Scraper service for API calls.
 */

import axios from '../api/axios'
import { API_ENDPOINTS } from '../api/endpoints'

export const scraperService = {
  /**
   * Get status of all scrapers
   */
  async getScrapersStatus() {
    return await axios.get(API_ENDPOINTS.SCRAPERS_STATUS)
  },

  /**
   * Get scraper run history
   */
  async getScraperRuns(sourceKey, params = {}) {
    const queryParams = {
      page: params.page || 1,
      page_size: params.pageSize || 20
    }

    return await axios.get(API_ENDPOINTS.SCRAPER_RUNS(sourceKey), {
      params: queryParams
    })
  },

  /**
   * Trigger a scraper manually
   */
  async triggerScraper(sourceKey) {
    return await axios.post(API_ENDPOINTS.SCRAPER_TRIGGER(sourceKey))
  },

  /**
   * Enable a scraper
   */
  async enableScraper(sourceKey) {
    return await axios.put(API_ENDPOINTS.SCRAPER_ENABLE(sourceKey))
  },

  /**
   * Disable a scraper
   */
  async disableScraper(sourceKey) {
    return await axios.put(API_ENDPOINTS.SCRAPER_DISABLE(sourceKey))
  },

  /**
   * Update scraper configuration
   */
  async updateScraperConfig(sourceKey, config) {
    return await axios.put(`/scrapers/${sourceKey}/config`, config)
  },

  /**
   * Create a new scraper
   */
  async createScraper(data) {
    return await axios.post('/scrapers', data)
  }
}

export default scraperService
