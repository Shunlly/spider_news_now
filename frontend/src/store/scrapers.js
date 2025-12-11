/**
 * Scrapers store using Pinia.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import scraperService from '../services/scraperService'

export const useScrapersStore = defineStore('scrapers', () => {
  // State
  const scrapers = ref([])
  const selectedScraper = ref(null)
  const scraperRuns = ref([])
  const loading = ref(false)
  const error = ref(null)
  const totalScrapers = ref(0)
  const activeRuns = ref(0)
  const runsPagination = ref({
    page: 1,
    pageSize: 20,
    total: 0
  })

  // Getters
  const hasScrapers = computed(() => scrapers.value.length > 0)

  const enabledScrapers = computed(() => scrapers.value.filter((s) => s.enabled))

  const runningScrapers = computed(() => scrapers.value.filter((s) => s.status === 'running'))

  const failedScrapers = computed(() => scrapers.value.filter((s) => s.status === 'failed'))

  const scraperMap = computed(() => {
    const map = {}
    scrapers.value.forEach((s) => {
      map[s.source_key] = s
    })
    return map
  })

  // Actions
  async function fetchScrapersStatus() {
    loading.value = true
    error.value = null

    try {
      const response = await scraperService.getScrapersStatus()
      scrapers.value = response.scrapers
      totalScrapers.value = response.total_scrapers
      activeRuns.value = response.active_runs
      return response
    } catch (err) {
      error.value = err.message
      console.error('Failed to fetch scrapers status:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchScraperRuns(sourceKey, params = {}) {
    loading.value = true
    error.value = null

    try {
      const response = await scraperService.getScraperRuns(sourceKey, params)
      scraperRuns.value = response.runs
      runsPagination.value = {
        page: response.page,
        pageSize: response.page_size,
        total: response.total
      }
      return response
    } catch (err) {
      error.value = err.message
      console.error('Failed to fetch scraper runs:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function triggerScraper(sourceKey) {
    error.value = null

    try {
      const response = await scraperService.triggerScraper(sourceKey)
      // Refresh status after triggering
      await fetchScrapersStatus()
      return response
    } catch (err) {
      error.value = err.message
      console.error('Failed to trigger scraper:', err)
      throw err
    }
  }

  async function enableScraper(sourceKey) {
    error.value = null

    try {
      const response = await scraperService.enableScraper(sourceKey)
      // Update local state
      const scraper = scraperMap.value[sourceKey]
      if (scraper) {
        scraper.enabled = true
        scraper.status = 'idle'
      }
      return response
    } catch (err) {
      error.value = err.message
      console.error('Failed to enable scraper:', err)
      throw err
    }
  }

  async function disableScraper(sourceKey) {
    error.value = null

    try {
      const response = await scraperService.disableScraper(sourceKey)
      // Update local state
      const scraper = scraperMap.value[sourceKey]
      if (scraper) {
        scraper.enabled = false
        scraper.status = 'disabled'
      }
      return response
    } catch (err) {
      error.value = err.message
      console.error('Failed to disable scraper:', err)
      throw err
    }
  }

  async function updateScraperConfig(sourceKey, config) {
    error.value = null

    try {
      const response = await scraperService.updateScraperConfig(sourceKey, config)
      // Refresh status after update
      await fetchScrapersStatus()
      return response
    } catch (err) {
      error.value = err.message
      console.error('Failed to update scraper config:', err)
      throw err
    }
  }

  async function createScraper(data) {
    error.value = null

    try {
      const response = await scraperService.createScraper(data)
      // Refresh status after creation
      await fetchScrapersStatus()
      return response
    } catch (err) {
      error.value = err.message
      console.error('Failed to create scraper:', err)
      throw err
    }
  }

  function selectScraper(sourceKey) {
    selectedScraper.value = scraperMap.value[sourceKey] || null
  }

  function clearSelection() {
    selectedScraper.value = null
    scraperRuns.value = []
  }

  return {
    // State
    scrapers,
    selectedScraper,
    scraperRuns,
    loading,
    error,
    totalScrapers,
    activeRuns,
    runsPagination,
    // Getters
    hasScrapers,
    enabledScrapers,
    runningScrapers,
    failedScrapers,
    scraperMap,
    // Actions
    fetchScrapersStatus,
    fetchScraperRuns,
    triggerScraper,
    enableScraper,
    disableScraper,
    updateScraperConfig,
    createScraper,
    selectScraper,
    clearSelection
  }
})
