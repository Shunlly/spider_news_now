/**
 * 认证流程 E2E 测试
 * Authentication E2E Tests
 * T059: E2E test for user registration flow
 * T060: E2E test for user login flow
 *
 * 测试场景：
 * - 用户注册完整流程
 * - 用户登录完整流程
 * - 表单验证
 * - 验证码功能
 */

import { test, expect } from '@playwright/test'

// ============== T059: 用户注册流程测试 ==============
test.describe('用户注册流程 (T059)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register')
  })

  test('应该正确显示注册表单', async ({ page }) => {
    // 检查页面标题
    await expect(page.getByText('用户注册')).toBeVisible()
    await expect(page.getByText('Create your account')).toBeVisible()

    // 检查表单元素
    await expect(page.getByPlaceholder('用户名')).toBeVisible()
    await expect(page.getByPlaceholder('邮箱')).toBeVisible()
    await expect(page.getByPlaceholder('密码')).toBeVisible()
    await expect(page.getByPlaceholder('确认密码')).toBeVisible()
    await expect(page.getByRole('button', { name: '下一步' })).toBeVisible()
  })

  test('空表单提交应该显示验证错误', async ({ page }) => {
    // 点击下一步按钮
    await page.getByRole('button', { name: '下一步' }).click()

    // 应该显示验证错误
    await expect(page.getByText('请输入用户名')).toBeVisible()
  })

  test('用户名格式验证', async ({ page }) => {
    // 输入短用户名
    await page.getByPlaceholder('用户名').fill('ab')
    await page.getByPlaceholder('邮箱').fill('test@example.com')
    await page.getByPlaceholder('密码').fill('password123')
    await page.getByPlaceholder('确认密码').fill('password123')
    await page.getByRole('button', { name: '下一步' }).click()

    // 应该显示用户名长度错误
    await expect(page.getByText('用户名至少3个字符')).toBeVisible()
  })

  test('用户名格式要求字母开头', async ({ page }) => {
    // 输入数字开头的用户名
    await page.getByPlaceholder('用户名').fill('123user')
    await page.getByPlaceholder('邮箱').fill('test@example.com')
    await page.getByPlaceholder('密码').fill('password123')
    await page.getByPlaceholder('确认密码').fill('password123')
    await page.getByRole('button', { name: '下一步' }).click()

    // 应该显示格式错误
    await expect(page.getByText(/用户名需以字母开头/)).toBeVisible()
  })

  test('邮箱格式验证', async ({ page }) => {
    await page.getByPlaceholder('用户名').fill('testuser')
    await page.getByPlaceholder('邮箱').fill('invalid-email')
    await page.getByPlaceholder('密码').fill('password123')
    await page.getByPlaceholder('确认密码').fill('password123')
    await page.getByRole('button', { name: '下一步' }).click()

    // 应该显示邮箱格式错误
    await expect(page.getByText('请输入有效的邮箱地址')).toBeVisible()
  })

  test('密码长度验证', async ({ page }) => {
    await page.getByPlaceholder('用户名').fill('testuser')
    await page.getByPlaceholder('邮箱').fill('test@example.com')
    await page.getByPlaceholder('密码').fill('short')
    await page.getByPlaceholder('确认密码').fill('short')
    await page.getByRole('button', { name: '下一步' }).click()

    // 应该显示密码长度错误
    await expect(page.getByText('密码至少8位')).toBeVisible()
  })

  test('确认密码不一致验证', async ({ page }) => {
    await page.getByPlaceholder('用户名').fill('testuser')
    await page.getByPlaceholder('邮箱').fill('test@example.com')
    await page.getByPlaceholder('密码').fill('password123')
    await page.getByPlaceholder('确认密码').fill('different123')
    await page.getByRole('button', { name: '下一步' }).click()

    // 应该显示密码不一致错误
    await expect(page.getByText('两次密码输入不一致')).toBeVisible()
  })

  test('有效表单应该显示验证码步骤', async ({ page }) => {
    // 填写有效表单
    await page.getByPlaceholder('用户名').fill('testuser')
    await page.getByPlaceholder('邮箱').fill('test@example.com')
    await page.getByPlaceholder('密码').fill('password123')
    await page.getByPlaceholder('确认密码').fill('password123')
    await page.getByRole('button', { name: '下一步' }).click()

    // 应该显示验证码输入
    await expect(page.getByPlaceholder('请输入验证码')).toBeVisible({ timeout: 5000 })
    // 应该显示返回修改按钮
    await expect(page.getByRole('button', { name: '返回修改' })).toBeVisible()
    // 应该显示注册按钮
    await expect(page.getByRole('button', { name: '注册' })).toBeVisible()
  })

  test('返回修改按钮应该回到表单编辑', async ({ page }) => {
    // 填写表单并进入验证码步骤
    await page.getByPlaceholder('用户名').fill('testuser')
    await page.getByPlaceholder('邮箱').fill('test@example.com')
    await page.getByPlaceholder('密码').fill('password123')
    await page.getByPlaceholder('确认密码').fill('password123')
    await page.getByRole('button', { name: '下一步' }).click()

    // 等待验证码步骤
    await expect(page.getByRole('button', { name: '返回修改' })).toBeVisible()

    // 点击返回修改
    await page.getByRole('button', { name: '返回修改' }).click()

    // 应该回到表单编辑状态
    await expect(page.getByRole('button', { name: '下一步' })).toBeVisible()
    // 表单值应该保留
    await expect(page.getByPlaceholder('用户名')).toHaveValue('testuser')
  })

  test('应该有返回登录链接', async ({ page }) => {
    const loginLink = page.getByText('已有账号？返回登录')
    await expect(loginLink).toBeVisible()

    await loginLink.click()
    await expect(page).toHaveURL(/\/login/)
  })

  test('密码可见性切换', async ({ page }) => {
    const passwordInput = page.getByPlaceholder('密码')
    await expect(passwordInput).toHaveAttribute('type', 'password')

    // 点击密码可见性切换按钮
    const toggleButton = page.locator('button').filter({ has: page.locator('svg') }).first()
    await toggleButton.click()

    // 密码应该变为可见
    await expect(passwordInput).toHaveAttribute('type', 'text')
  })

  test('应该在移动端正确显示', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    await expect(page.getByPlaceholder('用户名')).toBeVisible()
    await expect(page.getByPlaceholder('邮箱')).toBeVisible()
    await expect(page.getByRole('button', { name: '下一步' })).toBeVisible()
  })
})

