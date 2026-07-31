import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ArrowLeft, ArrowUp, ArrowUpDown, ChevronDown, ExternalLink, RotateCcw, Scale, Search, Upload, User } from 'lucide-react'

import { api } from '../api'
import { MatchResultCard, SkillRadarChart } from '../components'
import ExportPDFButton from '@/components/ExportPDFButton'
import JobCompareSheet from '@/components/JobCompareSheet'
import { useProfile } from '@/components/ProfileContext'
import ResumeProfileForm, {
  emptyProfileFormData,
  type ProfileFormData,
  resumeToFormData,
} from '@/components/ResumeProfileForm'
import type { Job, MatchResult, UserSkillProfile } from '../types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Stepper } from '@/components/ui/stepper'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useMediaQuery } from '@/hooks/useMediaQuery'
import { cn, getSourceLabel } from '@/lib/utils'

// 页面顶部步骤：填写画像 → 选择岗位 → 查看结果
const WIZARD_STEPS = [
  { label: '填写画像', description: '技能、经验、目标岗位' },
  { label: '选择目标岗位', description: '搜索并单选岗位' },
  { label: '查看匹配结果', description: '分数、技能标签、雷达图' },
]

// 流式匹配内部节点，用于进度展示
const STREAM_STEP_LABELS: Record<string, string> = {
  parse_profile: '解析画像',
  retrieve_jobs: '检索岗位',
  match_skills: '技能匹配',
  analyze_gap: '差距分析',
  finalize: '完成',
}
const STREAM_STEP_ORDER = ['parse_profile', 'retrieve_jobs', 'match_skills', 'analyze_gap', 'finalize']

const EXAMPLE_PROFILES = [
  {
    label: 'Java 后端',
    name: 'Java 后端工程师',
    skills: 'Java, Spring Boot, MySQL, Redis, Kafka, Docker',
    target: 'Java 后端工程师, 后端开发工程师',
    experience: '3-5年',
  },
  {
    label: '前端工程师',
    name: '前端开发工程师',
    skills: 'JavaScript, TypeScript, React, Vue, CSS, Webpack',
    target: '前端工程师, Web 前端开发',
    experience: '1-3年',
  },
  {
    label: '算法工程师',
    name: '算法工程师',
    skills: 'Python, PyTorch, TensorFlow, 机器学习, 深度学习, SQL',
    target: '算法工程师, 机器学习工程师',
    experience: '3-5年',
  },
]

type SortKey = 'salary' | 'posted_at' | null
type SortDirection = 'asc' | 'desc'

function arraysEqual(a: string[], b: string[]): boolean {
  if (a.length !== b.length) return false
  const setB = new Set(b)
  return a.every((v) => setB.has(v))
}

function formMatchesProfile(form: ProfileFormData, profile: UserSkillProfile): boolean {
  return (
    form.name.trim() === profile.name &&
    form.experienceLevel === profile.experience_level &&
    arraysEqual(
      form.skillsText.split(/[,，]/).map((s) => s.trim()).filter(Boolean),
      profile.skills,
    ) &&
    arraysEqual(
      form.targetJobTitles.split(/[,，]/).map((s) => s.trim()).filter(Boolean),
      profile.target_job_titles,
    )
  )
}

function formatSalary(job: Job): string {
  return `¥${job.salary_min.toLocaleString()}-${job.salary_max.toLocaleString()}`
}

function formatPostedAt(job: Job): string {
  return job.posted_at ? new Date(job.posted_at).toLocaleDateString('zh-CN') : '-'
}

