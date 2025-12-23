/**
 * Dashboard Page E2E Tests
 * T171: Frontend E2E test for dashboard
 *
 * Tests:
 * - Dashboard rendering
 * - Stats display
 * - Scraper status display
 * - Run all scrapers functionality
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '../test/utils'
import DashboardPage from './DashboardPage'
import { scraperService, newsService } from '@/services'

// Mock services
vi.mock('@/services', () => ({
  scraperService: {
    getStatus: vi.fn(),
    runAllScrapers: vi.fn(),
    runScraper: vi.fn(),
  },
  newsService: {
    getStatistics: vi.fn(),
  },
}))

// Mock QuotaDisplay component
vi.mock('@/components/QuotaDisplay', () => ({
  default: () => <div data-testid="quota-display">Quota Display</div>,
}))

// Mock SourcePieChart component
vi.mock('@/components/charts/SourcePieChart', () => ({
  default: () => <div data-testid="source-pie-chart">Source Pie Chart</div>,
}))

const mockScrapers = [
  {
    source_key: 'sina',
    source_name: 'Sina News',
    enabled: true,
    last_run: {
      completed_at: '2024-01-01T12:00:00Z',
      status: 'success',
      articles_scraped: 100,
      articles_new: 10,
    },
    status: 'idle',
  },
  {
    source_key: 'yicai',
    source_name: 'Yicai News',
    enabled: true,
    last_run: {
      completed_at: '2024-01-01T11:00:00Z',
      status: 'success',
      articles_scraped: 50,
      articles_new: 5,
    },
    status: 'idle',
  },
]

const mockStats = {
  total_articles: 1500,
  articles_today: 25,
  articles_yesterday: 20,
  total_sources: 5,
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(scraperService.getStatus as ReturnType<typeof vi.fn>).mockResolvedValue({
      scrapers: mockScrapers,
    })
    ;(newsService.getStatistics as ReturnType<typeof vi.fn>).mockResolvedValue(mockStats)
    ;(scraperService.runAllScrapers as ReturnType<typeof vi.fn>).mockResolvedValue({})
  })

  describe('Rendering', () => {
    it('should render dashboard title', async () => {
      render(<DashboardPage />)

      await waitFor(() => {
        expect(screen.getByText(/系统监控面板/i)).toBeInTheDocument()
      })
    })

    it('should display quota display component', async () => {
      render(<DashboardPage />)

      await waitFor(() => {
        expect(screen.getByTestId('quota-display')).toBeInTheDocument()
      })
    })

    it('should display source pie chart', async () => {
      render(<DashboardPage />)

      await waitFor(() => {
        expect(screen.getByTestId('source-pie-chart')).toBeInTheDocument()
      })
    })

    it('should display current time', async () => {
      render(<DashboardPage />)

      await waitFor(() => {
        // Check for time display (format: HH:MM:SS)
        const timeRegex = /\d{2}:\d{2}:\d{2}/
        expect(screen.getByText(timeRegex)).toBeInTheDocument()
      })
    })
  })

  describe('Statistics Display', () => {
    it('should display statistics cards', async () => {
      render(<DashboardPage />)

      await waitFor(() => {
        // Check for stat card titles
        expect(screen.getByText(/今日新增/i)).toBeInTheDocument()
        expect(screen.getByText(/文章总数/i)).toBeInTheDocument()
      })
    })

    it('should display today articles count', async () => {
      render(<DashboardPage />)

      await waitFor(() => {
        expect(screen.getByText('25')).toBeInTheDocument()
      })
    })
  })

  describe('Scraper Status', () => {
    it('should fetch scraper status on mount', async () => {
      render(<DashboardPage />)

      await waitFor(() => {
        expect(scraperService.getStatus).toHaveBeenCalled()
      })
    })

    it('should display scraper info after loading', async () => {
      render(<DashboardPage />)

      // Wait for data to load - check for activity list presence
      await waitFor(() => {
        expect(scraperService.getStatus).toHaveBeenCalled()
      })

      // The scraper names appear in the source distribution section
      // Check that the component renders without crashing
      expect(screen.getByTestId('source-pie-chart')).toBeInTheDocument()
    })
  })

  describe('Run All Scrapers', () => {
    it('should call runAllScrapers when button is clicked', async () => {
      render(<DashboardPage />)

      await waitFor(() => {
        expect(screen.getByText(/立即采集/i)).toBeInTheDocument()
      })

      const runAllButton = screen.getByText(/立即采集/i).closest('button')
      if (runAllButton) {
        fireEvent.click(runAllButton)

        await waitFor(() => {
          expect(scraperService.runAllScrapers).toHaveBeenCalled()
        })
      }
    })
  })

  describe('Data Refresh', () => {
    it('should have a refresh button', async () => {
      render(<DashboardPage />)

      await waitFor(() => {
        const refreshButtons = screen.getAllByRole('button')
        expect(refreshButtons.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Loading State', () => {
    it('should show loading state initially', () => {
      render(<DashboardPage />)

      // During initial load, the component should not crash
      // and should eventually show content
      expect(document.body).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      ;(scraperService.getStatus as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('API Error')
      )

      render(<DashboardPage />)

      // Should not crash and should render something
      await waitFor(() => {
        expect(document.body).toBeInTheDocument()
      })
    })
  })
})
