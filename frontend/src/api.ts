import type {
  ApiResponse,
  ConfigTestReport,
  CareDashboard,
  EncouragementQuote,
  PracticalTip,
  JobSearchStage,
  DashboardData,
  FavoriteJobListResponse,
  FavoriteJobOut,
  Job,
  JobListResponse,
  JobRecommendationOut,
  JobSearchResult,
  JDUploadOut,
  LearningPath,
  MatchResult,
  MatchStreamEvent,
  ObstacleAnalysis,
  ObstacleAnalysisRequest,
  ParsedJD,
  ProfileCreateRequest,
  ProfileResponse,
  ProfileUpdateRequest,
  RelatedSkill,
  ResumeOptimizeOut,
  ResumeOptimizeRequest,
  ResumeUploadOut,
  SearchOut,
  SearchRequest,
  Skill,
  SkillListResponse,
  TrendAnalysis,
  UserSkillProfileListResponse,
} from './types'

// 扩展环境下通过全局变量或 URL 查询参数指定后端地址，Web 开发环境继续走 Vite 代理
function resolveApiBase(): string {
  if (typeof window === 'undefined') return '/api/v1'
  const globalBase = (window as unknown as { TALENTMATCH_API_BASE?: string }).TALENTMATCH_API_BASE
  if (globalBase) return globalBase
  const params = new URLSearchParams(window.location.search)
  const queryBase = params.get('apiBase')
  if (queryBase) return queryBase
  return '/api/v1'
}

const API_BASE = resolveApiBase()

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `HTTP ${res.status}`)
  }
  const wrapper = (await res.json()) as ApiResponse<T>
  return wrapper.data
}

function buildQuery(params: Record<string, string | number | boolean | undefined>): string {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      qs.set(key, String(value))
    }
  })
  return qs.toString()
}

