/**
 * 饼图实现组件
 * Pie Chart Implementation (contains recharts imports)
 */

import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from 'recharts'

// 默认颜色
const DEFAULT_COLORS = ['#78716c', '#57534e', '#44403c', '#292524', '#a8a29e', '#d6d3d1']

interface SourceData {
  name: string
  value: number
  color?: string
}

interface Props {
  data: SourceData[]
}

export default function SourcePieChartImpl({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={50}
          outerRadius={80}
          paddingAngle={2}
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e7e5e4',
            borderRadius: '12px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          }}
          itemStyle={{ color: '#44403c' }}
          labelStyle={{ color: '#1c1917', fontWeight: 'bold', marginBottom: '4px' }}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
