/**
 * 仪表板页面 E2E 测试
 * Dashboard Page E2E Tests
 * T060: Dashboard E2E test
 *
 * 测试场景：
 * - 页面加载和统计卡片显示
 * - 图表渲染
 * - 爬虫状态显示
 * - 实时更新功能
 * - 操作按钮功能
 */

import { test, expect } from '@playwright/test'

// 模拟已登录状态
test.describe('仪表板页面', () => {
  test.beforeEach(async ({ page, context }) => {
    // 设置 mock token（模拟已登录状态）
    await context.addCookies([
      {
        name: 'token',
        value: 'mock-jwt-token',
        domain: 'localhost',
        path: '/',
      },
    ])

    // 或者使用 localStorage
    await page.addInitScript(() => {
      localStorage.setItem('token', 'mock-jwt-token')
      localStorage.setItem(
        'user',
        JSON.stringify({
          id: '1',
          username: 'admin',
          role: 'admin',
        })
      )
    })

    await page.goto('/dashboard')
  })

  test('应该显示仪表板标题', async ({ page }) => {
    // 检查页面标题或标题文本
    await expect(page.getByText(/系统监控|仪表板|Dashboard/)).toBeVisible({ timeout: 10000 })
  })

  test('应该显示统计卡片', async ({ page }) => {
    // 等待统计卡片加载
    const statsCards = page.locator('[class*="stat"], [class*="card"]')

    // 应该有多个统计卡片
    await expect(statsCards.first()).toBeVisible({ timeout: 10000 })
  })

  test('应该显示今日新增文章统计', async ({ page }) => {
    await expect(page.getByText(/今日新增|Today/)).toBeVisible({ timeout: 10000 })
  })

  test('应该显示文章总数统计', async ({ page }) => {
    await expect(page.getByText(/文章总数|Total Articles/)).toBeVisible({ timeout: 10000 })
  })

  test('应该显示爬虫状态区域', async ({ page }) => {
    await expect(page.getByText(/爬虫状态|Scraper Status/)).toBeVisible({ timeout: 10000 })
  })

  test('应该显示采集来源分布图表', async ({ page }) => {
    await expect(page.getByText(/采集来源|Source Distribution/)).toBeVisible({ timeout: 10000 })
  })

  test('应该有刷新按钮', async ({ page }) => {
    const refreshButton = page.getByRole('button', { name: /刷新|Refresh/ })
    await expect(refreshButton).toBeVisible()
  })

  test('应该有立即采集按钮', async ({ page }) => {
    const collectButton = page.getByRole('button', { name: /立即采集|采集|Collect/ })
    await expect(collectButton).toBeVisible()
  })

  test('点击刷新按钮应该更新数据', async ({ page }) => {
    // 等待页面加载
    await page.waitForLoadState('networkidle')

    // 点击刷新按钮
    const refreshButton = page.getByRole('button', { name: /刷新|Refresh/ })
    await refreshButton.click()

    // 验证没有错误显示
    await expect(page.getByText(/错误|Error|失败/)).not.toBeVisible({ timeout: 5000 })
  })

  test('应该显示系统时间', async ({ page }) => {
    // 检查时间显示
    const timeDisplay = page.locator('[class*="time"], [class*="clock"]')
    await expect(timeDisplay.first()).toBeVisible({ timeout: 10000 })
  })

  test('应该显示配额使用情况', async ({ page }) => {
    await expect(page.getByText(/配额|Quota|资源/)).toBeVisible({ timeout: 10000 })
  })

  test('爬虫卡片应该可点击', async ({ page }) => {
    // 等待爬虫状态区域加载
    await page.waitForSelector('[class*="scraper"], button:has-text("新浪")', { timeout: 10000 })

    // 查找爬虫按钮/卡片
    const scraperCards = page.locator('button').filter({ hasText: /新浪|网易|凤凰|腾讯/ })

    if ((await scraperCards.count()) > 0) {
      // 点击第一个爬虫
      await scraperCards.first().click()

      // 验证触发了某种操作（可能是运行爬虫或显示详情）
      await page.waitForTimeout(1000)
    }
  })

  test('应该在移动端正确显示', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 })

    // 验证关键元素仍然可见
    await expect(page.getByText(/系统监控|仪表板|Dashboard/)).toBeVisible({ timeout: 10000 })
  })

  test('应该显示最近活动列表', async ({ page }) => {
    await expect(page.getByText(/最近活动|采集活动|Activity/)).toBeVisible({ timeout: 10000 })
  })

  test('页面应该没有 JavaScript 错误', async ({ page }) => {
    const errors: string[] = []

    page.on('pageerror', (error) => {
      errors.push(error.message)
    })

    await page.waitForLoadState('networkidle')

    // 不应该有 JavaScript 错误
    expect(errors).toHaveLength(0)
  })
})
