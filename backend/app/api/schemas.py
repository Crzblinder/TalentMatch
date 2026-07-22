from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _load_json_list(value: Any) -> list[Any]:
    """将 ORM 中存储的 JSON 字符串解析为列表。"""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []
    return []


# ---------------------------------------------------------------------------
# 通用响应包装
# ---------------------------------------------------------------------------
class ApiResponse(BaseModel):
    """统一 API 响应结构。"""

    code: int = 0
    data: Any | None = None
    message: str = "ok"


# ---------------------------------------------------------------------------
# Skill
# ---------------------------------------------------------------------------
class SkillOut(BaseModel):
    id: int
    name: str
    category: str
    aliases: list[str]
    definition: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("aliases", mode="before")
    @classmethod
    def _parse_aliases(cls, v: Any) -> list[str]:
        return [str(x) for x in _load_json_list(v)]


class SkillListOut(BaseModel):
    total: int
    items: list[SkillOut]


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------
class CompanyOut(BaseModel):
    id: int
    name: str
    industry: str
    size: str
    city: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Job
# ---------------------------------------------------------------------------
class JobOut(BaseModel):
    id: int
    title: str
    company: CompanyOut
    city: str
    salary_min: int
    salary_max: int
    experience_level: str
    education_level: str
    required_skills: list[str]
    description: str
    posted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("required_skills", mode="before")
    @classmethod
    def _parse_required_skills(cls, v: Any) -> list[str]:
        # 兼容结构化技能格式，仅返回技能名称列表
        from app.models.job import parse_required_skills

        return [item["name"] for item in parse_required_skills(v)]


class JobListParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    q: str | None = None
    city: str | None = None
    industry: str | None = None
    experience_level: str | None = None


class JobListOut(BaseModel):
    total: int
    page: int
    size: int
    items: list[JobOut]


class JobSearchQuery(BaseModel):
    query: str
    top_k: int = Field(10, ge=1, le=50)
    city: str | None = None
    industry: str | None = None
    experience_level: str | None = None


class JobSearchResult(BaseModel):
    id: str
    document: str
    metadata: dict[str, Any]
    score: float | None = None
    keyword_score: float | None = None
    hybrid_score: float | None = None
    source: str = "chroma"


class JobStatisticsOut(BaseModel):
    total_jobs: int
    total_companies: int
    avg_salary_min: int
    avg_salary_max: int
    top_cities: list[dict[str, Any]]
    top_industries: list[dict[str, Any]]
    hot_skills: list[dict[str, Any]]
    experience_distribution: list[dict[str, Any]]


class JobRecommendationOut(BaseModel):
    """岗位智能推荐结果，包含岗位信息与匹配得分明细。"""

    job: JobOut
    match_score: float
    skill_score: float | None = None
    experience_match: float | None = None
    education_match: float | None = None
    matched_skills: list[str]
    missing_skills: list[str]
    transferable_skills: list[str]


# ---------------------------------------------------------------------------
# FavoriteJob
# ---------------------------------------------------------------------------
class FavoriteJobOut(BaseModel):
    """用户岗位收藏记录输出结构，包含关联的岗位详情。"""

    id: int
    profile_id: int
    job_id: int
    created_at: datetime | None = None
    job: JobOut | None = None

    model_config = ConfigDict(from_attributes=True)


class FavoriteJobListOut(BaseModel):
    """收藏列表分页输出结构。"""

    total: int
    page: int
    size: int
    items: list[FavoriteJobOut]


class FavoriteRequest(BaseModel):
    """添加收藏请求体。"""

    job_id: int = Field(..., ge=1, description="要收藏的岗位 ID")


# ---------------------------------------------------------------------------
# UserSkillProfile
# ---------------------------------------------------------------------------
class UserSkillProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    skills: list[str]
    experience_level: str = "不限"
    target_job_titles: list[str] = []


class UserSkillProfileOut(BaseModel):
    id: int
    name: str
    skills: list[str]
    experience_level: str
    target_job_titles: list[str]
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("skills", "target_job_titles", mode="before")
    @classmethod
    def _parse_profile_lists(cls, v: Any) -> list[str]:
        return [str(x) for x in _load_json_list(v)]


