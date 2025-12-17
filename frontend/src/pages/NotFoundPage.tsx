/**
 * 404 页面
 * Not Found Page
 */

import { useNavigate } from 'react-router-dom'
import { Home, ArrowLeft } from 'lucide-react'
import { StoneButton } from '../components/ui'

export default function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-stone-200 flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        {/* 404 数字 */}
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-stone-300 select-none">
            404
          </h1>
        </div>

        {/* 标题和描述 */}
        <h2 className="text-2xl font-semibold text-stone-900 mb-3">
          页面未找到
        </h2>
        <p className="text-stone-600 mb-8">
          抱歉，您访问的页面不存在或已被移动。请检查 URL 或返回首页。
        </p>

        {/* 操作按钮 */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <StoneButton
            variant="secondary"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回上页
          </StoneButton>

          <StoneButton
            variant="primary"
            onClick={() => navigate('/')}
          >
            <Home className="w-4 h-4 mr-2" />
            返回首页
          </StoneButton>
        </div>

        {/* 快速链接 */}
        <div className="mt-12 pt-8 border-t border-stone-300">
          <p className="text-sm text-stone-500 mb-4">或者尝试以下页面：</p>
          <div className="flex flex-wrap gap-2 justify-center">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-sm text-stone-600 hover:text-stone-900 px-3 py-1 rounded-lg hover:bg-stone-100 transition-colors"
            >
              仪表盘
            </button>
            <button
              onClick={() => navigate('/news')}
              className="text-sm text-stone-600 hover:text-stone-900 px-3 py-1 rounded-lg hover:bg-stone-100 transition-colors"
            >
              新闻管理
            </button>
            <button
              onClick={() => navigate('/social')}
              className="text-sm text-stone-600 hover:text-stone-900 px-3 py-1 rounded-lg hover:bg-stone-100 transition-colors"
            >
              社交媒体
            </button>
            <button
              onClick={() => navigate('/settings')}
              className="text-sm text-stone-600 hover:text-stone-900 px-3 py-1 rounded-lg hover:bg-stone-100 transition-colors"
            >
              设置
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
