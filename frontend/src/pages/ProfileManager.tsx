import { useMemo, useState } from 'react'
import { Edit2, Plus, Trash2, User } from 'lucide-react'

import { useProfile } from '@/components/ProfileContext'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import type { ProfileCreateRequest, ProfileUpdateRequest, UserSkillProfile } from '@/types'

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

interface FormState {
  name: string
  skillsText: string
  experienceLevel: string
  targetJobTitlesText: string
  isActive: boolean
}

const emptyForm = (): FormState => ({
  name: '',
  skillsText: '',
  experienceLevel: '不限',
  targetJobTitlesText: '',
  isActive: false,
})

const formFromProfile = (profile: UserSkillProfile): FormState => ({
  name: profile.name,
  skillsText: profile.skills.join(', '),
  experienceLevel: profile.experience_level,
  targetJobTitlesText: profile.target_job_titles.join(', '),
  isActive: profile.is_active,
})

const parseCommaList = (text: string) =>
  text
    .split(/[,，]/)
    .map((s) => s.trim())
    .filter(Boolean)

export default function ProfileManager() {
  const { profiles, loading, createProfile, updateProfile, deleteProfile, setActiveProfile } =
    useProfile()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingProfile, setEditingProfile] = useState<UserSkillProfile | null>(null)
  const [form, setForm] = useState<FormState>(emptyForm())
  const [submitting, setSubmitting] = useState(false)

  const [deleteTarget, setDeleteTarget] = useState<UserSkillProfile | null>(null)
  const [deleting, setDeleting] = useState(false)

  const openCreate = () => {
    setEditingProfile(null)
    setForm(emptyForm())
    setDialogOpen(true)
  }

  const openEdit = (profile: UserSkillProfile) => {
    setEditingProfile(profile)
    setForm(formFromProfile(profile))
    setDialogOpen(true)
  }

  const closeDialog = () => {
    setDialogOpen(false)
    setEditingProfile(null)
  }

  const handleSubmit = async () => {
    if (!form.name.trim() || !form.skillsText.trim()) return
    setSubmitting(true)
    try {
      const payloadBase = {
        name: form.name.trim(),
        skills: parseCommaList(form.skillsText),
        experience_level: form.experienceLevel,
        target_job_titles: parseCommaList(form.targetJobTitlesText),
      }
      if (editingProfile) {
        const payload: ProfileUpdateRequest = { ...payloadBase, is_active: form.isActive }
        await updateProfile(editingProfile.id, payload)
      } else {
        const payload: ProfileCreateRequest = { ...payloadBase, is_active: form.isActive }
        await createProfile(payload)
      }
      closeDialog()
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await deleteProfile(deleteTarget.id)
      setDeleteTarget(null)
    } finally {
      setDeleting(false)
    }
  }

  const sortedProfiles = useMemo(
    () => [...profiles].sort((a, b) => (b.is_active ? 1 : 0) - (a.is_active ? 1 : 0)),
    [profiles]
  )

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-2xl font-bold tracking-tight">画像管理</h2>
        <Button onClick={openCreate} className="min-h-[44px]">
          <Plus className="mr-2 h-4 w-4" />
          新建画像
        </Button>
      </div>

      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-4">
                <Skeleton className="h-6 w-1/3" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : sortedProfiles.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <User className="mx-auto mb-4 h-12 w-12 opacity-50" />
            <p>暂无画像，点击右上角新建画像开始使用。</p>
            <Button className="mt-4 min-h-[44px]" onClick={openCreate}>
              <Plus className="mr-2 h-4 w-4" />
              新建画像
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {sortedProfiles.map((profile) => (
            <Card key={profile.id} className={cn(profile.is_active && 'border-primary/50 bg-primary/5')}>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-start justify-between gap-3 text-lg">
                  <div className="flex items-center gap-2">
                    <User className="h-5 w-5 text-primary" />
                    <span className="truncate">{profile.name}</span>
                    {profile.is_active && (
                      <Badge variant="default" className="h-5 px-1.5 text-[10px]">
                        活跃
                      </Badge>
                    )}
                  </div>
                  <div className="flex shrink-0 items-center gap-1">
                    {!profile.is_active && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="min-h-[44px] px-2 md:min-h-0"
                        onClick={() => setActiveProfile(profile.id)}
                      >
                        设为活跃
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-11 w-11 md:h-9 md:w-9"
                      onClick={() => openEdit(profile)}
                      aria-label="编辑画像"
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-11 w-11 text-destructive hover:text-destructive md:h-9 md:w-9"
                      onClick={() => setDeleteTarget(profile)}
                      aria-label="删除画像"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 pt-0">
                <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                  <span>经验：</span>
                  <Badge variant="outline">{profile.experience_level}</Badge>
                  <span className="ml-2">技能：</span>
                  {profile.skills.slice(0, 6).map((skill) => (
                    <Badge key={skill} variant="secondary" className="text-xs">
                      {skill}
                    </Badge>
                  ))}
                  {profile.skills.length > 6 && (
                    <Badge variant="outline" className="text-xs">
                      +{profile.skills.length - 6}
                    </Badge>
                  )}
                </div>
                {profile.target_job_titles.length > 0 && (
                  <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                    <span>目标岗位：</span>
                    {profile.target_job_titles.map((title) => (
                      <Badge key={title} variant="outline" className="text-xs">
                        {title}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* 创建/编辑弹窗 */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingProfile ? '编辑画像' : '新建画像'}</DialogTitle>
            <DialogDescription>
              维护画像的基本信息、技能与目标岗位。设为活跃后，岗位匹配与收藏将默认使用该画像。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label>
                画像名称 <span className="text-destructive">*</span>
              </Label>
              <Input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="例如：Java 后端工程师"
                className="min-h-[44px] md:min-h-10"
              />
            </div>
            <div className="space-y-1.5">
              <Label>
                技能 <span className="text-destructive">*</span>
              </Label>
              <Textarea
                value={form.skillsText}
                onChange={(e) => setForm((f) => ({ ...f, skillsText: e.target.value }))}
                placeholder="用逗号分隔，例如：Java, Spring Boot, MySQL"
                className="min-h-[88px]"
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>经验级别</Label>
                <Select
                  value={form.experienceLevel}
                  onValueChange={(v) => setForm((f) => ({ ...f, experienceLevel: v }))}
                >
                  <SelectTrigger className="min-h-[44px] md:min-h-10">
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
              <div className="space-y-1.5">
                <Label>目标岗位</Label>
                <Input
                  value={form.targetJobTitlesText}
                  onChange={(e) => setForm((f) => ({ ...f, targetJobTitlesText: e.target.value }))}
                  placeholder="用逗号分隔"
                  className="min-h-[44px] md:min-h-10"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="is-active"
                checked={form.isActive}
                onCheckedChange={(checked) =>
                  setForm((f) => ({ ...f, isActive: Boolean(checked) }))
                }
              />
              <label htmlFor="is-active" className="text-sm font-medium">
                设为当前活跃画像
              </label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={closeDialog} disabled={submitting} className="min-h-[44px] md:min-h-10">
              取消
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!form.name.trim() || !form.skillsText.trim() || submitting}
              className="min-h-[44px] md:min-h-10"
            >
              {submitting ? '保存中...' : editingProfile ? '保存' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认弹窗 */}
      <Dialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>删除画像</DialogTitle>
            <DialogDescription>
              确定要删除画像「{deleteTarget?.name}」吗？相关匹配记录与收藏也将被删除，此操作不可恢复。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteTarget(null)}
              disabled={deleting}
              className="min-h-[44px] md:min-h-10"
            >
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleting}
              className="min-h-[44px] md:min-h-10"
            >
              {deleting ? '删除中...' : '删除'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
