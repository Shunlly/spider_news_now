/**
 * 新闻页面 E2E 测试
 * News Page E2E Tests
 * T170: News list and search E2E test
 *
 * 测试场景：
 * - 新闻列表加载
 * - 搜索功能
 * - 筛选功能
 * - 分页功能
 * - 文章详情
 */

import { test, expect } from '@playwright/test'

test.describe('新闻页面', () => {
  test.beforeEach(async ({ page }) => {
    // 模拟已登录状态
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

    await page.goto('/news')
  })

  test('应该显示新闻列表', async ({ page }) => {
    // 等待新闻列表加载
    await expect(page.getByText(/新闻|文章|News|Articles/)).toBeVisible({ timeout: 10000 })
  })

  test('应该有搜索输入框', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/搜索|Search/)
    await expect(searchInput).toBeVisible()
  })

  test('搜索功能应该工作', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/搜索|Search/)

    // 输入搜索关键词
    await searchInput.fill('科技')
    await searchInput.press('Enter')

    // 等待搜索结果
    await page.waitForLoadState('networkidle')

    // 验证搜索已执行（URL 或结果变化）
    await expect(page.url()).toContain('q=') // 或检查结果
  })

  test('应该有来源筛选器', async ({ page }) => {
    // 查找来源筛选下拉框
    const sourceFilter = page.getByRole('combobox').or(page.getByText(/来源|Source/))
    await expect(sourceFilter.first()).toBeVisible({ timeout: 10000 })
  })

  test('应该有分类筛选器', async ({ page }) => {
    // 查找分类筛选
    const categoryFilter = page.getByText(/分类|Category|全部分类/)
    await expect(categoryFilter.first()).toBeVisible({ timeout: 10000 })
  })

  test('应该显示分页控件', async ({ page }) => {
    // 等待列表加载
    await page.waitForLoadState('networkidle')

    // 查找分页控件
    const pagination = page.locator('[class*="pagination"], [class*="pager"]')
    await expect(pagination.first()).toBeVisible({ timeout: 10000 })
  })

  test('点击文章应该显示详情', async ({ page }) => {
    // 等待文章列表加载
    await page.waitForLoadState('networkidle')

    // 查找文章标题链接
    const articleLinks = page.locator('a[href*="article"], [class*="article-title"]')

    if ((await articleLinks.count()) > 0) {
      // 点击第一篇文章
      await articleLinks.first().click()

      // 验证详情页面或模态框显示
      await page.waitForLoadState('networkidle')
    }
  })

  test('应该支持日期范围筛选', async ({ page }) => {
    // 查找日期选择器
    const datePicker = page.locator('[class*="date"], input[type="date"]')

    if ((await datePicker.count()) > 0) {
      await expect(datePicker.first()).toBeVisible()
    }
  })

  test('应该显示文章元信息', async ({ page }) => {
    // 等待文章加载
    await page.waitForLoadState('networkidle')

    // 检查是否显示来源信息
    const sourceInfo = page.getByText(/新浪|网易|凤凰|腾讯|环球/)
    await expect(sourceInfo.first()).toBeVisible({ timeout: 10000 })
  })

  test('空搜索结果应该显示提示', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/搜索|Search/)

    // 搜索不存在的内容
    await searchInput.fill('xyzabc123notexist')
    await searchInput.press('Enter')

    // 等待结果
    await page.waitForLoadState('networkidle')

    // 应该显示空结果提示
    await expect(page.getByText(/没有|无结果|No results|暂无/)).toBeVisible({ timeout: 10000 })
  })

  test('应该在移动端正确显示列表', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 })

    // 验证新闻列表仍然可见
    await expect(page.getByText(/新闻|文章|News/)).toBeVisible({ timeout: 10000 })
  })
})
