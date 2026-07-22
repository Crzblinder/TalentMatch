"""为 E2E 冒烟测试注入少量新版主题数据。

数据量小且不需要下载 Embedding 模型，只覆盖岗位匹配流程所需的最小数据集：
企业 -> 岗位 -> 技能 -> 技能关系 -> 示例求职者画像。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.models.base import SessionLocal
from app.models import Company, Job, Skill, SkillRelation, UserSkillProfile


def _json_list(value: list[str]) -> str:
    return json.dumps(value, ensure_ascii=False)


def main() -> None:
    db = SessionLocal()
    try:
        # 技能
        skill_names = {
            "Python": "编程语言",
            "FastAPI": "后端框架",
            "PostgreSQL": "数据库",
            "Docker": "运维工具",
            "Java": "编程语言",
            "Spring Boot": "后端框架",
            "MySQL": "数据库",
            "React": "前端框架",
            "JavaScript": "编程语言",
        }
        skill_map: dict[str, Skill] = {}
        existing_skills = {s.name: s for s in db.query(Skill).all()}
        for name, category in skill_names.items():
            skill = existing_skills.get(name)
            if skill is None:
                skill = Skill(
                    name=name,
                    category=category,
                    aliases=_json_list([name.lower()]),
                    definition=f"{name} 是 {category} 相关技能。",
                )
                db.add(skill)
            skill_map[name] = skill
        db.commit()
        for skill in skill_map.values():
            db.refresh(skill)

        # 技能关系（依赖 + 相似）
        relations = [
            ("Python", "FastAPI", "dependency", 0.9),
            ("Python", "PostgreSQL", "dependency", 0.75),
            ("Python", "Docker", "co_occurrence", 0.7),
            ("Java", "Spring Boot", "dependency", 0.95),
            ("Java", "MySQL", "dependency", 0.7),
            ("JavaScript", "React", "dependency", 0.9),
            ("FastAPI", "Spring Boot", "similarity", 0.75),
            ("PostgreSQL", "MySQL", "similarity", 0.85),
        ]
        existing_rels = {
            (r.source_skill_id, r.target_skill_id, r.relation_type)
            for r in db.query(SkillRelation).all()
        }
        for source_name, target_name, rel_type, weight in relations:
            source = skill_map.get(source_name)
            target = skill_map.get(target_name)
            if source is None or target is None:
                continue
            key = (source.id, target.id, rel_type)
            if key in existing_rels:
                continue
            db.add(
                SkillRelation(
                    source_skill_id=source.id,
                    target_skill_id=target.id,
                    relation_type=rel_type,
                    weight=weight,
                )
            )
        db.commit()

        # 企业
        company_map: dict[str, Company] = {}
        existing_companies = {c.name: c for c in db.query(Company).all()}
        for name, industry, size, city in [
            ("示例科技", "互联网", "100-499人", "北京"),
            ("示例软件", "企业服务", "500-999人", "上海"),
        ]:
            company = existing_companies.get(name)
            if company is None:
                company = Company(name=name, industry=industry, size=size, city=city)
                db.add(company)
            company_map[name] = company
        db.commit()
        for company in company_map.values():
            db.refresh(company)

        # 岗位
        jobs_data = [
            (
                "Python 后端工程师",
                company_map["示例科技"].id,
                "北京",
                ["Python", "FastAPI", "PostgreSQL"],
                "负责后端服务开发，要求熟悉 Python、FastAPI 和 PostgreSQL。",
            ),
            (
                "Java 后端工程师",
                company_map["示例软件"].id,
                "上海",
                ["Java", "Spring Boot", "MySQL"],
                "负责 Java 后端系统开发，要求熟悉 Spring Boot 和 MySQL。",
            ),
            (
                "前端工程师",
                company_map["示例科技"].id,
                "北京",
                ["JavaScript", "React"],
                "负责 Web 前端开发，要求熟悉 React 和现代 JavaScript。",
            ),
        ]
        existing_job_titles = {j.title for j in db.query(Job).all()}
        for title, company_id, city, skills, description in jobs_data:
            if title in existing_job_titles:
                continue
            db.add(
                Job(
                    title=title,
                    company_id=company_id,
                    city=city,
                    salary_min=20000,
                    salary_max=35000,
                    experience_level="3-5年",
                    education_level="本科",
                    required_skills=_json_list(skills),
                    description=description,
                )
            )
        db.commit()

        # 示例画像
        if db.query(UserSkillProfile).count() == 0:
            db.add(
                UserSkillProfile(
                    name="示例候选人",
                    skills=_json_list(["Python", "FastAPI", "Docker"]),
                    experience_level="3-5年",
                    target_job_titles=_json_list(["Python 后端工程师"]),
                )
            )
            db.commit()

        print(
            f"Minimal seed done: "
            f"{db.query(Company).count()} companies, "
            f"{db.query(Job).count()} jobs, "
            f"{db.query(Skill).count()} skills, "
            f"{db.query(SkillRelation).count()} relations, "
            f"{db.query(UserSkillProfile).count()} profiles"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
