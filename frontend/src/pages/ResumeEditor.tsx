import { useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  ArrowLeft,
  ArrowUpDown,
  Check,
  Edit3,
  FileText,
  RotateCcw,
  Search,
  Sparkles,
  Upload,
} from 'lucide-react'
import { api } from '../api'
import type {
  ObstacleAnalysis,
  ResumeUploadOut,
  ResumeProjectExperience,
  ResumeWorkExperience,
  ResumeOptimizeOut,
  SearchOut,
} from '../types'
import JDUploader from '../components/JDUploader'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'

const SEARCH_INTENTS = [
  { value: 'company', label: '公司评价' },
  { value: 'interview', label: '面经' },
  { value: 'salary', label: '薪资' },
  { value: 'fresh_graduate', label: '校招' },
]

type FieldOrderItem = 'project' | 'internship' | 'advantage'

const FIELD_LABELS: Record<FieldOrderItem, string> = {
  project: '项目经历',
  internship: '实习经历',
  advantage: '个人优势',
}

export default function ResumeEditor() {
  const navigate = useNavigate()

  const [resume, setResume] = useState<ResumeUploadOut | null>(null)
  const [optimized, setOptimized] = useState<ResumeOptimizeOut | null>(null)
  const [jdText, setJdText] = useState('')
  const [fieldOrder, setFieldOrder] = useState<FieldOrderItem[]>(['project', 'internship', 'advantage'])
  const [optimizing, setOptimizing] = useState(false)
  const [showCompare, setShowCompare] = useState(false)

  // ---- 简历上传状态 ----
  const resumeFileInputRef = useRef<HTMLInputElement>(null)
  const [resumeUploadLoading, setResumeUploadLoading] = useState(false)
  const [resumeUploadError, setResumeUploadError] = useState('')
  const [resumePreview, setResumePreview] = useState('')
  const [resumeObstacles, setResumeObstacles] = useState<ObstacleAnalysis | null>(null)

  // ---- 联网搜索状态 ----
  const [searchQuery, setSearchQuery] = useState('')
  const [searchIntent, setSearchIntent] = useState('fresh_graduate')
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchResult, setSearchResult] = useState<SearchOut | null>(null)

  const handleJDParse = useCallback((result: { parsed: { title: string; description?: string } }) => {
    setJdText(result.parsed.title + '\n' + (result.parsed.description || ''))
  }, [])

  const handleResumeUploadClick = () => {
    resumeFileInputRef.current?.click()
  }

  const handleResumeFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setResumeUploadLoading(true)
    setResumeUploadError('')
    setResumePreview('')
    setResumeObstacles(null)

    const ext = file.name.split('.').pop()?.toLowerCase()
    if (ext === 'pdf' || ['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(ext || '')) {
      setResumePreview(URL.createObjectURL(file))
    }

    try {
      const res = await api.uploadResume(file)
      setResume(res)
      setResumeObstacles(res.obstacles || null)
      if (res.job_intention?.expected_position) {
        setSearchQuery(`${res.job_intention.expected_position} 校招 应届生`)
      }
    } catch (err: any) {
      setResumeUploadError(err.message || '简历上传失败')
    } finally {
      setResumeUploadLoading(false)
      if (resumeFileInputRef.current) resumeFileInputRef.current.value = ''
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    setSearchLoading(true)
    try {
      const res = await api.search({
        query: searchQuery.trim(),
        intent: searchIntent,
        top_n: 5,
        summarize: true,
      })
      setSearchResult(res)
    } catch (err: any) {
      setResumeUploadError(err.message || '搜索失败')
    } finally {
      setSearchLoading(false)
    }
  }

  const handleOptimize = async () => {
    if (!resume || !jdText.trim()) return

    setOptimizing(true)
    try {
      const res = await api.optimizeResume({
        resume_data: resume as unknown as Record<string, unknown>,
        jd_text: jdText,
        field_order: fieldOrder,
      })
      setOptimized(res)
      setShowCompare(true)
    } catch (err: any) {
      alert(err.message || '优化失败')
    } finally {
      setOptimizing(false)
    }
  }

  const moveField = (fromIndex: number, toIndex: number) => {
    const newOrder = [...fieldOrder]
    const [removed] = newOrder.splice(fromIndex, 1)
    newOrder.splice(toIndex, 0, removed)
    setFieldOrder(newOrder)
  }

  const updateProject = (index: number, updates: Partial<ResumeProjectExperience>) => {
    if (!resume) return
    const newProjects = [...resume.project_experience]
    newProjects[index] = { ...newProjects[index], ...updates }
    setResume({ ...resume, project_experience: newProjects })
  }

  const updateWork = (index: number, updates: Partial<ResumeWorkExperience>) => {
    if (!resume) return
    const newWork = [...resume.work_experience]
    newWork[index] = { ...newWork[index], ...updates }
    setResume({ ...resume, work_experience: newWork })
  }

  const updateSelfEvaluation = (value: string) => {
    if (!resume) return
    setResume({ ...resume, self_evaluation: value })
  }

  const renderFieldSection = () => {
    return fieldOrder.map((field, index) => {
      const canMoveUp = index > 0
      const canMoveDown = index < fieldOrder.length - 1

      const renderContent = () => {
        switch (field) {
          case 'project':
            return (
              <div className="space-y-4">
                {resume!.project_experience?.length > 0 ? (
                  resume!.project_experience.map((proj, idx) => (
                    <div key={idx} className="rounded-lg border p-4">
                      <div className="grid gap-3 sm:grid-cols-3">
                        <div>
                          <Label className="text-xs">项目名称</Label>
                          <Input
                            value={proj.name}
                            onChange={(e) => updateProject(idx, { name: e.target.value })}
                            className="mt-1 min-h-[44px] text-sm focus-visible:ring-2 focus-visible:ring-primary md:min-h-10"
                          />
                        </div>
                        <div>
                          <Label className="text-xs">担任角色</Label>
                          <Input
                            value={proj.role}
                            onChange={(e) => updateProject(idx, { role: e.target.value })}
                            className="mt-1 min-h-[44px] text-sm focus-visible:ring-2 focus-visible:ring-primary md:min-h-10"
                          />
                        </div>
                        <div className="sm:col-span-3">
                          <Label className="text-xs">项目描述</Label>
                          <Textarea
                            value={proj.description}
                            onChange={(e) => updateProject(idx, { description: e.target.value })}
                            className="mt-1 min-h-[88px] text-sm focus-visible:ring-2 focus-visible:ring-primary md:min-h-[120px]"
                            rows={4}
                          />
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-sm text-muted-foreground py-8">
                    暂无项目经历，可添加或上传简历自动填充
                  </div>
                )}
              </div>
            )

          case 'internship':
            return (
              <div className="space-y-4">
                {resume!.work_experience?.length > 0 ? (
                  resume!.work_experience.map((work, idx) => (
                    <div key={idx} className="rounded-lg border p-4">
                      <div className="grid gap-3 sm:grid-cols-3">
                        <div>
                          <Label className="text-xs">公司名称</Label>
                          <Input
                            value={work.company}
                            onChange={(e) => updateWork(idx, { company: e.target.value })}
                            className="mt-1 min-h-[44px] text-sm focus-visible:ring-2 focus-visible:ring-primary md:min-h-10"
                          />
                        </div>
                        <div>
                          <Label className="text-xs">职位</Label>
                          <Input
                            value={work.position}
                            onChange={(e) => updateWork(idx, { position: e.target.value })}
                            className="mt-1 min-h-[44px] text-sm focus-visible:ring-2 focus-visible:ring-primary md:min-h-10"
                          />
                        </div>
                        <div className="sm:col-span-3">
                          <Label className="text-xs">工作描述</Label>
                          <Textarea
                            value={work.description}
                            onChange={(e) => updateWork(idx, { description: e.target.value })}
                            className="mt-1 min-h-[88px] text-sm focus-visible:ring-2 focus-visible:ring-primary md:min-h-[120px]"
                            rows={4}
                          />
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-sm text-muted-foreground py-8">
                    暂无工作/实习经历，可添加或上传简历自动填充
                  </div>
                )}
              </div>
            )

          case 'advantage':
            return (
              <div>
                <Label className="text-xs">个人优势/自我评价</Label>
                <Textarea
                  value={resume?.self_evaluation || ''}
                  onChange={(e) => updateSelfEvaluation(e.target.value)}
                  className="mt-1 min-h-[88px] text-sm focus-visible:ring-2 focus-visible:ring-primary md:min-h-[120px]"
                  rows={6}
                  placeholder="请描述您的核心竞争力和个人优势..."
                />
              </div>
            )

          default:
            return null
        }
      }

      return (
        <div key={field} className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="secondary">{index + 1}</Badge>
              <span className="font-medium">{FIELD_LABELS[field]}</span>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-11 w-11 md:h-7 md:w-7"
                onClick={() => moveField(index, index - 1)}
                disabled={!canMoveUp}
              >
                <ArrowUpDown className="h-3.5 w-3.5 rotate-[-90deg]" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-11 w-11 md:h-7 md:w-7"
                onClick={() => moveField(index, index + 1)}
                disabled={!canMoveDown}
              >
                <ArrowUpDown className="h-3.5 w-3.5 rotate-[90deg]" />
              </Button>
            </div>
          </div>
          {renderContent()}
        </div>
      )
    })
  }

  const renderComparison = () => {
    if (!optimized) return null

    return (
      <Tabs defaultValue="project" className="mt-6">
        <TabsList className="mb-4 flex-wrap">
          <TabsTrigger value="project">项目经历对比</TabsTrigger>
          <TabsTrigger value="work">工作经历对比</TabsTrigger>
          <TabsTrigger value="advantage">个人优势对比</TabsTrigger>
        </TabsList>

        <TabsContent value="project" className="space-y-4">
          {optimized.optimized_project_experience.length > 0 ? (
            optimized.optimized_project_experience.map((proj, idx) => {
              const original = optimized.original_project_experience[idx]
              return (
                <Card key={idx}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Edit3 className="h-4 w-4" />
                      {proj.name || original?.name || `项目 ${idx + 1}`}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <div className="text-xs text-muted-foreground mb-2">优化前</div>
                        <div className="rounded-md border bg-muted/30 p-3 text-sm">
                          {original?.description || '-'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-green-600 mb-2">优化后</div>
                        <div className="rounded-md border border-green-200 bg-green-50/50 p-3 text-sm">
                          {proj.description || '-'}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })
          ) : (
            <div className="text-center text-muted-foreground py-8">无项目经历</div>
          )}
        </TabsContent>

        <TabsContent value="work" className="space-y-4">
          {optimized.optimized_work_experience.length > 0 ? (
            optimized.optimized_work_experience.map((work, idx) => {
              const original = optimized.original_work_experience[idx]
              return (
                <Card key={idx}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Edit3 className="h-4 w-4" />
                      {work.company || original?.company || `公司 ${idx + 1}`}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <div className="text-xs text-muted-foreground mb-2">优化前</div>
                        <div className="rounded-md border bg-muted/30 p-3 text-sm">
                          {original?.description || '-'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-green-600 mb-2">优化后</div>
                        <div className="rounded-md border border-green-200 bg-green-50/50 p-3 text-sm">
                          {work.description || '-'}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })
          ) : (
            <div className="text-center text-muted-foreground py-8">无工作经历</div>
          )}
        </TabsContent>

        <TabsContent value="advantage" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <div className="text-xs text-muted-foreground mb-2">优化前</div>
              <div className="rounded-md border bg-muted/30 p-4 text-sm">
                {optimized.original_self_evaluation || '-'}
              </div>
            </div>
            <div>
              <div className="text-xs text-green-600 mb-2">优化后</div>
              <div className="rounded-md border border-green-200 bg-green-50/50 p-4 text-sm">
                {optimized.optimized_self_evaluation || '-'}
              </div>
            </div>
          </div>

          {optimized.suggested_changes.length > 0 && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
              <div className="text-sm font-medium text-amber-800 mb-2">修改建议</div>
              <ul className="list-inside list-disc text-sm text-amber-700 space-y-1">
                {optimized.suggested_changes.map((change, idx) => (
                  <li key={idx}>{change}</li>
                ))}
              </ul>
            </div>
          )}
        </TabsContent>
      </Tabs>
    )
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6 flex items-center justify-between gap-2">
        <Button variant="ghost" onClick={() => navigate(-1)} className="h-11 px-2 md:h-9">
          <ArrowLeft className="mr-2 h-4 w-4" />
          返回
        </Button>
        <h2 className="flex-1 truncate text-center text-lg font-bold md:text-xl">简历编辑器</h2>
        <div className="w-10 md:w-24" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                JD 解析与优化配置
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <JDUploader onParseComplete={handleJDParse} />

              <div>
                <Label className="text-xs">目标岗位描述文本</Label>
                <Textarea
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  className="mt-1 min-h-[88px] text-sm focus-visible:ring-2 focus-visible:ring-primary md:min-h-[120px]"
                  rows={6}
                  placeholder="粘贴或上传岗位描述内容..."
                />
              </div>

              <div>
                <Label className="text-xs">字段排放顺序（拖拽调整）</Label>
                <div className="mt-2 space-y-2">
                  {fieldOrder.map((field, index) => (
                    <div
                      key={field}
                      className="flex min-h-[44px] items-center gap-2 rounded-md border p-2 cursor-move"
                      draggable
                      onDragStart={(e) => e.dataTransfer.setData('index', String(index))}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={(e) => {
                        const fromIndex = parseInt(e.dataTransfer.getData('index'))
                        moveField(fromIndex, index)
                      }}
                    >
                      <ArrowUpDown className="h-4 w-4 text-muted-foreground" />
                      <Badge variant="secondary">{index + 1}</Badge>
                      <span className="flex-1 truncate">{FIELD_LABELS[field]}</span>
                    </div>
                  ))}
                </div>
              </div>

              <Button
                className="h-11 w-full md:h-10"
                onClick={handleOptimize}
                disabled={optimizing || !resume || !jdText.trim()}
              >
                {optimizing ? (
                  <Skeleton className="h-4 w-4" />
                ) : (
                  <Sparkles className="mr-2 h-4 w-4" />
                )}
                {optimizing ? '正在优化...' : 'AI 优化简历'}
              </Button>
            </CardContent>
          </Card>

          {optimized && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  优化完成
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-3">{optimized.optimization_notes}</p>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => setShowCompare(!showCompare)}>
                    {showCompare ? '隐藏对比' : '查看对比'}
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setResume({
                        ...resume!,
                        project_experience: optimized.optimized_project_experience,
                        work_experience: optimized.optimized_work_experience,
                        self_evaluation: optimized.optimized_self_evaluation,
                      })
                      setShowCompare(false)
                    }}
                  >
                    <Check className="mr-2 h-4 w-4" />
                    应用优化结果
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => setOptimized(null)}
                  >
                    <RotateCcw className="mr-2 h-4 w-4" />
                    重置
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          {/* 简历上传卡片 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                上传简历
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div
                className="flex h-32 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-input bg-muted/30 transition-colors hover:border-primary/50 hover:bg-muted/50"
                onClick={handleResumeUploadClick}
              >
                <input
                  ref={resumeFileInputRef}
                  type="file"
                  accept=".pdf,.docx,.doc,.png,.jpg,.jpeg,.webp,.gif"
                  className="hidden"
                  data-testid="resume-file-input"
                  onChange={handleResumeFileChange}
                />
                <Upload className="mb-2 h-8 w-8 text-muted-foreground" />
                <div className="text-sm font-medium">点击上传简历文件</div>
                <div className="text-xs text-muted-foreground">支持 PDF、DOCX、图片（PNG/JPG）</div>
              </div>

              {resumePreview && (
                <div className="rounded-lg border overflow-hidden">
                  <img
                    src={resumePreview}
                    alt="Resume Preview"
                    className="w-full max-h-64 object-contain"
                  />
                </div>
              )}

              {resumeUploadLoading && (
                <div className="space-y-3">
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-full" />
                </div>
              )}

              {resumeUploadError && (
                <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
                  {resumeUploadError}
                </div>
              )}

              {resume && !resumeUploadLoading && (
                <div className="space-y-4 rounded-lg border bg-card p-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-primary" />
                    <span className="font-medium">解析结果</span>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div>
                      <div className="text-xs text-muted-foreground">姓名</div>
                      <div className="font-medium">{resume.name || '-'}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">学历</div>
                      <Badge variant="outline">{resume.education_level || '不限'}</Badge>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">经验级别</div>
                      <Badge variant="outline">{resume.experience_level || '不限'}</Badge>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">技能数</div>
                      <Badge variant="outline">{resume.skills?.length || 0}</Badge>
                    </div>
                  </div>

                  {resume.skills && resume.skills.length > 0 && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-2">识别技能</div>
                      <div className="flex flex-wrap gap-2">
                        {resume.skills.map((skill, idx) => (
                          <Badge key={idx} variant="secondary" className="gap-1">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {resumeObstacles && resumeObstacles.obstacles.length > 0 && (
                    <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                      <div className="flex items-center gap-2 text-sm font-medium text-amber-800 mb-2">
                        <AlertCircle className="h-4 w-4" />
                        求职困境识别
                      </div>
                      <ul className="list-inside list-disc text-sm text-amber-700 space-y-1">
                        {resumeObstacles.obstacles.map((item, idx) => (
                          <li key={idx}>{item.label}: {item.detail}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* 简历内容编辑卡片 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Edit3 className="h-5 w-5" />
                简历内容编辑
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {resume ? (
                renderFieldSection()
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>请先上传简历或从岗位匹配页跳转过来</p>
                  <Button
                    variant="outline"
                    className="mt-4"
                    onClick={() => navigate('/match')}
                  >
                    去填写画像
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 联网求职情报卡片 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                联网求职情报
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="输入公司/岗位关键词搜索"
                  className="h-11 min-w-0 flex-1"
                />
                <select
                  value={searchIntent}
                  onChange={(e) => setSearchIntent(e.target.value)}
                  className="h-11 min-w-[6rem] rounded-md border bg-background px-2 text-sm"
                >
                  {SEARCH_INTENTS.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
                <Button
                  onClick={handleSearch}
                  disabled={searchLoading || !searchQuery.trim()}
                  className="h-11"
                >
                  {searchLoading ? '搜索中...' : '搜索'}
                </Button>
              </div>

              {searchResult && (
                <div className="space-y-3">
                  {searchResult.summary && (
                    <div className="rounded-md bg-muted/50 p-3 text-sm">
                      {searchResult.summary}
                    </div>
                  )}
                  <div className="space-y-2">
                    {searchResult.results.map((item, idx) => (
                      <a
                        key={idx}
                        href={item.url}
                        target="_blank"
                        rel="noreferrer"
                        className="block rounded-md border p-3 text-sm hover:bg-muted/50"
                      >
                        <div className="font-medium text-primary">{item.title}</div>
                        <div className="mt-1 text-xs text-muted-foreground line-clamp-2">
                          {item.snippet}
                        </div>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {showCompare && renderComparison()}
    </div>
  )
}
