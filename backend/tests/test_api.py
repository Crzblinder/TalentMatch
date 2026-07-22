"""新版岗位技能图谱与人才匹配 API 测试。"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["OPENAI_API_KEY"] = ""
os.environ["DATABASE_URL"] = "sqlite:///./test_jobs.db"
os.environ["VECTOR_DB_PATH"] = "./test_jobs_chroma"

from app.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.main import app  # noqa: E402
from app.models import Company, Job, Skill, UserSkillProfile  # noqa: E402
from app.models.base import Base, get_db  # noqa: E402

# 清理测试产物
for p in [Path("./test_jobs.db"), Path("./test_jobs_chroma")]:
    if p.exists():
        if p.is_file():
            p.unlink()
        else:
            shutil.rmtree(p, ignore_errors=True)

engine = create_engine(
    os.environ["DATABASE_URL"], connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def _seed_data():
    db = TestingSessionLocal()
    try:
        company = Company(
            name="示例科技",
            industry="互联网",
            size="100-499人",
            city="北京",
        )
        db.add(company)
        db.flush()

        skill = Skill(
            name="Python",
            category="编程语言",
            aliases=json.dumps(["python", "py"], ensure_ascii=False),
            definition="Python 是一门通用编程语言。",
        )
        db.add(skill)
        db.flush()

        job = Job(
            title="Python 后端工程师",
            company_id=company.id,
            city="北京",
            salary_min=20000,
            salary_max=35000,
            experience_level="3-5年",
            education_level="本科",
            required_skills=json.dumps(
                ["Python", "FastAPI", "PostgreSQL"], ensure_ascii=False
            ),
            description="负责后端服务开发，要求熟悉 Python、FastAPI 和 PostgreSQL。",
        )
        db.add(job)

        profile = UserSkillProfile(
            name="测试候选人",
            skills=json.dumps(["Python", "FastAPI"], ensure_ascii=False),
            experience_level="3-5年",
            target_job_titles=json.dumps(["Python 后端工程师"], ensure_ascii=False),
        )
        db.add(profile)

        db.commit()
    finally:
        db.close()


_seed_data()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_jobs_health():
    response = client.get("/api/v1/jobs/health")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["status"] == "ok"


def test_list_jobs():
    response = client.get("/api/v1/jobs?page=1&size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["total"] >= 1
    assert len(data["data"]["items"]) >= 1
    assert data["data"]["items"][0]["title"]


def test_get_job():
    response = client.get("/api/v1/jobs/1")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["id"] == 1


def test_list_skills():
    response = client.get("/api/v1/skills")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["total"] >= 1


def test_parse_jd():
    jd_text = (
        "某科技公司招聘 Python 后端工程师\n"
        "岗位职责：负责后端服务开发。\n"
        "岗位要求：熟悉 Python、FastAPI、PostgreSQL，3-5 年经验，本科及以上学历。"
    )
    response = client.post("/api/v1/jobs/parse", json={"jd_text": jd_text})
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["title"]
    assert "Python" in data["data"]["required_skills"]


def test_create_match():
    response = client.post("/api/v1/matches", json={"profile_id": 1, "job_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "match_score" in data["data"]
    assert data["data"]["user_profile_id"] == 1
    assert data["data"]["job_id"] == 1


def test_generate_learning_path():
    response = client.post(
        "/api/v1/matches/learning-path", json={"profile_id": 1, "job_id": 1}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "learning_path" in data["data"]


def test_match_stream():
    response = client.post(
        "/api/v1/matches/stream",
        json={"profile_id": 1, "job_id": 1},
    )
    assert response.status_code == 200
    events = []
    for line in response.iter_lines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    assert len(events) >= 1
    assert events[0]["node"] in (
        "jd_parser",
        "talent_matcher",
        "trend_predictor",
        "learning_planner",
        "skill_advisor",
    )