export const api = {
  /* ---- Health ---- */
  healthCheck: (): Promise<{ status: string }> => request('/jobs/health'),

  /* ---- Config Tests ---- */
  getConfigTests: (): Promise<ConfigTestReport> => request('/config-tests'),

  /* ---- Jobs ---- */
  listJobs: (params?: {
    page?: number
    size?: number
    city?: string
    industry?: string
    experience_level?: string
    q?: string
  }): Promise<JobListResponse> => {
    const qs = buildQuery({
      page: params?.page ?? 1,
      size: params?.size ?? 20,
      city: params?.city,
      industry: params?.industry,
      experience_level: params?.experience_level,
      q: params?.q,
    })
    return request(`/jobs?${qs}`)
  },

  getJob: (jobId: number): Promise<Job> => request(`/jobs/${jobId}`),

  searchJobs: (query: string, topK = 10): Promise<JobSearchResult[]> => {
    const qs = buildQuery({ query, top_k: topK })
    return request(`/jobs/search?${qs}`)
  },

  parseJD: (jdText: string): Promise<ParsedJD> =>
    request('/jobs/parse', {
      method: 'POST',
      body: JSON.stringify({ jd_text: jdText }),
    }),

  uploadJD: async (file: File): Promise<JDUploadOut> => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${API_BASE}/jobs/upload`, {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) {
      const err = await res.text()
      throw new Error(err || `HTTP ${res.status}`)
    }
    const wrapper = (await res.json()) as ApiResponse<JDUploadOut>
    return wrapper.data
  },

  /* ---- Resumes ---- */
  uploadResume: async (file: File): Promise<ResumeUploadOut> => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${API_BASE}/resumes/upload`, {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) {
      const err = await res.text()
      throw new Error(err || `HTTP ${res.status}`)
    }
    const wrapper = (await res.json()) as ApiResponse<ResumeUploadOut>
    return wrapper.data
  },

  optimizeResume: (payload: ResumeOptimizeRequest): Promise<ResumeOptimizeOut> =>
    request('/resumes/optimize', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  /* ---- Search ---- */
  search: (payload: SearchRequest): Promise<SearchOut> =>
    request('/search', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  /* ---- Obstacles ---- */
  analyzeObstacles: (payload: ObstacleAnalysisRequest): Promise<ObstacleAnalysis> =>
    request('/obstacles/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  analyzeProfileObstacles: (
    profileId: number,
    payload?: ObstacleAnalysisRequest,
  ): Promise<ObstacleAnalysis> =>
    request(`/profiles/${profileId}/obstacles`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    }),

  /* ---- Skills ---- */
  listSkills: (category?: string): Promise<SkillListResponse> => {
    const qs = buildQuery({ category })
    return request(`/skills${qs ? `?${qs}` : ''}`)
  },

  getSkill: (skillId: number): Promise<Skill> => request(`/skills/${skillId}`),

  getRelatedSkills: (skillId: number, relationType?: string): Promise<RelatedSkill[]> => {
    const qs = buildQuery({ relation_type: relationType })
    return request(`/skills/${skillId}/related${qs ? `?${qs}` : ''}`)
  },

  /* ---- Profiles ---- */
  listProfiles: (): Promise<UserSkillProfileListResponse> => request('/profiles'),

  getActiveProfile: (): Promise<ProfileResponse | null> => request('/profiles/active'),

  getProfile: (profileId: number): Promise<ProfileResponse> =>
    request(`/profiles/${profileId}`),

  // 创建用户画像，返回完整画像信息
  createProfile: (payload: ProfileCreateRequest): Promise<ProfileResponse> =>
    request('/profiles', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // 更新用户画像
  updateProfile: (profileId: number, payload: ProfileUpdateRequest): Promise<ProfileResponse> =>
    request(`/profiles/${profileId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),

  // 设置活跃画像
  setActiveProfile: (profileId: number): Promise<ProfileResponse> =>
    request(`/profiles/${profileId}/set-active`, {
      method: 'POST',
    }),

  // 删除用户画像
  deleteProfile: (profileId: number): Promise<{ deleted: boolean }> =>
    request(`/profiles/${profileId}`, {
      method: 'DELETE',
    }),

  // 根据画像 ID 获取智能推荐岗位列表
  getRecommendations: (profileId: number, topN = 5): Promise<JobRecommendationOut[]> =>
    request(`/profiles/${profileId}/recommendations?top_n=${topN}`),

  // 获取指定画像的收藏岗位列表
  listFavorites: (profileId: number): Promise<FavoriteJobListResponse> =>
    request(`/profiles/${profileId}/favorites`),

  // 为指定画像收藏岗位
  addFavorite: (profileId: number, jobId: number): Promise<FavoriteJobOut> =>
    request(`/profiles/${profileId}/favorites`, {
      method: 'POST',
      body: JSON.stringify({ job_id: jobId }),
    }),

  // 取消指定画像对岗位的收藏
  removeFavorite: (profileId: number, jobId: number): Promise<{ deleted: boolean }> =>
    request(`/profiles/${profileId}/favorites/${jobId}`, {
      method: 'DELETE',
    }),

  /* ---- Matches ---- */
  createMatch: (profileId: number, jobId: number): Promise<MatchResult> =>
    request('/matches', {
      method: 'POST',
      body: JSON.stringify({ profile_id: profileId, job_id: jobId }),
    }),

  getMatch: (matchId: number): Promise<MatchResult> => request(`/matches/${matchId}`),

  generateLearningPath: (profileId: number, jobId: number): Promise<LearningPath> =>
    request('/matches/learning-path', {
      method: 'POST',
      body: JSON.stringify({ profile_id: profileId, job_id: jobId }),
    }),

  /** SSE 流式匹配分析：通过回调接收每个节点的中间结果 */
  matchStream: async (
    payload: {
      jd_text?: string
      profile_id?: number
      profile?: Record<string, unknown>
      job_id?: number
      job_data?: unknown[]
      enable_search?: boolean
    },
    onEvent?: (event: MatchStreamEvent) => void,
  ): Promise<MatchResult | null> => {
    const res = await fetch(`${API_BASE}/matches/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok || !res.body) {
      throw new Error(`HTTP ${res.status}`)
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let finalResult: MatchResult | null = null

    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const payloadText = line.slice(6).trim()
          if (payloadText === '[DONE]') continue
          try {
            const parsed = JSON.parse(payloadText) as MatchStreamEvent
            if (parsed.final_result) {
              finalResult = parsed.final_result
            }
            onEvent?.(parsed)
          } catch {
            // skip malformed JSON
          }
        }
      }
    }
    return finalResult
  },

  /* ---- Trends ---- */
  getTrends: (): Promise<TrendAnalysis> => request('/trends'),

  /* ---- Dashboard ---- */
  getDashboard: (): Promise<DashboardData> => request('/dashboard'),

  /* ---- Care (求职关怀) ---- */
  getCareQuote: (scene?: string, category?: string): Promise<EncouragementQuote> => {
    const qs = buildQuery({ scene, category })
    return request(`/care/quote${qs ? `?${qs}` : ''}`)
  },

  getCareQuotes: (count = 5, scene?: string, category?: string): Promise<EncouragementQuote[]> => {
    const qs = buildQuery({ count, scene, category })
    return request(`/care/quotes?${qs}`)
  },

  getCareTips: (category?: string, difficulty?: string): Promise<PracticalTip[]> => {
    const qs = buildQuery({ category, difficulty })
    return request(`/care/tips${qs ? `?${qs}` : ''}`)
  },

  getCareStages: (): Promise<JobSearchStage[]> => request('/care/stages'),

  getCareDashboard: (profileId?: number): Promise<CareDashboard> => {
    const qs = buildQuery({ profile_id: profileId })
    return request(`/care/dashboard${qs ? `?${qs}` : ''}`)
  },
}
