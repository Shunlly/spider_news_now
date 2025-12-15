/**
 * 根应用组件
 * Root Application Component
 */

import { Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider } from '@arco-design/web-react'
import MainLayout from './layouts/MainLayout'
import DashboardPage from './pages/DashboardPage'
import NewsPage from './pages/NewsPage'
import SocialPage from './pages/SocialPage'
import TelegramPage from './pages/TelegramPage'
import SearchPage from './pages/SearchPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <ConfigProvider
      componentConfig={{
        // Arco Design 全局配置
        Card: {
          bordered: false,
        },
        Table: {
          border: false,
          stripe: true,
        },
      }}
    >
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="news" element={<NewsPage />} />
          <Route path="social" element={<SocialPage />} />
          <Route path="telegram" element={<TelegramPage />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </ConfigProvider>
  )
}

export default App
