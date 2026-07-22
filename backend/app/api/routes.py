"""新版岗位技能图谱与人才匹配 API 路由。"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agents.graph_state import JobMatchState
from app.agents.trend_predictor import TrendPredictor
from app.agents.workflow import run_job_match_stream
from app.api.schemas import (
    ApiResponse,
    FavoriteJobListOut,
    FavoriteJobOut,
    FavoriteRequest,
    JDFuzzyParseRequest,
    JDParseOut,
    JDParseRequest,
    JDUploadOut,
    JobListOut,
    JobListParams,
    JobOut,
    JobRecommendationOut,
    JobSearchResult,
    LearningPathOut,
    LearningPathRequest,
    MatchRequest,
    MatchResultListOut,
    MatchResultOut,
    MatchStreamRequest,
    ObstacleAnalysisOut,
    ObstacleAnalysisRequest,
    ResumeFuzzyParseRequest,
    ResumeOptimizeOut,
    ResumeOptimizeRequest,
    ResumeParseRequest,
    ResumeUploadOut,
    SearchOut,
    SearchRequest,
    SkillListOut,
    SkillOut,
    UserSkillProfileCreate,
    UserSkillProfileListOut,
    UserSkillProfileOut,
)
from app.crawler.scraper import get_status as get_crawler_status
from app.models import Job, UserSkillProfile
from app.models.base import get_db
from app.scheduler import trigger_fetch_jobs
from app.services.favorite_service import FavoriteService
from app.services.jd_service import JDService
from app.services.job_service import JobService
from app.services.matching_service import MatchingService
from app.services.resume_service import ResumeService, should_use_fuzzy_parsing
from app.services.skill_service import SkillService
from app.utils.content_safety import check_text_safety

logger = logging.getLogger(__name__)

api_router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _success(data: Any, message: str = "ok") -> ApiResponse:
    return ApiResponse(code=0, data=data, message=message)


def _job_to_dict(job: Job) -> dict[str, Any]:
    return {
        "id": job.id,
        "title": job.title,
        "company": {
            "id": job.company.id,
            "name": job.company.name,
            "industry": job.company.industry,
            "size": job.company.size,
            "city": job.company.city,
        },
        "city": job.city,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "experience_level": job.experience_level,
        "education_level": job.education_level,
        "required_skills": _load_json_list(job.required_skills),
        "description": job.description,
        "posted_at": job.posted_at,
    }


def _profile_to_dict(profile: UserSkillProfile) -> dict[str, Any]:
    return {
        "id": profile.id,
        "name": profile.name,
        "skills": _load_json_list(profile.skills),
        "experience_level": profile.experience_level,
        "target_job_titles": _load_json_list(profile.target_job_titles),
        "created_at": profile.created_at,
    }


def _load_json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []
    return []


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@api_router.get("/jobs/health")
def jobs_health() -> ApiResponse:
    return _success({"status": "ok"}, message="服务健康")


@api_router.get("/config-tests", response_model=ApiResponse)
def config_tests() -> ApiResponse:
    """运行外部配置可用性检测并返回可视化报告。"""
    from app.utils.config_tester import run_config_tests

    report = run_config_tests()
    return _success(
        {
            "tested_at": report.tested_at,
            "total": report.total,
            "passed": report.passed,
            "failed": report.failed,
            "skipped": report.skipped,
            "results": [
                {
                    "name": r.name,
                    "category": r.category,
                    "status": r.status,
                    "message": r.message,
                    "response_time_ms": r.response_time_ms,
                    "configured": r.configured,
                    "detail": r.detail,
                }
                for r in report.results
            ],
        },
        message=f"检测完成：通过 {report.passed}，失败 {report.failed}，跳过 {report.skipped}",
    )


@api_router.get("/skills/config")
def skills_config() -> ApiResponse:
    """返回 TalentMatch Skills 与 MCP 配置。"""
    from app.skills import load_mcp_config, load_skills_config

    return _success({
        "skills": load_skills_config(),
        "mcp": load_mcp_config(),
    })


@api_router.get("/crawler/status", response_model=ApiResponse)
def crawler_status() -> ApiResponse:
    """返回 JD 爬虫最近一次运行状态。"""
    return _success(get_crawler_status())


@api_router.post("/crawler/trigger", response_model=ApiResponse)
def crawler_trigger() -> ApiResponse:
    """手动触发一次岗位采集任务。"""
    result = trigger_fetch_jobs()
    if result.get("success"):
        return _success(result, message="采集任务已触发并完成")
    logger.warning("手动采集任务执行失败: %s", result.get("error"))
    raise HTTPException(status_code=500, detail=f"采集任务执行失败: {result.get('error')}")


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
@api_router.get("/jobs", response_model=ApiResponse)
def list_jobs(
    params: JobListParams = Depends(),
    db: Session = Depends(get_db),
) -> ApiResponse:
    service = JobService(db)
    result = service.list_jobs(
        page=params.page,
        size=params.size,
        q=params.q,
        city=params.city,
        industry=params.industry,
        experience_level=params.experience_level,
    )
    result["items"] = [JobOut.model_validate(_job_to_dict(job)) for job in result["items"]]
    return _success(JobListOut.model_validate(result).model_dump())


@api_router.get("/jobs/search", response_model=ApiResponse)
def search_jobs(
    query: str = Query(..., min_length=1),
    top_k: int = Query(10, ge=1, le=50),
    city: str | None = None,
    industry: str | None = None,
    experience_level: str | None = None,
    db: Session = Depends(get_db),
) -> ApiResponse:
    service = JobService(db)
    results = service.search_jobs(
        query=query,
        top_k=top_k,
        city=city,
        industry=industry,
        experience_level=experience_level,
    )
    return _success([JobSearchResult.model_validate(r).model_dump() for r in results])


@api_router.post("/jobs/parse", response_model=ApiResponse)
def parse_jd(payload: JDParseRequest, db: Session = Depends(get_db)) -> ApiResponse:
    service = JDService()
    actual_fuzzy = (
        payload.fuzzy
        if payload.fuzzy is not None
        else should_use_fuzzy_parsing(payload.jd_text, "jd")
    )
    try:
        parsed = service.parse_jd_text(
            payload.jd_text,
            fuzzy=actual_fuzzy,
            prompt_variant=payload.prompt_variant,
        )
    except ValueError as exc:
        logger.warning("JD 解析参数错误: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("JD 解析失败")
        raise HTTPException(status_code=500, detail=f"JD 解析失败: {exc}") from exc
    parsed["fuzzy"] = actual_fuzzy
    return _success(JDParseOut.model_validate(parsed).model_dump())


@api_router.post("/jobs/fuzzy-parse", response_model=ApiResponse)
def fuzzy_parse_jd(payload: JDFuzzyParseRequest) -> ApiResponse:
    """JD 模糊识别解析：自动识别应届生友好度、隐性门槛、技能别名等。"""
    from app.agents.tools import fuzzy_parse_jd as _fuzzy_parse_jd_tool

    try:
        result = _fuzzy_parse_jd_tool(jd_text=payload.jd_text, focus=payload.focus)
        parsed = result.get("parsed", {})
        if not payload.detect_obstacles:
            parsed.pop("obstacles", None)
    except Exception as exc:
        logger.exception("JD 模糊解析失败")
        raise HTTPException(status_code=500, detail=f"JD 模糊解析失败: {exc}") from exc
    return _success(JDParseOut.model_validate(parsed).model_dump())


@api_router.post("/jobs/upload", response_model=ApiResponse)
async def upload_jd(
    file: UploadFile = File(...),
    fuzzy: bool | None = Query(None, description="是否启用模糊识别（应届生友好模式）；不传则自动判定"),
) -> ApiResponse:
    """上传 JD 文件（支持 PDF、DOCX、图片）并解析。

    图片文件使用多模态模型进行 OCR 识别。
    """
    file_bytes = await file.read()

    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="文件大小超过 10MB 限制")

    filename = file.filename or ""
    ext = filename.split(".")[-1].lower() if "." in filename else ""

    from app.agents.jd_parser import JDParser
    from app.config import get_settings

    settings = get_settings()

    raw_text = ""

    if ext in ("pdf", "docx", "doc"):
        from app.services.resume_service import ResumeService

        resume_service = ResumeService()
        raw_text = resume_service._extract_text(file_bytes, filename)
    elif ext in ("png", "jpg", "jpeg", "webp", "gif"):
        from app.services.jd_service import JDService

        jd_service = JDService()
        try:
            raw_text = jd_service.extract_text_from_image(file_bytes, ext, settings)
        except Exception as exc:
            logger.error("图片 OCR 识别失败: %s", exc)
            raise HTTPException(status_code=500, detail=f"图片识别失败: {exc}") from exc
    else:
        raw_text = file_bytes.decode("utf-8", errors="ignore")

    safety = check_text_safety(raw_text, settings)
    if not safety.get("safe", True):
        labels = safety.get("labels", [])
        logger.warning("上传 JD 文件内容安全检测未通过，labels: %s", labels)
        raise HTTPException(
            status_code=400,
            detail=f"JD 内容未通过安全检测，违规标签: {', '.join(labels) if labels else '未知'}",
        )

    actual_fuzzy = fuzzy if fuzzy is not None else should_use_fuzzy_parsing(raw_text, "jd")
    parser = JDParser(prompt_variant="fresh_graduate" if actual_fuzzy else "default")

    try:
        parsed = parser.parse_jd(raw_text)
    except ValueError as exc:
        logger.warning("JD 解析参数错误: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("JD 解析失败")
        raise HTTPException(status_code=500, detail=f"JD 解析失败: {exc}") from exc

    return _success(
        JDUploadOut(
            raw_text=raw_text,
            parsed=JDParseOut.model_validate(parsed),
            fuzzy=actual_fuzzy,
        ).model_dump()
    )


@api_router.get("/jobs/{job_id}", response_model=ApiResponse)
def get_job(job_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    service = JobService(db)
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"岗位不存在: {job_id}")
    return _success(JobOut.model_validate(_job_to_dict(job)).model_dump())


# ---------------------------------------------------------------------------
# Resumes
# ---------------------------------------------------------------------------
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


@api_router.post("/resumes/parse", response_model=ApiResponse)
def parse_resume(payload: ResumeParseRequest) -> ApiResponse:
    """直接解析简历文本，默认根据内容自动判断是否启用模糊解析。"""
    service = ResumeService()
    actual_fuzzy = (
        payload.fuzzy
        if payload.fuzzy is not None
        else should_use_fuzzy_parsing(payload.resume_text, "resume")
    )
    try:
        result = service.parse_resume_text(
            payload.resume_text,
            fuzzy=actual_fuzzy,
            prompt_variant=payload.prompt_variant,
        )
        result["fuzzy"] = actual_fuzzy
        if actual_fuzzy:
            from app.agents.obstacle_detector import ObstacleDetector

            detector = ObstacleDetector()
            result["obstacles"] = detector.detect_from_resume(result)
    except ValueError as exc:
        logger.warning("简历解析参数错误: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("简历解析失败")
        raise HTTPException(status_code=500, detail=f"简历解析失败: {exc}") from exc

    return _success(ResumeUploadOut.model_validate(result).model_dump())


@api_router.post("/resumes/upload", response_model=ApiResponse)
async def upload_resume(
    file: UploadFile = File(...),
    fuzzy: bool | None = Query(None, description="是否启用模糊识别（应届生友好模式）；不传则自动判定"),
) -> ApiResponse:
    """上传简历并解析为结构化信息。"""
    file_bytes = await file.read()

    # 限制上传文件大小不超过 10MB
    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="文件大小超过 10MB 限制")

    service = ResumeService()
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    try:
        if ext == ".pdf":
            raw_text = service.extract_text_from_pdf(file_bytes)
        elif ext == ".docx":
            raw_text = service.extract_text_from_docx(file_bytes)
        else:
            raise ValueError("仅支持 PDF 和 DOCX 格式")

        actual_fuzzy = fuzzy if fuzzy is not None else should_use_fuzzy_parsing(raw_text, "resume")
        result = service.parse_resume_text(
            raw_text,
            fuzzy=actual_fuzzy,
        )
        result["fuzzy"] = actual_fuzzy
        if actual_fuzzy:
            from app.agents.obstacle_detector import ObstacleDetector

            detector = ObstacleDetector()
            result["obstacles"] = detector.detect_from_resume(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("简历解析失败")
        raise HTTPException(status_code=500, detail=f"简历解析失败: {exc}") from exc

    return _success(ResumeUploadOut.model_validate(result).model_dump())


@api_router.post("/resumes/fuzzy-parse", response_model=ApiResponse)
def fuzzy_parse_resume(payload: ResumeFuzzyParseRequest) -> ApiResponse:
    """简历模糊识别解析：自动识别经历边界、零经验技能、求职困境等。"""
    from app.agents.tools import fuzzy_parse_resume as _fuzzy_parse_resume_tool

    try:
        result = _fuzzy_parse_resume_tool(
            resume_text=payload.resume_text,
            focus=payload.focus,
        )
        parsed = result.get("parsed", {})
        parsed["fuzzy"] = True
        if not payload.detect_obstacles:
            parsed.pop("obstacles", None)
    except Exception as exc:
        logger.exception("简历模糊解析失败")
        raise HTTPException(status_code=500, detail=f"简历模糊解析失败: {exc}") from exc
    return _success(ResumeUploadOut.model_validate(parsed).model_dump())


@api_router.post("/resumes/optimize", response_model=ApiResponse)
def optimize_resume(payload: ResumeOptimizeRequest) -> ApiResponse:
    """根据目标岗位描述优化简历内容。

    支持动态修改项目经历、实习经历、个人优势，并可配置字段排放顺序。
    """
    from app.agents.resume_optimizer import ResumeOptimizer

    optimizer = ResumeOptimizer()
    try:
        result = optimizer.optimize_resume(
            resume_data=payload.resume_data,
            jd_text=payload.jd_text,
            field_order=payload.field_order,
        )
    except Exception as exc:
        logger.exception("简历优化失败")
        raise HTTPException(status_code=500, detail=f"简历优化失败: {exc}") from exc

    return _success(ResumeOptimizeOut.model_validate(result).model_dump())


# ---------------------------------------------------------------------------
# Search & Obstacles
# ---------------------------------------------------------------------------
@api_router.post("/search", response_model=ApiResponse)
def web_search(payload: SearchRequest) -> ApiResponse:
    """联网智能搜索：支持公司、面经、薪资、校招、技能趋势等意图。"""
    from app.agents.search_agent import SearchAgent

    agent = SearchAgent()
    try:
        result = agent.search(
            query=payload.query,
            intent=payload.intent,
            location=payload.location,
            top_n=payload.top_n,
            summarize=payload.summarize,
        )
    except Exception as exc:
        logger.exception("联网搜索失败")
        raise HTTPException(status_code=500, detail=f"联网搜索失败: {exc}") from exc
    return _success(SearchOut.model_validate(result).model_dump())


@api_router.post("/obstacles/analyze", response_model=ApiResponse)
def analyze_obstacles(payload: ObstacleAnalysisRequest) -> ApiResponse:
    """分析应届毕业生的求职困境与障碍。"""
    from app.agents.obstacle_detector import ObstacleDetector

    detector = ObstacleDetector()
    try:
        result = detector.detect(
            resume=payload.resume_data or {},
            jd=payload.jd_data or {},
        )
    except Exception as exc:
        logger.exception("求职困境分析失败")
        raise HTTPException(status_code=500, detail=f"求职困境分析失败: {exc}") from exc
    return _success(ObstacleAnalysisOut.model_validate(result).model_dump())


@api_router.post("/profiles/{profile_id}/obstacles", response_model=ApiResponse)
def analyze_profile_obstacles(
    profile_id: int,
    payload: ObstacleAnalysisRequest | None = None,
    db: Session = Depends(get_db),
) -> ApiResponse:
    """根据用户画像与可选的岗位数据，分析求职困境。"""
    from app.agents.obstacle_detector import ObstacleDetector

    profile = db.query(UserSkillProfile).filter(UserSkillProfile.id == profile_id).first()
    if profile is None:
        raise HTTPException(status_code=404, detail=f"用户画像不存在: {profile_id}")

    resume_data = {
        "name": profile.name,
        "skills": _load_json_list(profile.skills),
        "experience_level": profile.experience_level,
        "target_job_titles": _load_json_list(profile.target_job_titles),
    }
    if payload and payload.resume_data:
        resume_data.update(payload.resume_data)

    detector = ObstacleDetector()
    try:
        result = detector.detect(
            resume=resume_data,
            jd=(payload.jd_data if payload else {}) or {},
        )
    except Exception as exc:
        logger.exception("求职困境分析失败")
        raise HTTPException(status_code=500, detail=f"求职困境分析失败: {exc}") from exc
    return _success(ObstacleAnalysisOut.model_validate(result).model_dump())


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------
@api_router.get("/skills", response_model=ApiResponse)
def list_skills(
    category: str | None = None,
    db: Session = Depends(get_db),
) -> ApiResponse:
    service = SkillService(db)
    result = service.list_skills(category=category)
    return _success(SkillListOut.model_validate(result).model_dump())


@api_router.get("/skills/{skill_id}", response_model=ApiResponse)
def get_skill(skill_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    service = SkillService(db)
    skill = service.get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"技能不存在: {skill_id}")
    return _success(SkillOut.model_validate(skill).model_dump())


@api_router.get("/skills/{skill_id}/related", response_model=ApiResponse)
def get_related_skills(
    skill_id: int,
    relation_type: str | None = None,
    db: Session = Depends(get_db),
) -> ApiResponse:
    service = SkillService(db)
    skill = service.get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"技能不存在: {skill_id}")
    related = service.get_related_skills(
        skill_name=skill.name,
        relation_type=relation_type,
    )
    return _success(related)


@api_router.post("/skills/invalidate-cache", response_model=ApiResponse)
def invalidate_skill_cache(db: Session = Depends(get_db)) -> ApiResponse:
    """开发调试：手动清空技能图谱缓存，使下次请求重新从数据库构建图谱。"""
    service = SkillService(db)
    service.invalidate_cache()
    return _success({"invalidated": True}, message="技能图谱缓存已清空")


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------
@api_router.post("/profiles", response_model=ApiResponse)
def create_profile(
    payload: UserSkillProfileCreate,
    db: Session = Depends(get_db),
) -> ApiResponse:
    import json as _json

    profile = UserSkillProfile(
        name=payload.name,
        skills=_json.dumps(payload.skills, ensure_ascii=False),
        experience_level=payload.experience_level,
        target_job_titles=_json.dumps(payload.target_job_titles, ensure_ascii=False),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _success(UserSkillProfileOut.model_validate(profile).model_dump())


@api_router.get("/profiles", response_model=ApiResponse)
def list_profiles(db: Session = Depends(get_db)) -> ApiResponse:
    items = db.query(UserSkillProfile).order_by(UserSkillProfile.created_at.desc()).all()
    return _success(
        UserSkillProfileListOut(
            total=len(items),
            items=[UserSkillProfileOut.model_validate(p) for p in items],
        ).model_dump()
    )


@api_router.get("/profiles/{profile_id}/recommendations", response_model=ApiResponse)
def recommend_jobs_for_profile(
    profile_id: int,
    top_n: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ApiResponse:
    """根据用户画像智能推荐岗位，按匹配分数降序返回。"""
    profile = db.query(UserSkillProfile).filter(UserSkillProfile.id == profile_id).first()
    if profile is None:
        raise HTTPException(status_code=404, detail=f"用户画像不存在: {profile_id}")

    service = MatchingService(db)
    try:
        recommendations = service.recommend_jobs(profile_id=profile_id, top_n=top_n)
    except Exception as exc:
        logger.exception("岗位推荐失败")
        raise HTTPException(status_code=500, detail=f"岗位推荐失败: {exc}") from exc

    items: list[dict[str, Any]] = []
    for rec in recommendations:
        job_dict = _job_to_dict(rec["job"])
        items.append(
            JobRecommendationOut(
                job=JobOut.model_validate(job_dict),
                match_score=rec["match_score"],
                skill_score=rec["skill_score"],
                experience_match=rec["experience_match"],
                education_match=rec["education_match"],
                matched_skills=rec["matched_skills"],
                missing_skills=rec["missing_skills"],
                transferable_skills=rec["transferable_skills"],
            ).model_dump()
        )
    return _success(items)


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------
@api_router.post("/profiles/{profile_id}/favorites", response_model=ApiResponse)
def add_favorite(
    profile_id: int,
    payload: FavoriteRequest,
    db: Session = Depends(get_db),
) -> ApiResponse:
    """为指定用户画像收藏岗位。"""
    service = FavoriteService(db)
    if service.get_profile(profile_id) is None:
        raise HTTPException(status_code=404, detail=f"用户画像不存在: {profile_id}")
    if service.get_job(payload.job_id) is None:
        raise HTTPException(status_code=404, detail=f"岗位不存在: {payload.job_id}")

    favorite = service.add_favorite(profile_id=profile_id, job_id=payload.job_id)
    return _success(FavoriteJobOut.model_validate(favorite).model_dump(), message="收藏成功")


@api_router.delete("/profiles/{profile_id}/favorites/{job_id}", response_model=ApiResponse)
def remove_favorite(
    profile_id: int,
    job_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse:
    """取消指定用户画像对岗位的收藏。"""
    service = FavoriteService(db)
    if service.get_profile(profile_id) is None:
        raise HTTPException(status_code=404, detail=f"用户画像不存在: {profile_id}")

    deleted = service.remove_favorite(profile_id=profile_id, job_id=job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="收藏记录不存在")
    return _success({"deleted": True}, message="已取消收藏")


@api_router.get("/profiles/{profile_id}/favorites", response_model=ApiResponse)
def list_favorites(
    profile_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ApiResponse:
    """获取指定用户画像的收藏岗位列表。"""
    service = FavoriteService(db)
    if service.get_profile(profile_id) is None:
        raise HTTPException(status_code=404, detail=f"用户画像不存在: {profile_id}")

    result = service.list_favorites(profile_id=profile_id, page=page, size=size)
    return _success(
        FavoriteJobListOut(
            total=result["total"],
            page=result["page"],
            size=result["size"],
            items=[FavoriteJobOut.model_validate(item) for item in result["items"]],
        ).model_dump()
    )


# ---------------------------------------------------------------------------
# Matches
# ---------------------------------------------------------------------------
@api_router.post("/matches", response_model=ApiResponse)
def create_match(
    payload: MatchRequest,
    db: Session = Depends(get_db),
) -> ApiResponse:
    service = MatchingService(db)
    try:
        match_result = service.match_profile_to_job(
            profile_id=payload.profile_id,
            job_id=payload.job_id,
            profile_override=payload.profile,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("匹配失败")
        raise HTTPException(status_code=500, detail=f"匹配失败: {exc}") from exc
    return _success(MatchResultOut.model_validate(match_result).model_dump())


@api_router.get("/matches/{match_id}", response_model=ApiResponse)
def get_match(match_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    service = MatchingService(db)
    match_result = service.get_match_result(match_id)
    if match_result is None:
        raise HTTPException(status_code=404, detail=f"匹配结果不存在: {match_id}")
    return _success(MatchResultOut.model_validate(match_result).model_dump())


@api_router.get("/matches", response_model=ApiResponse)
def list_matches(
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ApiResponse:
    service = MatchingService(db)
    result = service.list_match_results(profile_id=profile_id)
    return _success(
        MatchResultListOut(
            total=result["total"],
            items=[MatchResultOut.model_validate(m) for m in result["items"]],
        ).model_dump()
    )


@api_router.post("/matches/learning-path", response_model=ApiResponse)
def generate_learning_path(
    payload: LearningPathRequest,
    db: Session = Depends(get_db),
) -> ApiResponse:
    service = MatchingService(db)
    try:
        result = service.generate_learning_path(
            profile_id=payload.profile_id,
            job_id=payload.job_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("生成学习路径失败")
        raise HTTPException(status_code=500, detail=f"生成学习路径失败: {exc}") from exc
    return _success(LearningPathOut.model_validate(result).model_dump())


# ---------------------------------------------------------------------------
# Trends
# ---------------------------------------------------------------------------
@api_router.get("/trends", response_model=ApiResponse)
def get_trends(db: Session = Depends(get_db)) -> ApiResponse:
    job_data = []
    for job in db.query(Job).all():
        job_data.append(
            {
                "title": job.title,
                "city": job.city,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "required_skills": _load_json_list(job.required_skills),
            }
        )

    agent = TrendPredictor()
    trend = agent.predict(job_data)
    return _success(
        {
            "summary": trend.get("summary", ""),
            "top_skills": trend.get("top_skills", []),
            "avg_salary_range": trend.get("avg_salary_range", ""),
            "hot_job_titles": trend.get("hot_job_titles", []),
            "key_metrics": trend.get("key_metrics", {}),
        }
    )


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@api_router.get("/dashboard", response_model=ApiResponse)
def get_dashboard(db: Session = Depends(get_db)) -> ApiResponse:
    job_service = JobService(db)
    skill_service = SkillService(db)

    job_stats = job_service.get_job_statistics()
    skill_stats = skill_service.get_skill_statistics()

    job_data = []
    for job in db.query(Job).all():
        job_data.append(
            {
                "title": job.title,
                "city": job.city,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "required_skills": _load_json_list(job.required_skills),
            }
        )
    agent = TrendPredictor()
    trend = agent.predict(job_data)

    return _success(
        {
            "jobs": job_stats,
            "skills": skill_stats,
            "trends": {
                "summary": trend.get("summary", ""),
                "top_skills": trend.get("top_skills", []),
                "avg_salary_range": trend.get("avg_salary_range", ""),
                "hot_job_titles": trend.get("hot_job_titles", []),
                "key_metrics": trend.get("key_metrics", {}),
            },
        }
    )


# ---------------------------------------------------------------------------
# SSE Stream
# ---------------------------------------------------------------------------
async def _match_stream_events(
    db: Session,
    payload: MatchStreamRequest,
) -> Any:
    input_text = payload.jd_text or ""
    target_job = None
    profile = payload.profile or {}

    if payload.job_id is not None:
        job = db.query(Job).filter(Job.id == payload.job_id).first()
        if job is not None:
            target_job = job
            input_text = input_text or job.description

    if payload.profile_id is not None:
        profile_obj = (
            db.query(UserSkillProfile)
            .filter(UserSkillProfile.id == payload.profile_id)
            .first()
        )
        if profile_obj is not None:
            profile = _profile_to_dict(profile_obj)

    job_data = payload.job_data or []
    if not job_data:
        for job in db.query(Job).all():
            job_data.append(
                {
                    "title": job.title,
                    "city": job.city,
                    "salary_min": job.salary_min,
                    "salary_max": job.salary_max,
                    "required_skills": _load_json_list(job.required_skills),
                }
            )

    state: JobMatchState = {
        "input_text": input_text,
        "profile": profile,
        "target_job": target_job,
        "job_data": job_data,
        "fuzzy": payload.fuzzy,
        "enable_search": payload.enable_search,
    }

    try:
        async for event in run_job_match_stream(db, state):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    except Exception as exc:
        logger.exception("流式分析失败")
        error_event = {
            "node": "error",
            "status": "failed",
            "message": str(exc),
        }
        yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"


@api_router.post("/matches/stream")
def match_stream(
    payload: MatchStreamRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    return StreamingResponse(
        _match_stream_events(db, payload),
        media_type="text/event-stream",
    )
