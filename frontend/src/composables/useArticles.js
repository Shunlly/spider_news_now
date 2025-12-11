/**
 * Composable for reactive article fetching logic.
 */

import { ref, watch, onMounted } from 'vue'
import { useArticlesStore } from '../store/articles'
import { storeToRefs } from 'pinia'

/**
 * Composable for working with articles
 *
 * @param {Object} options - Configuration options
 * @param {boolean} options.fetchOnMount - Whether to fetch articles on mount
 * @param {boolean} options.grouped - Whether to fetch grouped articles
 * @param {Object} options.initialFilters - Initial filter values
 */
export function useArticles(options = {}) {
  const { fetchOnMount = true, grouped = false, initialFilters = {} } = options

  const store = useArticlesStore()
  const {
    articles,
    groupedArticles,
    currentArticle,
    loading,
    error,
    pagination,
    hasArticles,
    hasGroupedArticles
  } = storeToRefs(store)

  // Local filter state
  const filters = ref({
    source: initialFilters.source || null,
    category: initialFilters.category || null,
    startDate: initialFilters.startDate || null,
    endDate: initialFilters.endDate || null,
    page: initialFilters.page || 1,
    pageSize: initialFilters.pageSize || 50,
    sortBy: initialFilters.sortBy || 'published_at',
    sortOrder: initialFilters.sortOrder || 'desc'
  })

  /**
   * Fetch articles with current filters
   */
  async function fetchArticles() {
    if (grouped) {
      return await store.fetchGroupedArticles({
        category: filters.value.category,
        startDate: filters.value.startDate,
        limitPerSource: filters.value.pageSize
      })
    } else {
      return await store.fetchArticles(filters.value)
    }
  }

  /**
   * Fetch a single article by ID
   */
  async function fetchArticle(id) {
    return await store.fetchArticle(id)
  }

  /**
   * Update filters and refetch
   */
  async function updateFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
    // Reset to page 1 when filters change (except page itself)
    if (!('page' in newFilters)) {
      filters.value.page = 1
    }
    return await fetchArticles()
  }

  /**
   * Go to a specific page
   */
  async function goToPage(page) {
    return await updateFilters({ page })
  }

  /**
   * Reset all filters to defaults
   */
  async function resetFilters() {
    filters.value = {
      source: null,
      category: null,
      startDate: null,
      endDate: null,
      page: 1,
      pageSize: 50,
      sortBy: 'published_at',
      sortOrder: 'desc'
    }
    return await fetchArticles()
  }

  /**
   * Refresh current data
   */
  async function refresh() {
    return await fetchArticles()
  }

  // Fetch on mount if enabled
  onMounted(() => {
    if (fetchOnMount) {
      fetchArticles()
    }
  })

  return {
    // State from store
    articles,
    groupedArticles,
    currentArticle,
    loading,
    error,
    pagination,
    hasArticles,
    hasGroupedArticles,
    // Local state
    filters,
    // Actions
    fetchArticles,
    fetchArticle,
    updateFilters,
    goToPage,
    resetFilters,
    refresh,
    clearArticles: store.clearArticles
  }
}

export default useArticles