export default function JobMatch() {
  // ---- 全局生效画像 ----
  const { effectiveProfile } = useProfile()
  const isDesktop = useMediaQuery('(min-width: 768px)')
  const profilePrefilledRef = useRef(false)

  // ---- 画像表单状态 ----
  const [profileFormData, setProfileFormData] = useState<ProfileFormData>(emptyProfileFormData())

  // ---- 岗位选择状态 ----
  const [jobs, setJobs] = useState<Job[]>([])
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [jobSearch, setJobSearch] = useState('')
  const [jobsLoading, setJobsLoading] = useState(false)
  const [sortConfig, setSortConfig] = useState<{ key: SortKey; direction: SortDirection }>({
    key: null,
    direction: 'desc',
  })

  // ---- 匹配结果状态 ----
  const [result, setResult] = useState<MatchResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // ---- 步骤与流式状态 ----
  const [wizardStep, setWizardStep] = useState(1)
  const [streamActiveStep, setStreamActiveStep] = useState<string>('')
  const [streamCompletedSteps, setStreamCompletedSteps] = useState<string[]>([])
  const [useStream, setUseStream] = useState(false)

  // ---- 简历上传状态 ----
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadLoading, setUploadLoading] = useState(false)
  const [uploadError, setUploadError] = useState('')

  // ---- 岗位对比状态 ----
  const [compareJobs, setCompareJobs] = useState<Job[]>([])
  const [compareOpen, setCompareOpen] = useState(false)

  // 加载岗位列表
  const loadJobs = useCallback(async (q = '') => {
    setJobsLoading(true)
    try {
      const res = await api.listJobs({ q, size: 50 })
      setJobs(res.items)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setJobsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadJobs()
  }, [loadJobs])

  // 预填充生效画像到表单
  useEffect(() => {
    if (effectiveProfile && !profilePrefilledRef.current) {
      setProfileFormData((prev) => ({
        ...prev,
        name: effectiveProfile.name,
        skillsText: effectiveProfile.skills.join(', '),
        experienceLevel: effectiveProfile.experience_level,
        targetJobTitles: effectiveProfile.target_job_titles.join(', '),
      }))
      profilePrefilledRef.current = true
    }
  }, [effectiveProfile])

  const selectedJob = jobs.find((j) => j.id === selectedJobId) || null

  const skills = useMemo(
    () => profileFormData.skillsText.split(/[,，]/).map((s) => s.trim()).filter(Boolean),
    [profileFormData.skillsText]
  )
  const targetJobTitles = useMemo(
    () => profileFormData.targetJobTitles.split(/[,，]/).map((s) => s.trim()).filter(Boolean),
    [profileFormData.targetJobTitles]
  )

  const profileMatchesEffective = useMemo(
    () => (effectiveProfile ? formMatchesProfile(profileFormData, effectiveProfile) : false),
    [effectiveProfile, profileFormData]
  )

  // 排序后的岗位列表
  const sortedJobs = useMemo(() => {
    if (!sortConfig.key) return jobs
    const sorted = [...jobs]
    sorted.sort((a, b) => {
      if (sortConfig.key === 'salary') {
        const valA = a.salary_max
        const valB = b.salary_max
        return sortConfig.direction === 'asc' ? valA - valB : valB - valA
      }
      if (sortConfig.key === 'posted_at') {
        const valA = a.posted_at ? new Date(a.posted_at).getTime() : 0
        const valB = b.posted_at ? new Date(b.posted_at).getTime() : 0
        return sortConfig.direction === 'asc' ? valA - valB : valB - valA
      }
      return 0
    })
    return sorted
  }, [jobs, sortConfig])

  // 切换排序规则
  const toggleSort = (key: SortKey) => {
    setSortConfig((prev) => {
      if (prev.key !== key) return { key, direction: 'desc' }
      return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' }
    })
  }

  // 排序表头图标
  const sortIcon = (key: SortKey) => {
    if (sortConfig.key !== key) return <ArrowUpDown className="ml-1 h-3.5 w-3.5" />
    return sortConfig.direction === 'asc' ? (
      <ArrowUp className="ml-1 h-3.5 w-3.5" />
    ) : (
      <ChevronDown className="ml-1 h-3.5 w-3.5" />
    )
  }

  // 应用快速示例
  const applyExample = (ex: typeof EXAMPLE_PROFILES[0]) => {
    setProfileFormData({
      ...emptyProfileFormData(),
      name: ex.name,
      skillsText: ex.skills,
      experienceLevel: ex.experience,
      targetJobTitles: ex.target,
    })
    setResult(null)
    setError('')
  }

  // 上传简历并自动填充画像
  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadLoading(true)
    setUploadError('')
    try {
      const resume = await api.uploadResume(file)
      setProfileFormData(resumeToFormData(resume))
      setResult(null)
    } catch (err: any) {
      setUploadError(err.message || '简历上传失败')
    } finally {
      setUploadLoading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  // 执行匹配
  const handleMatch = async () => {
    if (!selectedJobId) return
    setLoading(true)
    setError('')
    setResult(null)
    setStreamActiveStep('')
    setStreamCompletedSteps([])

    try {
      let profileId: number
      if (profileMatchesEffective && effectiveProfile) {
        profileId = effectiveProfile.id
      } else {
        const profile = await api.createProfile({
          name: profileFormData.name.trim(),
          skills,
          experience_level: profileFormData.experienceLevel,
          target_job_titles: targetJobTitles,
        })
        profileId = profile.id
      }

      if (useStream) {
        const res = await api.matchStream(
          { profile_id: profileId, job_id: selectedJobId },
          (event) => {
            const node = event.node || event.status
            if (node) {
              setStreamActiveStep(node)
              setStreamCompletedSteps((prev) => (prev.includes(node) ? prev : [...prev, node]))
            }
          },
        )
        if (res) setResult(res)
      } else {
        const res = await api.createMatch(profileId, selectedJobId)
        setResult(res)
      }
      // 匹配成功后进入结果步骤
      setWizardStep(3)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
      setStreamActiveStep('')
    }
  }

  // 步骤校验：至少需要姓名和技能
  const canEnterStep2 = profileFormData.name.trim().length > 0 && skills.length > 0

  // 导航控制
  const nextStep = () => {
    if (wizardStep === 1 && canEnterStep2) setWizardStep(2)
  }

  const prevStep = () => {
    if (wizardStep > 1) setWizardStep(wizardStep - 1)
  }

  // 重新开始
  const resetMatch = () => {
    setWizardStep(1)
    setResult(null)
    setError('')
    setSelectedJobId(null)
    setCompareOpen(false)
    setCompareJobs([])
    setProfileFormData(emptyProfileFormData())
    profilePrefilledRef.current = false
    // 重置后如果仍有生效画像，允许再次预填充
  }

  // 打开岗位对比面板，并预先将当前匹配的岗位加入对比
  const openCompareWithCurrentJob = () => {
    if (!selectedJob) return
    setCompareJobs([selectedJob])
    setCompareOpen(true)
  }

  // 关闭岗位对比面板
  const closeCompare = () => {
    setCompareOpen(false)
    setCompareJobs([])
  }

  // 雷达图数据：取岗位要求与用户技能的并集，最多 12 项
  const radarSkills = useMemo(() => {
    if (!selectedJob) return []
    const required = selectedJob.required_skills
    const userSet = new Set(skills)
    const matchedSet = new Set(result?.matched_skills ?? [])
    const allSkills = Array.from(new Set([...required, ...userSet]))
    return allSkills.slice(0, 12).map((skillName) => ({
      name: skillName,
      userScore: matchedSet.has(skillName) ? 90 : userSet.has(skillName) ? 80 : 0,
      requiredScore: required.includes(skillName) ? 100 : 0,
    }))
  }, [selectedJob, skills, result])

  // 流式进度当前节点序号，用于 Stepper 高亮
  const streamStepIndex = useMemo(() => {
    if (streamActiveStep) {
      const idx = STREAM_STEP_ORDER.indexOf(streamActiveStep)
      if (idx >= 0) return idx + 1
    }
    return streamCompletedSteps.length
  }, [streamActiveStep, streamCompletedSteps])

  // 移动端岗位卡片渲染辅助
  const handleSelectJob = useCallback((jobId: number) => {
    setSelectedJobId(jobId)
  }, [])

  return (
    <div className="mx-auto max-w-6xl">
      {/* 页面标题 */}
      <div className="page-header">
        <h2>岗位技能匹配</h2>
      </div>

      {/* 桌面端步骤指示器 */}
      <Card className="mb-6 hidden md:block">
        <CardContent className="pt-6">
          <Stepper steps={WIZARD_STEPS} currentStep={wizardStep} />
        </CardContent>
      </Card>

      {/* 移动端简化步骤指示器 */}
      <Card className="mb-6 md:hidden">
        <CardContent className="pt-6">
          <div className="text-sm font-medium text-foreground">
            步骤 {wizardStep}/{WIZARD_STEPS.length}：{WIZARD_STEPS[wizardStep - 1]?.label}
          </div>
          <div className="mt-3 h-2 w-full rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${(wizardStep / WIZARD_STEPS.length) * 100}%` }}
            />
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            {WIZARD_STEPS[wizardStep - 1]?.description}
          </div>
        </CardContent>
      </Card>

      {/* 错误提示 */}
      {error && <div className="error-banner mb-6">{error}</div>}

      {/* ---- 步骤 1：填写画像 ---- */}
      {wizardStep === 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">1. 填写技能画像</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {effectiveProfile && (
              <div className="rounded-lg border bg-primary/5 p-3 text-sm">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <span className="flex items-center gap-2">
                    <User className="h-4 w-4 text-primary" />
                    当前使用画像：
                    <span className="font-medium">{effectiveProfile.name}</span>
                  </span>
                  <span className="text-xs text-muted-foreground">
                    修改下方表单后将基于当前画像创建新匹配
                  </span>
                </div>
              </div>
            )}

            <ResumeProfileForm
              value={profileFormData}
              onChange={setProfileFormData}
              disabled={uploadLoading || loading}
            />

            {/* 快速示例与简历上传 */}
            <div className="flex flex-col gap-4 rounded-lg border border-dashed border-input bg-muted/30 p-4">
              <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="text-sm font-medium">上传简历</div>
                  <div className="text-xs text-muted-foreground">支持 PDF、DOCX、图片（PNG/JPG/WEBP/GIF），上传后自动解析并填充下方画像</div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleUploadClick}
                  disabled={uploadLoading}
                  className="min-h-[44px] md:min-h-9"
                >
                  <Upload className="mr-2 h-4 w-4" />
                  {uploadLoading ? '上传中...' : '选择简历'}
                </Button>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.png,.jpg,.jpeg,.webp,.gif,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,image/png,image/jpeg,image/webp,image/gif"
                className="hidden"
                onChange={handleFileChange}
              />
              {uploadError && <div className="text-xs text-destructive">{uploadError}</div>}

              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="text-muted-foreground">快速示例：</span>
                {EXAMPLE_PROFILES.map((ex) => (
                  <Button
                    key={ex.label}
                    variant="outline"
                    size="sm"
                    onClick={() => applyExample(ex)}
                    disabled={loading}
                    className="min-h-[44px] md:min-h-9"
                  >
                    {ex.label}
                  </Button>
                ))}
              </div>
            </div>

            {/* 底部操作 */}
            <div className="flex justify-end pt-2">
              <Button onClick={nextStep} disabled={!canEnterStep2} className="min-h-[44px] md:min-h-10">
                下一步
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ---- 步骤 2：选择目标岗位 ---- */}
      {wizardStep === 2 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">2. 选择目标岗位</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 搜索与工具栏 */}
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex gap-2">
                <Input
                  value={jobSearch}
                  onChange={(e) => setJobSearch(e.target.value)}
                  placeholder="搜索岗位"
                  className="h-11 w-full sm:w-64"
                  onKeyDown={(e) => e.key === 'Enter' && loadJobs(jobSearch)}
                />
                <Button
                  variant="secondary"
                  size="icon"
                  onClick={() => loadJobs(jobSearch)}
                  disabled={jobsLoading}
                  className="h-11 w-11 shrink-0"
                >
                  <Search className="h-4 w-4" />
                </Button>
              </div>
              <div className="flex items-center gap-3">
                {!isDesktop && (
                  <div className="flex flex-1 items-center gap-2">
                    <Button
                      variant={sortConfig.key === 'salary' ? 'secondary' : 'outline'}
                      size="sm"
                      onClick={() => toggleSort('salary')}
                      className="h-10 flex-1"
                    >
                      薪资 {sortIcon('salary')}
                    </Button>
                    <Button
                      variant={sortConfig.key === 'posted_at' ? 'secondary' : 'outline'}
                      size="sm"
                      onClick={() => toggleSort('posted_at')}
                      className="h-10 flex-1"
                    >
                      时间 {sortIcon('posted_at')}
                    </Button>
                  </div>
                )}
                <div className="flex shrink-0 items-center gap-2">
                  <Checkbox
                    id="stream"
                    checked={useStream}
                    onCheckedChange={(checked) => setUseStream(Boolean(checked))}
                    disabled={loading}
                  />
                  <label htmlFor="stream" className="text-sm text-muted-foreground">
                    流式分析
                  </label>
                </div>
              </div>
            </div>

            {/* 岗位总数 */}
            <div className="text-xs text-muted-foreground">
              共 {jobs.length} 个岗位{selectedJob ? `，已选择：${selectedJob.title}` : ''}
            </div>

            {/* 桌面端岗位表格 */}
            <div className="hidden max-h-[420px] overflow-auto rounded-md border md:block">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">选择</TableHead>
                    <TableHead>岗位</TableHead>
                    <TableHead>公司</TableHead>
                    <TableHead>城市</TableHead>
                    <TableHead
                      className="cursor-pointer"
                      onClick={() => toggleSort('salary')}
                    >
                      <span className="flex items-center">薪资 {sortIcon('salary')}</span>
                    </TableHead>
                    <TableHead
                      className="cursor-pointer"
                      onClick={() => toggleSort('posted_at')}
                    >
                      <span className="flex items-center">发布时间 {sortIcon('posted_at')}</span>
                    </TableHead>
                    <TableHead>经验</TableHead>
                    <TableHead>来源</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobsLoading ? (
                    // 骨架屏：加载岗位列表
                    Array.from({ length: 5 }).map((_, i) => (
                      <TableRow key={i}>
                        <TableCell><Skeleton className="h-4 w-4 rounded-full" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-28" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                      </TableRow>
                    ))
                  ) : sortedJobs.length ? (
                    sortedJobs.map((job) => (
                      <TableRow
                        key={job.id}
                        className="cursor-pointer data-[state=selected]:bg-muted"
                        data-state={selectedJobId === job.id ? 'selected' : undefined}
                        onClick={() => setSelectedJobId(job.id)}
                      >
                        <TableCell onClick={(e) => e.stopPropagation()}>
                          <input
                            type="radio"
                            name="selected-job"
                            checked={selectedJobId === job.id}
                            onChange={() => setSelectedJobId(job.id)}
                            className="h-4 w-4 cursor-pointer accent-primary"
                          />
                        </TableCell>
                        <TableCell className="font-medium">{job.title}</TableCell>
                        <TableCell>{job.company.name}</TableCell>
                        <TableCell>{job.city}</TableCell>
                        <TableCell>{formatSalary(job)}</TableCell>
                        <TableCell>{formatPostedAt(job)}</TableCell>
                        <TableCell>{job.experience_level}</TableCell>
                        <TableCell>
                          {job.source ? (
                            <div className="flex items-center gap-1">
                              <Badge variant="outline" className="max-w-[100px] truncate text-xs">
                                {getSourceLabel(job.source)}
                              </Badge>
                              {job.source_url && (
                                <a
                                  href={job.source_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center text-muted-foreground hover:text-foreground"
                                  onClick={(e) => e.stopPropagation()}
                                  title="跳转到原始页面"
                                >
                                  <ExternalLink className="h-3 w-3" />
                                </a>
                              )}
                            </div>
                          ) : (
                            '-'
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                        暂无岗位
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            {/* 移动端岗位卡片列表 */}
            <div className="space-y-3 md:hidden">
              {jobsLoading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-36 w-full rounded-lg" />
                ))
              ) : sortedJobs.length ? (
                sortedJobs.map((job) => (
                  <MobileJobCard
                    key={job.id}
                    job={job}
                    selected={selectedJobId === job.id}
                    onSelect={handleSelectJob}
                  />
                ))
              ) : (
                <div className="py-12 text-center text-muted-foreground">暂无岗位</div>
              )}
            </div>

            {/* 流式进度 */}
            {loading && useStream && (
              <Card className="border-primary/20 bg-primary/5">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">匹配进度</CardTitle>
                </CardHeader>
                <CardContent>
                  <Stepper
                    steps={STREAM_STEP_ORDER.map((key) => ({ label: STREAM_STEP_LABELS[key] || key }))}
                    currentStep={streamStepIndex}
                  />
                </CardContent>
              </Card>
            )}

            {/* 底部操作 */}
            <div className="flex justify-between pt-2">
              <Button variant="outline" onClick={prevStep} className="min-h-[44px] md:min-h-10">
                <ArrowLeft className="mr-2 h-4 w-4" />
                上一步
              </Button>
              <Button onClick={handleMatch} disabled={!selectedJobId || loading} className="min-h-[44px] md:min-h-10">
                {loading ? '匹配中...' : `开始匹配${useStream ? '（流式）' : ''}`}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ---- 步骤 3：查看匹配结果 ---- */}
      {wizardStep === 3 && (
        <div className="space-y-6">
          {result && (
            <>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-end">
                <Button variant="outline" onClick={openCompareWithCurrentJob} className="min-h-[44px] md:min-h-10">
                  <Scale className="mr-2 h-4 w-4" />
                  与其他岗位对比
                </Button>
                <ExportPDFButton job={selectedJob} match={result} />
              </div>
              <MatchResultCard matchResult={result} jobTitle={selectedJob?.title} job={selectedJob} />
              {radarSkills.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">技能对比雷达图</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <SkillRadarChart skills={radarSkills} />
                  </CardContent>
                </Card>
              )}
            </>
          )}
          {!result && !loading && (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                暂无匹配结果，请返回上一步重新匹配。
              </CardContent>
            </Card>
          )}
          <div className="flex flex-col-reverse justify-between gap-3 sm:flex-row">
            <Button variant="outline" onClick={() => setWizardStep(2)} className="min-h-[44px] md:min-h-10">
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回选择岗位
            </Button>
            <Button onClick={resetMatch} className="min-h-[44px] md:min-h-10">
              <RotateCcw className="mr-2 h-4 w-4" />
              重新匹配
            </Button>
          </div>
        </div>
      )}

      {/* 岗位对比抽屉 */}
      {compareOpen && <JobCompareSheet jobs={compareJobs} onClose={closeCompare} />}
    </div>
  )
}

