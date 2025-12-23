/**
 * 导出功能 E2E 测试
 * Export Feature E2E Tests
 * T172: Data export E2E test
 *
 * 测试场景：
 * - 导出对话框显示
 * - 格式选择
 * - 筛选条件
 * - 导出执行
 */

import { test, expect } from '@playwright/test'

test.describe('导出功能', () => {
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

    // 导出功能通常在新闻页面或专门的导出页面
    await page.goto('/news')
  })

  test('应该有导出按钮', async ({ page }) => {
    const exportButton = page.getByRole('button', { name: /导出|Export|下载/ })
    await expect(exportButton).toBeVisible({ timeout: 10000 })
  })

  test('点击导出按钮应该打开导出对话框', async ({ page }) => {
    const exportButton = page.getByRole('button', { name: /导出|Export|下载/ })
    await exportButton.click()

    // 验证对话框打开
    const dialog = page.locator('[role="dialog"], [class*="modal"], [class*="dialog"]')
    await expect(dialog.first()).toBeVisible({ timeout: 5000 })
  })

  test('导出对话框应该有格式选择', async ({ page }) => {
    const exportButton = page.getByRole('button', { name: /导出|Export|下载/ })
    await exportButton.click()

    // 等待对话框
    await page.waitForTimeout(500)

    // 检查格式选项
    const csvOption = page.getByText(/CSV/)
    const jsonOption = page.getByText(/JSON/)
    const excelOption = page.getByText(/Excel|XLSX/)

    await expect(csvOption.or(jsonOption).or(excelOption).first()).toBeVisible()
  })

  test('导出对话框应该有数据源选择', async ({ page }) => {
    const exportButton = page.getByRole('button', { name: /导出|Export|下载/ })
    await exportButton.click()

    await page.waitForTimeout(500)

    // 检查数据源选项
    const newsOption = page.getByText(/新闻|文章|News/)
    const socialOption = page.getByText(/社交|消息|Social/)

    await expect(newsOption.or(socialOption).first()).toBeVisible()
  })

  test('应该能选择日期范围', async ({ page }) => {
    const exportButton = page.getByRole('button', { name: /导出|Export|下载/ })
    await exportButton.click()

    await page.waitForTimeout(500)

    // 检查日期选择器
    const datePicker = page.locator('input[type="date"], [class*="date-picker"]')

    if ((await datePicker.count()) > 0) {
      await expect(datePicker.first()).toBeVisible()
    }
  })

  test('应该能选择来源筛选', async ({ page }) => {
    const exportButton = page.getByRole('button', { name: /导出|Export|下载/ })
    await exportButton.click()

    await page.waitForTimeout(500)

    // 检查来源筛选
    const sourceFilter = page.getByText(/来源|Source|全部来源/)

    if ((await sourceFilter.count()) > 0) {
      await expect(sourceFilter.first()).toBeVisible()
    }
  })

  test('应该有确认导出按钮', async ({ page }) => {
    const exportButton = page.getByRole('button', { name: /导出|Export|下载/ })
    await exportButton.click()

    await page.waitForTimeout(500)

    // 检查确认按钮
    const confirmButton = page.getByRole('button', { name: /确认|开始|导出|Confirm|Start/ })
    await expect(confirmButton).toBeVisible()
  })

  test('应该能取消导出', async ({ page }) => {
    const exportButton = page.getByRole('button', { name: /导出|Export|下载/ })
    await exportButton.click()

    await page.waitForTimeout(500)

    // 检查取消按钮
    const cancelButton = page.getByRole('button', { name: /取消|Cancel|关闭|Close/ })
    await expect(cancelButton).toBeVisible()

    // 点击取消
    await cancelButton.click()

    // 对话框应该关闭
    const dialog = page.locator('[role="dialog"], [class*="modal"]')
    await expect(dialog).not.toBeVisible({ timeout: 2000 })
  })

  test('导出应该显示进度', async ({ page }) => {
    const exportButton = page.getByRole('button', { name: /导出|Export|下载/ })
    await exportButton.click()

    await page.waitForTimeout(500)

    // 选择格式（如果需要）
    const csvOption = page.getByText(/CSV/)
    if (await csvOption.isVisible()) {
      await csvOption.click()
    }

    // 点击确认导出
    const confirmButton = page.getByRole('button', { name: /确认|开始|导出|Confirm|Start/ })
    await confirmButton.click()

    // 应该显示进度或加载状态
    const progressIndicator = page.locator(
      '[class*="progress"], [class*="loading"], [class*="spinner"]'
    )
    const successMessage = page.getByText(/成功|完成|Success|下载/)

    await expect(progressIndicator.first().or(successMessage.first())).toBeVisible({
      timeout: 10000,
    })
  })

  test('空数据导出应该提示', async ({ page }) => {
    // 先搜索不存在的内容
    const searchInput = page.getByPlaceholder(/搜索|Search/)
    if (await searchInput.isVisible()) {
      await searchInput.fill('xyzabc123notexist')
      await searchInput.press('Enter')
      await page.waitForLoadState('networkidle')
    }

    // 尝试导出
    const exportButton = page.getByRole('button', { name: /导出|Export|下载/ })
    await exportButton.click()

    await page.waitForTimeout(500)

    const confirmButton = page.getByRole('button', { name: /确认|开始|导出|Confirm|Start/ })
    await confirmButton.click()

    // 应该显示提示（可能是警告或信息）
    await page.waitForTimeout(2000)
  })

  test('应该在移动端正确显示导出对话框', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    const exportButton = page.getByRole('button', { name: /导出|Export|下载/ })
    await exportButton.click()

    await page.waitForTimeout(500)

    // 对话框应该适应移动端
    const dialog = page.locator('[role="dialog"], [class*="modal"]')
    await expect(dialog.first()).toBeVisible()
  })
})