// ============== T060: 用户登录流程测试 ==============
test.describe('用户登录流程 (T060)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
  })

  test('应该正确显示登录表单', async ({ page }) => {
    // 检查页面标题
    await expect(page.getByText('新闻爬虫系统')).toBeVisible()
    await expect(page.getByText('News Scraper Dashboard')).toBeVisible()

    // 检查表单元素
    await expect(page.getByPlaceholder('用户名')).toBeVisible()
    await expect(page.getByPlaceholder('密码')).toBeVisible()
    await expect(page.getByRole('button', { name: '下一步' })).toBeVisible()
  })

  test('空表单提交应该显示验证错误', async ({ page }) => {
    await page.getByRole('button', { name: '下一步' }).click()

    // 应该显示验证错误
    await expect(page.getByText('请输入用户名')).toBeVisible()
  })

  test('用户名长度验证', async ({ page }) => {
    await page.getByPlaceholder('用户名').fill('ab')
    await page.getByPlaceholder('密码').fill('password123')
    await page.getByRole('button', { name: '下一步' }).click()

    await expect(page.getByText('用户名至少3个字符')).toBeVisible()
  })

  test('有效凭证应该显示验证码步骤', async ({ page }) => {
    await page.getByPlaceholder('用户名').fill('testuser')
    await page.getByPlaceholder('密码').fill('password123')
    await page.getByRole('button', { name: '下一步' }).click()

    // 应该显示滑块验证码组件
    await expect(page.locator('.captcha-wrapper, [class*="captcha"]')).toBeVisible({ timeout: 5000 })
    // 应该显示返回修改按钮
    await expect(page.getByRole('button', { name: '返回修改' })).toBeVisible()
    // 应该显示登录按钮（但禁用状态直到验证码完成）
    await expect(page.getByRole('button', { name: '登录' })).toBeVisible()
  })

  test('返回修改按钮应该回到凭证输入', async ({ page }) => {
    await page.getByPlaceholder('用户名').fill('testuser')
    await page.getByPlaceholder('密码').fill('password123')
    await page.getByRole('button', { name: '下一步' }).click()

    await expect(page.getByRole('button', { name: '返回修改' })).toBeVisible()
    await page.getByRole('button', { name: '返回修改' }).click()

    // 应该回到凭证输入状态
    await expect(page.getByRole('button', { name: '下一步' })).toBeVisible()
    // 表单值应该保留
    await expect(page.getByPlaceholder('用户名')).toHaveValue('testuser')
  })

  test('密码可见性切换', async ({ page }) => {
    const passwordInput = page.getByPlaceholder('密码')
    await expect(passwordInput).toHaveAttribute('type', 'password')

    // 点击密码可见性切换按钮
    const toggleButton = page.locator('.relative button').first()
    await toggleButton.click()

    await expect(passwordInput).toHaveAttribute('type', 'text')
  })

  test('应该有注册链接', async ({ page }) => {
    const registerLink = page.getByText('没有账号？立即注册')
    await expect(registerLink).toBeVisible()

    await registerLink.click()
    await expect(page).toHaveURL(/\/register/)
  })

  test('应该在移动端正确显示', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    await expect(page.getByPlaceholder('用户名')).toBeVisible()
    await expect(page.getByPlaceholder('密码')).toBeVisible()
    await expect(page.getByRole('button', { name: '下一步' })).toBeVisible()
  })

  test('未验证时登录按钮应该禁用', async ({ page }) => {
    await page.getByPlaceholder('用户名').fill('testuser')
    await page.getByPlaceholder('密码').fill('password123')
    await page.getByRole('button', { name: '下一步' }).click()

    // 等待验证码步骤
    await expect(page.getByRole('button', { name: '登录' })).toBeVisible()
    // 登录按钮应该是禁用状态（因为验证码未完成）
    await expect(page.getByRole('button', { name: '登录' })).toBeDisabled()
  })

  test('页面应该没有 JavaScript 错误', async ({ page }) => {
    const errors: string[] = []

    page.on('pageerror', (error) => {
      errors.push(error.message)
    })

    await page.waitForLoadState('networkidle')

    expect(errors).toHaveLength(0)
  })
})

// ============== 认证流程集成测试 ==============
test.describe('认证流程集成', () => {
  test('未登录访问受保护页面应该跳转到登录', async ({ page }) => {
    // 清除可能存在的 token
    await page.addInitScript(() => {
      localStorage.clear()
    })

    // 尝试访问受保护页面
    await page.goto('/dashboard')

    // 应该被重定向到登录页面
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 })
  })

  test('登录页和注册页可以互相切换', async ({ page }) => {
    await page.goto('/login')

    // 点击注册链接
    await page.getByText('没有账号？立即注册').click()
    await expect(page).toHaveURL(/\/register/)

    // 点击返回登录链接
    await page.getByText('已有账号？返回登录').click()
    await expect(page).toHaveURL(/\/login/)
  })
})
