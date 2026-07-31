"""新版 Agent 单元测试：覆盖岗位技能图谱与人才匹配引擎的 5 个核心 Agent。

测试默认在无 LLM Key 的环境下运行，依赖内置的确定性降级规则引擎。
"""
# ruff: noqa: E402

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["OPENAI_API_KEY"] = ""
os.environ["DATABASE_URL"] = "sqlite:///./test_agents.db"
os.environ["VECTOR_DB_PATH"] = "./test_agents_chroma"

from app.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.agents.jd_parser import JDParser
from app.agents.learning_planner import LearningPlanner
from app.agents.skill_advisor import SkillAdvisor
from app.agents.talent_matcher import TalentMatcher
from app.agents.trend_predictor import TrendPredictor
from app.agents.workflow import build_job_match_graph
from app.models import Company, Job
from app.models.base import Base
from app.services.resume_service import should_use_fuzzy_parsing

# 清理测试产物
for p in [Path("./test_agents.db"), Path("./test_agents_chroma")]:
    if p.exists():
        if p.is_file():
            p.unlink()
        else:
            import shutil

            shutil.rmtree(p, ignore_errors=True)

engine = create_engine(
    os.environ["DATABASE_URL"], connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="module")
def db_session():
    """提供绑定到测试数据库的 Session。"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _make_job(session, title: str, required_skills: list[str], description: str = "") -> Job:
    """构造一个测试岗位并持久化。"""
    company = session.query(Company).filter_by(name="示例科技").first()
    if company is None:
        company = Company(
            name="示例科技",
            industry="互联网",
            size="100-499人",
            city="北京",
        )
        session.add(company)
        session.flush()

    job = Job(
        title=title,
        company_id=company.id,
        city="北京",
        salary_min=20000,
        salary_max=35000,
        experience_level="3-5年",
        education_level="本科",
        required_skills=json.dumps(required_skills, ensure_ascii=False),
        description=description or f"招聘 {title}，要求掌握 {', '.join(required_skills)}。",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def test_jd_parser():
    agent = JDParser()
    jd_text = (
        "某科技公司招聘 Python 后端工程师\n"
        "岗位职责：负责后端服务开发。\n"
        "岗位要求：熟悉 Python、FastAPI、PostgreSQL，3-5 年经验，本科及以上学历。"
    )
    result = agent.parse_jd(jd_text)

    assert result["title"]
    assert "Python" in result["required_skills"]
    assert result["experience_level"] in ("3-5年", "不限")
    assert result["education_level"] in ("本科", "本科及以上", "不限")


def test_talent_matcher(db_session):
    job = _make_job(
        db_session,
        title="Python 后端工程师",
        required_skills=["Python", "FastAPI", "PostgreSQL"],
    )
    agent = TalentMatcher()
    result = agent.match(["Python", "FastAPI"], job, db_session)

    assert 0.0 <= result["match_score"] <= 1.0
    assert "Python" in result["matched_skills"]
    assert "FastAPI" in result["matched_skills"]
    assert "PostgreSQL" in result["missing_skills"]
    assert isinstance(result["analysis_summary"], str)


def test_trend_predictor():
    agent = TrendPredictor()
    job_data = [
        {
            "title": "Python 后端工程师",
            "city": "北京",
            "salary_min": 20000,
            "salary_max": 35000,
            "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        },
        {
            "title": "Java 后端工程师",
            "city": "上海",
            "salary_min": 22000,
            "salary_max": 38000,
            "required_skills": ["Java", "Spring Boot", "MySQL"],
        },
    ]
    result = agent.predict(job_data)

    assert "summary" in result
    assert result["key_metrics"]["job_count"] == 2
    assert isinstance(result["top_skills"], list)
    assert isinstance(result["hot_job_titles"], list)


def test_learning_planner(db_session):
    agent = LearningPlanner()
    plan = agent.plan(
        missing_skills=["PostgreSQL", "Docker"],
        current_skills=["Python", "FastAPI"],
        session=db_session,
    )

    assert isinstance(plan, list)
    assert len(plan) == 2
    skills = {item["skill"] for item in plan}
    assert {"PostgreSQL", "Docker"}.issubset(skills)
    for item in plan:
        assert item["difficulty"] in ("入门", "进阶", "高级")
        assert item["estimated_weeks"] > 0
        assert isinstance(item["prerequisites"], list)


def test_skill_advisor(db_session):
    job = _make_job(
        db_session,
        title="Python 后端工程师",
        required_skills=["Python", "FastAPI", "PostgreSQL"],
    )
    agent = SkillAdvisor()
    profile = {"skills": ["Python", "FastAPI"]}
    match_result = {
        "match_score": 0.66,
        "matched_skills": ["Python", "FastAPI"],
        "missing_skills": ["PostgreSQL"],
        "transferable_skills": [],
    }
    advice = agent.advise(profile, job, match_result)

    assert isinstance(advice, str)
    assert len(advice) > 0
    assert "匹配度" in advice


def test_langgraph_workflow_compiles_and_runs(db_session):
    job = _make_job(
        db_session,
        title="Python 后端工程师",
        required_skills=["Python", "FastAPI", "PostgreSQL"],
    )
    graph = build_job_match_graph(db_session)
    assert graph is not None

    state = {
        "input_text": job.description,
        "profile": {"skills": ["Python", "FastAPI"]},
        "target_job": job,
        "job_data": [
            {
                "title": job.title,
                "city": job.city,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "required_skills": ["Python", "FastAPI", "PostgreSQL"],
            }
        ],
    }
    config = {"configurable": {"session": db_session}}
    final_state = graph.invoke(state, config=config)

    assert final_state["parsed_jd"] is not None
    assert final_state["match_result"] is not None
    assert final_state["trend_analysis"] is not None
    assert isinstance(final_state["learning_path"], list)
    assert final_state["advice"]


def test_should_use_fuzzy_parsing_for_short_resume():
    """短文本简历应触发模糊解析。"""
    text = "张三，计算机专业在校生，有课程设计和项目经验。"
    assert should_use_fuzzy_parsing(text, "resume") is True


def test_should_use_fuzzy_parsing_for_fresh_graduate_resume():
    """包含应届生关键词的简历应触发模糊解析。"""
    text = (
        "李四，2024届毕业生，曾在某互联网公司实习三个月，"
        "参与多个项目开发，熟悉 Python 和 FastAPI。"
    )
    assert should_use_fuzzy_parsing(text, "resume") is True


def test_should_use_fuzzy_parsing_for_standard_resume():
    """标准社招简历不应触发模糊解析。"""
    text = (
        "王五，资深 Java 后端开发工程师，拥有八年互联网后端架构与团队管理经验，"
        "熟悉高并发、高可用分布式系统设计，具备大型复杂业务系统从 0 到 1 的落地能力。"
        "擅长技术方案评审、性能调优、系统稳定性建设，对电商、金融、供应链等业务领域有深入理解。\n"
        "工作经历\n"
        "2020-至今 某头部科技公司，资深后端工程师/架构师\n"
        "负责公司核心交易平台的整体技术架构设计与演进，主导完成订单、支付、结算等关键域的"
        "微服务化改造；设计并实现日均亿级流量的网关接入层，QPS 峰值提升至 50k；"
        "带领 15 人后端团队建立代码规范、CI/CD 流程及线上故障应急响应机制；"
        "推动单元测试覆盖率从 45% 提升至 85%，核心接口可用性达到 99.99%。\n"
        "2017-2020 某知名互联网公司，高级 Java 开发工程师\n"
        "参与电商中台建设，负责商品中心、库存中心、价格中心的核心模块开发，"
        "主导缓存与数据库一致性方案设计，将核心接口平均耗时从 300ms 降低至 80ms；"
        "推动团队完成从 Spring MVC 到 Spring Cloud 的技术栈升级，"
        "建设统一的监控告警体系，线上问题平均发现时间缩短 60%。\n"
        "2014-2017 某初创公司，Java 开发工程师\n"
        "负责 B2B 供应链系统的后端开发，参与需求分析、数据库设计、接口开发及上线运维，"
        "积累了完整的业务交付经验；独立负责多个核心模块的性能优化与重构工作，"
        "支撑公司业务从日均千单增长至日均十万单。\n"
        "工作业绩：主导搭建公司级服务治理平台，实现服务注册发现、限流降级、灰度发布能力；"
        "推动日志链路追踪体系落地，排查效率提升三倍以上；设计并实施数据库读写分离与分库分表方案，"
        "支撑核心表数据量从百万级增长至十亿级；组织技术分享与代码评审，培养多名高级开发工程师。\n"
        "技能：Java、Spring Boot、Spring Cloud、MySQL、Redis、Kafka、RocketMQ、"
        "Elasticsearch、Docker、Kubernetes、Prometheus、Grafana、DDD、分库分表、分布式事务。\n"
        "教育经历：2010-2014 某重点大学 计算机科学与技术 本科。"
        "自我评价：具有较强的业务抽象与技术落地能力，善于在复杂场景下做出平衡可扩展性与交付效率的架构决策，"
        "能够独立带领团队完成大型系统的规划、实施与持续优化，对工程质量与线上稳定性有极高要求。"
    )
    assert should_use_fuzzy_parsing(text, "resume") is False


def test_should_use_fuzzy_parsing_for_campus_jd():
    """校招/应届生 JD 应触发模糊解析。"""
    text = "某科技公司招聘应届生，接受零基础，经验不限，优秀毕业生优先。"
    assert should_use_fuzzy_parsing(text, "jd") is True


def test_should_use_fuzzy_parsing_for_intern_jd():
    """实习生 JD 应触发模糊解析。"""
    text = (
        "招聘算法实习生，面向在校学生，无经验亦可，"
        "计算机相关专业优先。"
    )
    assert should_use_fuzzy_parsing(text, "jd") is True


def test_should_use_fuzzy_parsing_for_standard_jd():
    """标准社招 JD 不应触发模糊解析。"""
    text = (
        "某科技公司招聘 Python 后端工程师。\n"
        "岗位职责：负责后端服务开发。\n"
        "岗位要求：熟悉 Python、FastAPI、PostgreSQL，3-5 年经验，本科及以上学历。"
    )
    assert should_use_fuzzy_parsing(text, "jd") is False
