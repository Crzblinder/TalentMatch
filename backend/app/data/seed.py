import json
import logging
import random
from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from app.crawler.scraper import MIN_REAL_JOBS, TARGET_TOTAL_JOBS, fetch_real_jobs
from app.data.generator import (
    COMPANY_SIZES,
    INDUSTRIES,
    generate_all_data,
    generate_companies,
    generate_jobs,
    infer_missing_fields,
)
from app.models import (
    Company,
    Job,
    MatchResult,
    Skill,
    SkillRelation,
    UserSkillProfile,
)

logger = logging.getLogger(__name__)

# 预定义依赖关系：source -> [target]
DEPENDENCY_RULES: dict[str, list[tuple[str, float]]] = {
    "Python": [
        ("FastAPI", 0.9),
        ("Django", 0.85),
        ("Flask", 0.8),
        ("Pandas", 0.75),
        ("PyTorch", 0.7),
    ],
    "Java": [("Spring Boot", 0.95), ("MySQL", 0.7)],
    # 占位项会在后续过滤掉
    "JavaScript": [
        ("React", 0.9),
        ("Vue.js", 0.85),
        ("Angular", 0.75),
        ("Node.js后端工程师", 0.0),
    ],
    "TypeScript": [("React", 0.85), ("Vue.js", 0.8), ("Angular", 0.8), ("NestJS", 0.75)],
    "Go": [("Gin", 0.85), ("Beego", 0.7), ("Echo", 0.75)],
    "C#": [("ASP.NET Core", 0.9), ("SQL Server", 0.75)],
    "PHP": [("Laravel", 0.85), ("ThinkPHP", 0.75)],
    "Ruby": [("Ruby on Rails", 0.9)],
    "Swift": [("iOS开发工程师", 0.0)],  # 过滤
    "Kotlin": [("Android开发工程师", 0.0)],  # 过滤
    "SQL": [("MySQL", 0.8), ("PostgreSQL", 0.75)],
}

# 预定义相似关系：两两互为相似
SIMILARITY_PAIRS: list[tuple[str, str, float]] = [
    ("Vue.js", "React", 0.9),
    ("MySQL", "PostgreSQL", 0.85),
    ("Django", "Flask", 0.85),
    ("PyTorch", "TensorFlow", 0.9),
    ("Spring Boot", "Django", 0.75),
    ("Redis", "MongoDB", 0.7),
    ("Docker", "Kubernetes", 0.8),
    ("React", "Angular", 0.8),
    ("Pandas", "NumPy", 0.85),
    ("Git", "GitHub Actions", 0.75),
]


def _json_list(value: list[Any]) -> str:
    return json.dumps(value, ensure_ascii=False)


def _persist_skills(db: Session, skills: list[dict[str, Any]]) -> dict[str, Skill]:
    existing = {s.name: s for s in db.query(Skill).all()}
    skill_map = {}
    for item in skills:
        skill = existing.get(item["name"])
        if skill is None:
            skill = Skill(
                id=item["id"],
                name=item["name"],
                category=item["category"],
                aliases=_json_list(item.get("aliases", [])),
                definition=item["definition"],
            )
            db.add(skill)
        skill_map[item["name"]] = skill
    db.commit()
    for skill in skill_map.values():
        db.refresh(skill)
    logger.info("Persisted %s skills", len(skill_map))
    return skill_map


def _persist_companies(db: Session, companies: list[dict[str, Any]]) -> dict[int, Company]:
    existing = {c.id: c for c in db.query(Company).all()}
    company_map = {}
    for item in companies:
        company = existing.get(item["id"])
        if company is None:
            company = Company(
                id=item["id"],
                name=item["name"],
                industry=item["industry"],
                size=item["size"],
                city=item["city"],
            )
            db.add(company)
        company_map[item["id"]] = company
    db.commit()
    for company in company_map.values():
        db.refresh(company)
    logger.info("Persisted %s companies", len(company_map))
    return company_map


