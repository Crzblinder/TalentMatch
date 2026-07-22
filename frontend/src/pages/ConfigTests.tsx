import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Database,
  FileText,
  Globe,
  Loader2,
  RefreshCw,
  Search,
  Shield,
  SkipForward,
  Terminal,
  XCircle,
} from 'lucide-react'

import { api } from '../api'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import type { ConfigTestReport, ConfigTestItem } from '../types'

const CATEGORY_META: Record<string, { label: string; icon: typeof Activity; color: string }> = {
  database: { label: '数据库', icon: Database, color: 'text-blue-500' },
  vector: { label: '向量数据库', icon: Database, color: 'text-indigo-500' },
  llm: { label: '大语言模型', icon: Terminal, color: 'text-violet-500' },
  search: { label: '联网搜索', icon: Search, color: 'text-cyan-500' },
  parse: { label: '文档解析', icon: FileText, color: 'text-amber-500' },
  crawler: { label: '招聘平台抓取', icon: Globe, color: 'text-emerald-500' },
  safety: { label: '内容安全', icon: Shield, color: 'text-rose-500' },
}

function StatusIcon({ status }: { status: ConfigTestItem['status'] }) {
  switch (status) {
    case 'ok':
      return <CheckCircle2 className="h-5 w-5 text-green-500" />
    case 'fail':
      return <XCircle className="h-5 w-5 text-red-500" />
    case 'skip':
      return <SkipForward className="h-5 w-5 text-slate-400" />
    default:
      return <AlertCircle className="h-5 w-5 text-slate-400" />
  }
}

function StatusBadge({ status }: { status: ConfigTestItem['status'] }) {
  const variants: Record<ConfigTestItem['status'], string> = {
    ok: 'bg-green-100 text-green-700 hover:bg-green-100',
    fail: 'bg-red-100 text-red-700 hover:bg-red-100',
    skip: 'bg-slate-100 text-slate-600 hover:bg-slate-100',
  }
  const labels = { ok: '通过', fail: '失败', skip: '跳过' }
  return <Badge className={variants[status]}>{labels[status]}</Badge>
}

function MetricCard({
  title,
  value,
  icon: Icon,
  className,
}: {
  title: string
  value: number
  icon: typeof Activity
  className?: string
}) {
  return (
    <Card className={className}>
      <CardContent className="flex items-center justify-between p-6">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="mt-1 text-3xl font-bold">{value}</p>
        </div>
        <Icon className="h-8 w-8 text-muted-foreground/50" />
      </CardContent>
    </Card>
  )
}

function TestResultCard({ item }: { item: ConfigTestItem }) {
  const [expanded, setExpanded] = useState(false)
  const meta = CATEGORY_META[item.category] || {
    label: item.category,
    icon: Activity,
    color: 'text-slate-500',
  }
  const Icon = meta.icon
  const hasDetail = item.detail && Object.keys(item.detail).length > 0

  return (
    <Card className="overflow-hidden transition-shadow hover:shadow-sm">
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          <div className={`mt-0.5 ${meta.color}`}>
            <Icon className="h-5 w-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h4 className="font-semibold">{item.name}</h4>
                <p className="text-xs text-muted-foreground mt-0.5">{meta.label}</p>
              </div>
              <StatusBadge status={item.status} />
            </div>
            <p className="mt-2 text-sm text-slate-700 break-words">{item.message}</p>
            <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
              <span>耗时 {item.response_time_ms.toFixed(0)} ms</span>
              <span>{item.configured ? '已配置' : '未配置'}</span>
            </div>
            {hasDetail && (
              <div className="mt-2">
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="flex items-center text-xs text-primary hover:underline"
                >
                  {expanded ? (
                    <>
                      <ChevronUp className="mr-1 h-3 w-3" /> 收起详情
                    </>
                  ) : (
                    <>
                      <ChevronDown className="mr-1 h-3 w-3" /> 查看详情
                    </>
                  )}
                </button>
                {expanded && (
                  <pre className="mt-2 max-h-40 overflow-auto rounded-md bg-slate-50 p-3 text-xs text-slate-700">
                    {JSON.stringify(item.detail, null, 2)}
                  </pre>
                )}
              </div>
            )}
          </div>
          <div className="hidden sm:block">
            <StatusIcon status={item.status} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default function ConfigTests() {
  const [report, setReport] = useState<ConfigTestReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [activeCategory, setActiveCategory] = useState<string>('all')

  const runTests = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await api.getConfigTests()
      setReport(data)
    } catch (e: any) {
      setError(e.message || '检测失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    runTests()
  }, [runTests])

  const categories = useMemo(() => {
    if (!report) return []
    const set = new Set(report.results.map((r) => r.category))
    return Array.from(set).sort()
  }, [report])

  const filteredResults = useMemo(() => {
    if (!report) return []
    if (activeCategory === 'all') return report.results
    return report.results.filter((r) => r.category === activeCategory)
  }, [report, activeCategory])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">外部配置可用性检测</h2>
          <p className="text-sm text-muted-foreground mt-1">
            自动检测 LLM、搜索、文档解析、招聘平台抓取、内容安全等外部服务是否可用
          </p>
        </div>
        <Button onClick={runTests} disabled={loading}>
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
          {loading ? '检测中...' : '重新检测'}
        </Button>
      </div>

      {/* Summary */}
      {loading && !report ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : report ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard title="总检测项" value={report.total} icon={Activity} />
          <MetricCard
            title="通过"
            value={report.passed}
            icon={CheckCircle2}
            className="border-green-200/60 bg-green-50/30"
          />
          <MetricCard
            title="失败"
            value={report.failed}
            icon={XCircle}
            className="border-red-200/60 bg-red-50/30"
          />
          <MetricCard
            title="跳过"
            value={report.skipped}
            icon={SkipForward}
            className="border-slate-200/60 bg-slate-50/30"
          />
        </div>
      ) : null}

      {/* Timestamp & error */}
      {report?.tested_at && (
        <p className="text-xs text-muted-foreground">
          检测时间：{new Date(report.tested_at).toLocaleString('zh-CN')}
        </p>
      )}
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            <span>检测出错：{error}</span>
          </div>
        </div>
      )}

      {/* Category filter */}
      {categories.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <Button
            variant={activeCategory === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveCategory('all')}
          >
            全部
          </Button>
          {categories.map((cat) => {
            const meta = CATEGORY_META[cat]
            return (
              <Button
                key={cat}
                variant={activeCategory === cat ? 'default' : 'outline'}
                size="sm"
                onClick={() => setActiveCategory(cat)}
              >
                {meta?.label || cat}
              </Button>
            )
          })}
        </div>
      )}

      {/* Results list */}
      <div className="space-y-3">
        {loading && report
          ? Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32" />)
          : filteredResults.map((item, idx) => <TestResultCard key={`${item.name}-${idx}`} item={item} />)}
      </div>

      {!loading && filteredResults.length === 0 && !error && (
        <div className="rounded-md border border-dashed p-8 text-center text-sm text-muted-foreground">
          暂无检测结果，点击上方「重新检测」开始
        </div>
      )}
    </div>
  )
}
