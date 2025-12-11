/**
 * Composable for source listing logic.
 */

import { ref, computed, onMounted } from 'vue'
import articleService from '../services/articleService'

/**
 * Composable for working with news sources
 *
 * @param {Object} options - Configuration options
 * @param {boolean} options.fetchOnMount - Whether to fetch sources on mount
 * @param {boolean} options.enabledOnly - Whether to fetch only enabled sources
 */
export function useSources(options = {}) {
  const { fetchOnMount = true, enabledOnly = false } = options

  // State
  const sources = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Computed
  const hasSources = computed(() => sources.value.length > 0)

  const enabledSources = computed(() => sources.value.filter((s) => s.enabled))

  const sourceOptions = computed(() =>
    sources.value.map((s) => ({
      label: s.display_name,
      value: s.source_key
    }))
  )

  const sourceMap = computed(() => {
    const map = {}
    sources.value.forEach((s) => {
      map[s.source_key] = s
    })
    return map
  })

  /**
   * Fetch all sources
   */
  async function fetchSources() {
    loading.value = true
    error.value = null

    try {
      const response = await articleService.getSources(enabledOnly)
      sources.value = response.sources
      return response
    } catch (err) {
      error.value = err.message
      console.error('Failed to fetch sources:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Get source by key
   */
  function getSourceByKey(key) {
    return sourceMap.value[key] || null
  }

  /**
   * Get source display name by key
   */
  function getSourceName(key) {
    const source = getSourceByKey(key)
    return source ? source.display_name : key
  }

  /**
   * Refresh sources
   */
  async function refresh() {
    return await fetchSources()
  }

  // Fetch on mount if enabled
  onMounted(() => {
    if (fetchOnMount) {
      fetchSources()
    }
  })

  return {
    // State
    sources,
    loading,
    error,
    // Computed
    hasSources,
    enabledSources,
    sourceOptions,
    sourceMap,
    // Actions
    fetchSources,
    getSourceByKey,
    getSourceName,
    refresh
  }
}

export default useSources