def _persist_jobs(db: Session, jobs: list[dict[str, Any]]) -> list[Job]:
    existing_ids = {j.id for j in db.query(Job.id).all()}
    persisted = []
    for item in jobs:
        if item["id"] in existing_ids:
            continue
        job = Job(
            id=item["id"],
            title=item["title"],
            company_id=item["company_id"],
            city=item["city"],
            salary_min=item["salary_min"],
            salary_max=item["salary_max"],
            experience_level=item["experience_level"],
            education_level=item["education_level"],
            required_skills=_json_list(item.get("required_skills", [])),
            description=item["description"],
        )
        db.add(job)
        persisted.append(job)
    db.commit()
    for job in persisted:
        db.refresh(job)
    logger.info("Persisted %s jobs", len(persisted))
    return persisted


def _build_skill_relations(
    db: Session,
    skill_map: dict[str, Skill],
    jobs: list[dict[str, Any]],
) -> int:
    """基于预定义规则与共现频率构建技能关系。"""
    relations: list[SkillRelation] = []
    relation_keys: set[tuple[int, int, str]] = set()

    def _add_relation(
        source_name: str, target_name: str, relation_type: str, weight: float
    ) -> None:
        source = skill_map.get(source_name)
        target = skill_map.get(target_name)
        if source is None or target is None:
            return
        if source.id == target.id:
            return
        key = (source.id, target.id, relation_type)
        if key in relation_keys:
            return
        relation_keys.add(key)
        relations.append(
            SkillRelation(
                source_skill_id=source.id,
                target_skill_id=target.id,
                relation_type=relation_type,
                weight=round(weight, 3),
            )
        )

    # 依赖关系
    for source_name, targets in DEPENDENCY_RULES.items():
        for target_name, weight in targets:
            _add_relation(source_name, target_name, "dependency", weight)

    # 相似关系（双向）
    for a, b, weight in SIMILARITY_PAIRS:
        _add_relation(a, b, "similarity", weight)
        _add_relation(b, a, "similarity", weight)

    # 共现关系：统计 JD 中同时出现的技能对
    pair_counter: Counter[tuple[str, str]] = Counter()
    for job in jobs:
        skills = job.get("required_skills", [])
        for i in range(len(skills)):
            for j in range(i + 1, len(skills)):
                a, b = skills[i], skills[j]
                if a not in skill_map or b not in skill_map:
                    continue
                pair = tuple(sorted([a, b]))
                pair_counter[pair] += 1

    max_count = max(pair_counter.values()) if pair_counter else 1
    for (a, b), count in pair_counter.items():
        weight = min(1.0, count / max_count)
        if weight < 0.05:
            continue
        _add_relation(a, b, "co_occurrence", weight)
        _add_relation(b, a, "co_occurrence", weight)

    # 去重写入（按 source/target/type）
    existing = {
        (r.source_skill_id, r.target_skill_id, r.relation_type)
        for r in db.query(SkillRelation).all()
    }
    new_relations = [
        r
        for r in relations
        if (r.source_skill_id, r.target_skill_id, r.relation_type) not in existing
    ]
    db.bulk_save_objects(new_relations)
    db.commit()
    logger.info("Persisted %s skill relations", len(new_relations))
    return len(new_relations)


