import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ZoomIn, ZoomOut, RotateCcw, Search } from 'lucide-react'
import { api } from '../api'
import { SkillNetworkGraph } from '../components'
import type {
  SkillNetworkGraphRef,
  SkillNetworkLink,
  SkillNetworkNode,
} from '../components/SkillNetworkGraph'
import type { RelatedSkill, Skill } from '../types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

// 关系类型选项
const RELATION_TYPES = [
  { value: '', label: '全部关系' },
  { value: 'prerequisite', label: '依赖' },
  { value: 'similar', label: '相似' },
  { value: 'cooccurrence', label: '共现' },
]

// 关系类型对应颜色
const RELATION_COLORS: Record<string, string> = {
  prerequisite: '#ef4444',
  similar: '#3b82f6',
  cooccurrence: '#22c55e',
}

export default function SkillGraph() {
  const [skills, setSkills] = useState<Skill[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null)
  const [related, setRelated] = useState<RelatedSkill[]>([])
  const [relationFilter, setRelationFilter] = useState('')
  const [graphLoading, setGraphLoading] = useState(false)

  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<SkillNetworkGraphRef>(null)
  const [size, setSize] = useState({ width: 600, height: 480 })

  // 监听容器尺寸变化
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        setSize({ width: Math.max(320, rect.width - 40), height: 480 })
      }
    }
    updateSize()
    window.addEventListener('resize', updateSize)
    return () => window.removeEventListener('resize', updateSize)
  }, [])

  // 加载技能列表
  useEffect(() => {
    setLoading(true)
    api
      .listSkills()
      .then((res) => setSkills(res.items))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  // 加载中心技能的关联数据
  const loadRelated = useCallback(
    async (skill: Skill, filter = relationFilter) => {
      setGraphLoading(true)
      setError('')
      try {
        const res = await api.getRelatedSkills(skill.id, filter || undefined)
        setRelated(res)
        setSelectedSkill(skill)
      } catch (e: any) {
        setError(e.message)
      } finally {
        setGraphLoading(false)
      }
    },
    [relationFilter],
  )

  // 根据当前筛选条件过滤已加载的关联数据
  const filteredRelated = useMemo(() => {
    return relationFilter ? related.filter((r) => r.relation_type === relationFilter) : related
  }, [related, relationFilter])

  // 计算每个目标技能的最大权重，用于映射节点大小
  const targetWeights = useMemo(() => {
    const map = new Map<string, number>()
    filteredRelated.forEach((r) => {
      map.set(r.target_skill, Math.max(map.get(r.target_skill) || 0, r.weight))
    })
    return map
  }, [filteredRelated])

  // 构建图谱所需的节点与边数据
  const graphData = useMemo(() => {
    if (!selectedSkill) return { nodes: [], links: [] }

    const definitionMap = new Map(skills.map((s) => [s.name, s.definition]))
    const nodes: SkillNetworkNode[] = [
      {
        id: selectedSkill.name,
        name: selectedSkill.name,
        r: 36,
        isCenter: true,
        definition: selectedSkill.definition,
      },
    ]

    const targets = Array.from(new Set(filteredRelated.map((r) => r.target_skill)))
    targets.forEach((name) => {
      const weight = targetWeights.get(name) || 0.5
      nodes.push({
        id: name,
        name,
        r: 14 + weight * 18,
        isCenter: false,
        definition: definitionMap.get(name),
      })
    })

    const links: SkillNetworkLink[] = filteredRelated.map((r) => ({
      source: r.skill,
      target: r.target_skill,
      relation_type: r.relation_type,
      weight: r.weight,
    }))

    return { nodes, links }
  }, [selectedSkill, filteredRelated, skills, targetWeights])

  // 搜索并选中技能
  const handleSearch = () => {
    const keyword = search.trim().toLowerCase()
    const found = skills.find(
      (s) =>
        s.name.toLowerCase().includes(keyword) ||
        s.aliases.some((a) => a.toLowerCase().includes(keyword)),
    )
    if (found) {
      loadRelated(found)
    } else {
      setError('未找到相关技能')
    }
  }

  // 点击图谱节点时以该节点为中心重新加载
  const handleNodeClick = useCallback(
    (node: SkillNetworkNode) => {
      if (node.isCenter) return
      const found = skills.find((s) => s.name === node.name)
      if (found) {
        setError('')
        loadRelated(found)
      } else {
        setError(`未找到技能「${node.name}」的详细信息`)
      }
    },
    [skills, loadRelated],
  )

  // 统计各关系类型数量
  const stats = useMemo(() => {
    const counts: Record<string, number> = {}
    related.forEach((r) => {
      counts[r.relation_type] = (counts[r.relation_type] || 0) + 1
    })
    return counts
  }, [related])

  // 技能分类集合
  const categories = useMemo(
    () => Array.from(new Set(skills.map((s) => s.category))),
    [skills],
  )

  return (
    <div className="space-y-6">
      <div className="page-header">
        <h2>技能知识图谱</h2>
      </div>

      {/* 搜索、筛选与视图控制工具栏 */}
      <Card>
        <CardContent className="flex flex-wrap items-center gap-3 py-4">
          <div className="flex w-full max-w-sm items-center gap-2 sm:w-auto">
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索技能名称"
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button onClick={handleSearch} disabled={loading || !search.trim()}>
              <Search className="mr-1 h-4 w-4" />
              搜索
            </Button>
          </div>

          <Select
            value={relationFilter}
            onValueChange={(value) => {
              setRelationFilter(value)
              if (selectedSkill) loadRelated(selectedSkill, value)
            }}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="关系类型" />
            </SelectTrigger>
            <SelectContent>
              {RELATION_TYPES.map((t) => (
                <SelectItem key={t.value} value={t.value}>
                  {t.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="ml-auto flex items-center gap-2">
            <span className="text-sm text-muted-foreground">技能库共 {skills.length} 项</span>
            <Button
              variant="outline"
              size="icon"
              onClick={() => graphRef.current?.zoomIn()}
              title="放大"
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() => graphRef.current?.zoomOut()}
              title="缩小"
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => graphRef.current?.resetZoom()}
            >
              <RotateCcw className="mr-1 h-4 w-4" />
              重置视图
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && <div className="error-banner">{error}</div>}

      {/* 图谱与关联列表 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        {/* 力导向图谱 */}
        <Card ref={containerRef}>
          <CardHeader>
            <CardTitle className="text-base">技能关联图</CardTitle>
          </CardHeader>
          <CardContent>
            {graphLoading ? (
              <Skeleton className="mx-auto" style={{ width: size.width, height: size.height }} />
            ) : selectedSkill ? (
              <SkillNetworkGraph
                ref={graphRef}
                nodes={graphData.nodes}
                links={graphData.links}
                width={size.width}
                height={size.height}
                onNodeClick={handleNodeClick}
                relationColors={RELATION_COLORS}
              />
            ) : (
              <div className="chart-empty">搜索并选择一个技能查看关联图谱</div>
            )}

            {/* 图例 */}
            <div className="mt-3 flex flex-wrap justify-center gap-3">
              {RELATION_TYPES.slice(1).map((t) => (
                <div key={t.value} className="flex items-center gap-1.5 text-sm">
                  <span
                    className="inline-block h-2.5 w-2.5 rounded-full"
                    style={{ background: RELATION_COLORS[t.value] }}
                  />
                  {t.label}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 关联技能列表 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">关联技能列表</CardTitle>
          </CardHeader>
          <CardContent>
            {selectedSkill ? (
              <>
                <div className="mb-4">
                  <span className="text-xs text-muted-foreground">中心技能</span>
                  <div className="text-lg font-semibold">{selectedSkill.name}</div>
                  <p className="mt-1 text-sm text-muted-foreground">{selectedSkill.definition}</p>
                </div>
                {graphLoading ? (
                  <div className="space-y-2">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Skeleton key={i} className="h-10 w-full" />
                    ))}
                  </div>
                ) : filteredRelated.length ? (
                  <ScrollArea className="h-[320px] pr-3">
                    <div className="space-y-2">
                      {filteredRelated.map((r, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-3 rounded-md border p-2 text-sm hover:bg-muted/50"
                        >
                          <span className="w-5 text-xs text-muted-foreground">{idx + 1}</span>
                          <span className="flex-1 font-medium">{r.target_skill}</span>
                          <Badge
                            style={{
                              background: RELATION_COLORS[r.relation_type] || '#e2e8f0',
                              color: '#fff',
                            }}
                          >
                            {RELATION_TYPES.find((t) => t.value === r.relation_type)?.label || r.relation_type}
                          </Badge>
                          <span className="min-w-[40px] text-right font-semibold">
                            {(r.weight * 100).toFixed(0)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                ) : (
                  <div className="chart-empty">该关系类型下暂无关联</div>
                )}
              </>
            ) : (
              <div className="chart-empty">请选择一个技能</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 关系统计卡片 */}
      {selectedSkill && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {RELATION_TYPES.slice(1).map((t) => (
            <Card key={t.value}>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <span
                    className="inline-block h-3 w-3 rounded-full"
                    style={{ background: RELATION_COLORS[t.value] }}
                  />
                  {t.label}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stats[t.value] || 0}</div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* 技能分类 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">技能分类</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {categories.map((category) => (
              <Badge key={category} variant="secondary">
                {category}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
