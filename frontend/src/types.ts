export interface ApiResponse<T> {
  code: number
  data: T
  message: string
}

export interface PaginatedResponse<T> {
  total: number
  items: T[]
}

export interface PagedResponse<T> {
  total: number
  page: number
  size: number
  items: T[]
}

/* ---- Skill ---- */

export interface Skill {
  id: number
  name: string
  category: string
  aliases: string[]
  definition: string
}

export interface SkillListResponse {
  total: number
  items: Skill[]
}

export interface RelatedSkill {
  skill: string
  relation_type: string
  weight: number
  target_skill: string
}

export interface SkillStatistics {
  total_skills: number
  total_relations: number
  category_distribution: Array<{ category: string; count: number }>
  hot_skills: Array<{ skill: string; count: number }>
  relation_type_distribution: Array<{ relation_type: string; count: number }>
}

/* ---- Company ---- */

export interface Company {
  id: number
  name: string
  industry: string
  size: string
  city: string
}

/* ---- Job ---- */

export interface Job {
  id: number
  title: string
  company: Company
  city: string
  salary_min: number
  salary_max: number
  experience_level: string
  education_level: string
  required_skills: string[]
  description: string
  source: string
  source_url: string
  posted_at: string | null
}

export interface JobListResponse {
  total: number
  page: number
  size: number
  items: Job[]
}

export interface JobSearchResult {
  id: string
  document: string
  metadata: Record<string, unknown>
  score?: number
  keyword_score?: number
  hybrid_score?: number
  source: string
}

export interface ParsedJD {
  title: string
  company: string
  required_skills: string[]
  experience_level: string
  education_level: string
  implicit_needs: string[]
  fresh_graduate_friendly?: boolean | null
  barriers_for_fresh_graduates?: string[]
}

export interface JobStatistics {
  total_jobs: number
  total_companies: number
  avg_salary_min: number
  avg_salary_max: number
  top_cities: Array<{ city: string; count: number }>
  top_industries: Array<{ industry: string; count: number }>
  hot_skills: Array<{ skill: string; count: number }>
  experience_distribution: Array<{ experience_level: string; count: number }>
}

/* ---- UserSkillProfile ---- */

export interface UserSkillProfile {
  id: number
  name: string
  skills: string[]
  experience_level: string
  target_job_titles: string[]
  is_active: boolean
  created_at: string | null
}

export interface UserSkillProfileListResponse {
  total: number
  items: UserSkillProfile[]
}

/* ---- 新手引导画像类型 ---- */

// 创建画像请求体
export interface ProfileCreateRequest {
  name: string
  skills: string[]
  experience_level: string
  target_job_titles: string[]
  is_active?: boolean
}

// 更新画像请求体
export interface ProfileUpdateRequest {
  name?: string
  skills?: string[]
  experience_level?: string
  target_job_titles?: string[]
  is_active?: boolean
}

// 创建画像后的响应结构
export interface ProfileResponse {
  id: number
  name: string
  skills: string[]
  experience_level: string
  target_job_titles: string[]
  is_active: boolean
  created_at: string | null
}

// 岗位智能推荐结果
export interface JobRecommendationOut {
  job: Job
  match_score: number
  skill_score: number | null
  experience_match: number | null
  education_match: number | null
  matched_skills: string[]
  missing_skills: string[]
  transferable_skills: string[]
}

/* ---- MatchResult ---- */

export interface MatchResult {
  id: number
  user_profile_id: number
  job_id: number
  match_score: number
  skill_score?: number | null
  experience_match?: number | null
  education_match?: number | null
  matched_skills: string[]
  missing_skills: string[]
  transferable_skills: string[]
  analysis_summary: string | null
  created_at: string | null
}

/* ---- FavoriteJob ---- */

export interface FavoriteJobOut {
  id: number
  profile_id: number
  job_id: number
  created_at: string | null
  job: Job | null
}

export interface FavoriteJobListResponse {
  total: number
  page: number
  size: number
  items: FavoriteJobOut[]
}

export interface LearningPathItem {
  skill: string
  difficulty: string
  estimated_weeks: number
  resource_type: string
  prerequisites: string[]
}

export interface LearningPath {
  profile_id: number
  job_id: number
  learning_path: LearningPathItem[]
}

/* ---- Trend ---- */

export interface TrendAnalysis {
  summary: string
  top_skills: string[]
  avg_salary_range: string
  hot_job_titles: string[]
  key_metrics: Record<string, number | string>
}

/* ---- Dashboard ---- */

export interface DashboardData {
  jobs: JobStatistics
  skills: SkillStatistics
  trends: TrendAnalysis
}

/* ---- Resume ---- */

