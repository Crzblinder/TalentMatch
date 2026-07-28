"""岗位相关服务。"""

from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models import Company, Job
from app.models.job import parse_required_skills
from app.rag.retriever import HybridJobRetriever
from app.services.cache_service import CACHE_KEYS, DEFAULT_TTLS, cached

logger = logging.getLogger(__name__)


def _load_json_list(value: Any) -> list[Any]:
    """兼容字符串 JSON 与原生列表。"""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []
    return []


def _job_to_dict(job: Job) -> dict[str, Any]:
    """将 Job ORM 对象序列化为可缓存/可 JSON 化的字典。"""
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
        "source": job.source or "",
        "source_url": job.source_url or "",
        "posted_at": job.posted_at,
    }


class JobService:
    def __init__(self, db: Session):
        self.db = db

    @cached(prefix=CACHE_KEYS["job_list"], ttl=DEFAULT_TTLS["job_list"])
    def list_jobs(
        self,
        page: int = 1,
        size: int = 20,
        q: str | None = None,
        city: str | None = None,
        industry: str | None = None,
        experience_level: str | None = None,
    ) -> dict[str, Any]:
        query = self.db.query(Job).options(joinedload(Job.company))

        if city:
            query = query.filter(Job.city == city)
        if experience_level:
            query = query.filter(Job.experience_level == experience_level)
        if industry:
            query = query.join(Company, Job.company_id == Company.id).filter(
                Company.industry == industry
            )
        if q:
            like_pattern = f"%{q}%"
            query = query.filter(
                Job.title.ilike(like_pattern) | Job.description.ilike(like_pattern)
            )

        total = query.count()
        items = (
            query.order_by(Job.posted_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "size": size,
            "items": [_job_to_dict(job) for job in items],
        }

    def get_job(self, job_id: int) -> Job | None:
        return (
            self.db.query(Job)
            .options(joinedload(Job.company))
            .filter(Job.id == job_id)
            .first()
        )

    def search_jobs(
        self,
        query: str,
        top_k: int = 10,
        city: str | None = None,
        industry: str | None = None,
        experience_level: str | None = None,
    ) -> list[dict[str, Any]]:
        retriever = HybridJobRetriever(self.db)
        return retriever.search_jobs(
            query=query,
            city=city,
            industry=industry,
            experience_level=experience_level,
            top_k=top_k,
        )

    @cached(prefix=CACHE_KEYS["job_statistics"], ttl=DEFAULT_TTLS["job_statistics"])
    def get_job_statistics(self) -> dict[str, Any]:
        total_jobs = self.db.query(Job).count()
        total_companies = self.db.query(Company).count()

        salary_stats = self.db.query(
            func.coalesce(func.avg(Job.salary_min), 0).label("avg_min"),
            func.coalesce(func.avg(Job.salary_max), 0).label("avg_max"),
        ).first()

        top_cities = (
            self.db.query(Job.city, func.count(Job.id).label("count"))
            .group_by(Job.city)
            .order_by(func.count(Job.id).desc())
            .limit(10)
            .all()
        )

        top_industries = (
            self.db.query(Company.industry, func.count(Job.id).label("count"))
            .join(Job, Company.id == Job.company_id)
            .group_by(Company.industry)
            .order_by(func.count(Job.id).desc())
            .limit(10)
            .all()
        )

        experience_distribution = (
            self.db.query(Job.experience_level, func.count(Job.id).label("count"))
            .group_by(Job.experience_level)
            .order_by(func.count(Job.id).desc())
            .all()
        )

        # 热门技能统计（兼容结构化技能格式，仅按技能名称计数）
        skill_counter: Counter = Counter()
        for row in self.db.query(Job.required_skills).all():
            for skill_info in parse_required_skills(row[0]):
                skill_counter[skill_info["name"]] += 1

        hot_skills = [
            {"skill": skill, "count": count}
            for skill, count in skill_counter.most_common(20)
        ]

        return {
            "total_jobs": total_jobs,
            "total_companies": total_companies,
            "avg_salary_min": int(salary_stats.avg_min or 0),
            "avg_salary_max": int(salary_stats.avg_max or 0),
            "top_cities": [{"city": c, "count": n} for c, n in top_cities],
            "top_industries": [{"industry": i, "count": n} for i, n in top_industries],
            "hot_skills": hot_skills,
            "experience_distribution": [
                {"experience_level": e, "count": n} for e, n in experience_distribution
            ],
        }
