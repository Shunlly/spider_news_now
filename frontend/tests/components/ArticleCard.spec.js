/**
 * Unit tests for ArticleCard component.
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ArticleCard from '../../src/components/news/ArticleCard.vue'
import ElementPlus from 'element-plus'

describe('ArticleCard', () => {
  const mockArticle = {
    id: 1,
    title: 'Test Article Title',
    url: 'https://example.com/article',
    source_key: 'sina',
    category: 'tech',
    published_at: new Date().toISOString()
  }

  function createWrapper(props = {}) {
    return mount(ArticleCard, {
      props: {
        article: mockArticle,
        ...props
      },
      global: {
        plugins: [ElementPlus]
      }
    })
  }

  it('renders article title', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('Test Article Title')
  })

  it('renders article link with correct href', () => {
    const wrapper = createWrapper()
    const link = wrapper.find('a')
    expect(link.attributes('href')).toBe('https://example.com/article')
  })

  it('opens link in new tab', () => {
    const wrapper = createWrapper()
    const link = wrapper.find('a')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toBe('noopener noreferrer')
  })

  it('renders source key tag', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('sina')
  })

  it('renders category tag when provided', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('tech')
  })

  it('does not render category tag when not provided', () => {
    const articleWithoutCategory = { ...mockArticle, category: null }
    const wrapper = createWrapper({ article: articleWithoutCategory })
    const tags = wrapper.findAll('.el-tag')
    expect(tags.length).toBe(1) // Only source tag
  })

  it('formats recent time correctly', () => {
    const recentArticle = {
      ...mockArticle,
      published_at: new Date(Date.now() - 30 * 60 * 1000).toISOString() // 30 minutes ago
    }
    const wrapper = createWrapper({ article: recentArticle })
    expect(wrapper.text()).toContain('分钟前')
  })

  it('formats hour time correctly', () => {
    const hourAgoArticle = {
      ...mockArticle,
      published_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() // 2 hours ago
    }
    const wrapper = createWrapper({ article: hourAgoArticle })
    expect(wrapper.text()).toContain('小时前')
  })

  it('has hover effect class', () => {
    const wrapper = createWrapper()
    expect(wrapper.classes()).toContain('article-card')
  })
})