// 提取为独立组件，避免在父组件内部定义导致每次渲染都重新创建
interface MobileJobCardProps {
  job: Job
  selected: boolean
  onSelect: (jobId: number) => void
}

const MobileJobCard = memo(function MobileJobCard({
  job,
  selected,
  onSelect,
}: MobileJobCardProps) {
  return (
    <Card
      className={cn(
        'cursor-pointer transition-colors',
        selected ? 'border-primary bg-primary/5' : 'hover:bg-accent'
      )}
      onClick={() => onSelect(job.id)}
    >
      <CardContent className="space-y-3 p-4">
        <div className="flex items-start gap-3">
          <input
            type="radio"
            name="selected-job"
            checked={selected}
            onChange={() => onSelect(job.id)}
            className="mt-1 h-5 w-5 cursor-pointer accent-primary"
            onClick={(e) => e.stopPropagation()}
          />
          <div className="min-w-0 flex-1 space-y-1">
            <div className="truncate font-medium">{job.title}</div>
            <div className="text-sm text-muted-foreground">
              {job.company.name} · {job.city}
            </div>
            <div className="text-sm">{formatSalary(job)}</div>
            <div className="flex flex-wrap gap-1">
              {job.required_skills.slice(0, 4).map((skill, idx) => (
                <Badge key={idx} variant="secondary" className="text-xs">
                  {skill}
                </Badge>
              ))}
              {job.required_skills.length > 4 && (
                <Badge variant="outline" className="text-xs">
                  +{job.required_skills.length - 4}
                </Badge>
              )}
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
          <span>经验：{job.experience_level}</span>
          <span>发布：{formatPostedAt(job)}</span>
          {job.source && (
            <span className="flex items-center gap-1">
              来源：
              <Badge variant="outline" className="text-[10px]">
                {getSourceLabel(job.source)}
              </Badge>
              {job.source_url && (
                <a
                  href={job.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center hover:text-foreground"
                  onClick={(e) => e.stopPropagation()}
                >
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  )
})
