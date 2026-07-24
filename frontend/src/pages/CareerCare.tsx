import { useEffect, useState } from 'react'
import { RefreshCw, Lightbulb, Heart, TrendingUp, Target, Clock } from 'lucide-react'

import { api } from '@/api'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useProfile } from '@/components/ProfileContext'
import type { CareDashboard } from '@/types'

export default function CareerCare() {
  const { effectiveProfile } = useProfile()
  const [data, setData] = useState<CareDashboard | null>(null)
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    setLoading(true)
    try {
      const result = await api.getCareDashboard(effectiveProfile?.id)
      setData(result)
    } catch (err) {
      console.error('Failed to load care dashboard:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [effectiveProfile?.id])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground">求职关怀</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            求职路上你不是一个人，这里有一些鼓励和实用建议
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={loadData} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          换一条
        </Button>
      </div>

      {/* 今日鼓励语 */}
      {data?.daily_quote && (
        <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-secondary/5">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Heart className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">今日鼓励</CardTitle>
              <Badge variant="secondary" className="ml-auto">{data.daily_quote.category}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-base leading-relaxed text-foreground">
              {data.daily_quote.text}
            </p>
            {data.daily_quote.scene && (
              <p className="mt-2 text-xs text-muted-foreground">
                适用场景：{data.daily_quote.scene}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* 数据统计 */}
      {data?.stats && (
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>岗位库总量</CardDescription>
              <CardTitle className="text-2xl">{data.stats.total_jobs}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>应届友好岗位</CardDescription>
              <CardTitle className="text-2xl text-primary">{data.stats.fresh_friendly_jobs}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>应届友好占比</CardDescription>
              <CardTitle className="text-2xl text-primary">{data.stats.fresh_friendly_ratio}%</CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      {/* 实用建议 */}
      {data?.tips && data.tips.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-amber-500" />
              <CardTitle className="text-lg">实用建议</CardTitle>
            </div>
            <CardDescription>针对毕业生求职过程中的实际困境</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.tips.map((tip, idx) => (
              <div key={idx} className="rounded-lg border p-4">
                <div className="mb-2 flex items-center gap-2">
                  <Target className="h-4 w-4 text-primary" />
                  <h3 className="font-semibold text-foreground">{tip.title}</h3>
                  <Badge variant="outline" className="ml-auto">{tip.category}</Badge>
                  <Badge variant={tip.difficulty === 'easy' ? 'secondary' : 'default'}>
                    {tip.difficulty === 'easy' ? '入门' : '进阶'}
                  </Badge>
                </div>
                <p className="text-sm leading-relaxed text-muted-foreground">{tip.content}</p>
                <div className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  预计耗时：{tip.estimated_time}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* 求职阶段指南 */}
      {data?.stages && data.stages.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">求职阶段指南</CardTitle>
            </div>
            <CardDescription>从准备到入职，每一步都有清晰的行动方向</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.stages.map((stage, idx) => (
              <div key={idx} className="rounded-lg border p-4">
                <div className="mb-3 flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
                    {idx + 1}
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground">{stage.stage}</h3>
                    <p className="text-xs text-muted-foreground">建议周期：{stage.duration}</p>
                  </div>
                </div>
                <ul className="mb-3 space-y-1 pl-11">
                  {stage.tasks.map((task, i) => (
                    <li key={i} className="text-sm text-muted-foreground">
                      • {task}
                    </li>
                  ))}
                </ul>
                <div className="rounded bg-secondary/50 p-3 text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">小贴士：</span> {stage.tips}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* 个人画像信息 */}
      {data?.profile && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">你的画像</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">姓名：</span>
                <span className="font-medium text-foreground">{data.profile.name}</span>
              </div>
              <div>
                <span className="text-muted-foreground">经验等级：</span>
                <Badge variant="secondary">{data.profile.experience_level}</Badge>
              </div>
              <div>
                <span className="text-muted-foreground">技能数：</span>
                <span className="font-medium text-foreground">{data.profile.skills_count}</span>
              </div>
              <div>
                <span className="text-muted-foreground">目标岗位：</span>
                {data.profile.target_job_titles.map((title, i) => (
                  <Badge key={i} variant="outline" className="mr-1">{title}</Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
