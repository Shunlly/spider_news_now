/**
 * HUD 风格懒加载饼图组件
 * HUD-style Lazy-loaded Pie Chart Component
 *
 * 将 recharts 动态导入以减少初始 bundle 大小
 */

import { Suspense, lazy } from 'react'
import { Loader2 } from 'lucide-react'

interface SourceData {
  name: string
  value: number
  color?: string
}

interface SourcePieChartProps {
  data: SourceData[]
}

// 图表加载占位符 - HUD 风格
function ChartLoading() {
  return (
    <div className="w-full h-[200px] flex items-center justify-center">
      <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
    </div>
  )
}

// 懒加载的图表实现
const LazyChartImpl = lazy(() => import('./SourcePieChartImpl'))

// 导出的懒加载饼图组件
export default function SourcePieChart({ data }: SourcePieChartProps) {
  return (
    <Suspense fallback={<ChartLoading />}>
      <LazyChartImpl data={data} />
    </Suspense>
  )
}

export type { SourceData, SourcePieChartProps }
