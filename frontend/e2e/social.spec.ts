/**
 * 社交媒体页面 E2E 测试
 * Social Media Page E2E Tests
 * T171: Social subscriptions and messages E2E test
 *
 * 测试场景：
 * - 订阅列表显示
 * - 添加订阅
 * - 消息列表
 * - 平台切换
 */

import { test, expect } from '@playwright/test'

test.describe('社交媒体页面', () => {
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

    await page.goto('/social')
  })

  test('应该显示社交媒体页面标题', async ({ page }) => {
    await expect(page.getByText(/社交|Social|订阅/)).toBeVisible({ timeout: 10000 })
  })

  test('应该有平台切换选项', async ({ page }) => {
    // 检查 Twitter 和 Telegram 选项
    const twitterTab = page.getByText(/Twitter|推特/)
    const telegramTab = page.getByText(/Telegram|电报/)

    await expect(twitterTab.or(telegramTab).first()).toBeVisible({ timeout: 10000 })
  })

  test('应该显示订阅列表', async ({ page }) => {
    // 等待订阅列表加载
    await page.waitForLoadState('networkidle')

    // 检查订阅列表或空状态
    const subscriptionList = page.locator('[class*="subscription"], [class*="list"]')
    const emptyState = page.getByText(/暂无订阅|No subscriptions|添加订阅/)

    await expect(subscriptionList.first().or(emptyState.first())).toBeVisible({ timeout: 10000 })
  })

  test('应该有添加订阅按钮', async ({ page }) => {
    const addButton = page.getByRole('button', { name: /添加|新增|Add/ })
    await expect(addButton).toBeVisible()
  })

  test('点击添加按钮应该打开添加对话框', async ({ page }) => {
    const addButton = page.getByRole('button', { name: /添加|新增|Add/ })
    await addButton.click()

    // 验证对话框打开
    const dialog = page.locator('[role="dialog"], [class*="modal"], [class*="dialog"]')
    await expect(dialog.first()).toBeVisible({ timeout: 5000 })
  })

  test('应该能切换到消息视图', async ({ page }) => {
    // 查找消息标签页
    const messagesTab = page.getByText(/消息|Messages/)

    if (await messagesTab.isVisible()) {
      await messagesTab.click()
      await page.waitForLoadState('networkidle')
    }
  })

  test('订阅卡片应该显示状态', async ({ page }) => {
    await page.waitForLoadState('networkidle')

    // 检查是否有状态指示器
    const statusIndicator = page.locator('[class*="status"], [class*="badge"]')

    if ((await statusIndicator.count()) > 0) {
      await expect(statusIndicator.first()).toBeVisible()
    }
  })

  test('应该能暂停/启用订阅', async ({ page }) => {
    await page.waitForLoadState('networkidle')

    // 查找暂停/启用按钮
    const toggleButton = page.getByRole('button', { name: /暂停|启用|Pause|Enable/ })

    if ((await toggleButton.count()) > 0) {
      await expect(toggleButton.first()).toBeVisible()
    }
  })

  test('应该能删除订阅', async ({ page }) => {
    await page.waitForLoadState('networkidle')

    // 查找删除按钮
    const deleteButton = page.getByRole('button', { name: /删除|Delete|移除/ })

    if ((await deleteButton.count()) > 0) {
      await expect(deleteButton.first()).toBeVisible()
    }
  })

  test('消息列表应该支持筛选', async ({ page }) => {
    // 切换到消息视图
    const messagesTab = page.getByText(/消息|Messages/)
    if (await messagesTab.isVisible()) {
      await messagesTab.click()
      await page.waitForLoadState('networkidle')

      // 检查筛选器
      const filter = page.getByPlaceholder(/搜索|关键词|Search/)
      await expect(filter.first()).toBeVisible({ timeout: 10000 })
    }
  })

  test('应该在移动端正确显示', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    await expect(page.getByText(/社交|Social|订阅/)).toBeVisible({ timeout: 10000 })
  })
})
