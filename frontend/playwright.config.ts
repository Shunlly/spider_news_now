/**
 * Playwright E2E 测试配置
 * Playwright E2E Test Configuration
 */

import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  // 测试目录
  testDir: './e2e',

  // 测试超时时间
  timeout: 30 * 1000,

  // 期望断言超时
  expect: {
    timeout: 5000,
  },

  // 并行执行
  fullyParallel: true,

  // CI 模式下禁止 .only
  forbidOnly: !!process.env.CI,

  // 失败重试次数
  retries: process.env.CI ? 2 : 0,

  // 并行 worker 数量
  workers: process.env.CI ? 1 : undefined,

  // 测试报告
  reporter: 'html',

  // 全局配置
  use: {
    // 基础 URL
    baseURL: 'http://localhost:5173',

    // 追踪失败的测试
    trace: 'on-first-retry',

    // 截图
    screenshot: 'only-on-failure',

    // 视频
    video: 'on-first-retry',
  },

  // 项目配置
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // 开发服务器
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
})
