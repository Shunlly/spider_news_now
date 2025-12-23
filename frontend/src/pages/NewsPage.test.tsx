/**
 * News Page E2E Tests
 * T172: Frontend E2E test for news browsing
 *
 * Tests:
 * - News list rendering
 * - Search functionality
 * - Source filtering
 * - Pagination
 * - Export functionality
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '../test/utils'
import NewsPage from './NewsPage'
import { newsService, scraperService, exportsService } from '@/services'

// Mock services
vi.mock('@/services', () => ({
  newsService: {
    getArticles: vi.fn(),
    getArticle: vi.fn(),
  },
  scraperService: {
    getSources: vi.fn(),
  },
  exportsService: {
    createExport: vi.fn(),
    getExportTasks: vi.fn(),
    downloadExport: vi.fn(),
  },
}))

// Mock createPortal for article detail modal
vi.mock('react-dom', async () => {
  const actual = await vi.importActual('react-dom')
  return {
    ...actual,
    createPortal: (node: React.ReactNode) => node,
  }
})

const mockArticles = [
  {
    id: 1,
    title: 'Test Article 1',
    url: 'https://example.com/article1',
    source_key: 'sina',
    category: 'finance',
    published_at: '2024-01-15T10:00:00Z',
    content_text: '<p>Article content here</p>',
  },
  {
    id: 2,
    title: 'Test Article 2',
    url: 'https://example.com/article2',
    source_key: 'yicai',
    category: 'tech',
    published_at: '2024-01-14T09:00:00Z',
    content_text: null,
  },
]

const mockSources = [
  { source_key: 'sina', display_name: 'Sina News', enabled: true },
  { source_key: 'yicai', display_name: 'Yicai News', enabled: true },
]

const mockExportTasks = [
  {
    id: 1,
    filename: 'news_export_20240115.csv',
    status: 'COMPLETED',
    exported_records: 100,
  },
]

describe('NewsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(newsService.getArticles as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: mockArticles,
      total: 100,
    })
    ;(newsService.getArticle as ReturnType<typeof vi.fn>).mockResolvedValue(mockArticles[0])
    ;(scraperService.getSources as ReturnType<typeof vi.fn>).mockResolvedValue({
      sources: mockSources,
    })
    ;(exportsService.getExportTasks as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: mockExportTasks,
    })
    ;(exportsService.createExport as ReturnType<typeof vi.fn>).mockResolvedValue({
      success: true,
      message: 'Export task created',
    })
  })

  describe('Rendering', () => {
    it('should render page title', async () => {
      render(<NewsPage />)

      expect(await screen.findByText(/新闻管理/i)).toBeInTheDocument()
    })

    it('should display total articles info', async () => {
      render(<NewsPage />)

      // Wait for the page to load and check for article count display
      expect(await screen.findByText(/篇文章/i)).toBeInTheDocument()
    })

    it('should render search input', async () => {
      render(<NewsPage />)

      expect(await screen.findByPlaceholderText(/搜索文章标题/i)).toBeInTheDocument()
    })

    it('should render refresh button', async () => {
      render(<NewsPage />)

      expect(await screen.findByText(/刷新/i)).toBeInTheDocument()
    })

    it('should render export button', async () => {
      render(<NewsPage />)

      expect(await screen.findByText(/导出/i)).toBeInTheDocument()
    })
  })

  describe('Article List', () => {
    it('should fetch articles on mount', async () => {
      render(<NewsPage />)

      await waitFor(() => {
        expect(newsService.getArticles).toHaveBeenCalled()
      })
    })

    it('should display article titles', async () => {
      render(<NewsPage />)

      expect(await screen.findByText('Test Article 1')).toBeInTheDocument()
      expect(await screen.findByText('Test Article 2')).toBeInTheDocument()
    })

    it('should display article source keys', async () => {
      render(<NewsPage />)

      expect(await screen.findByText('sina')).toBeInTheDocument()
      expect(await screen.findByText('yicai')).toBeInTheDocument()
    })

    it('should show empty state when no articles', async () => {
      ;(newsService.getArticles as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: [],
        total: 0,
      })

      render(<NewsPage />)

      expect(await screen.findByText(/暂无文章数据/i)).toBeInTheDocument()
    })
  })

  describe('Search', () => {
    it('should update search query on input', async () => {
      render(<NewsPage />)

      const searchInput = await screen.findByPlaceholderText(/搜索文章标题/i)
      fireEvent.change(searchInput, { target: { value: 'test query' } })

      expect(searchInput).toHaveValue('test query')
    })
  })

  describe('Source Filtering', () => {
    it('should fetch sources on mount', async () => {
      render(<NewsPage />)

      await waitFor(() => {
        expect(scraperService.getSources).toHaveBeenCalled()
      })
    })

    it('should display source filter dropdown', async () => {
      render(<NewsPage />)

      expect(await screen.findByText(/全部来源/i)).toBeInTheDocument()
    })
  })

  describe('Pagination', () => {
    it('should display pagination controls', async () => {
      render(<NewsPage />)

      expect(await screen.findByText(/每页/i)).toBeInTheDocument()
      expect(await screen.findByText('GO')).toBeInTheDocument()
    })

    it('should have page navigation buttons', async () => {
      render(<NewsPage />)

      // Wait for content to load
      await screen.findByText('Test Article 1')

      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)
    })
  })

  describe('Export Functionality', () => {
    it('should have export button', async () => {
      render(<NewsPage />)

      const exportButton = await screen.findByText(/导出/i)
      expect(exportButton).toBeInTheDocument()
    })
  })

  describe('Refresh', () => {
    it('should have refresh button', async () => {
      render(<NewsPage />)

      const refreshButton = await screen.findByText(/刷新/i)
      expect(refreshButton).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      ;(newsService.getArticles as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('API Error')
      )

      render(<NewsPage />)

      // Should not crash - page title should still render
      expect(await screen.findByText(/新闻管理/i)).toBeInTheDocument()

      consoleSpy.mockRestore()
    })

    it('should handle source fetch errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      ;(scraperService.getSources as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Sources Error')
      )

      render(<NewsPage />)

      // Should not crash and still show page
      expect(await screen.findByText(/新闻管理/i)).toBeInTheDocument()

      consoleSpy.mockRestore()
    })
  })
})
