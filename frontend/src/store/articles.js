/**
 * Articles store using Pinia.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import articleService from '../services/articleService'

export const useArticlesStore = defineStore('articles', () => {
  // State
  const groupedArticles = ref([])
  const articles = ref([])
  const currentArticle = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const pagination = ref({
    page: 1,
    pageSize: 50,
    total: 0,
    totalPages: 0
  })

  // Getters
  const hasArticles = computed(() => articles.value.length > 0)
  const hasGroupedArticles = computed(() => groupedArticles.value.length > 0)

  // Actions
  async function fetchGroupedArticles(params = {}) {
    loading.value = true
    error.value = null

    try {
      const response = await articleService.getGroupedArticles(params)
      groupedArticles.value = response.groups
      return response
    } catch (err) {
      error.value = err.message
      console.error('Failed to fetch grouped articles:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchArticles(params = {}) {
    loading.value = true
    error.value = null

    try {
      const response = await articleService.getArticles(params)
      articles.value = response.data
      pagination.value = {
        page: response.page,
        pageSize: response.page_size,
        total: response.total,
        totalPages: response.total_pages
      }
      return response
    } catch (err) {
      error.value = err.message
      console.error('Failed to fetch articles:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchArticle(id) {
    loading.value = true
    error.value = null

    try {
      const response = await articleService.getArticle(id)
      currentArticle.value = response
      return response
    } catch (err) {
      error.value = err.message
      console.error('Failed to fetch article:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearArticles() {
    articles.value = []
    groupedArticles.value = []
    currentArticle.value = null
    error.value = null
  }

  return {
    // State
    groupedArticles,
    articles,
    currentArticle,
    loading,
    error,
    pagination,
    // Getters
    hasArticles,
    hasGroupedArticles,
    // Actions
    fetchGroupedArticles,
    fetchArticles,
    fetchArticle,
    clearArticles
  }
})
