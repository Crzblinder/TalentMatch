import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const PIE_COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#84cc16']

export interface TrendChartsProps {
  topSkills?: Array<{ skill: string; count: number }>
  topCities?: Array<{ city: string; count: number }>
  salaryDistribution?: Array<{ range: string; value: number }>
  experienceDistribution?: Array<{ experience_level: string; count: number }>
}

interface ChartItem {
  key: string
  title: string
  content: React.ReactNode
}

export default function TrendCharts({
  topSkills,
  topCities,
  salaryDistribution,
  experienceDistribution,
}: TrendChartsProps) {
  const charts: ChartItem[] = []

  if (topSkills?.length) {
    charts.push({
      key: 'topSkills',
      title: '技能热度排行 TOP10',
      content: (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={topSkills} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="skill" type="category" tick={{ fontSize: 12 }} width={90} />
            <Tooltip />
            <Bar dataKey="count" fill="#2563eb" radius={[0, 4, 4, 0]} name="出现次数" />
          </BarChart>
        </ResponsiveContainer>
      ),
    })
  }

  if (topCities?.length) {
    charts.push({
      key: 'topCities',
      title: '城市需求分布 TOP10',
      content: (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={topCities}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="city" tick={{ fontSize: 12 }} />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} name="岗位数" />
          </BarChart>
        </ResponsiveContainer>
      ),
    })
  }

  if (salaryDistribution?.length) {
    charts.push({
      key: 'salaryDistribution',
      title: '薪资分布',
      content: (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={salaryDistribution}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="range" tick={{ fontSize: 12 }} />
            <YAxis />
            <Tooltip formatter={(value) => `¥${Number(value).toLocaleString()}`} />
            <Bar dataKey="value" fill="#22c55e" radius={[4, 4, 0, 0]} name="薪资（元/月）" />
          </BarChart>
        </ResponsiveContainer>
      ),
    })
  }

  if (experienceDistribution?.length) {
    charts.push({
      key: 'experienceDistribution',
      title: '经验要求分布',
      content: (
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={experienceDistribution}
              dataKey="count"
              nameKey="experience_level"
              cx="50%"
              cy="50%"
              outerRadius={100}
              label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
            >
              {experienceDistribution.map((_, i) => (
                <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      ),
    })
  }

  const rows: React.ReactNode[] = []
  for (let i = 0; i < charts.length; i += 2) {
    rows.push(
      <div key={i} className="chart-row">
        {charts.slice(i, i + 2).map((chart) => (
          <Card key={chart.key} className="chart-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">{chart.title}</CardTitle>
            </CardHeader>
            <CardContent>{chart.content}</CardContent>
          </Card>
        ))}
      </div>,
    )
  }

  return <>{rows}</>
}
