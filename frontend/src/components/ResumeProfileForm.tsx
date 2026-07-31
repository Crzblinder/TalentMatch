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

import { useMediaQuery } from '@/hooks/useMediaQuery'
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
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import type {
  ResumeBasicInfo,
  ResumeCompetitionExperience,
  ResumeEducation,
  ResumePortfolio,
  ResumeProjectExperience,
  ResumeUploadOut,
  ResumeWorkExperience,
} from '@/types'

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

const EDUCATION_LEVEL_OPTIONS = ['大专', '本科', '硕士', '博士', '其他']

const RECRUITMENT_SOURCE_OPTIONS = [
  '校园宣讲会',
  '招聘网站',
  '社交媒体',
  '内推',
  '猎头',
  '学校就业中心',
  '其他',
]

const YES_NO_OPTIONS = ['是', '否']

const COUNTRY_OPTIONS = ['中国', '美国', '英国', '日本', '德国', '法国', '其他']

const LAB_EXPERIENCE_OPTIONS = ['是', '否', '未知']

// 左侧导航分组配置
const SECTIONS = [
  { id: 'basic', label: '基本信息', icon: User },
  { id: 'intention', label: '求职意向', icon: Briefcase },
  { id: 'education', label: '教育经历', icon: GraduationCap },
  { id: 'work', label: '工作经历', icon: Briefcase },
  { id: 'project', label: '项目经历', icon: Lightbulb },
  { id: 'competition', label: '赛事经历', icon: Trophy },
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
  // 大疆网申字段扩展
  highestEducation: string
  recruitmentSource: string
  otherIntendedPosition: string
  acceptCityAdjustment: string
  currentCountry: string
  currentLocation: string
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
  competitionExperience: ResumeCompetitionExperience[]
  awardsText: string
  certificationsText: string
  languageSkillsText: string
  publicationsText: string
  portfolio: ResumePortfolio[]
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
  // 大疆网申字段扩展
  highest_education: '',
  recruitment_source: '',
  other_intended_position: '',
  accept_city_adjustment: '',
  current_country: '',
  current_location: '',
}

