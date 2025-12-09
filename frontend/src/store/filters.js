/**
 * Filters store using Pinia.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useFiltersStore = defineStore('filters', () => {
  // State
  const selectedSource = ref(null)
  const selectedCategory = ref(null)
  const dateRange = ref([])

  // Actions
  function setSource(source) {
    selectedSource.value = source
  }

  function setCategory(category) {
    selectedCategory.value = category
  }

  function setDateRange(range) {
    dateRange.value = range
  }

  function clearFilters() {
    selectedSource.value = null
    selectedCategory.value = null
    dateRange.value = []
  }

  function getFiltersAsParams() {
    const params = {}

    if (selectedSource.value) {
      params.source = selectedSource.value
    }

    if (selectedCategory.value) {
      params.category = selectedCategory.value
    }

    if (dateRange.value && dateRange.value.length === 2) {
      params.startDate = dateRange.value[0]
      params.endDate = dateRange.value[1]
    }

    return params
  }

  return {
    // State
    selectedSource,
    selectedCategory,
    dateRange,
    // Actions
    setSource,
    setCategory,
    setDateRange,
    clearFilters,
    getFiltersAsParams
  }
})
