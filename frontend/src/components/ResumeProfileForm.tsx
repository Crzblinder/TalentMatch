import { useEffect, useMemo, useState } from 'react'
import {
  AlertCircle,
  Briefcase,
  GraduationCap,
  Lightbulb,
  Mail,
  Trophy,
  User,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import type {
  ResumeBasicInfo,
  ResumeEducation,
  ResumeProjectExperience,
  ResumeWorkExperience,
  ResumeUploadOut,
} from '@/types'

// 经验级别选项（与岗位库/匹配页保持一致）
const EXPERIENCE_LEVELS = ['不限', '应届生', '1-3年', '3-5年', '5-10年', '10年以上']

const GENDER_OPTIONS = ['男', '女', '保密']

const POLITICAL_OPTIONS = [
  '中共党员',
  '中共预备党员',
  '共青团员',
  '群众',
  '民主党派',
  '无党派人士',
]

const MARRIAGE_OPTIONS = ['未婚', '已婚', '保密']

const ID_CARD_TYPE_OPTIONS = [
  '居民身份证',
  '护照',
  '港澳居民来往内地通行证',
  '台湾居民来往大陆通行证',
  '其他',
]

const PROVINCE_OPTIONS = [
  '北京',
  '上海',
  '天津',
  '重庆',
  '河北',
  '山西',
  '辽宁',
  '吉林',
  '黑龙江',
  '江苏',
  '浙江',
  '安徽',
  '福建',
  '江西',
  '山东',
  '河南',
  '湖北',
  '湖南',
  '广东',
  '海南',
  '四川',
  '贵州',
  '云南',
  '陕西',
  '甘肃',
  '青海',
  '台湾',
  '内蒙古',
  '广西',
  '西藏',
  '宁夏',
  '新疆',
  '香港',
  '澳门',
]

// 左侧导航分组配置
const SECTIONS = [
  { id: 'basic', label: '基本信息', icon: User },
  { id: 'intention', label: '求职意向', icon: Briefcase },
  { id: 'education', label: '教育经历', icon: GraduationCap },
  { id: 'work', label: '工作经历', icon: Briefcase },
  { id: 'project', label: '项目经历', icon: Lightbulb },
  { id: 'skills', label: '技能优势', icon: Trophy },
  { id: 'other', label: '其他信息', icon: Mail },
] as const

export interface ProfileFormData {
  name: string
  phone: string
  email: string
  gender: string
  birthDate: string
  politicalStatus: string
  marriage: string
  idCardType: string
  hukou: string
  jiguan: string
  expectedPosition: string
  expectedCity: string
  expectedSalary: string
  expectedIndustry: string
  skillsText: string
  selfEvaluation: string
  experienceLevel: string
  targetJobTitles: string
  education: ResumeEducation[]
  workExperience: ResumeWorkExperience[]
  projectExperience: ResumeProjectExperience[]
  awardsText: string
  certificationsText: string
  languageSkillsText: string
}

interface ResumeProfileFormProps {
  value: ProfileFormData
  onChange: (value: ProfileFormData) => void
  disabled?: boolean
}

const EMPTY_BASIC: ResumeBasicInfo = {
  name: '',
  phone: '',
  email: '',
  gender: '',
  birth_date: '',
  political_status: '',
  marriage: '',
  wechat: '',
  qq: '',
  id_card_type: '',
  id_card_no: '',
  hukou: '',
  jiguan: '',
}

const EMPTY_EDUCATION: ResumeEducation = {
  school: '',
  major: '',
  degree: '',
  start_date: '',
  end_date: '',
  description: '',
}

const EMPTY_WORK: ResumeWorkExperience = {
  company: '',
  position: '',
  start_date: '',
  end_date: '',
  description: '',
}

const EMPTY_PROJECT: ResumeProjectExperience = {
  name: '',
  role: '',
  start_date: '',
  end_date: '',
  description: '',
}

export function resumeToFormData(resume: ResumeUploadOut): ProfileFormData {
  const basic = resume.basic_info || EMPTY_BASIC
  const intention = resume.job_intention || {
    expected_position: '',
    expected_city: '',
    expected_salary: '',
    expected_industry: '',
  }

  return {
    name: resume.name || basic.name || '',
    phone: basic.phone || '',
    email: basic.email || '',
    gender: basic.gender || '',
    birthDate: basic.birth_date || '',
    politicalStatus: basic.political_status || '',
    marriage: basic.marriage || '',
    idCardType: basic.id_card_type || '',
    hukou: basic.hukou || '',
    jiguan: basic.jiguan || '',
    expectedPosition: intention.expected_position || '',
    expectedCity: intention.expected_city || '',
    expectedSalary: intention.expected_salary || '',
    expectedIndustry: intention.expected_industry || '',
    skillsText: (resume.skills || []).join(', '),
    selfEvaluation: resume.self_evaluation || '',
    experienceLevel: resume.experience_level || '不限',
    targetJobTitles: '',
    education: (resume.education || []).length > 0 ? resume.education : [EMPTY_EDUCATION],
    workExperience: (resume.work_experience || []).length > 0 ? resume.work_experience : [EMPTY_WORK],
    projectExperience:
      (resume.project_experience || []).length > 0 ? resume.project_experience : [EMPTY_PROJECT],
    awardsText: (resume.awards || []).join('\n'),
    certificationsText: (resume.certifications || []).join('\n'),
    languageSkillsText: (resume.language_skills || []).join('\n'),
  }
}

export function emptyProfileFormData(): ProfileFormData {
  return {
    name: '',
    phone: '',
    email: '',
    gender: '',
    birthDate: '',
    politicalStatus: '',
    marriage: '',
    idCardType: '',
    hukou: '',
    jiguan: '',
    expectedPosition: '',
    expectedCity: '',
    expectedSalary: '',
    expectedIndustry: '',
    skillsText: '',
    selfEvaluation: '',
    experienceLevel: '不限',
    targetJobTitles: '',
    education: [EMPTY_EDUCATION],
    workExperience: [EMPTY_WORK],
    projectExperience: [EMPTY_PROJECT],
    awardsText: '',
    certificationsText: '',
    languageSkillsText: '',
  }
}

function countFilled(fields: (string | undefined)[]): number {
  return fields.filter((f) => f && String(f).trim().length > 0).length
}

function FieldTip({ empty, tip }: { empty: boolean; tip: string }) {
  if (!empty) return null
  return (
    <span className="ml-2 text-xs font-normal text-amber-600">
      {tip}
    </span>
  )
}

export default function ResumeProfileForm({ value, onChange, disabled }: ResumeProfileFormProps) {
  const [activeTab, setActiveTab] = useState('basic')

  // 当基本信息变化时，自动更新目标岗位为期望岗位
  useEffect(() => {
    if (value.expectedPosition && !value.targetJobTitles) {
      onChange({ ...value, targetJobTitles: value.expectedPosition })
    }
  }, [value.expectedPosition, value.targetJobTitles])

  const update = <K extends keyof ProfileFormData>(key: K, val: ProfileFormData[K]) => {
    onChange({ ...value, [key]: val })
  }

  const updateEducation = (index: number, field: keyof ResumeEducation, val: string) => {
    const next = [...value.education]
    next[index] = { ...next[index], [field]: val }
    onChange({ ...value, education: next })
  }

  const addEducation = () => {
    onChange({ ...value, education: [...value.education, EMPTY_EDUCATION] })
  }

  const removeEducation = (index: number) => {
    const next = value.education.filter((_, i) => i !== index)
    onChange({ ...value, education: next.length ? next : [EMPTY_EDUCATION] })
  }

  const updateWork = (index: number, field: keyof ResumeWorkExperience, val: string) => {
    const next = [...value.workExperience]
    next[index] = { ...next[index], [field]: val }
    onChange({ ...value, workExperience: next })
  }

  const addWork = () => {
    onChange({ ...value, workExperience: [...value.workExperience, EMPTY_WORK] })
  }

  const removeWork = (index: number) => {
    const next = value.workExperience.filter((_, i) => i !== index)
    onChange({ ...value, workExperience: next.length ? next : [EMPTY_WORK] })
  }

  const updateProject = (index: number, field: keyof ResumeProjectExperience, val: string) => {
    const next = [...value.projectExperience]
    next[index] = { ...next[index], [field]: val }
    onChange({ ...value, projectExperience: next })
  }

  const addProject = () => {
    onChange({ ...value, projectExperience: [...value.projectExperience, EMPTY_PROJECT] })
  }

  const removeProject = (index: number) => {
    const next = value.projectExperience.filter((_, i) => i !== index)
    onChange({ ...value, projectExperience: next.length ? next : [EMPTY_PROJECT] })
  }

  // 各分组完成度
  const progress = useMemo(() => {
    return {
      basic: {
        filled: countFilled([
          value.name,
          value.phone,
          value.email,
          value.gender,
          value.birthDate,
          value.politicalStatus,
          value.marriage,
          value.idCardType,
          value.hukou,
          value.jiguan,
        ]),
        total: 10,
      },
      intention: {
        filled: countFilled([
          value.expectedPosition,
          value.expectedCity,
          value.expectedSalary,
          value.expectedIndustry,
          value.experienceLevel && value.experienceLevel !== '不限' ? value.experienceLevel : '',
        ]),
        total: 5,
      },
      education: {
        filled: value.education.filter((e) => e.school || e.major || e.degree).length,
        total: value.education.length || 1,
      },
      work: {
        filled: value.workExperience.filter((w) => w.company || w.position).length,
        total: value.workExperience.length || 1,
      },
      project: {
        filled: value.projectExperience.filter((p) => p.name || p.role).length,
        total: value.projectExperience.length || 1,
      },
      skills: {
        filled: countFilled([value.skillsText, value.selfEvaluation]),
        total: 2,
      },
      other: {
        filled: countFilled([value.awardsText, value.certificationsText, value.languageSkillsText]),
        total: 3,
      },
    }
  }, [value])

  const incompleteSections = SECTIONS.filter(
    (section) => progress[section.id as keyof typeof progress].filled < progress[section.id as keyof typeof progress].total
  )

  return (
    <div className="space-y-4">
      {/* 顶部未填项提醒与跳转指引 */}
      {incompleteSections.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          <div className="mb-2 flex items-center gap-2 font-medium">
            <AlertCircle className="h-4 w-4" />
            以下分组还可以继续完善，点击即可跳转：
          </div>
          <div className="flex flex-wrap gap-2">
            {incompleteSections.map((section) => {
              const Icon = section.icon
              const p = progress[section.id as keyof typeof progress]
              return (
                <Button
                  key={section.id}
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-7 gap-1 border-amber-200 bg-white text-xs hover:bg-amber-100"
                  onClick={() => setActiveTab(section.id)}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {section.label}
                  <Badge variant="secondary" className="ml-1 h-4 px-1 text-[10px]">
                    {p.filled}/{p.total}
                  </Badge>
                </Button>
              )
            })}
          </div>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex min-h-[560px] flex-col gap-4 md:flex-row">
        {/* 左侧导航 */}
        <TabsList className="flex h-auto flex-col items-stretch justify-start gap-1.5 rounded-xl border bg-muted/40 p-2 shadow-sm md:w-48">
          {SECTIONS.map((section) => {
            const Icon = section.icon
            const p = progress[section.id as keyof typeof progress]
            const incomplete = p.filled < p.total
            return (
              <TabsTrigger
                key={section.id}
                value={section.id}
                className="relative flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2.5 text-sm font-medium transition-all hover:bg-muted data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm"
              >
                <span className="flex items-center gap-2">
                  <Icon className="h-4 w-4" />
                  {section.label}
                </span>
                {incomplete && (
                  <Badge variant="outline" className="h-5 px-1.5 text-[10px] text-amber-600 border-amber-200 bg-amber-50 data-[state=active]:border-primary-foreground/30 data-[state=active]:bg-primary-foreground/20 data-[state=active]:text-primary-foreground">
                    {p.filled}/{p.total}
                  </Badge>
                )}
              </TabsTrigger>
            )
          })}
        </TabsList>

        {/* 右侧内容 */}
        <div className="flex-1 rounded-xl border bg-card p-4 shadow-sm md:p-6">
          <TabsContent value="basic" className="mt-0 space-y-4">
          <h3 className="text-base font-semibold">
            基本信息
            <FieldTip empty={progress.basic.filled < progress.basic.total} tip="建议补充完整，提升匹配准确度" />
          </h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>
                姓名
                {!value.name && <span className="text-amber-600"> *</span>}
              </Label>
              <Input value={value.name} onChange={(e) => update('name', e.target.value)} placeholder="请输入姓名" disabled={disabled} />
            </div>
            <div className="space-y-1.5">
              <Label>性别</Label>
              <Select value={value.gender} onValueChange={(v) => update('gender', v)} disabled={disabled}>
                <SelectTrigger>
                  <SelectValue placeholder="选择性别" />
                </SelectTrigger>
                <SelectContent>
                  {GENDER_OPTIONS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>
                手机号
                {!value.phone && <span className="text-xs text-muted-foreground">（建议补充）</span>}
              </Label>
              <Input value={value.phone} onChange={(e) => update('phone', e.target.value)} placeholder="请输入手机号" disabled={disabled} />
            </div>
            <div className="space-y-1.5">
              <Label>
                邮箱
                {!value.email && <span className="text-xs text-muted-foreground">（建议补充）</span>}
              </Label>
              <Input value={value.email} onChange={(e) => update('email', e.target.value)} placeholder="请输入邮箱" disabled={disabled} />
            </div>
            <div className="space-y-1.5">
              <Label>出生日期</Label>
              <Input type="date" value={value.birthDate} onChange={(e) => update('birthDate', e.target.value)} disabled={disabled} />
            </div>
            <div className="space-y-1.5">
              <Label>政治面貌</Label>
              <Select value={value.politicalStatus} onValueChange={(v) => update('politicalStatus', v)} disabled={disabled}>
                <SelectTrigger>
                  <SelectValue placeholder="选择政治面貌" />
                </SelectTrigger>
                <SelectContent>
                  {POLITICAL_OPTIONS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>婚姻状况</Label>
              <Select value={value.marriage} onValueChange={(v) => update('marriage', v)} disabled={disabled}>
                <SelectTrigger>
                  <SelectValue placeholder="选择婚姻状况" />
                </SelectTrigger>
                <SelectContent>
                  {MARRIAGE_OPTIONS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>身份证类型</Label>
              <Select value={value.idCardType} onValueChange={(v) => update('idCardType', v)} disabled={disabled}>
                <SelectTrigger>
                  <SelectValue placeholder="选择身份证类型" />
                </SelectTrigger>
                <SelectContent>
                  {ID_CARD_TYPE_OPTIONS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>户口所在地</Label>
              <Select value={value.hukou} onValueChange={(v) => update('hukou', v)} disabled={disabled}>
                <SelectTrigger>
                  <SelectValue placeholder="选择户口所在地" />
                </SelectTrigger>
                <SelectContent>
                  {PROVINCE_OPTIONS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>籍贯</Label>
              <Select value={value.jiguan} onValueChange={(v) => update('jiguan', v)} disabled={disabled}>
                <SelectTrigger>
                  <SelectValue placeholder="选择籍贯" />
                </SelectTrigger>
                <SelectContent>
                  {PROVINCE_OPTIONS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="intention" className="mt-0 space-y-4">
          <h3 className="text-base font-semibold">
            求职意向
            <FieldTip empty={progress.intention.filled < progress.intention.total} tip="填写意向可提升岗位推荐精准度" />
          </h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>
                期望岗位
                {!value.expectedPosition && <span className="text-xs text-muted-foreground">（建议补充）</span>}
              </Label>
              <Input value={value.expectedPosition} onChange={(e) => update('expectedPosition', e.target.value)} placeholder="例如：产品经理" disabled={disabled} />
            </div>
            <div className="space-y-1.5">
              <Label>经验级别</Label>
              <Select value={value.experienceLevel} onValueChange={(v) => update('experienceLevel', v)} disabled={disabled}>
                <SelectTrigger>
                  <SelectValue placeholder="选择经验" />
                </SelectTrigger>
                <SelectContent>
                  {EXPERIENCE_LEVELS.map((level) => (
                    <SelectItem key={level} value={level}>
                      {level}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>期望城市</Label>
              <Input value={value.expectedCity} onChange={(e) => update('expectedCity', e.target.value)} placeholder="例如：上海" disabled={disabled} />
            </div>
            <div className="space-y-1.5">
              <Label>期望薪资</Label>
              <Input value={value.expectedSalary} onChange={(e) => update('expectedSalary', e.target.value)} placeholder="例如：15k-25k" disabled={disabled} />
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label>期望行业</Label>
              <Input value={value.expectedIndustry} onChange={(e) => update('expectedIndustry', e.target.value)} placeholder="例如：互联网" disabled={disabled} />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="education" className="mt-0 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold">
              教育经历
              <FieldTip empty={progress.education.filled < progress.education.total} tip="教育背景影响岗位学历匹配" />
            </h3>
            <Button type="button" variant="outline" size="sm" onClick={addEducation} disabled={disabled}>
              + 添加
            </Button>
          </div>
          {value.education.map((edu, idx) => (
            <div key={idx} className="relative rounded-lg border p-3">
              {value.education.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-2 top-2 h-7 text-destructive"
                  onClick={() => removeEducation(idx)}
                  disabled={disabled}
                >
                  删除
                </Button>
              )}
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>学校</Label>
                  <Input value={edu.school} onChange={(e) => updateEducation(idx, 'school', e.target.value)} placeholder="学校名称" disabled={disabled} />
                </div>
                <div className="space-y-1.5">
                  <Label>专业</Label>
                  <Input value={edu.major} onChange={(e) => updateEducation(idx, 'major', e.target.value)} placeholder="专业" disabled={disabled} />
                </div>
                <div className="space-y-1.5">
                  <Label>学历</Label>
                  <Input value={edu.degree} onChange={(e) => updateEducation(idx, 'degree', e.target.value)} placeholder="本科 / 硕士" disabled={disabled} />
                </div>
                <div className="space-y-1.5">
                  <Label>起止时间</Label>
                  <div className="flex items-center gap-2">
                    <Input value={edu.start_date} onChange={(e) => updateEducation(idx, 'start_date', e.target.value)} placeholder="2020-09" disabled={disabled} />
                    <span className="text-muted-foreground">~</span>
                    <Input value={edu.end_date} onChange={(e) => updateEducation(idx, 'end_date', e.target.value)} placeholder="2024-06" disabled={disabled} />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </TabsContent>

        <TabsContent value="work" className="mt-0 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold">
              工作经历
              <FieldTip empty={progress.work.filled < progress.work.total} tip="工作经历是经验判断的重要依据" />
            </h3>
            <Button type="button" variant="outline" size="sm" onClick={addWork} disabled={disabled}>
              + 添加
            </Button>
          </div>
          {value.workExperience.map((work, idx) => (
            <div key={idx} className="relative rounded-lg border p-3">
              {value.workExperience.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-2 top-2 h-7 text-destructive"
                  onClick={() => removeWork(idx)}
                  disabled={disabled}
                >
                  删除
                </Button>
              )}
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>公司</Label>
                  <Input value={work.company} onChange={(e) => updateWork(idx, 'company', e.target.value)} placeholder="公司名称" disabled={disabled} />
                </div>
                <div className="space-y-1.5">
                  <Label>职位</Label>
                  <Input value={work.position} onChange={(e) => updateWork(idx, 'position', e.target.value)} placeholder="职位" disabled={disabled} />
                </div>
                <div className="space-y-1.5">
                  <Label>起止时间</Label>
                  <div className="flex items-center gap-2">
                    <Input value={work.start_date} onChange={(e) => updateWork(idx, 'start_date', e.target.value)} placeholder="2022-07" disabled={disabled} />
                    <span className="text-muted-foreground">~</span>
                    <Input value={work.end_date} onChange={(e) => updateWork(idx, 'end_date', e.target.value)} placeholder="至今" disabled={disabled} />
                  </div>
                </div>
                <div className="space-y-1.5 sm:col-span-2">
                  <Label>工作内容</Label>
                  <Textarea value={work.description} onChange={(e) => updateWork(idx, 'description', e.target.value)} placeholder="简述工作内容和成果" disabled={disabled} />
                </div>
              </div>
            </div>
          ))}
        </TabsContent>

        <TabsContent value="project" className="mt-0 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold">
              项目经历
              <FieldTip empty={progress.project.filled < progress.project.total} tip="项目经历能补充技能匹配维度" />
            </h3>
            <Button type="button" variant="outline" size="sm" onClick={addProject} disabled={disabled}>
              + 添加
            </Button>
          </div>
          {value.projectExperience.map((proj, idx) => (
            <div key={idx} className="relative rounded-lg border p-3">
              {value.projectExperience.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-2 top-2 h-7 text-destructive"
                  onClick={() => removeProject(idx)}
                  disabled={disabled}
                >
                  删除
                </Button>
              )}
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>项目名称</Label>
                  <Input value={proj.name} onChange={(e) => updateProject(idx, 'name', e.target.value)} placeholder="项目名称" disabled={disabled} />
                </div>
                <div className="space-y-1.5">
                  <Label>担任角色</Label>
                  <Input value={proj.role} onChange={(e) => updateProject(idx, 'role', e.target.value)} placeholder="负责人 / 开发者" disabled={disabled} />
                </div>
                <div className="space-y-1.5">
                  <Label>起止时间</Label>
                  <div className="flex items-center gap-2">
                    <Input value={proj.start_date} onChange={(e) => updateProject(idx, 'start_date', e.target.value)} placeholder="2023-03" disabled={disabled} />
                    <span className="text-muted-foreground">~</span>
                    <Input value={proj.end_date} onChange={(e) => updateProject(idx, 'end_date', e.target.value)} placeholder="至今" disabled={disabled} />
                  </div>
                </div>
                <div className="space-y-1.5 sm:col-span-2">
                  <Label>项目描述</Label>
                  <Textarea value={proj.description} onChange={(e) => updateProject(idx, 'description', e.target.value)} placeholder="简述项目背景、职责和成果" disabled={disabled} />
                </div>
              </div>
            </div>
          ))}
        </TabsContent>

        <TabsContent value="skills" className="mt-0 space-y-4">
          <h3 className="text-base font-semibold">
            技能优势
            <FieldTip empty={progress.skills.filled < progress.skills.total} tip="技能是岗位匹配的核心依据" />
          </h3>
          <div className="space-y-1.5">
            <Label>
              技能
              {!value.skillsText && <span className="text-amber-600"> *</span>}
            </Label>
            <Textarea
              value={value.skillsText}
              onChange={(e) => update('skillsText', e.target.value)}
              placeholder="输入技能，用逗号分隔，例如：Python, MySQL, 数据分析"
              disabled={disabled}
            />
            <p className="text-xs text-muted-foreground">多个技能请用中文或英文逗号分隔</p>
          </div>
          <div className="space-y-1.5">
            <Label>个人优势 / 自我评价</Label>
            <Textarea
              value={value.selfEvaluation}
              onChange={(e) => update('selfEvaluation', e.target.value)}
              placeholder="简述你的核心优势和特点"
              disabled={disabled}
            />
          </div>
        </TabsContent>

        <TabsContent value="other" className="mt-0 space-y-4">
          <h3 className="text-base font-semibold">
            其他信息
            <FieldTip empty={progress.other.filled < progress.other.total} tip="补充信息可让匹配更立体" />
          </h3>
          <div className="space-y-1.5">
            <Label>获奖情况（每行一条）</Label>
            <Textarea value={value.awardsText} onChange={(e) => update('awardsText', e.target.value)} placeholder="例如：全国人工智能应用创新大赛 国家级二等奖" disabled={disabled} />
          </div>
          <div className="space-y-1.5">
            <Label>资格证书（每行一条）</Label>
            <Textarea value={value.certificationsText} onChange={(e) => update('certificationsText', e.target.value)} placeholder="例如：计算机二级" disabled={disabled} />
          </div>
          <div className="space-y-1.5">
            <Label>语言能力（每行一条）</Label>
            <Textarea value={value.languageSkillsText} onChange={(e) => update('languageSkillsText', e.target.value)} placeholder="例如：CET-6: 601" disabled={disabled} />
          </div>
        </TabsContent>
      </div>
    </Tabs>
    </div>
  )
}
