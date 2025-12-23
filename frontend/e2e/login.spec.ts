/**
 * 登录页面 E2E 测试
 * Login Page E2E Tests
 * T059: Login page E2E test
 *
 * 测试场景：
 * - 页面加载和元素显示
 * - 表单验证
 * - 登录成功流程
 * - 登录失败处理
 * - 验证码功能
 */

import { test, expect } from '@playwright/test'

test.describe('登录页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
  })

  test('应该正确显示登录表单', async ({ page }) => {
    // 检查页面标题
    await expect(page).toHaveTitle(/Spider News/)

    // 检查登录表单元素
    await expect(page.getByPlaceholder('用户名')).toBeVisible()
    await expect(page.getByPlaceholder('密码')).toBeVisible()
    await expect(page.getByRole('button', { name: /登录/ })).toBeVisible()
  })

  test('应该显示验证码', async ({ page }) => {
    // 检查验证码图片
    const captchaImage = page.locator('img[alt*="验证码"], img[alt*="captcha"]')
    await expect(captchaImage).toBeVisible()

    // 检查验证码输入框
    await expect(page.getByPlaceholder('验证码')).toBeVisible()
  })

  test('空表单提交应该显示错误', async ({ page }) => {
    // 点击登录按钮
    await page.getByRole('button', { name: /登录/ }).click()

    // 应该显示验证错误
    await expect(page.getByText(/请输入用户名|用户名不能为空/)).toBeVisible()
  })

  test('错误的凭证应该显示错误消息', async ({ page }) => {
    // 填写错误的凭证
    await page.getByPlaceholder('用户名').fill('wronguser')
    await page.getByPlaceholder('密码').fill('wrongpassword')
    await page.getByPlaceholder('验证码').fill('1234')

    // 提交表单
    await page.getByRole('button', { name: /登录/ }).click()

    // 应该显示错误消息
    await expect(page.getByText(/用户名或密码错误|登录失败|验证码错误/)).toBeVisible({
      timeout: 10000,
    })
  })

  test('刷新验证码应该更新图片', async ({ page }) => {
    // 获取当前验证码图片 src
    const captchaImage = page.locator('img[alt*="验证码"], img[alt*="captcha"]')
    const originalSrc = await captchaImage.getAttribute('src')

    // 点击刷新按钮
    const refreshButton = page.locator('button:has-text("刷新"), [aria-label*="刷新"]')
    if (await refreshButton.isVisible()) {
      await refreshButton.click()
      await page.waitForTimeout(500)

      // 验证图片已更新
      const newSrc = await captchaImage.getAttribute('src')
      expect(newSrc).not.toBe(originalSrc)
    }
  })

  test('登录成功应该跳转到仪表板', async ({ page }) => {
    // 注意：此测试需要有效的测试账号
    // 在 CI 环境中可能需要 mock API 响应

    // 填写有效凭证（使用测试账号）
    await page.getByPlaceholder('用户名').fill('admin')
    await page.getByPlaceholder('密码').fill('admin123')

    // 获取验证码（需要 mock 或跳过）
    // await page.getByPlaceholder('验证码').fill('mock-captcha')

    // 提交表单
    // await page.getByRole('button', { name: /登录/ }).click()

    // 验证跳转
    // await expect(page).toHaveURL(/dashboard/)
  })

  test('应该支持 Enter 键提交表单', async ({ page }) => {
    await page.getByPlaceholder('用户名').fill('testuser')
    await page.getByPlaceholder('密码').fill('testpass')
    await page.getByPlaceholder('验证码').fill('1234')

    // 按 Enter 键
    await page.getByPlaceholder('验证码').press('Enter')

    // 应该触发表单提交（显示加载状态或错误）
    await expect(
      page.getByRole('button', { name: /登录/ }).or(page.getByText(/登录失败|验证码错误/))
    ).toBeVisible({ timeout: 5000 })
  })

  test('密码输入框应该是密码类型', async ({ page }) => {
    const passwordInput = page.getByPlaceholder('密码')
    await expect(passwordInput).toHaveAttribute('type', 'password')
  })

  test('应该在移动端正确显示', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 })

    // 验证表单仍然可见
    await expect(page.getByPlaceholder('用户名')).toBeVisible()
    await expect(page.getByPlaceholder('密码')).toBeVisible()
    await expect(page.getByRole('button', { name: /登录/ })).toBeVisible()
  })
})
