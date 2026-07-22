"""最小测试脚本：验证新 Agent 与工作流在降级模式下可运行。"""

import os
import sys
from pathlib import Path

# 确保从 backend 根目录导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("OPENAI_API_KEY", "")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agents import (
    JDParser,
    TalentMatcher,
    build_job_match_graph,
    run_job_match_sync,
)
from app.data.seed import seed_database
from app.models.base import Base, SessionLocal
from app.models.job import Job


def main():
    # 使用内存 SQLite 避免污染项目数据库
    db_url = "sqlite:///:memory:"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    try:
        # 1. 准备测试数据
        print("[1/4] Seeding test data...")
        seed_database(session, n_skills=80, n_companies=5, n_jobs=20)

        # 2. 测试 JDParser.parse_jd
        print("[2/4] Testing JDParser.parse_jd()...")
        sample_jd = """
        招聘：Python后端工程师
        公司：示例科技

        岗位职责：
        1. 使用 Python、FastAPI 开发后端服务；
        2. 熟悉 PostgreSQL、Redis；
        3. 具备 Docker、Kubernetes 使用经验。

        任职要求：
        1. 本科及以上学历，3-5年相关经验；
        2. 熟悉 Linux，具备良好的沟通能力和团队协作精神。
        """
        parser = JDParser()
        parsed = parser.parse_jd(sample_jd)
        print(f"  Parsed title: {parsed.get('title')}")
        print(f"  Required skills: {parsed.get('required_skills')}")
        print(f"  Experience level: {parsed.get('experience_level')}")
        print(f"  Education level: {parsed.get('education_level')}")
        assert parsed.get("title"), "JDParser should extract title"
        assert "Python" in parsed.get("required_skills", []), "JDParser should extract Python"

        # 3. 测试 TalentMatcher.match
        print("[3/4] Testing TalentMatcher.match()...")
        job = session.query(Job).filter(Job.title == "Python后端工程师").first()
        if job is None:
            job = session.query(Job).first()
        profile_skills = ["Python", "Django", "PostgreSQL", "Docker", "Linux"]
        matcher = TalentMatcher()
        match_result = matcher.match(profile_skills, job, session)
        print(f"  Job title: {job.title}")
        print(f"  Match score: {match_result.get('match_score')}")
        print(f"  Matched skills: {match_result.get('matched_skills')}")
        print(f"  Missing skills: {match_result.get('missing_skills')}")
        print(f"  Transferable skills: {match_result.get('transferable_skills')}")
        assert 0 <= match_result.get("match_score", 0) <= 1, "Match score should be in [0,1]"

        # 4. 测试工作流编译与降级运行
        print("[4/4] Testing build_job_match_graph() and workflow fallback...")
        graph = build_job_match_graph(session)
        assert graph is not None, "Graph should compile"

        state = {
            "input_text": sample_jd,
            "profile": {"skills": profile_skills, "experience_level": "3-5年"},
            "target_job": job,
            "job_data": [
                {
                    "title": j.title,
                    "required_skills": j.required_skills,
                    "salary_min": j.salary_min,
                    "salary_max": j.salary_max,
                }
                for j in session.query(Job).all()
            ],
        }
        final_state = run_job_match_sync(session, state)
        print(f"  Parsed JD title: {final_state.get('parsed_jd', {}).get('title')}")
        print(f"  Match score: {final_state.get('match_result', {}).get('match_score')}")
        print(f"  Trend summary: {final_state.get('trend_analysis', {}).get('summary', '')[:60]}...")
        print(f"  Learning path length: {len(final_state.get('learning_path', []))}")
        print(f"  Advice length: {len(final_state.get('advice', ''))}")
        assert final_state.get("parsed_jd"), "Workflow should produce parsed_jd"
        assert final_state.get("match_result"), "Workflow should produce match_result"
        assert final_state.get("advice"), "Workflow should produce advice"

        print("\nAll tests passed!")
    finally:
        session.close()


if __name__ == "__main__":
    main()
