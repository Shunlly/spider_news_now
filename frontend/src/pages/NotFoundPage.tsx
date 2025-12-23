/**
 * HUD 风格 404 页面
 * HUD-style Not Found Page
 */

import { useNavigate } from 'react-router-dom'
import { Home, ArrowLeft, AlertTriangle } from 'lucide-react'
import { StoneButton } from '../components/ui'

export default function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 relative overflow-hidden">
      {/* 背景网格 */}
      <div
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(6, 182, 212, 0.5) 1px, transparent 1px),
            linear-gradient(90deg, rgba(6, 182, 212, 0.5) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px',
        }}
      />

      {/* 背景发光 */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-red-500/5 rounded-full blur-[120px]" />

      <div className="text-center max-w-md relative z-10">
        {/* 警告图标 */}
        <div className="mb-6 flex justify-center">
          <div className="p-4 rounded-full bg-red-500/10 border border-red-500/30">
            <AlertTriangle className="w-8 h-8 text-red-400" />
          </div>
        </div>

        {/* 404 数字 */}
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-transparent bg-clip-text bg-gradient-to-b from-slate-600 to-slate-800 select-none font-mono tracking-wider">
            404
          </h1>
          <div className="h-1 w-32 mx-auto bg-gradient-to-r from-transparent via-red-500/50 to-transparent" />
        </div>

        {/* 标题和描述 */}
        <h2 className="text-2xl font-bold text-red-400 mb-3 tracking-wide uppercase">
          页面未找到
        </h2>
        <p className="text-slate-500 mb-8">
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
        <div className="mt-12 pt-8 border-t border-slate-800">
          <p className="text-xs text-slate-600 mb-4 uppercase tracking-wider">或者尝试以下页面</p>
          <div className="flex flex-wrap gap-2 justify-center">
            {[
              { path: '/dashboard', label: '仪表盘' },
              { path: '/news', label: '新闻管理' },
              { path: '/social', label: '社交媒体' },
              { path: '/settings', label: '设置' },
            ].map((link) => (
              <button
                key={link.path}
                onClick={() => navigate(link.path)}
                className="text-sm text-slate-500 hover:text-cyan-400 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-cyan-500/30 hover:shadow-[0_0_10px_rgba(6,182,212,0.2)] transition-all"
              >
                {link.label}
              </button>
            ))}
          </div>
        </div>

        {/* 错误代码 */}
        <div className="mt-8 text-xs text-slate-700 font-mono">
          ERROR_CODE: PAGE_NOT_FOUND | STATUS: 404
        </div>
      </div>

      {/* 扫描线效果 */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div
          className="absolute inset-0 bg-gradient-to-b from-transparent via-red-500/5 to-transparent"
          style={{
            animation: 'scanline 4s linear infinite',
          }}
        />
      </div>

      <style>{`
        @keyframes scanline {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(100%); }
        }
      `}</style>
    </div>
  )
}
