import { useCallback, useEffect, useState, type ComponentType, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
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
} from 'recharts'
import {
  RefreshCw,
  Briefcase,
  Banknote,
  Brain,
  Building2,
  Link2,
  Flame,
  Sparkles,
} from 'lucide-react'

import { api } from '../api'
import { TrendCharts } from '../components'
import EmptyState from '@/components/EmptyState'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { DashboardData } from '../types'

const PIE_COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#84cc16']
const BAR_COLOR = '#2563eb'

export default function SkillDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  // 初始化为 true，避免首次渲染闪烁空状态
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null)
  const navigate = useNavigate()

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.getDashboard()
      setData(res)
      setUpdatedAt(new Date())
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const jobs = data?.jobs
  const skills = data?.skills
  const trends = data?.trends

  const avgSalary = jobs ? Math.round((jobs.avg_salary_min + jobs.avg_salary_max) / 2) : 0

  // 空状态判定：从未加载成功过 或 核心指标均为 0
  const isDataEmpty = !data && !loading && !error
  const isMetricsEmpty = data && data.jobs.total_jobs === 0 && data.skills.total_skills === 0

  return (
    <div className="space-y-6">
      {/* 页面顶部标题与刷新按钮 */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold tracking-tight">技能图谱仪表盘</h2>
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? '加载中...' : '刷新'}
        </Button>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* 更新时间 */}
      {updatedAt && !loading && (
        <p className="text-xs text-muted-foreground">
          更新时间：{updatedAt.toLocaleString('zh-CN')}
        </p>
      )}

      {/* 空状态：引导用户创建画像 */}
      {(isDataEmpty || isMetricsEmpty) && (
        <EmptyState
          title="暂无仪表盘数据"
          description="当前还没有岗位和技能数据，请先创建一份技能画像，系统将为您生成分析看板。"
          action={{ label: '去创建画像', onClick: () => navigate('/match') }}
        />
      )}

      {/* 数据看板主体 */}
      {!isDataEmpty && !isMetricsEmpty && (
        <>
          {/* 核心指标卡片：4 列网格 */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="岗位总数"
              value={jobs?.total_jobs ?? 0}
              icon={Briefcase}
              loading={loading}
            />
            <StatCard
              label="平均薪资"
              value={avgSalary ? `¥${avgSalary.toLocaleString()}` : '-'}
              icon={Banknote}
              loading={loading}
              sub={
                jobs
                  ? `区间 ¥${jobs.avg_salary_min.toLocaleString()}-${jobs.avg_salary_max.toLocaleString()}`
                  : undefined
              }
            />
            <StatCard
              label="技能总数"
              value={skills?.total_skills ?? 0}
              icon={Brain}
              loading={loading}
            />
            <StatCard
              label="企业总数"
              value={jobs?.total_companies ?? 0}
              icon={Building2}
              loading={loading}
            />
          </div>

          {/* 次要指标卡片：放在核心指标下方 */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <StatCard
              label="技能关系数"
              value={skills?.total_relations ?? 0}
              icon={Link2}
              loading={loading}
            />
            <StatCard
              label="热门岗位"
              value={trends?.hot_job_titles?.length ?? 0}
              icon={Flame}
              loading={loading}
            />
            <StatCard
              label="热门技能"
              value={trends?.top_skills?.length ?? 0}
              icon={Sparkles}
              loading={loading}
            />
          </div>

          {/* 城市分布与经验分布：通过 TrendCharts 渲染 */}
          {!loading && (
            <TrendCharts
              topCities={jobs?.top_cities}
              experienceDistribution={jobs?.experience_distribution}
            />
          )}

          {/* 图表区域：热门技能饼图 + 行业分布柱状图 */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {loading ? (
              <>
                <Skeleton className="h-[360px] w-full rounded-lg" />
                <Skeleton className="h-[360px] w-full rounded-lg" />
              </>
            ) : (
              <>
                {/* 热门技能饼图 */}
                <Card>
                  <CardHeader>
                    <CardTitle>热门技能分布</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {jobs?.hot_skills?.length ? (
                      <ResponsiveContainer width="100%" height={260}>
                        <PieChart>
                          <Pie
                            data={jobs.hot_skills.slice(0, 8)}
                            dataKey="count"
                            nameKey="skill"
                            cx="50%"
                            cy="50%"
                            outerRadius={90}
                            label={({ name, percent }) =>
                              `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
                            }
                          >
                            {jobs.hot_skills.slice(0, 8).map((_, i) => (
                              <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="py-12 text-center text-muted-foreground">暂无数据</p>
                    )}
                  </CardContent>
                </Card>

                {/* 行业分布柱状图 */}
                <Card>
                  <CardHeader>
                    <CardTitle>行业需求分布</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {jobs?.top_industries?.length ? (
                      <ResponsiveContainer width="100%" height={260}>
                        <BarChart data={jobs.top_industries} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" />
                          <YAxis
                            dataKey="industry"
                            type="category"
                            tick={{ fontSize: 12 }}
                            width={80}
                          />
                          <Tooltip />
                          <Bar
                            dataKey="count"
                            fill={BAR_COLOR}
                            radius={[0, 4, 4, 0]}
                            name="岗位数"
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="py-12 text-center text-muted-foreground">暂无数据</p>
                    )}
                  </CardContent>
                </Card>
              </>
            )}
          </div>

          {/* 市场趋势洞察 */}
          {!loading && trends?.summary && (
            <Card>
              <CardHeader>
                <CardTitle>市场趋势洞察</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="leading-relaxed text-muted-foreground">{trends.summary}</p>
                {trends.avg_salary_range && (
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">主流薪资范围</Badge>
                    <span className="font-medium">{trends.avg_salary_range}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* 热门岗位 TOP10：带排名数字 */}
          {!loading && trends?.hot_job_titles?.length ? (
            <Card>
              <CardHeader>
                <CardTitle>热门岗位 TOP10</CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="space-y-3">
                  {trends.hot_job_titles.slice(0, 10).map((title, idx) => (
                    <li key={idx} className="flex items-center gap-3">
                      <Badge
                        variant={idx < 3 ? 'default' : 'secondary'}
                        className="h-6 w-6 justify-center rounded-full p-0"
                      >
                        {idx + 1}
                      </Badge>
                      <span className="text-sm font-medium">{title}</span>
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          ) : null}
        </>
      )}
    </div>
  )
}

// 统计卡片组件：统一处理加载骨架与数字展示
interface StatCardProps {
  label: string
  value: ReactNode
  icon?: ComponentType<{ className?: string }>
  loading?: boolean
  sub?: string
}

function StatCard({ label, value, icon: Icon, loading, sub }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription className="flex items-center gap-2">
          {Icon && <Icon className="h-4 w-4" />}
          {label}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-9 w-28" />
        ) : (
          <>
            <div className="text-3xl font-bold">{value}</div>
            {sub && <p className="mt-1 text-xs text-muted-foreground">{sub}</p>}
          </>
        )}
      </CardContent>
    </Card>
  )
}
