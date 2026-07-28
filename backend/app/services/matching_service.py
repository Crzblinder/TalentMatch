"""人岗匹配与学习路径服务。"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.agents.learning_planner import LearningPlanner
from app.agents.talent_matcher import TalentMatcher
from app.models import Job, MatchResult, UserSkillProfile
from app.services.skill_service import SkillService

logger = logging.getLogger(__name__)


def _dump_list(value: list[Any]) -> str:
    return json.dumps(value, ensure_ascii=False)


def _load_list(value: str | list[Any]) -> list[Any]:
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


class MatchingService:
    def __init__(self, db: Session):
        self.db = db

    def match_profile_to_job(
        self,
        profile_id: int,
        job_id: int,
        profile_override: dict[str, Any] | None = None,
    ) -> MatchResult:
        profile = (
            self.db.query(UserSkillProfile)
            .filter(UserSkillProfile.id == profile_id)
            .first()
        )
        if profile is None:
            raise ValueError(f"用户画像不存在: profile_id={profile_id}")

        job = (
            self.db.query(Job)
            .options(joinedload(Job.company))
            .filter(Job.id == job_id)
            .first()
        )
        if job is None:
            raise ValueError(f"岗位不存在: job_id={job_id}")

        profile_override = profile_override or {}

        # 优先使用内联画像的技能，否则使用数据库中存储的技能
        profile_skills = profile_override.get("skills")
        if profile_skills is None:
            profile_skills = _load_list(profile.skills)

        # 先对用户画像技能进行归一化，确保别名能与岗位标准名称匹配
        skill_service = SkillService(self.db)
        profile_skills = [
            skill_service.normalize_skill_name(name) or name for name in profile_skills
        ]

        # 组装完整的画像上下文传给匹配器
        matcher_profile: dict[str, Any] = {
            "skills": profile_skills,
            "experience_level": profile_override.get(
                "experience_level", profile.experience_level
            ),
            "education_level": profile_override.get("education_level", "不限"),
        }
        if "experience_years" in profile_override:
            matcher_profile["experience_years"] = profile_override["experience_years"]

        matcher = TalentMatcher()
        result = matcher.match(matcher_profile, job, self.db)

        match_result = MatchResult(
            user_profile_id=profile_id,
            job_id=job_id,
            match_score=float(result.get("match_score", 0.0)),
            skill_score=result.get("skill_score"),
            experience_match=result.get("experience_match"),
            education_match=result.get("education_match"),
            matched_skills=_dump_list(result.get("matched_skills", [])),
            missing_skills=_dump_list(result.get("missing_skills", [])),
            transferable_skills=_dump_list(result.get("transferable_skills", [])),
            analysis_summary=result.get("analysis_summary"),
        )
        self.db.add(match_result)
        self.db.commit()
        self.db.refresh(match_result)
        return match_result

    def recommend_jobs(self, profile_id: int, top_n: int = 20) -> list[dict[str, Any]]:
        """为指定用户画像智能推荐岗位。

        遍历岗位库，调用 TalentMatcher 计算匹配分数，返回按匹配度降序排列的推荐列表。
        该接口不持久化匹配结果，仅做实时推荐。
        """
        profile = (
            self.db.query(UserSkillProfile)
            .filter(UserSkillProfile.id == profile_id)
            .first()
        )
        if profile is None:
            raise ValueError(f"用户画像不存在: profile_id={profile_id}")

        # 批量加载岗位及所属公司，避免 N+1 查询
        jobs = self.db.query(Job).options(joinedload(Job.company)).all()
        if not jobs:
            return []

        # 归一化画像技能，确保别名能与岗位标准名称匹配
        profile_skills = _load_list(profile.skills)
        skill_service = SkillService(self.db)
        profile_skills = [
            skill_service.normalize_skill_name(name) or name for name in profile_skills
        ]

        # 组装完整的画像上下文传给匹配器
        matcher_profile: dict[str, Any] = {
            "skills": profile_skills,
            "experience_level": profile.experience_level,
            "education_level": "不限",
        }

        matcher = TalentMatcher()
        recommendations: list[dict[str, Any]] = []
        for job in jobs:
            result = matcher.match(matcher_profile, job, self.db)
            recommendations.append(
                {
                    "job": job,
                    "match_score": float(result.get("match_score", 0.0)),
                    "skill_score": result.get("skill_score"),
                    "experience_match": result.get("experience_match"),
                    "education_match": result.get("education_match"),
                    "matched_skills": result.get("matched_skills", []),
                    "missing_skills": result.get("missing_skills", []),
                    "transferable_skills": result.get("transferable_skills", []),
                }
            )

        # 按匹配分数降序排列，取前 top_n 个
        recommendations.sort(key=lambda item: item["match_score"], reverse=True)
        return recommendations[:top_n]

    def get_match_result(self, match_id: int) -> MatchResult | None:
        return self.db.query(MatchResult).filter(MatchResult.id == match_id).first()

    def list_match_results(
        self, profile_id: int | None = None
    ) -> dict[str, Any]:
        query = self.db.query(MatchResult)
        if profile_id is not None:
            query = query.filter(MatchResult.user_profile_id == profile_id)
        items = query.order_by(MatchResult.created_at.desc()).all()
        return {"total": len(items), "items": items}

    def generate_learning_path(
        self, profile_id: int, job_id: int
    ) -> dict[str, Any]:
        profile = (
            self.db.query(UserSkillProfile)
            .filter(UserSkillProfile.id == profile_id)
            .first()
        )
        if profile is None:
            raise ValueError(f"用户画像不存在: profile_id={profile_id}")

        job = (
            self.db.query(Job)
            .options(joinedload(Job.company))
            .filter(Job.id == job_id)
            .first()
        )
        if job is None:
            raise ValueError(f"岗位不存在: job_id={job_id}")

        current_skills = _load_list(profile.skills)

        # 优先使用已有的最新匹配结果中的缺失技能
        latest_match = (
            self.db.query(MatchResult)
            .filter(
                MatchResult.user_profile_id == profile_id,
                MatchResult.job_id == job_id,
            )
            .order_by(MatchResult.created_at.desc())
            .first()
        )

        if latest_match:
            missing_skills = _load_list(latest_match.missing_skills)
        else:
            matcher = TalentMatcher()
            match_result = matcher.match(current_skills, job, self.db)
            missing_skills = match_result.get("missing_skills", [])

        planner = LearningPlanner()
        plan = planner.plan(missing_skills, current_skills, self.db)

        return {
            "profile_id": profile_id,
            "job_id": job_id,
            "learning_path": plan,
        }
