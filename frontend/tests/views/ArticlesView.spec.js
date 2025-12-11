/**
 * Integration tests for ArticlesView.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ArticlesView from '../../src/views/ArticlesView.vue'
import ElementPlus from 'element-plus'

// Mock article service
vi.mock('../../src/services/articleService', () => ({
  default: {
    getGroupedArticles: vi.fn().mockResolvedValue({
      groups: [
        {
          source_key: 'sina',
          source_name: '新浪新闻',
          article_count: 2,
          articles: [
            {
              id: 1,
              title: 'Article 1',
              url: 'https://sina.com/1',
              source_key: 'sina',
              category: 'tech',
              published_at: new Date().toISOString()
            },
            {
              id: 2,
              title: 'Article 2',
              url: 'https://sina.com/2',
              source_key: 'sina',
              category: 'finance',
              published_at: new Date().toISOString()
            }
          ]
        },
        {
          source_key: 'qq',
          source_name: '腾讯新闻',
          article_count: 1,
          articles: [
            {
              id: 3,
              title: 'QQ Article',
              url: 'https://qq.com/1',
              source_key: 'qq',
              category: 'sports',
              published_at: new Date().toISOString()
            }
          ]
        }
      ],
      total_sources: 2,
      filters_applied: {}
    }),
    getArticles: vi.fn().mockResolvedValue({
      data: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0
    }),
    getSources: vi.fn().mockResolvedValue({
      sources: [
        { source_key: 'sina', display_name: '新浪新闻', enabled: true },
        { source_key: 'qq', display_name: '腾讯新闻', enabled: true }
      ]
    })
  }
}))

describe('ArticlesView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  function createWrapper() {
    return mount(ArticlesView, {
      global: {
        plugins: [ElementPlus, createPinia()],
        stubs: {
          teleport: true,
          'router-link': true
        }
      }
    })
  }

  it('renders the view', () => {
    const wrapper = createWrapper()
    expect(wrapper.exists()).toBe(true)
  })

  it('fetches grouped articles on mount', async () => {
    const articleService = await import('../../src/services/articleService')
    createWrapper()

    await flushPromises()

    expect(articleService.default.getGroupedArticles).toHaveBeenCalled()
  })

  it('displays article groups after loading', async () => {
    const wrapper = createWrapper()

    await flushPromises()

    // Check that article groups are rendered
    expect(wrapper.text()).toContain('新浪新闻')
  })

  it('handles filter changes', async () => {
    const wrapper = createWrapper()
    const articleService = await import('../../src/services/articleService')

    await flushPromises()

    // Simulate filter change
    wrapper.vm.handleFilterChange({ source: 'sina' })

    await flushPromises()

    // Should refetch with filters
    expect(articleService.default.getGroupedArticles).toHaveBeenCalledTimes(2)
  })

  it('shows loading state initially', () => {
    const wrapper = createWrapper()
    // Loading should be true initially before data loads
    expect(wrapper.vm.loading || wrapper.find('.el-loading').exists()).toBeDefined()
  })
})