def _seed_demo_profiles(db: Session, skill_map: dict[str, Skill]) -> list[UserSkillProfile]:
    """写入若干示例求职者画像。"""
    if db.query(UserSkillProfile).first():
        return []

    demo_profiles = [
        {
            "name": "求职者A-全栈方向",
            "skills": ["JavaScript", "TypeScript", "React", "Python", "MySQL", "Git", "Docker"],
            "experience_level": "3-5年",
            "target_job_titles": ["全栈工程师", "前端开发工程师", "Python后端工程师"],
        },
        {
            "name": "求职者B-算法方向",
            "skills": ["Python", "PyTorch", "Pandas", "NumPy", "机器学习", "自然语言处理"],
            "experience_level": "1-3年",
            "target_job_titles": ["算法工程师", "机器学习工程师", "NLP工程师"],
        },
        {
            "name": "求职者C-后端方向",
            "skills": ["Java", "Spring Boot", "MySQL", "Redis", "Kafka", "Docker"],
            "experience_level": "5-10年",
            "target_job_titles": ["Java后端工程师", "高级Java后端工程师", "Java架构师"],
        },
    ]

    profiles = []
    for item in demo_profiles:
        profile = UserSkillProfile(
            name=item["name"],
            skills=_json_list(item["skills"]),
            experience_level=item["experience_level"],
            target_job_titles=_json_list(item["target_job_titles"]),
        )
        db.add(profile)
        profiles.append(profile)
    db.commit()
    for profile in profiles:
        db.refresh(profile)
    logger.info("Persisted %s demo user profiles", len(profiles))
    return profiles


def _seed_demo_matches(
    db: Session,
    profiles: list[UserSkillProfile],
    jobs: list[Job],
    skill_map: dict[str, Skill],
) -> int:
    """为示例画像生成简单匹配结果。"""
    if db.query(MatchResult).first():
        return 0

    matches = []
    for profile in profiles:
        profile_skills = set(json.loads(profile.skills))
        candidate_jobs = [j for j in jobs if j.title in json.loads(profile.target_job_titles)]
        if not candidate_jobs:
            candidate_jobs = random.sample(jobs, min(5, len(jobs)))
        for job in candidate_jobs[:3]:
            required = set(json.loads(job.required_skills))
            matched = list(profile_skills & required)
            missing = list(required - profile_skills)
            # 可迁移技能：通过相似关系查找
            transferable: list[str] = []
            for miss in missing:
                miss_skill = skill_map.get(miss)
                if miss_skill is None:
                    continue
                similar = db.query(SkillRelation).filter_by(
                    source_skill_id=miss_skill.id,
                    relation_type="similarity",
                ).all()
                for rel in similar:
                    target = db.query(Skill).get(rel.target_skill_id)
                    if target and target.name in profile_skills:
                        transferable.append(f"{target.name}->{miss_skill.name}")
                        break
            score = len(matched) / max(len(required), 1)
            matches.append(
                MatchResult(
                    user_profile_id=profile.id,
                    job_id=job.id,
                    match_score=round(score, 3),
                    matched_skills=_json_list(matched),
                    missing_skills=_json_list(missing),
                    transferable_skills=_json_list(transferable),
                    analysis_summary=(
                        f"匹配度 {score:.1%}，掌握 {len(matched)} 项核心技能，"
                        f"缺失 {len(missing)} 项。"
                    ),
                )
            )

    db.bulk_save_objects(matches)
    db.commit()
    logger.info("Persisted %s demo match results", len(matches))
    return len(matches)


def _extract_companies_from_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """从真实 JD 中提取公司信息并按名称去重。"""
    companies_by_name: dict[str, dict[str, Any]] = {}
    for job in jobs:
        name = job.get("company_name") or "未命名公司"
        if name in companies_by_name:
            continue
        companies_by_name[name] = {
            "name": name,
            "industry": random.choice(INDUSTRIES),
            "size": random.choice(COMPANY_SIZES),
            "city": job.get("city") or random.choice(["北京", "上海", "深圳", "杭州"]),
        }
    return list(companies_by_name.values())