export interface ResumeBasicInfo {
  name: string
  phone: string
  email: string
  gender: string
  birth_date: string
  political_status: string
  marriage: string
  wechat: string
  qq: string
  id_card_type: string
  id_card_no: string
  hukou: string
  jiguan: string
  // 大疆网申字段扩展
  highest_education: string
  recruitment_source: string
  other_intended_position: string
  accept_city_adjustment: string
  current_country: string
  current_location: string
}

export interface ResumeEducation {
  school: string
  major: string
  degree: string
  start_date: string
  end_date: string
  description: string
  // 大疆网申字段扩展
  department: string
  ranking: string
  has_lab_experience: string
}

export interface ResumeWorkExperience {
  company: string
  position: string
  start_date: string
  end_date: string
  description: string
}

export interface ResumeProjectExperience {
  name: string
  role: string
  start_date: string
  end_date: string
  description: string
}

export interface ResumeJobIntention {
  expected_position: string
  expected_city: string
  expected_salary: string
  expected_industry: string
}

export interface ResumeCompetitionExperience {
  start_date: string
  end_date: string
  competition_name: string
  other_competition_name: string
  description: string
}

export interface ResumePublication {
  title: string
}

export interface ResumePortfolio {
  file_url: string
  link_url: string
}

export interface ResumeUploadOut {
  name: string
  skills: string[]
  experience_level: string
  education_level: string
  raw_text: string
  basic_info: ResumeBasicInfo
  education: ResumeEducation[]
  work_experience: ResumeWorkExperience[]
  project_experience: ResumeProjectExperience[]
  competition_experience: ResumeCompetitionExperience[]
  awards: string[]
  certifications: string[]
  language_skills: string[]
  self_evaluation: string
  job_intention: ResumeJobIntention
  publications: ResumePublication[]
  portfolio: ResumePortfolio[]
  fuzzy?: boolean
  obstacles?: ObstacleAnalysis
}

export interface JDUploadOut {
  raw_text: string
  parsed: ParsedJD
}

export interface ResumeOptimizeRequest {
  resume_data: Record<string, unknown>
  jd_text: string
  field_order?: string[]
}

export interface ResumeOptimizeOut {
  original_project_experience: ResumeProjectExperience[]
  original_work_experience: ResumeWorkExperience[]
  original_self_evaluation: string
  optimized_project_experience: ResumeProjectExperience[]
  optimized_work_experience: ResumeWorkExperience[]
  optimized_self_evaluation: string
  field_order: string[]
  optimization_notes: string
  suggested_changes: string[]
}

/* ---- Stream ---- */

export interface MatchStreamEvent {
  node?: string
  status?: string
  message?: string
  final_result?: MatchResult
}

/* ---- Search ---- */

export interface SearchRequest {
  query: string
  intent?: string
  location?: string
  top_n?: number
  summarize?: boolean
}

export interface SearchResultItem {
  title: string
  url: string
  snippet: string
}

export interface SearchOut {
  query: string
  original_query: string
  intent: string
  source: string
  results: SearchResultItem[]
  summary: string
  error?: string
}

/* ---- Obstacles ---- */

export interface ObstacleItem {
  key: string
  label: string
  detail: string
  description?: string
  suggestions?: string[]
}

export interface ObstacleAnalysis {
  obstacles: ObstacleItem[]
  summary: string
  action_plan: string[]
  severity_score: number
}

/* ---- Config Tests ---- */

export interface ConfigTestItem {
  name: string
  category: string
  status: 'ok' | 'fail' | 'skip'
  message: string
  response_time_ms: number
  configured: boolean
  detail: Record<string, any>
}

export interface ConfigTestReport {
  tested_at: string
  total: number
  passed: number
  failed: number
  skipped: number
  results: ConfigTestItem[]
}

export interface ObstacleAnalysisRequest {
  resume_data?: Record<string, unknown>
  jd_data?: Record<string, unknown>
}

/* ---- Care (求职关怀) ---- */

export interface EncouragementQuote {
  text: string
  category: string
  scene: string
}

export interface PracticalTip {
  title: string
  category: string
  content: string
  difficulty: string
  estimated_time: string
}

export interface JobSearchStage {
  stage: string
  duration: string
  tasks: string[]
  tips: string
}

export interface CareDashboard {
  daily_quote: EncouragementQuote
  tips: PracticalTip[]
  stages: JobSearchStage[]
  stats: {
    total_jobs: number
    fresh_friendly_jobs: number
    fresh_friendly_ratio: number
  }
  profile: {
    name: string
    skills_count: number
    target_job_titles: string[]
    experience_level: string
  } | null
  generated_at: string
}
