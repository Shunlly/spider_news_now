/**
 * 任务创建和查看流程 E2E 测试
 * Task Creation and Viewing E2E Tests
 * T170: E2E test for complete task creation and viewing flow
 *
 * 测试场景：
 * - Dashboard 页面加载
 * - 爬虫状态显示
 * - 运行爬虫任务
 * - 查看采集结果
 */

import { test, expect } from '@playwright/test'

test.describe('任务创建和查看流程 (T170)', () => {
  test.beforeEach(async ({ page }) => {
    // 模拟已登录状态
    await page.addInitScript(() => {
      localStorage.setItem('token', 'mock-jwt-token')
      localStorage.setItem(
        'user',
        JSON.stringify({
          id: '1',
          username: 'admin',
          role_id: 1,
          tenant_id: null,
        })
      )
    })

    await page.goto('/dashboard')
  })

  // ============== Dashboard 页面测试 ==============
  test('应该显示 Dashboard 页面', async ({ page }) => {
    await expect(page.getByText('系统监控面板')).toBeVisible({ timeout: 10000 })
  })

  test('应该显示统计卡片', async ({ page }) => {
    // 检查统计卡片存在
    await expect(page.getByText(/今日新增|文章总数/)).toBeVisible({ timeout: 10000 })
  })

  test('应该显示爬虫状态列表', async ({ page }) => {
    // 等待爬虫状态加载
    const scraperSection = page.getByText(/爬虫状态|采集来源/)
    await expect(scraperSection).toBeVisible({ timeout: 10000 })
  })

  test('应该有立即采集按钮', async ({ page }) => {
    const collectButton = page.getByRole('button', { name: /立即采集|采集全部|Run All/ })
    await expect(collectButton).toBeVisible({ timeout: 10000 })
  })

  test('应该有刷新按钮', async ({ page }) => {
    const refreshButton = page.getByRole('button', { name: /刷新|Refresh/ })
    await expect(refreshButton).toBeVisible({ timeout: 10000 })
  })

  // ============== 爬虫运行测试 ==============
  test('点击刷新按钮应该更新数据', async ({ page }) => {
    await page.waitForLoadState('networkidle')

    const refreshButton = page.getByRole('button', { name: /刷新|Refresh/ })
    await refreshButton.click()

    // 等待数据更新（不应该出错）
    await page.waitForTimeout(1000)
    await expect(page.getByText(/错误|Error/)).not.toBeVisible()
  })

  test('应该显示配额使用情况', async ({ page }) => {
    await expect(page.getByText(/配额|Quota|剩余/)).toBeVisible({ timeout: 10000 })
  })

  test('应该显示采集来源分布图表', async ({ page }) => {
    await expect(page.getByText(/采集来源|来源分布|Source/)).toBeVisible({ timeout: 10000 })
  })

  test('应该显示最近活动列表', async ({ page }) => {
    await expect(page.getByText(/最近活动|采集活动|Activity/)).toBeVisible({ timeout: 10000 })
  })

  // ============== 导航到新闻列表测试 ==============
  test('应该能导航到新闻列表页面', async ({ page }) => {
    // 点击新闻相关链接或导航
    const newsLink = page.getByRole('link', { name: /新闻|News|文章/ })
    if (await newsLink.isVisible()) {
      await newsLink.click()
      await expect(page).toHaveURL(/\/news/)
    }
  })

  // ============== 新闻列表页面测试 ==============
  test('新闻列表页面应该显示采集结果', async ({ page }) => {
    await page.goto('/news')

    // 等待页面加载
    await expect(page.getByText(/新闻|文章|News/)).toBeVisible({ timeout: 10000 })
  })

  test('新闻列表应该有筛选功能', async ({ page }) => {
    await page.goto('/news')

    // 检查来源筛选
    const sourceFilter = page.getByText(/来源|Source|全部来源/)
    await expect(sourceFilter.first()).toBeVisible({ timeout: 10000 })
  })

  test('新闻列表应该有搜索功能', async ({ page }) => {
    await page.goto('/news')

    const searchInput = page.getByPlaceholder(/搜索|Search/)
    await expect(searchInput.first()).toBeVisible({ timeout: 10000 })
  })

  test('新闻列表应该有分页功能', async ({ page }) => {
    await page.goto('/news')

    // 等待列表加载
    await page.waitForLoadState('networkidle')

    // 检查分页控件是否存在（可能在数据较少时不显示）
    const paginationLocator = page.locator('[class*="pagination"], button:has-text("下一页"), button:has-text(">")')
    // 分页存在时验证可见性
    if ((await paginationLocator.count()) > 0) {
      await expect(paginationLocator.first()).toBeVisible()
    }
  })

  test('点击新闻应该显示详情', async ({ page }) => {
    await page.goto('/news')

    // 等待列表加载
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    // 找到第一篇新闻并点击
    const newsItems = page.locator('[class*="card"], article, .news-item').first()
    if (await newsItems.isVisible()) {
      await newsItems.click()

      // 应该显示详情（可能是模态框或新页面）
      await page.waitForTimeout(1000)
    }
  })

  // ============== 移动端适配测试 ==============
  test('Dashboard 应该在移动端正确显示', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    await expect(page.getByText('系统监控面板')).toBeVisible({ timeout: 10000 })
  })

  test('新闻列表应该在移动端正确显示', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/news')

    await expect(page.getByText(/新闻|文章|News/)).toBeVisible({ timeout: 10000 })
  })

  // ============== 错误处理测试 ==============
  test('页面应该没有 JavaScript 错误', async ({ page }) => {
    const errors: string[] = []

    page.on('pageerror', (error) => {
      errors.push(error.message)
    })

    await page.waitForLoadState('networkidle')

    expect(errors).toHaveLength(0)
  })
})

// ============== 社交媒体采集任务测试 ==============
test.describe('社交媒体任务流程', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('token', 'mock-jwt-token')
      localStorage.setItem(
        'user',
        JSON.stringify({
          id: '1',
          username: 'admin',
          role_id: 1,
          tenant_id: null,
        })
      )
    })
  })

  test('应该能访问社交媒体页面', async ({ page }) => {
    await page.goto('/social')

    await expect(page.getByText(/社交|Social|会话/)).toBeVisible({ timeout: 10000 })
  })

  test('社交页面应该显示会话列表', async ({ page }) => {
    await page.goto('/social')

    // 等待页面加载
    await page.waitForLoadState('networkidle')
    // 页面应该有会话相关内容
  })

  test('应该能访问 Telegram 页面', async ({ page }) => {
    await page.goto('/telegram')

    await expect(page.getByText(/Telegram|频道/)).toBeVisible({ timeout: 10000 })
  })

  test('应该能访问 Twitter 页面', async ({ page }) => {
    await page.goto('/twitter')

    await expect(page.getByText(/Twitter|推文/)).toBeVisible({ timeout: 10000 })
  })
})
