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
  }
}

export default scraperService