class UserSkillProfileListOut(BaseModel):
    total: int
    items: list[UserSkillProfileOut]


# ---------------------------------------------------------------------------
# MatchResult
# ---------------------------------------------------------------------------
class MatchResultOut(BaseModel):
    id: int
    user_profile_id: int
    job_id: int
    match_score: float
    skill_score: float | None = None
    experience_match: float | None = None
    education_match: float | None = None
    matched_skills: list[str]
    missing_skills: list[str]
    transferable_skills: list[str]
    analysis_summary: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("matched_skills", "missing_skills", "transferable_skills", mode="before")
    @classmethod
    def _parse_match_lists(cls, v: Any) -> list[str]:
        return [str(x) for x in _load_json_list(v)]


class MatchRequest(BaseModel):
    profile_id: int
    job_id: int
    profile: dict[str, Any] | None = None


class MatchResultListOut(BaseModel):
    total: int
    items: list[MatchResultOut]


# ---------------------------------------------------------------------------
# JD Parse
# ---------------------------------------------------------------------------
class JDParseRequest(BaseModel):
    jd_text: str = Field(..., min_length=10)
    fuzzy: bool | None = Field(
        None, description="是否启用模糊识别（应届生友好模式）；显式传值时跳过自动判定"
    )
    prompt_variant: str | None = Field(None, description="提示词变体，如 fresh_graduate")


class JDParseOut(BaseModel):
    title: str
    company: str
    required_skills: list[str]
    experience_level: str
    education_level: str
    implicit_needs: list[str]
    fresh_graduate_friendly: bool | None = None
    barriers_for_fresh_graduates: list[str] = []
    fuzzy: bool = False


class JDUploadOut(BaseModel):
    raw_text: str
    parsed: JDParseOut
    fuzzy: bool = False


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------
class ResumeBasicInfo(BaseModel):
    """简历基本信息。"""

    name: str = ""
    phone: str = ""
    email: str = ""
    gender: str = ""
    birth_date: str = ""
    political_status: str = ""
    marriage: str = ""
    wechat: str = ""
    qq: str = ""
    id_card_type: str = ""
    id_card_no: str = ""
    hukou: str = ""
    jiguan: str = ""


class ResumeEducation(BaseModel):
    """教育经历条目。"""

    school: str = ""
    major: str = ""
    degree: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


class ResumeWorkExperience(BaseModel):
    """工作经历条目。"""

    company: str = ""
    position: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


class ResumeProjectExperience(BaseModel):
    """项目经历条目。"""

    name: str = ""
    role: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


class ResumeJobIntention(BaseModel):
    """求职意向。"""

    expected_position: str = ""
    expected_city: str = ""
    expected_salary: str = ""
    expected_industry: str = ""


class ResumeUploadOut(BaseModel):
    """简历上传解析输出。"""

    name: str
    skills: list[str]
    experience_level: str
    education_level: str
    raw_text: str
    basic_info: ResumeBasicInfo
    education: list[ResumeEducation]
    work_experience: list[ResumeWorkExperience]
    project_experience: list[ResumeProjectExperience]
    awards: list[str]
    certifications: list[str]
    language_skills: list[str]
    self_evaluation: str
    job_intention: ResumeJobIntention
    fuzzy: bool = False
    obstacles: dict[str, Any] | None = None


class ResumeOptimizeRequest(BaseModel):
    """简历优化请求。"""

    resume_data: dict[str, Any] = Field(..., description="简历数据")
    jd_text: str = Field(..., description="目标岗位描述")
    field_order: list[str] = Field(
        ["project", "internship", "advantage"],
        description="字段排放顺序：project(项目经历), internship(实习经历), advantage(个人优势)",
    )