def _normalize_real_jobs(
    raw_jobs: list[dict[str, Any]],
    skills: list[dict[str, Any]],
    companies: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """将爬虫原始数据转换为与生成器一致的 job schema，并补全缺失字段。"""
    company_name_to_id = {c["name"]: c["id"] for c in companies if "id" in c}
    normalized = []
    for raw in raw_jobs:
        filled = infer_missing_fields(raw, skills)
        company_name = raw.get("company_name") or "未命名公司"
        company_id = company_name_to_id.get(company_name)
        if company_id is None:
            # 未命中说明该岗位公司名未在 companies 列表中，使用第一个公司兜底
            company_id = companies[0]["id"] if companies else 1
        normalized.append({
            "title": filled["title"],
            "company_id": company_id,
            "city": filled["city"],
            "salary_min": filled["salary_min"],
            "salary_max": filled["salary_max"],
            "experience_level": filled["experience_level"],
            "education_level": filled["education_level"],
            "required_skills": filled["required_skills"],
            "description": filled["description"],
            "source": raw.get("source", ""),
            "source_url": raw.get("source_url", ""),
        })
    return normalized


def seed_database(
    db: Session,
    n_skills: int = 80,
    n_companies: int = 40,
    n_jobs: int = 250,
    fetch_real: bool = True,
) -> dict[str, Any]:
    """生成新版结构化数据并持久化到数据库。

    当 fetch_real=True 时，优先加载/采集真实 JD；数量不足时使用生成器补充。
    """
    logger.info("Generating seed data for skill-map and talent-matching engine...")

    # 1. 技能词表仍然使用人工整理版本
    data = generate_all_data(n_skills=n_skills, n_companies=0, n_jobs=0)
    skills = data["skills"]
    skill_map = _persist_skills(db, skills)

    # 2. 获取真实 JD
    real_raw_jobs: list[dict[str, Any]] = []
    if fetch_real:
        try:
            real_raw_jobs = fetch_real_jobs(
                min_count=MIN_REAL_JOBS,
                target_total=TARGET_TOTAL_JOBS,
            )
            logger.info("获取到 %d 条真实 JD", len(real_raw_jobs))
        except Exception as exc:
            logger.warning("获取真实 JD 失败，将使用生成数据: %s", exc)

    # 3. 提取真实公司并补充到目标数量
    real_companies = _extract_companies_from_jobs(real_raw_jobs)
    fallback_company_count = max(0, n_companies - len(real_companies))
    if fallback_company_count > 0:
        fallback_companies = generate_companies(fallback_company_count)
        # 避免名称冲突
        existing_names = {c["name"] for c in real_companies}
        for c in fallback_companies:
            if c["name"] not in existing_names:
                real_companies.append(c)
                existing_names.add(c["name"])

    # 分配公司 ID
    for idx, company in enumerate(real_companies, start=1):
        company["id"] = idx

    # 4. 规范化真实 JD
    real_jobs = _normalize_real_jobs(real_raw_jobs, skills, real_companies)

    # 5. 若真实 JD 不足，用生成器补充
    fallback_job_count = max(0, n_jobs - len(real_jobs))
    if fallback_job_count > 0:
        company_map_for_gen = {c["id"]: c for c in real_companies}
        fallback_jobs = generate_jobs(
            companies=list(company_map_for_gen.values()),
            skills=skills,
            n=fallback_job_count,
        )
        # generate_jobs 自带 id，需要重新编号以接在真实 JD 之后
        real_jobs.extend(fallback_jobs)

    # 统一分配 job ID（从 1 开始）
    for idx, job in enumerate(real_jobs, start=1):
        job["id"] = idx

    # 持久化公司与岗位
    _persist_companies(db, real_companies)
    jobs = _persist_jobs(db, real_jobs)
    relation_count = _build_skill_relations(db, skill_map, real_jobs)
    profiles = _seed_demo_profiles(db, skill_map)
    match_count = _seed_demo_matches(db, profiles, jobs, skill_map)

    logger.info(
        "Seeded %s skills, %s companies, %s jobs (real=%s, fallback=%s), "
        "%s relations, %s profiles, %s matches",
        len(skill_map),
        len(real_companies),
        len(jobs),
        len(real_raw_jobs),
        len(real_jobs) - len(real_raw_jobs),
        relation_count,
        len(profiles),
        match_count,
    )
    return {
        "skills": len(skill_map),
        "companies": len(real_companies),
        "jobs": len(jobs),
        "real_jobs": len(real_raw_jobs),
        "fallback_jobs": len(real_jobs) - len(real_raw_jobs),
        "relations": relation_count,
        "profiles": len(profiles),
        "matches": match_count,
    }
