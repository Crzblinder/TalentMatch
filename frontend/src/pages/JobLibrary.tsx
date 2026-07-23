import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import type { Job, UserSkillProfile } from '../types'

// shadcn/ui 组件导入
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { toast } from 'sonner'
import JobCompareSheet from '@/components/JobCompareSheet'

// 图标导入
import {
  ArrowUpDown,
  ChevronDown,
  ChevronUp,
  Heart,
  Scale,
  Search,
  X,
} from 'lucide-react'

// 经验级别选项
const EXPERIENCE_LEVELS = ['不限', '应届生', '1-3年', '3-5年', '5-10年', '10年以上']

// 筛选条件类型
interface Filters {
  search: string
  city: string
  industry: string
  experienceLevel: string
}

// 排序字段类型
 type SortKey = 'salary_min' | 'posted_at' | 'match_score'

// 排序方向类型
type SortDirection = 'asc' | 'desc'

export default function JobLibrary() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  // 当前用户画像：系统无登录，使用已有画像列表中的第一个作为当前用户
  const [currentProfile, setCurrentProfile] = useState<UserSkillProfile | null>(null)
  const [profilesLoading, setProfilesLoading] = useState(false)

  // 岗位列表与分页状态
  const [jobs, setJobs] = useState<Job[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const pageSize = 15

  // 筛选条件状态
  const [filters, setFilters] = useState<Filters>({
    search: '',
    city: '',
    industry: '',
    experienceLevel: '',
  })

  // 是否只展示我的收藏（通过 URL ?favorites=1 进入）
  const showFavoritesOnly = searchParams.get('favorites') === '1'

  // 加载与错误状态
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // 岗位详情抽屉状态
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailOpen, setDetailOpen] = useState(false)

  // 岗位对比状态：记录已选中的岗位对象，最多 3 个
  const [compareMap, setCompareMap] = useState<Record<number, Job>>({})
  const [compareOpen, setCompareOpen] = useState(false)

  // 收藏状态：从后端加载当前画像的收藏岗位
  const [favoriteIds, setFavoriteIds] = useState<Set<number>>(new Set())
  const [favoriteJobs, setFavoriteJobs] = useState<Job[]>([])
  const [favoritesLoading, setFavoritesLoading] = useState(false)

  // 表格排序状态
  const [sortConfig, setSortConfig] = useState<{ key: SortKey; direction: SortDirection } | null>(null)

  // 加载用户画像列表，并将第一个设为当前画像（作为当前用户）
  useEffect(() => {
    let cancelled = false
    setProfilesLoading(true)
    api.listProfiles()
      .then((res) => {
        if (cancelled) return
        if (res.items.length > 0) {
          // 优先使用后台标记的活跃画像，其次使用列表第一个
          const active = res.items.find((p) => p.is_active)
          setCurrentProfile((prev) => prev || active || res.items[0])
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e.message)
      })
      .finally(() => {
        if (!cancelled) setProfilesLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  // 加载当前画像的收藏列表
  const loadFavorites = useCallback(async () => {
    if (!currentProfile) return
    setFavoritesLoading(true)
    try {
      const res = await api.listFavorites(currentProfile.id)
      const jobsFromFavorites = res.items
        .map((item) => item.job)
        .filter((job): job is Job => job !== null)
      setFavoriteJobs(jobsFromFavorites)
      setFavoriteIds(new Set(jobsFromFavorites.map((job) => job.id)))
    } catch (e: any) {
      setError(e.message)
    } finally {
      setFavoritesLoading(false)
    }
  }, [currentProfile])

  useEffect(() => {
    loadFavorites()
  }, [loadFavorites, showFavoritesOnly])

  // 加载岗位列表数据
  const load = useCallback(async (p: number) => {
    setLoading(true)
    setError('')
    try {
      if (showFavoritesOnly) {
        // 我的收藏模式：直接展示已收藏的岗位，并做前端分页
        const start = (p - 1) * pageSize
        setJobs(favoriteJobs.slice(start, start + pageSize))
        setTotal(favoriteJobs.length)
      } else {
        const res = await api.listJobs({
          page: p,
          size: pageSize,
          q: filters.search || undefined,
          city: filters.city || undefined,
          industry: filters.industry || undefined,
          experience_level: filters.experienceLevel || undefined,
        })
        setJobs(res.items)
        setTotal(res.total)
      }
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [filters, pageSize, showFavoritesOnly, favoriteJobs])

  // 当页码、筛选条件或收藏数据变化时重新加载数据
  useEffect(() => {
    load(page)
  }, [load, page])

  // 更新单个筛选条件并重置到第一页
  const updateFilter = (key: keyof Filters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
    setPage(1)
  }

  // 执行筛选
  const handleSearch = () => {
    setPage(1)
  }

  // 清空所有筛选条件
  const clearFilters = () => {
    setFilters({ search: '', city: '', industry: '', experienceLevel: '' })
    setPage(1)
  }

  // 最大页码
  const maxPage = Math.max(1, Math.ceil(total / pageSize))

  // 已启用的筛选数量
  const activeFilterCount = Object.values(filters).filter(Boolean).length

  // 打开岗位详情抽屉并加载详情
  const openDetail = (job: Job) => {
    setDetailOpen(true)
    setSelectedJob(null)
    setDetailLoading(true)
    api
      .getJob(job.id)
      .then(setSelectedJob)
      .catch((e) => setError(e.message))
      .finally(() => setDetailLoading(false))
  }

  // 关闭岗位详情抽屉
  const closeDetail = () => {
    setDetailOpen(false)
    setSelectedJob(null)
    setDetailLoading(false)
  }

  // 切换岗位对比选中状态，最多选择 3 个，超出时提示
  const toggleCompare = (job: Job) => {
    setCompareMap((prev) => {
      if (prev[job.id]) {
        const next = { ...prev }
        delete next[job.id]
        return next
      }
      if (Object.keys(prev).length >= 3) {
        toast.error('最多可选择 3 个岗位进行对比')
        return prev
      }
      return { ...prev, [job.id]: job }
    })
  }

  // 关闭对比抽屉并清空选择
  const closeCompare = () => {
    setCompareOpen(false)
    setCompareMap({})
  }

  // 切换收藏状态：调用后端接口实现持久化
  const toggleFavorite = async (id: number) => {
    if (!currentProfile) {
      toast.error('暂无用户画像，无法收藏')
      return
    }
    const isFavorite = favoriteIds.has(id)
    try {
      if (isFavorite) {
        await api.removeFavorite(currentProfile.id, id)
        toast.success('已取消收藏')
      } else {
        await api.addFavorite(currentProfile.id, id)
        toast.success('收藏成功')
      }
      // 操作成功后刷新后端收藏状态
      await loadFavorites()
    } catch (e: any) {
      toast.error(e.message || '操作失败')
    }
  }

  // 切换排序状态
  const requestSort = (key: SortKey) => {
    setSortConfig((prev) => {
      if (!prev || prev.key !== key) {
        return { key, direction: 'desc' }
      }
      return { key, direction: prev.direction === 'desc' ? 'asc' : 'desc' }
    })
  }

  // 根据排序配置对当前页岗位进行排序
  const displayJobs = useMemo(() => {
    if (!sortConfig) return jobs
    const sorted = [...jobs]
    const { key, direction } = sortConfig
    sorted.sort((a, b) => {
      let cmp = 0
      if (key === 'salary_min') {
        cmp = a.salary_min - b.salary_min
      } else if (key === 'posted_at') {
        const da = a.posted_at ? new Date(a.posted_at).getTime() : 0
        const db = b.posted_at ? new Date(b.posted_at).getTime() : 0
        cmp = da - db
      }
      // match_score 需要后端支持，当前仅保留排序状态，不实际排序
      return direction === 'asc' ? cmp : -cmp
    })
    return sorted
  }, [jobs, sortConfig])

  // 当前已选中的对比岗位列表
  const compareList = useMemo(() => Object.values(compareMap), [compareMap])

  // 排序表头图标
  const SortIcon = ({ columnKey }: { columnKey: SortKey }) => {
    if (sortConfig?.key !== columnKey) {
      return <ArrowUpDown className="ml-1 h-3 w-3 opacity-50" />
    }
    return sortConfig.direction === 'asc' ? (
      <ChevronUp className="ml-1 h-3 w-3" />
    ) : (
      <ChevronDown className="ml-1 h-3 w-3" />
    )
  }

  // 骨架屏行
  const skeletonRows = Array.from({ length: 5 }).map((_, i) => (
    <TableRow key={`sk-${i}`}>
      <TableCell><Skeleton className="h-4 w-4" /></TableCell>
      <TableCell><Skeleton className="h-4 w-24" /></TableCell>
      <TableCell><Skeleton className="h-4 w-24" /></TableCell>
      <TableCell><Skeleton className="h-4 w-16" /></TableCell>
      <TableCell><Skeleton className="h-4 w-20" /></TableCell>
      <TableCell><Skeleton className="h-4 w-16" /></TableCell>
      <TableCell><Skeleton className="h-4 w-16" /></TableCell>
      <TableCell><Skeleton className="h-4 w-32" /></TableCell>
      <TableCell><Skeleton className="h-4 w-20" /></TableCell>
      <TableCell><Skeleton className="h-4 w-12" /></TableCell>
      <TableCell><Skeleton className="h-4 w-8" /></TableCell>
      <TableCell><Skeleton className="h-8 w-20" /></TableCell>
    </TableRow>
  ))

  return (
    <div>
      {/* 页面标题卡片 */}
      <Card className="mb-4">
        <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle>{showFavoritesOnly ? '我的收藏' : '岗位库'}</CardTitle>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>当前画像：</span>
            {profilesLoading ? (
              <Skeleton className="h-4 w-24" />
            ) : currentProfile ? (
              <span className="font-medium text-foreground">{currentProfile.name}</span>
            ) : (
              <span>未选择</span>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* 筛选栏 */}
      <Card className="mb-4">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            {!showFavoritesOnly && (
              <>
                <Input
                  placeholder="搜索岗位关键词"
                  value={filters.search}
                  onChange={(e) => updateFilter('search', e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  className="w-full sm:w-64"
                />
                <Input
                  placeholder="城市"
                  value={filters.city}
                  onChange={(e) => updateFilter('city', e.target.value)}
                  className="w-full sm:w-32"
                />
                <Input
                  placeholder="行业"
                  value={filters.industry}
                  onChange={(e) => updateFilter('industry', e.target.value)}
                  className="w-full sm:w-40"
                />
                <Select
                  value={filters.experienceLevel || ''}
                  onValueChange={(value) => updateFilter('experienceLevel', value)}
                >
                  <SelectTrigger className="w-full sm:w-36">
                    <SelectValue placeholder="全部经验" />
                  </SelectTrigger>
                  <SelectContent>
                    {EXPERIENCE_LEVELS.map((level) => (
                      <SelectItem key={level} value={level}>
                        {level}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button onClick={handleSearch} disabled={loading}>
                  <Search className="mr-2 h-4 w-4" />
                  筛选
                </Button>
                {activeFilterCount > 0 && (
                  <Button variant="outline" onClick={clearFilters} disabled={loading}>
                    <X className="mr-2 h-4 w-4" />
                    清空
                  </Button>
                )}
              </>
            )}
            {showFavoritesOnly && (
              <Button
                variant="outline"
                onClick={() => {
                  searchParams.delete('favorites')
                  setSearchParams(searchParams)
                }}
              >
                <X className="mr-2 h-4 w-4" />
                返回岗位库
              </Button>
            )}
            <Button
              variant={showFavoritesOnly ? 'default' : 'outline'}
              onClick={() => {
                if (showFavoritesOnly) {
                  searchParams.delete('favorites')
                } else {
                  searchParams.set('favorites', '1')
                }
                setSearchParams(searchParams)
                setPage(1)
              }}
              disabled={!currentProfile || favoritesLoading}
              className="ml-auto"
            >
              <Heart className={`mr-2 h-4 w-4 ${showFavoritesOnly ? 'fill-current' : ''}`} />
              {showFavoritesOnly ? '我的收藏' : '我的收藏'}
            </Button>
            <span className="text-sm text-muted-foreground">
              共 {total} 条
            </span>
          </div>
        </CardContent>
      </Card>

      {/* 筛选摘要 */}
      {activeFilterCount > 0 && (
        <div className="mb-4 text-sm text-muted-foreground">
          已启用 {activeFilterCount} 项筛选，找到 <strong>{total}</strong> 条结果
        </div>
      )}

      {/* 错误提示 */}
      {error && (
        <div className="mb-4 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* 对比操作栏 */}
      {compareList.length > 0 && (
        <div className="mb-4 flex items-center gap-3">
          <Button variant="secondary" onClick={() => setCompareOpen(true)}>
            <Scale className="mr-2 h-4 w-4" />
            对比选中岗位 ({compareList.length})
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setCompareMap({})}>
            清空选择
          </Button>
        </div>
      )}

      {/* 岗位表格 */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">选择</TableHead>
                <TableHead>岗位</TableHead>
                <TableHead>公司</TableHead>
                <TableHead>城市</TableHead>
                <TableHead
                  className="cursor-pointer select-none"
                  onClick={() => requestSort('salary_min')}
                >
                  <div className="flex items-center">
                    薪资
                    <SortIcon columnKey="salary_min" />
                  </div>
                </TableHead>
                <TableHead>经验</TableHead>
                <TableHead>学历</TableHead>
                <TableHead>技能要求</TableHead>
                <TableHead
                  className="cursor-pointer select-none"
                  onClick={() => requestSort('posted_at')}
                >
                  <div className="flex items-center">
                    发布时间
                    <SortIcon columnKey="posted_at" />
                  </div>
                </TableHead>
                <TableHead
                  className="cursor-pointer select-none"
                  onClick={() => requestSort('match_score')}
                >
                  <div className="flex items-center">
                    匹配分数
                    <SortIcon columnKey="match_score" />
                  </div>
                </TableHead>
                <TableHead>收藏</TableHead>
                <TableHead>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                skeletonRows
              ) : (
                displayJobs.map((job) => (
                  <TableRow key={job.id}>
                    <TableCell>
                      <Checkbox
                        checked={!!compareMap[job.id]}
                        onCheckedChange={() => toggleCompare(job)}
                        disabled={!compareMap[job.id] && compareList.length >= 3}
                        aria-label={`选择 ${job.title} 进行对比`}
                      />
                    </TableCell>
                    <TableCell className="font-medium">{job.title}</TableCell>
                    <TableCell>{job.company.name}</TableCell>
                    <TableCell>{job.city}</TableCell>
                    <TableCell>
                      ¥{job.salary_min.toLocaleString()}-{job.salary_max.toLocaleString()}
                    </TableCell>
                    <TableCell>{job.experience_level}</TableCell>
                    <TableCell>{job.education_level}</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {job.required_skills.slice(0, 3).map((skill) => (
                          <Badge key={skill} variant="secondary">
                            {skill}
                          </Badge>
                        ))}
                        {job.required_skills.length > 3 && (
                          <Badge variant="outline">+{job.required_skills.length - 3}</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {job.posted_at
                        ? new Date(job.posted_at).toLocaleDateString('zh-CN')
                        : '-'}
                    </TableCell>
                    <TableCell>-</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => toggleFavorite(job.id)}
                        disabled={!currentProfile || favoritesLoading}
                        aria-label={favoriteIds.has(job.id) ? '取消收藏' : '收藏'}
                      >
                        <Heart
                          className={cn(
                            'h-4 w-4',
                            favoriteIds.has(job.id) && 'fill-red-500 text-red-500'
                          )}
                        />
                      </Button>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm" onClick={() => openDetail(job)}>
                          详情
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => navigate(`/match?jobId=${job.id}`)}
                        >
                          去匹配
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
              {!loading && displayJobs.length === 0 && (
                <TableRow>
                  <TableCell colSpan={12} className="py-8 text-center text-muted-foreground">
                    暂无岗位
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 分页 */}
      {maxPage > 1 && (
        <div className="mt-4 flex items-center justify-center gap-4">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1 || loading}
            onClick={() => setPage((p) => p - 1)}
          >
            上一页
          </Button>
          <span className="text-sm text-muted-foreground">
            {page} / {maxPage}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= maxPage || loading}
            onClick={() => setPage((p) => p + 1)}
          >
            下一页
          </Button>
        </div>
      )}

      {/* 岗位详情抽屉 */}
      <Sheet open={detailOpen} onOpenChange={(open) => !open && closeDetail()}>
        <SheetContent className="sm:max-w-md">
          <SheetHeader>
            <SheetTitle>{selectedJob?.title ?? '岗位详情'}</SheetTitle>
            {selectedJob && (
              <SheetDescription>
                {selectedJob.company.name} · {selectedJob.city}
              </SheetDescription>
            )}
          </SheetHeader>

          {detailLoading ? (
            <div className="mt-6 space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          ) : selectedJob ? (
            <div
              className="mt-6 space-y-6 overflow-y-auto pr-2"
              style={{ maxHeight: 'calc(100vh - 180px)' }}
            >
              {/* 基本信息 */}
              <section>
                <h4 className="mb-3 font-semibold">基本信息</h4>
                <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                  <div className="text-muted-foreground">公司</div>
                  <div>{selectedJob.company.name}</div>
                  <div className="text-muted-foreground">行业</div>
                  <div>{selectedJob.company.industry}</div>
                  <div className="text-muted-foreground">规模</div>
                  <div>{selectedJob.company.size}</div>
                  <div className="text-muted-foreground">城市</div>
                  <div>{selectedJob.city}</div>
                  <div className="text-muted-foreground">薪资</div>
                  <div>
                    ¥{selectedJob.salary_min.toLocaleString()}-{selectedJob.salary_max.toLocaleString()}
                  </div>
                  <div className="text-muted-foreground">经验</div>
                  <div>{selectedJob.experience_level}</div>
                  <div className="text-muted-foreground">学历</div>
                  <div>{selectedJob.education_level}</div>
                  <div className="text-muted-foreground">发布时间</div>
                  <div>
                    {selectedJob.posted_at
                      ? new Date(selectedJob.posted_at).toLocaleDateString('zh-CN')
                      : '-'}
                  </div>
                </div>
              </section>

              {/* 技能要求 */}
              <section>
                <h4 className="mb-3 font-semibold">技能要求</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedJob.required_skills.map((skill) => (
                    <Badge key={skill}>{skill}</Badge>
                  ))}
                </div>
              </section>

              {/* 岗位描述 */}
              <section>
                <h4 className="mb-3 font-semibold">岗位描述</h4>
                <p className="whitespace-pre-line text-sm leading-relaxed">
                  {selectedJob.description}
                </p>
              </section>

              {/* 去匹配按钮 */}
              <Button
                className="w-full"
                onClick={() => {
                  closeDetail()
                  navigate(`/match?jobId=${selectedJob.id}`)
                }}
              >
                去匹配
              </Button>
            </div>
          ) : null}
        </SheetContent>
      </Sheet>

      {/* 岗位对比抽屉：使用独立组件 */}
      {compareList.length > 0 && (
        <JobCompareSheet jobs={compareList} open={compareOpen} onClose={closeCompare} />
      )}
    </div>
  )
}