class ResumeOptimizeOut(BaseModel):
    """简历优化输出。"""

    original_project_experience: list[ResumeProjectExperience]
    original_work_experience: list[ResumeWorkExperience]
    original_self_evaluation: str
    optimized_project_experience: list[ResumeProjectExperience]
    optimized_work_experience: list[ResumeWorkExperience]
    optimized_self_evaluation: str
    field_order: list[str]
    optimization_notes: str
    suggested_changes: list[str]


# ---------------------------------------------------------------------------
# LearningPath
# ---------------------------------------------------------------------------
class LearningPathItem(BaseModel):
    skill: str
    difficulty: str
    estimated_weeks: int
    resource_type: str
    prerequisites: list[str]


class LearningPathRequest(BaseModel):
    profile_id: int
    job_id: int


class LearningPathOut(BaseModel):
    profile_id: int
    job_id: int
    learning_path: list[LearningPathItem]


# ---------------------------------------------------------------------------
# Trend
# ---------------------------------------------------------------------------
class TrendAnalysisOut(BaseModel):
    summary: str
    top_skills: list[str]
    avg_salary_range: str
    hot_job_titles: list[str]
    key_metrics: dict[str, Any]


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class DashboardOut(BaseModel):
    jobs: JobStatisticsOut
    trends: TrendAnalysisOut


# ---------------------------------------------------------------------------
# Stream
# ---------------------------------------------------------------------------
class MatchStreamRequest(BaseModel):
    jd_text: str | None = None
    profile_id: int | None = None
    profile: dict[str, Any] | None = None
    job_id: int | None = None
    job_data: list[dict[str, Any]] | None = None
    fuzzy: bool = False
    enable_search: bool = False


# ---------------------------------------------------------------------------
# Fuzzy Parse
# ---------------------------------------------------------------------------
class ResumeParseRequest(BaseModel):
    """简历文本解析请求。"""

    resume_text: str = Field(..., min_length=10, description="原始简历文本")
    fuzzy: bool | None = Field(
        None, description="是否启用模糊识别（应届生友好模式）；显式传值时跳过自动判定"
    )
    prompt_variant: str | None = Field(None, description="提示词变体，如 fresh_graduate")


class ResumeFuzzyParseRequest(BaseModel):
    """简历模糊识别解析请求。"""

    resume_text: str = Field(..., min_length=10, description="原始简历文本")
    focus: str = Field("auto", description="解析重点：auto/experience/skills/obstacles")
    detect_obstacles: bool = Field(True, description="是否同步识别求职困境")


class JDFuzzyParseRequest(BaseModel):
    """JD 模糊识别解析请求。"""

    jd_text: str = Field(..., min_length=10, description="原始岗位描述文本")
    focus: str = Field(
        "auto", description="解析重点：auto/requirements/barriers/fresh_graduate_friendly"
    )
    detect_obstacles: bool = Field(True, description="是否同步识别岗位门槛")


# ---------------------------------------------------------------------------
# Web Search
# ---------------------------------------------------------------------------
class SearchRequest(BaseModel):
    """联网搜索请求。"""

    query: str = Field(..., min_length=1, description="搜索关键词")
    intent: str = Field("general", description="搜索意图")
    location: str | None = Field(None, description="地域限定")
    top_n: int = Field(5, ge=1, le=20)
    summarize: bool = Field(True, description="是否使用 LLM 摘要")


class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str


class SearchOut(BaseModel):
    """联网搜索输出。"""

    query: str
    original_query: str
    intent: str
    source: str
    results: list[SearchResultItem]
    summary: str
    error: str | None = None


# ---------------------------------------------------------------------------
# Obstacle Detection
# ---------------------------------------------------------------------------
class ObstacleItem(BaseModel):
    key: str
    label: str
    detail: str
    description: str = ""
    suggestions: list[str] = []


class ObstacleAnalysisOut(BaseModel):
    """求职困境分析输出。"""

    obstacles: list[ObstacleItem]
    summary: str
    action_plan: list[str]
    severity_score: float


class ObstacleAnalysisRequest(BaseModel):
    """求职困境分析请求。"""

    resume_data: dict[str, Any] | None = None
    jd_data: dict[str, Any] | None = None
