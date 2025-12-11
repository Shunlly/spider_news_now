/**
 * Unit tests for FilterPanel component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import FilterPanel from '../../src/components/news/FilterPanel.vue'
import ElementPlus from 'element-plus'

// Mock article service
vi.mock('../../src/services/articleService', () => ({
  default: {
    getSources: vi.fn().mockResolvedValue({
      sources: [
        { source_key: 'sina', display_name: '新浪新闻' },
        { source_key: 'qq', display_name: '腾讯新闻' }
      ]
    })
  }
}))

describe('FilterPanel', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  function createWrapper() {
    return mount(FilterPanel, {
      global: {
        plugins: [ElementPlus, createPinia()],
        stubs: {
          teleport: true
        }
      }
    })
  }

  it('renders filter panel', () => {
    const wrapper = createWrapper()
    expect(wrapper.find('.filter-panel').exists()).toBe(true)
  })

  it('renders filter title', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('筛选条件')
  })

  it('has source select', () => {
    const wrapper = createWrapper()
    expect(wrapper.find('.el-select').exists()).toBe(true)
  })

  it('has clear button', () => {
    const wrapper = createWrapper()
    const clearButton = wrapper.find('button')
    expect(clearButton.exists()).toBe(true)
    expect(clearButton.text()).toContain('清空')
  })

  it('renders category options', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('分类')
  })

  it('renders date range picker', () => {
    const wrapper = createWrapper()
    expect(wrapper.find('.el-date-picker').exists()).toBe(true)
  })

  it('emits filter-change event when filter changes', async () => {
    const wrapper = createWrapper()

    // Simulate filter change by calling the method directly
    wrapper.vm.localFilters.source = 'sina'
    await wrapper.vm.handleFilterChange()

    expect(wrapper.emitted('filter-change')).toBeTruthy()
  })

  it('clears all filters when clear button clicked', async () => {
    const wrapper = createWrapper()

    // Set some filters
    wrapper.vm.localFilters.source = 'sina'
    wrapper.vm.localFilters.category = 'tech'

    // Clear filters
    await wrapper.vm.handleClearFilters()

    expect(wrapper.vm.localFilters.source).toBe(null)
    expect(wrapper.vm.localFilters.category).toBe(null)
    expect(wrapper.emitted('filter-change')).toBeTruthy()
  })

  it('computes hasActiveFilters correctly', () => {
    const wrapper = createWrapper()

    // Initially no active filters
    expect(wrapper.vm.hasActiveFilters).toBe(false)

    // Set a filter
    wrapper.vm.localFilters.source = 'sina'
    expect(wrapper.vm.hasActiveFilters).toBe(true)
  })

  it('clears individual filter', async () => {
    const wrapper = createWrapper()

    wrapper.vm.localFilters.source = 'sina'
    wrapper.vm.localFilters.category = 'tech'

    await wrapper.vm.clearFilter('source')

    expect(wrapper.vm.localFilters.source).toBe(null)
    expect(wrapper.vm.localFilters.category).toBe('tech')
  })
})
