import { useCallback, useEffect, useMemo, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { api } from '../api'
import { TrendCharts } from '../components'
import type { DashboardData, TrendAnalysis as TrendData } from '../types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

// 将趋势中的技能名称与仪表板的热度计数对齐
function normalizeTopSkills(skills: string[] | null | undefined, hotSkills: { skill: string; count: number }[]) {
  if (!skills?.length) return hotSkills.slice(0, 10)
  return skills.map((name) => {
    const found = hotSkills.find((h) => h.skill === name)
    return { skill: name, count: found?.count ?? 1 }
  })
}

export default function TrendAnalysis() {
  const [trend, setTrend] = useState<TrendData | null>(null)
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [trendRes, dashboardRes] = await Promise.all([
        api.getTrends().catch((e) => { setError((prev) => prev || e.message); return null }),
        api.getDashboard().catch((e) => { setError((prev) => prev || e.message); return null }),
      ])
      if (trendRes) setTrend(trendRes)
      if (dashboardRes) setDashboard(dashboardRes)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const topSkills = useMemo(
    () => normalizeTopSkills(trend?.top_skills, dashboard?.jobs.hot_skills || []),
    [trend, dashboard],
  )

  const salaryDistribution = useMemo(() => {
    const jobs = dashboard?.jobs
    if (!jobs) return []
    return [
      { range: '最低平均', value: jobs.avg_salary_min },
      { range: '最高平均', value: jobs.avg_salary_max },
    ]
  }, [dashboard])

  // 关键指标配置
  const metrics = useMemo(
    () => [
      { label: '岗位总数', value: dashboard?.jobs.total_jobs ?? '-' },
      {
        label: '平均薪资下限',
        value: dashboard ? `¥${dashboard.jobs.avg_salary_min.toLocaleString()}` : '-',
      },
      {
        label: '平均薪资上限',
        value: dashboard ? `¥${dashboard.jobs.avg_salary_max.toLocaleString()}` : '-',
      },
      { label: '主流薪资范围', value: trend?.avg_salary_range ?? '-' },
    ],
    [dashboard, trend],
  )

  // 首次加载无数据时展示骨架屏
  const showSkeleton = loading && !trend && !dashboard

  return (
    <div className="space-y-6">
      {/* 页面标题与刷新按钮 */}
      <div className="page-header">
        <h2>岗位趋势分析</h2>
        <Button onClick={load} disabled={loading} size="sm">
          <RefreshCw className={`mr-1 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? '加载中...' : '刷新'}
        </Button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {showSkeleton ? (
        <div className="space-y-6">
          <Skeleton className="h-32 w-full" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-28 w-full" />
            ))}
          </div>
          <Skeleton className="h-64 w-full" />
        </div>
      ) : (
        <>
          {/* 趋势摘要 */}
          {trend?.summary && (
            <Card className="border-l-4 border-l-primary">
              <CardHeader>
                <CardTitle className="text-lg">趋势摘要</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="leading-relaxed text-muted-foreground">{trend.summary}</p>
              </CardContent>
            </Card>
          )}

          {/* 关键指标 4 列网格 */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {metrics.map((m) => (
              <Card key={m.label}>
                <CardContent className="pt-6">
                  <div className="text-sm text-muted-foreground">{m.label}</div>
                  <div className="mt-1 text-3xl font-bold">{m.value}</div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* 图表区域：使用 TrendCharts 组件 */}
          <TrendCharts
            topSkills={topSkills}
            topCities={dashboard?.jobs.top_cities}
            salaryDistribution={salaryDistribution}
            experienceDistribution={dashboard?.jobs.experience_distribution}
          />

          {/* 关键指标表格 */}
          {trend?.key_metrics && Object.keys(trend.key_metrics).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">关键指标</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>指标</TableHead>
                      <TableHead>数值</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(trend.key_metrics).map(([key, value]) => (
                      <TableRow key={key}>
                        <TableCell>{key}</TableCell>
                        <TableCell>
                          {typeof value === 'number' ? value.toLocaleString() : String(value)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {/* 热门岗位排行榜 */}
          {trend?.hot_job_titles?.length ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">热门岗位</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-2">
                  {trend.hot_job_titles.map((title, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-3 rounded-md border p-3 text-sm hover:bg-muted/50"
                    >
                      <Badge
                        variant="secondary"
                        className={
                          idx < 3
                            ? 'bg-rose-100 text-rose-600 hover:bg-rose-100'
                            : 'bg-muted'
                        }
                      >
                        {idx + 1}
                      </Badge>
                      <span className="flex-1 font-medium">{title}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ) : null}
        </>
      )}
    </div>
  )
}