const EMPTY_EDUCATION: ResumeEducation = {
  school: '',
  major: '',
  degree: '',
  start_date: '',
  end_date: '',
  description: '',
  // 大疆网申字段扩展
  department: '',
  ranking: '',
  has_lab_experience: '',
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

const EMPTY_COMPETITION: ResumeCompetitionExperience = {
  start_date: '',
  end_date: '',
  competition_name: '',
  other_competition_name: '',
  description: '',
}

const EMPTY_PORTFOLIO: ResumePortfolio = {
  file_url: '',
  link_url: '',
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
    // 大疆网申字段扩展
    highestEducation: basic.highest_education || '',
    recruitmentSource: basic.recruitment_source || '',
    otherIntendedPosition: basic.other_intended_position || '',
    acceptCityAdjustment: basic.accept_city_adjustment || '',
    currentCountry: basic.current_country || '',
    currentLocation: basic.current_location || '',
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
    competitionExperience:
      (resume.competition_experience || []).length > 0
        ? resume.competition_experience
        : [EMPTY_COMPETITION],
    awardsText: (resume.awards || []).join('\n'),
    certificationsText: (resume.certifications || []).join('\n'),
    languageSkillsText: (resume.language_skills || []).join('\n'),
    publicationsText: (resume.publications || []).map((p) => p.title).join('\n'),
    portfolio: (resume.portfolio || []).length > 0 ? resume.portfolio : [EMPTY_PORTFOLIO],
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
    // 大疆网申字段扩展
    highestEducation: '',
    recruitmentSource: '',
    otherIntendedPosition: '',
    acceptCityAdjustment: '',
    currentCountry: '',
    currentLocation: '',
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
    competitionExperience: [EMPTY_COMPETITION],
    awardsText: '',
    certificationsText: '',
    languageSkillsText: '',
    publicationsText: '',
    portfolio: [EMPTY_PORTFOLIO],
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
  const [openAccordion, setOpenAccordion] = useState<string[]>(['basic'])
  const isDesktop = useMediaQuery('(min-width: 768px)')

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

  const updateCompetition = (
    index: number,
    field: keyof ResumeCompetitionExperience,
    val: string,
  ) => {
    const next = [...value.competitionExperience]
    next[index] = { ...next[index], [field]: val }
    onChange({ ...value, competitionExperience: next })
  }

  const addCompetition = () => {
    onChange({ ...value, competitionExperience: [...value.competitionExperience, EMPTY_COMPETITION] })
  }

  const removeCompetition = (index: number) => {
    const next = value.competitionExperience.filter((_, i) => i !== index)
    onChange({ ...value, competitionExperience: next.length ? next : [EMPTY_COMPETITION] })
  }

  const updatePortfolio = (index: number, field: keyof ResumePortfolio, val: string) => {
    const next = [...value.portfolio]
    next[index] = { ...next[index], [field]: val }
    onChange({ ...value, portfolio: next })
  }

  const addPortfolio = () => {
    onChange({ ...value, portfolio: [...value.portfolio, EMPTY_PORTFOLIO] })
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
          value.highestEducation,
          value.recruitmentSource,
          value.currentCountry,
          value.currentLocation,
          value.acceptCityAdjustment,
        ]),
        total: 15,
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
      competition: {
        filled: value.competitionExperience.filter((c) => c.competition_name || c.description)
          .length,
        total: value.competitionExperience.length || 1,
      },
      skills: {
        filled: countFilled([value.skillsText, value.selfEvaluation]),
        total: 2,
      },
      other: {
        filled: countFilled([
          value.awardsText,
          value.certificationsText,
          value.languageSkillsText,
          value.publicationsText,
        ]),
        total: 4,
      },
    }
  }, [value])

  const incompleteSections = SECTIONS.filter(
    (section) => progress[section.id as keyof typeof progress].filled < progress[section.id as keyof typeof progress].total
  )

  const inputClass = 'min-h-[44px] md:min-h-10'
  const selectTriggerClass = 'min-h-[44px] md:min-h-10'
  const addBtnClass = 'min-h-[44px] md:min-h-9'

  const sectionContent = (sectionId: string) => {
    switch (sectionId) {
      case 'basic':
        return (
          <div className="space-y-4">
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
                <Input
                  value={value.name}
                  onChange={(e) => update('name', e.target.value)}
                  placeholder="请输入姓名"
                  disabled={disabled}
                  className={inputClass}
                />
              </div>
              <div className="space-y-1.5">
                <Label>性别</Label>
                <Select value={value.gender} onValueChange={(v) => update('gender', v)} disabled={disabled}>
                  <SelectTrigger className={selectTriggerClass}>
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
                <Input
                  value={value.phone}
                  onChange={(e) => update('phone', e.target.value)}
                  placeholder="请输入手机号"
                  disabled={disabled}
                  className={inputClass}
                />
              </div>
              <div className="space-y-1.5">
                <Label>
                  邮箱
                  {!value.email && <span className="text-xs text-muted-foreground">（建议补充）</span>}
                </Label>
                <Input
                  value={value.email}
                  onChange={(e) => update('email', e.target.value)}
                  placeholder="请输入邮箱"
                  disabled={disabled}
                  className={inputClass}
                />
              </div>
              <div className="space-y-1.5">
                <Label>出生日期</Label>
                <Input type="date" value={value.birthDate} onChange={(e) => update('birthDate', e.target.value)} disabled={disabled} className={inputClass} />
              </div>
              <div className="space-y-1.5">
                <Label>政治面貌</Label>
                <Select value={value.politicalStatus} onValueChange={(v) => update('politicalStatus', v)} disabled={disabled}>
                  <SelectTrigger className={selectTriggerClass}>
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
                  <SelectTrigger className={selectTriggerClass}>
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
                  <SelectTrigger className={selectTriggerClass}>
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
                  <SelectTrigger className={selectTriggerClass}>
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
                  <SelectTrigger className={selectTriggerClass}>
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
              <div className="space-y-1.5">
                <Label>最高学历</Label>
                <Select
                  value={value.highestEducation}
                  onValueChange={(v) => update('highestEducation', v)}
                  disabled={disabled}
                >
                  <SelectTrigger className={selectTriggerClass}>
                    <SelectValue placeholder="选择最高学历" />
                  </SelectTrigger>
                  <SelectContent>
                    {EDUCATION_LEVEL_OPTIONS.map((option) => (
                      <SelectItem key={option} value={option}>
                        {option}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>招聘信息来源</Label>
                <Select
                  value={value.recruitmentSource}
                  onValueChange={(v) => update('recruitmentSource', v)}
                  disabled={disabled}
                >
                  <SelectTrigger className={selectTriggerClass}>
                    <SelectValue placeholder="选择来源" />
                  </SelectTrigger>
                  <SelectContent>
                    {RECRUITMENT_SOURCE_OPTIONS.map((option) => (
                      <SelectItem key={option} value={option}>
                        {option}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>其他意向职位</Label>
                <Input
                  value={value.otherIntendedPosition}
                  onChange={(e) => update('otherIntendedPosition', e.target.value)}
                  placeholder="请输入其他意向职位"
                  disabled={disabled}
                  className={inputClass}
                />
              </div>
              <div className="space-y-1.5">
                <Label>是否接受意向城市调剂</Label>
                <Select
                  value={value.acceptCityAdjustment}
                  onValueChange={(v) => update('acceptCityAdjustment', v)}
                  disabled={disabled}
                >
                  <SelectTrigger className={selectTriggerClass}>
                    <SelectValue placeholder="选择是否接受" />
                  </SelectTrigger>
                  <SelectContent>
                    {YES_NO_OPTIONS.map((option) => (
                      <SelectItem key={option} value={option}>
                        {option}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>当前所在国家</Label>
                <Select
                  value={value.currentCountry}
                  onValueChange={(v) => update('currentCountry', v)}
                  disabled={disabled}
                >
                  <SelectTrigger className={selectTriggerClass}>
                    <SelectValue placeholder="选择国家" />
                  </SelectTrigger>
                  <SelectContent>
                    {COUNTRY_OPTIONS.map((option) => (
                      <SelectItem key={option} value={option}>
                        {option}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>当前所在地</Label>
                <Select
                  value={value.currentLocation}
                  onValueChange={(v) => update('currentLocation', v)}
                  disabled={disabled}
                >
                  <SelectTrigger className={selectTriggerClass}>
                    <SelectValue placeholder="选择当前所在地" />
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
          </div>
        )

      case 'intention':
        return (
          <div className="space-y-4">
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
                <Input
                  value={value.expectedPosition}
                  onChange={(e) => update('expectedPosition', e.target.value)}
                  placeholder="例如：产品经理"
                  disabled={disabled}
                  className={inputClass}
                />
              </div>
              <div className="space-y-1.5">
                <Label>经验级别</Label>
                <Select value={value.experienceLevel} onValueChange={(v) => update('experienceLevel', v)} disabled={disabled}>
                  <SelectTrigger className={selectTriggerClass}>
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
                <Label>期望城市</Label>
                <Input value={value.expectedCity} onChange={(e) => update('expectedCity', e.target.value)} placeholder="例如：上海" disabled={disabled} className={inputClass} />
              </div>
              <div className="space-y-1.5">
                <Label>期望薪资</Label>
                <Input value={value.expectedSalary} onChange={(e) => update('expectedSalary', e.target.value)} placeholder="例如：15k-25k" disabled={disabled} className={inputClass} />
              </div>
              <div className="space-y-1.5 sm:col-span-2">
                <Label>期望行业</Label>
                <Input value={value.expectedIndustry} onChange={(e) => update('expectedIndustry', e.target.value)} placeholder="例如：互联网" disabled={disabled} className={inputClass} />
              </div>
            </div>
          </div>
        )

      case 'education':
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold">
                教育经历
                <FieldTip empty={progress.education.filled < progress.education.total} tip="教育背景影响岗位学历匹配" />
              </h3>
              <Button type="button" variant="outline" size="sm" onClick={addEducation} disabled={disabled} className={addBtnClass}>
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
                    className="absolute right-2 top-2 h-8 text-destructive md:h-7"
                    onClick={() => removeEducation(idx)}
                    disabled={disabled}
                  >
                    删除
                  </Button>
                )}
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label>学校</Label>
                    <Input value={edu.school} onChange={(e) => updateEducation(idx, 'school', e.target.value)} placeholder="学校名称" disabled={disabled} className={inputClass} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>专业</Label>
                    <Input value={edu.major} onChange={(e) => updateEducation(idx, 'major', e.target.value)} placeholder="专业" disabled={disabled} className={inputClass} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>院系</Label>
                    <Input value={edu.department} onChange={(e) => updateEducation(idx, 'department', e.target.value)} placeholder="例如：计算机学院" disabled={disabled} className={inputClass} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>学历</Label>
                    <Select
                      value={edu.degree}
                      onValueChange={(v) => updateEducation(idx, 'degree', v)}
                      disabled={disabled}
                    >
                      <SelectTrigger className={selectTriggerClass}>
                        <SelectValue placeholder="选择学历" />
                      </SelectTrigger>
                      <SelectContent>
                        {EDUCATION_LEVEL_OPTIONS.map((option) => (
                          <SelectItem key={option} value={option}>
                            {option}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label>起止时间</Label>
                    <div className="flex items-center gap-2">
                      <Input value={edu.start_date} onChange={(e) => updateEducation(idx, 'start_date', e.target.value)} placeholder="2020-09" disabled={disabled} className={inputClass} />
                      <span className="text-muted-foreground">~</span>
                      <Input value={edu.end_date} onChange={(e) => updateEducation(idx, 'end_date', e.target.value)} placeholder="2024-06" disabled={disabled} className={inputClass} />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label>成绩排名</Label>
                    <Input value={edu.ranking} onChange={(e) => updateEducation(idx, 'ranking', e.target.value)} placeholder="例如：前 10%" disabled={disabled} className={inputClass} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>是否有实验室经历</Label>
                    <Select
                      value={edu.has_lab_experience}
                      onValueChange={(v) => updateEducation(idx, 'has_lab_experience', v)}
                      disabled={disabled}
                    >
                      <SelectTrigger className={selectTriggerClass}>
                        <SelectValue placeholder="选择是否有实验室经历" />
                      </SelectTrigger>
                      <SelectContent>
                        {LAB_EXPERIENCE_OPTIONS.map((option) => (
                          <SelectItem key={option} value={option}>
                            {option}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )

      case 'work':
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold">
                工作经历
                <FieldTip empty={progress.work.filled < progress.work.total} tip="工作经历是经验判断的重要依据" />
              </h3>
              <Button type="button" variant="outline" size="sm" onClick={addWork} disabled={disabled} className={addBtnClass}>
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
                    className="absolute right-2 top-2 h-8 text-destructive md:h-7"
                    onClick={() => removeWork(idx)}
                    disabled={disabled}
                  >
                    删除
                  </Button>
                )}
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label>公司</Label>
                    <Input value={work.company} onChange={(e) => updateWork(idx, 'company', e.target.value)} placeholder="公司名称" disabled={disabled} className={inputClass} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>职位</Label>
                    <Input value={work.position} onChange={(e) => updateWork(idx, 'position', e.target.value)} placeholder="职位" disabled={disabled} className={inputClass} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>起止时间</Label>
                    <div className="flex items-center gap-2">
                      <Input value={work.start_date} onChange={(e) => updateWork(idx, 'start_date', e.target.value)} placeholder="2022-07" disabled={disabled} className={inputClass} />
                      <span className="text-muted-foreground">~</span>
                      <Input value={work.end_date} onChange={(e) => updateWork(idx, 'end_date', e.target.value)} placeholder="至今" disabled={disabled} className={inputClass} />
                    </div>
                  </div>
                  <div className="space-y-1.5 sm:col-span-2">
                    <Label>工作内容</Label>
                    <Textarea value={work.description} onChange={(e) => updateWork(idx, 'description', e.target.value)} placeholder="简述工作内容和成果" disabled={disabled} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )

      case 'project':
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold">
                项目经历
                <FieldTip empty={progress.project.filled < progress.project.total} tip="项目经历能补充技能匹配维度" />
              </h3>
              <Button type="button" variant="outline" size="sm" onClick={addProject} disabled={disabled} className={addBtnClass}>
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
                    className="absolute right-2 top-2 h-8 text-destructive md:h-7"
                    onClick={() => removeProject(idx)}
                    disabled={disabled}
                  >
                    删除
                  </Button>
                )}
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label>项目名称</Label>
                    <Input value={proj.name} onChange={(e) => updateProject(idx, 'name', e.target.value)} placeholder="项目名称" disabled={disabled} className={inputClass} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>担任角色</Label>
                    <Input value={proj.role} onChange={(e) => updateProject(idx, 'role', e.target.value)} placeholder="负责人 / 开发者" disabled={disabled} className={inputClass} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>起止时间</Label>
                    <div className="flex items-center gap-2">
                      <Input value={proj.start_date} onChange={(e) => updateProject(idx, 'start_date', e.target.value)} placeholder="2023-03" disabled={disabled} className={inputClass} />
                      <span className="text-muted-foreground">~</span>
                      <Input value={proj.end_date} onChange={(e) => updateProject(idx, 'end_date', e.target.value)} placeholder="至今" disabled={disabled} className={inputClass} />
                    </div>
                  </div>
                  <div className="space-y-1.5 sm:col-span-2">
                    <Label>项目描述</Label>
                    <Textarea value={proj.description} onChange={(e) => updateProject(idx, 'description', e.target.value)} placeholder="简述项目背景、职责和成果" disabled={disabled} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )

      case 'competition':
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold">
                赛事经历
                <FieldTip empty={progress.competition.filled < progress.competition.total} tip="竞赛经历能体现综合能力" />
              </h3>
              <Button type="button" variant="outline" size="sm" onClick={addCompetition} disabled={disabled} className={addBtnClass}>
                + 添加
              </Button>
            </div>
            {value.competitionExperience.map((comp, idx) => (
              <div key={idx} className="relative rounded-lg border p-3">
                {value.competitionExperience.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-2 top-2 h-8 text-destructive md:h-7"
                    onClick={() => removeCompetition(idx)}
                    disabled={disabled}
                  >
                    删除
                  </Button>
                )}
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label>赛事名称</Label>
                    <Input
                      value={comp.competition_name}
                      onChange={(e) => updateCompetition(idx, 'competition_name', e.target.value)}
                      placeholder="例如：挑战杯"
                      disabled={disabled}
                      className={inputClass}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label>其他赛事名称</Label>
                    <Input
                      value={comp.other_competition_name}
                      onChange={(e) => updateCompetition(idx, 'other_competition_name', e.target.value)}
                      placeholder="选择其他时填写"
                      disabled={disabled}
                      className={inputClass}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label>起止时间</Label>
                    <div className="flex items-center gap-2">
                      <Input
                        value={comp.start_date}
                        onChange={(e) => updateCompetition(idx, 'start_date', e.target.value)}
                        placeholder="2023-03"
                        disabled={disabled}
                        className={inputClass}
                      />
                      <span className="text-muted-foreground">~</span>
                      <Input
                        value={comp.end_date}
                        onChange={(e) => updateCompetition(idx, 'end_date', e.target.value)}
                        placeholder="至今"
                        disabled={disabled}
                        className={inputClass}
                      />
                    </div>
                  </div>
                  <div className="space-y-1.5 sm:col-span-2">
                    <Label>赛事描述</Label>
                    <Textarea
                      value={comp.description}
                      onChange={(e) => updateCompetition(idx, 'description', e.target.value)}
                      placeholder="简述参赛内容和成果"
                      disabled={disabled}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )

      case 'skills':
        return (
          <div className="space-y-4">
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
          </div>
        )

      case 'other':
        return (
          <div className="space-y-4">
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
            <div className="space-y-1.5">
              <Label>论文/期刊（每行一条）</Label>
              <Textarea
                value={value.publicationsText}
                onChange={(e) => update('publicationsText', e.target.value)}
                placeholder="例如：基于深度学习的图像分类方法研究"
                disabled={disabled}
              />
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label>作品附件/链接</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addPortfolio}
                  disabled={disabled}
                  className={addBtnClass}
                >
                  + 添加
                </Button>
              </div>
              {value.portfolio.map((item, idx) => (
                <div key={idx} className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Input
                      value={item.file_url}
                      onChange={(e) => updatePortfolio(idx, 'file_url', e.target.value)}
                      placeholder="附件文件地址"
                      disabled={disabled}
                      className={inputClass}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Input
                      value={item.link_url}
                      onChange={(e) => updatePortfolio(idx, 'link_url', e.target.value)}
                      placeholder="作品链接（如 GitHub）"
                      disabled={disabled}
                      className={inputClass}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )

      default:
        return null
    }
  }

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
                  className="h-9 gap-1 border-amber-200 bg-white text-xs hover:bg-amber-100 md:h-7"
                  onClick={() => {
                    setActiveTab(section.id)
                    setOpenAccordion((prev) =>
                      prev.includes(section.id) ? prev : [...prev, section.id]
                    )
                  }}
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

      {isDesktop ? (
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
            {SECTIONS.map((section) => (
              <TabsContent key={section.id} value={section.id} className="mt-0 space-y-4">
                {sectionContent(section.id)}
              </TabsContent>
            ))}
          </div>
        </Tabs>
      ) : (
        /* 移动端：折叠面板 */
        <Accordion
          type="multiple"
          value={openAccordion}
          onValueChange={setOpenAccordion}
          className="rounded-xl border bg-card p-2 shadow-sm"
        >
          {SECTIONS.map((section) => {
            const Icon = section.icon
            const p = progress[section.id as keyof typeof progress]
            const incomplete = p.filled < p.total
            return (
              <AccordionItem key={section.id} value={section.id} className="border-b-0 px-2">
                <AccordionTrigger className="py-3 text-sm font-medium hover:no-underline">
                  <span className="flex items-center gap-2">
                    <Icon className="h-4 w-4" />
                    {section.label}
                    {incomplete && (
                      <Badge variant="outline" className="h-5 px-1.5 text-[10px] text-amber-600 border-amber-200 bg-amber-50">
                        {p.filled}/{p.total}
                      </Badge>
                    )}
                  </span>
                </AccordionTrigger>
                <AccordionContent className="px-1 pb-4">
                  {sectionContent(section.id)}
                </AccordionContent>
              </AccordionItem>
            )
          })}
        </Accordion>
      )}
    </div>
  )
}
