import { useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Sparkles, Upload } from 'lucide-react'

import { api } from '../api'
import type { JobRecommendationOut, ProfileCreateRequest, ProfileResponse } from '../types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'

// 经验级别选项：value 为后端存储的实际值，label 为前端展示文案
// 与岗位库/匹配页保持一致，应届岗在后端统一存储为「应届/在校生」
const EXPERIENCE_LEVELS: { value: string; label: string }[] = [
  { value: '不限', label: '不限' },
  { value: '应届/在校生', label: '应届生' },
  { value: '1-3年', label: '1-3年' },
  { value: '3-5年', label: '3-5年' },
  { value: '5-10年', label: '5-10年' },
  { value: '10年以上', label: '10年以上' },
]

// localStorage 键名
const STORAGE_KEY_COMPLETED = 'onboarding_completed'
const STORAGE_KEY_PROFILE_ID = 'last_profile_id'

interface OnboardingDialogProps {
  // 引导完成或跳过后触发，用于父组件卸载弹窗
  onComplete?: () => void
}

// 新手引导弹窗：分 3 步完成画像创建、岗位推荐与匹配跳转
export default function OnboardingDialog({ onComplete }: OnboardingDialogProps) {
  const navigate = useNavigate()

  // 弹窗显示状态
  const [open, setOpen] = useState(true)

  // 当前步骤：1=创建画像，2=查看推荐，3=确认匹配
  const [step, setStep] = useState(1)

  // 画像输入状态
  const [name, setName] = useState('')
  const [skillsText, setSkillsText] = useState('')
  const [experienceLevel, setExperienceLevel] = useState('不限')
  const [targetText, setTargetText] = useState('')

  // 简历上传相关
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadLoading, setUploadLoading] = useState(false)

  // 已创建画像与推荐结果
  const [profile, setProfile] = useState<ProfileResponse | null>(null)
  const [recommendations, setRecommendations] = useState<JobRecommendationOut[]>([])
  const [recommendationsLoading, setRecommendationsLoading] = useState(false)

  // 用户选中的岗位 ID
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)

  // 全局加载与错误提示
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // 将输入文本解析为数组
  const skills = useMemo(
    () => skillsText.split(/[,，]/).map((s) => s.trim()).filter(Boolean),
    [skillsText],
  )
  const targetJobTitles = useMemo(
    () => targetText.split(/[,，]/).map((s) => s.trim()).filter(Boolean),
    [targetText],
  )

  // 步骤 1：创建临时画像并进入下一步
  const handleCreateProfile = async () => {
    if (!name.trim() || skills.length === 0) return
    setLoading(true)
    setError('')
    try {
      const payload: ProfileCreateRequest = {
        name: name.trim(),
        skills,
        experience_level: experienceLevel,
        target_job_titles: targetJobTitles,
      }
      const created = await api.createProfile(payload)
      setProfile(created)
      // 持久化画像 ID，方便后续页面使用
      localStorage.setItem(STORAGE_KEY_PROFILE_ID, String(created.id))
      setStep(2)
      // 自动加载推荐岗位
      await loadRecommendations(created.id)
    } catch (e: any) {
      setError(e.message || '创建画像失败，请检查输入后重试')
    } finally {
      setLoading(false)
    }
  }

  // 根据画像 ID 加载 Top 5 推荐岗位
  const loadRecommendations = async (profileId: number) => {
    setRecommendationsLoading(true)
    setError('')
    try {
      const items = await api.getRecommendations(profileId, 5)
      setRecommendations(items)
    } catch (e: any) {
      setError(e.message || '加载推荐岗位失败')
    } finally {
      setRecommendationsLoading(false)
    }
  }

  // 上传简历并自动填充画像字段
  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadLoading(true)
    setError('')
    try {
      const resume = await api.uploadResume(file)
      // 姓名优先使用简历解析结果
      setName((prev) => prev || resume.name)
      // 合并已有技能与简历解析出的技能，去重
      setSkillsText((prev) => {
        const existing = prev.split(/[,，]/).map((s) => s.trim()).filter(Boolean)
        const merged = Array.from(new Set([...existing, ...resume.skills]))
        return merged.join(', ')
      })
      // 仅当解析出的经验级别在可选范围内时才覆盖
      if (resume.experience_level && EXPERIENCE_LEVELS.some((l) => l.value === resume.experience_level)) {
        setExperienceLevel(resume.experience_level)
      }
    } catch (e: any) {
      setError(e.message || '简历解析失败')
    } finally {
      setUploadLoading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  // 上一步
  const handlePrev = () => {
    if (step > 1) setStep(step - 1)
  }

  // 下一步：根据当前步骤执行对应逻辑
  const handleNext = () => {
    if (step === 1) {
      handleCreateProfile()
    } else if (step === 2 && selectedJobId) {
      setStep(3)
    }
  }

  // 步骤 3：开始匹配，跳转至匹配页面
  const handleStartMatch = () => {
    if (!selectedJobId) return
    // 标记新手引导已完成
    localStorage.setItem(STORAGE_KEY_COMPLETED, 'true')
    if (profile) {
      localStorage.setItem(STORAGE_KEY_PROFILE_ID, String(profile.id))
    }
    setOpen(false)
    onComplete?.()
    navigate(`/match?jobId=${selectedJobId}`)
  }

  // 跳过引导
  const handleSkip = () => {
    localStorage.setItem(STORAGE_KEY_COMPLETED, 'true')
    setOpen(false)
    onComplete?.()
  }

  // 是否允许进入下一步
  const canGoNext =
    step === 1
      ? name.trim().length > 0 && skills.length > 0
      : step === 2
        ? selectedJobId !== null
        : true

  // 当前选中的推荐岗位
  const selectedRecommendation = recommendations.find((r) => r.job.id === selectedJobId)

  // 渲染步骤 1：创建画像
  const renderStep1 = () => (
    <div className="space-y-4">
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="onboarding-name">
          画像名称
        </label>
        <Input
          id="onboarding-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="例如：Java 后端工程师"
        />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="onboarding-skills">
          技能
        </label>
        <Textarea
          id="onboarding-skills"
          value={skillsText}
          onChange={(e) => setSkillsText(e.target.value)}
          placeholder="输入技能，用逗号分隔，例如：Java, Spring Boot, MySQL, Redis"
        />
        <div className="text-xs text-muted-foreground">已识别 {skills.length} 项技能</div>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium">经验</label>
          <Select value={experienceLevel} onValueChange={setExperienceLevel}>
            <SelectTrigger>
              <SelectValue placeholder="选择经验" />
            </SelectTrigger>
            <SelectContent>
                {EXPERIENCE_LEVELS.map((level) => (
                  <SelectItem key={level.value} value={level.value}>
                    {level.label}
                  </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium" htmlFor="onboarding-target">
            目标岗位（可选）
          </label>
          <Input
            id="onboarding-target"
            value={targetText}
            onChange={(e) => setTargetText(e.target.value)}
            placeholder="用逗号分隔"
          />
        </div>
      </div>
      <div className="rounded-lg border border-dashed border-input bg-muted/30 p-4">
        <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="text-sm font-medium">上传简历</div>
            <div className="text-xs text-muted-foreground">
              支持 PDF、DOCX，上传后自动解析并填充技能
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleUploadClick}
            disabled={uploadLoading}
          >
            <Upload className="mr-2 h-4 w-4" />
            {uploadLoading ? '解析中...' : '选择简历'}
          </Button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>
    </div>
  )

  // 渲染步骤 2：推荐岗位列表
  const renderStep2 = () => (
    <div className="space-y-4">
      {recommendationsLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-28 w-full rounded-lg" />
          ))}
        </div>
      ) : recommendations.length === 0 ? (
        <div className="py-8 text-center text-muted-foreground">暂无推荐岗位</div>
      ) : (
        <div className="space-y-3">
          {recommendations.map((rec) => (
            <Card
              key={rec.job.id}
              className={`cursor-pointer transition-colors ${
                selectedJobId === rec.job.id
                  ? 'border-primary bg-primary/5'
                  : 'hover:bg-accent'
              }`}
              onClick={() => setSelectedJobId(rec.job.id)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-1">
                    <div className="font-medium">{rec.job.title}</div>
                    <div className="text-sm text-muted-foreground">
                      {rec.job.company.name} · {rec.job.city}
                    </div>
                    <div className="text-sm">
                      ¥{rec.job.salary_min.toLocaleString()}-
                      {rec.job.salary_max.toLocaleString()}
                    </div>
                    <div className="flex flex-wrap gap-1 pt-1">
                      {rec.job.required_skills.slice(0, 4).map((skill, idx) => (
                        <Badge key={idx} variant="secondary" className="text-xs">
                          {skill}
                        </Badge>
                      ))}
                      {rec.job.required_skills.length > 4 && (
                        <Badge variant="outline" className="text-xs">
                          +{rec.job.required_skills.length - 4}
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold text-primary">
                      {(rec.match_score * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-muted-foreground">匹配度</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )

  // 渲染步骤 3：确认岗位并开始匹配
  const renderStep3 = () => (
    <div className="space-y-4">
      {selectedRecommendation ? (
        <Card>
          <CardContent className="space-y-3 p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-lg font-semibold">{selectedRecommendation.job.title}</div>
                <div className="text-sm text-muted-foreground">
                  {selectedRecommendation.job.company.name} · {selectedRecommendation.job.city}
                </div>
              </div>
              <div className="text-right">
                <div className="text-xl font-bold text-primary">
                  {(selectedRecommendation.match_score * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-muted-foreground">匹配度</div>
              </div>
            </div>
            <div className="text-sm">
              薪资：¥{selectedRecommendation.job.salary_min.toLocaleString()}-
              {selectedRecommendation.job.salary_max.toLocaleString()}
            </div>
            <div className="flex flex-wrap gap-1">
              {selectedRecommendation.job.required_skills.map((skill, idx) => (
                <Badge key={idx} variant="secondary" className="text-xs">
                  {skill}
                </Badge>
              ))}
            </div>
            <div className="space-y-1 rounded-md bg-muted p-3 text-sm">
              <div>
                <span className="font-medium">已匹配技能：</span>
                {selectedRecommendation.matched_skills.join('、') || '无'}
              </div>
              <div>
                <span className="font-medium">待提升技能：</span>
                {selectedRecommendation.missing_skills.join('、') || '无'}
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="py-8 text-center text-muted-foreground">请先选择一个岗位</div>
      )}
      <Button onClick={handleStartMatch} disabled={!selectedJobId} className="w-full">
        <Sparkles className="mr-2 h-4 w-4" />
        开始匹配
      </Button>
    </div>
  )

  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        // 用户点击关闭、遮罩或按 ESC 时视为跳过引导
        if (!value) handleSkip()
      }}
    >
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>新手引导</DialogTitle>
          <DialogDescription>
            {step === 1 && 'Step 1：创建你的技能画像'}
            {step === 2 && 'Step 2：查看为你推荐的岗位'}
            {step === 3 && 'Step 3：确认岗位并开始匹配'}
          </DialogDescription>
        </DialogHeader>

        {/* 步骤进度条 */}
        <div className="flex items-center gap-2 py-2">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`h-2 flex-1 rounded-full transition-colors ${
                s <= step ? 'bg-primary' : 'bg-muted'
              }`}
            />
          ))}
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* 步骤内容 */}
        {step === 1 && renderStep1()}
        {step === 2 && renderStep2()}
        {step === 3 && renderStep3()}

        {/* 底部操作区 */}
        <div className="flex flex-col gap-3 pt-4 sm:flex-row sm:items-center sm:justify-between">
          <Button variant="ghost" size="sm" onClick={handleSkip}>
            跳过引导
          </Button>
          <div className="flex gap-2">
            {step > 1 && (
              <Button
                variant="outline"
                onClick={handlePrev}
                disabled={loading || recommendationsLoading}
              >
                <ChevronLeft className="mr-2 h-4 w-4" />
                上一步
              </Button>
            )}
            {step < 3 && (
              <Button
                onClick={handleNext}
                disabled={!canGoNext || loading || recommendationsLoading}
              >
                {step === 1 && loading ? '创建中...' : '下一步'}
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
