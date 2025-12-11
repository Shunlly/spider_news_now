/**
 * Composable for filter application logic.
 */

import { computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useFiltersStore } from '../store/filters'
import { useArticlesStore } from '../store/articles'

/**
 * Composable for working with article filters
 *
 * @param {Object} options - Configuration options
 * @param {boolean} options.autoApply - Whether to automatically apply filters on change
 * @param {boolean} options.grouped - Whether to fetch grouped or paginated articles
 */
export function useFilters(options = {}) {
  const { autoApply = false, grouped = false } = options

  const filtersStore = useFiltersStore()
  const articlesStore = useArticlesStore()

  const { selectedSource, selectedCategory, dateRange } = storeToRefs(filtersStore)

  // Computed properties
  const hasActiveFilters = computed(() => {
    return (
      selectedSource.value !== null ||
      selectedCategory.value !== null ||
      (dateRange.value && dateRange.value.length === 2)
    )
  })

  const activeFilterCount = computed(() => {
    let count = 0
    if (selectedSource.value) count++
    if (selectedCategory.value) count++
    if (dateRange.value && dateRange.value.length === 2) count++
    return count
  })

  const filterSummary = computed(() => {
    const parts = []
    if (selectedSource.value) {
      parts.push(`Source: ${selectedSource.value}`)
    }
    if (selectedCategory.value) {
      parts.push(`Category: ${selectedCategory.value}`)
    }
    if (dateRange.value && dateRange.value.length === 2) {
      parts.push(`Date: ${dateRange.value[0]} - ${dateRange.value[1]}`)
    }
    return parts.join(', ') || 'No filters applied'
  })

  /**
   * Apply current filters and fetch articles
   */
  async function applyFilters() {
    const params = filtersStore.getFiltersAsParams()

    if (grouped) {
      return await articlesStore.fetchGroupedArticles({
        category: params.category,
        startDate: params.startDate,
        endDate: params.endDate
      })
    } else {
      return await articlesStore.fetchArticles({
        source: params.source,
        category: params.category,
        startDate: params.startDate,
        endDate: params.endDate,
        page: 1
      })
    }
  }

  /**
   * Set source filter
   */
  function setSource(source) {
    filtersStore.setSource(source)
  }

  /**
   * Set category filter
   */
  function setCategory(category) {
    filtersStore.setCategory(category)
  }

  /**
   * Set date range filter
   */
  function setDateRange(range) {
    filtersStore.setDateRange(range)
  }

  /**
   * Clear all filters and optionally refetch
   */
  async function clearFilters(refetch = true) {
    filtersStore.clearFilters()
    if (refetch) {
      return await applyFilters()
    }
  }

  /**
   * Set multiple filters at once
   */
  function setFilters({ source, category, dateRange: range }) {
    if (source !== undefined) {
      filtersStore.setSource(source)
    }
    if (category !== undefined) {
      filtersStore.setCategory(category)
    }
    if (range !== undefined) {
      filtersStore.setDateRange(range)
    }
  }

  // Auto-apply filters on change if enabled
  if (autoApply) {
    watch(
      [selectedSource, selectedCategory, dateRange],
      () => {
        applyFilters()
      },
      { deep: true }
    )
  }

  return {
    // State from store
    selectedSource,
    selectedCategory,
    dateRange,
    // Computed
    hasActiveFilters,
    activeFilterCount,
    filterSummary,
    // Actions
    applyFilters,
    setSource,
    setCategory,
    setDateRange,
    setFilters,
    clearFilters,
    getFiltersAsParams: filtersStore.getFiltersAsParams
  }
}

export default useFilters
