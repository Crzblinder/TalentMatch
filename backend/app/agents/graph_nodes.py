"""LangGraph node functions for the job skill-map and talent-matching workflow."""

from __future__ import annotations

import logging
import time
from typing import Any

from langchain_core.runnables import RunnableConfig
from sqlalchemy.orm import Session

from app.agents.jd_parser import JDParser
from app.agents.learning_planner import LearningPlanner
from app.agents.obstacle_detector import ObstacleDetector
from app.agents.resume_parser import ResumeParser
from app.agents.search_agent import SearchAgent
from app.agents.skill_advisor import SkillAdvisor
from app.agents.talent_matcher import TalentMatcher
from app.agents.trend_predictor import TrendPredictor

from .graph_state import JobMatchState

logger = logging.getLogger(__name__)


def _get_session(config: RunnableConfig) -> Session | None:
    """从 RunnableConfig 的可配置项中获取数据库 session。"""
    configurable = config.get("configurable") if config else None
    session = configurable.get("session") if configurable else None
    return session


def _append_event(
    state: JobMatchState,
    node: str,
    status: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """构造 SSE 风格的流式事件。"""
    event = {
        "node": node,
        "status": status,
        "timestamp_ms": int(time.time() * 1000),
    }
    if payload:
        event["payload"] = payload
    return event


def parse_jd_node(state: JobMatchState, config: RunnableConfig) -> dict[str, Any]:
    """解析 JD 文本节点。"""
    start = time.time()
    input_text = state.get("input_text", "")
    agent = JDParser()
    parsed = agent.parse_jd(input_text)

    return {
        "parsed_jd": parsed,
        "stream_events": [
            _append_event(state, "jd_parser", "completed", {"title": parsed.get("title")})
        ],
        "response_time_ms": int((time.time() - start) * 1000),
    }


def match_talent_node(state: JobMatchState, config: RunnableConfig) -> dict[str, Any]:
    """人才匹配节点。"""
    start = time.time()
    session = _get_session(config)
    profile = state.get("profile") or {}
    target_job = state.get("target_job")

    if session is None:
        raise ValueError(
            "match_talent_node requires a database session in config.configurable.session"
        )
    if target_job is None:
        raise ValueError("match_talent_node requires 'target_job' in state")

    # 将完整画像上下文传给匹配器，使其能综合经验与学历进行评分
    agent = TalentMatcher()
    match_result = agent.match(profile, target_job, session)

    return {
        "match_result": match_result,
        "stream_events": [
            _append_event(
                state,
                "talent_matcher",
                "completed",
                {"match_score": match_result.get("match_score")},
            )
        ],
        "response_time_ms": int((time.time() - start) * 1000),
    }


def predict_trend_node(state: JobMatchState, config: RunnableConfig) -> dict[str, Any]:
    """趋势预测节点。"""
    start = time.time()
    job_data = state.get("job_data") or []
    agent = TrendPredictor()
    trend = agent.predict(job_data)

    return {
        "trend_analysis": trend,
        "stream_events": [
            _append_event(
                state,
                "trend_predictor",
                "completed",
                {"job_count": trend.get("key_metrics", {}).get("job_count")},
            )
        ],
        "response_time_ms": int((time.time() - start) * 1000),
    }


def plan_learning_node(state: JobMatchState, config: RunnableConfig) -> dict[str, Any]:
    """学习路径规划节点。"""
    start = time.time()
    session = _get_session(config)
    if session is None:
        raise ValueError(
            "plan_learning_node requires a database session in config.configurable.session"
        )

    profile = state.get("profile") or {}
    current_skills = profile.get("skills") or []
    match_result = state.get("match_result") or {}
    missing_skills = match_result.get("missing_skills") or []

    agent = LearningPlanner()
    plan = agent.plan(missing_skills, current_skills, session)

    return {
        "learning_path": plan,
        "stream_events": [
            _append_event(
                state,
                "learning_planner",
                "completed",
                {"path_length": len(plan)},
            )
        ],
        "response_time_ms": int((time.time() - start) * 1000),
    }


def advise_skill_node(state: JobMatchState, config: RunnableConfig) -> dict[str, Any]:
    """综合建议节点。"""
    start = time.time()
    profile = state.get("profile") or {}
    target_job = state.get("target_job")
    match_result = state.get("match_result") or {}

    agent = SkillAdvisor()
    advice_result = agent.run(
        {"profile": profile, "job": target_job, "match_result": match_result}
    )

    return {
        "advice": advice_result.get("advice", ""),
        "stream_events": [
            _append_event(
                state,
                "skill_advisor",
                "completed",
                {"advice_length": len(advice_result.get("advice", ""))},
            )
        ],
        "response_time_ms": int((time.time() - start) * 1000),
    }


def parse_resume_node(state: JobMatchState, config: RunnableConfig) -> dict[str, Any]:
    """简历解析节点（支持模糊识别）。"""
    start = time.time()
    profile = state.get("profile") or {}
    raw_resume = profile.get("raw_resume", "")
    if not raw_resume:
        # 如果没有原始简历文本，跳过该节点
        return {
            "parsed_resume": profile,
            "stream_events": [
                _append_event(state, "resume_parser", "skipped", {"reason": "no_raw_resume"})
            ],
            "response_time_ms": int((time.time() - start) * 1000),
        }

    fuzzy = state.get("fuzzy", False)
    agent = ResumeParser(prompt_variant="fresh_graduate" if fuzzy else "default")
    parsed = agent.parse_resume(raw_resume)

    return {
        "parsed_resume": parsed,
        "stream_events": [
            _append_event(
                state,
                "resume_parser",
                "completed",
                {"name": parsed.get("basic_info", {}).get("name")},
            )
        ],
        "response_time_ms": int((time.time() - start) * 1000),
    }


def search_node(state: JobMatchState, config: RunnableConfig) -> dict[str, Any]:
    """联网搜索节点：根据 JD/画像自动搜索求职情报。"""
    start = time.time()
    if not state.get("enable_search", False):
        return {
            "search_results": [],
            "stream_events": [
                _append_event(state, "search_agent", "skipped", {"reason": "disabled"})
            ],
            "response_time_ms": int((time.time() - start) * 1000),
        }

    agent = SearchAgent()
    queries: list[dict[str, Any]] = []

    parsed_jd = state.get("parsed_jd") or {}
    if parsed_jd.get("title"):
        queries.append({
            "query": f"{parsed_jd['title']} 面经 面试经验",
            "intent": "interview",
            "location": parsed_jd.get("location", ""),
        })
        queries.append({
            "query": f"{parsed_jd['title']} 薪资待遇",
            "intent": "salary",
            "location": parsed_jd.get("location", ""),
        })

    profile = state.get("profile") or {}
    target_titles = profile.get("target_job_titles") or []
    if target_titles:
        queries.append({
            "query": f"{target_titles[0]} 校招 应届生",
            "intent": "fresh_graduate",
        })

    results: list[dict[str, Any]] = []
    for q in queries[:3]:
        try:
            search_result = agent.search(
                query=q["query"],
                intent=q["intent"],
                location=q.get("location") or None,
                top_n=3,
                summarize=True,
            )
            results.append(search_result)
        except Exception as exc:
            logger.warning("搜索失败: %s", exc)

    return {
        "search_results": results,
        "stream_events": [
            _append_event(
                state,
                "search_agent",
                "completed",
                {"result_count": len(results)},
            )
        ],
        "response_time_ms": int((time.time() - start) * 1000),
    }


def detect_obstacles_node(state: JobMatchState, config: RunnableConfig) -> dict[str, Any]:
    """求职困境识别节点。"""
    start = time.time()
    profile = state.get("profile") or {}
    parsed_resume = state.get("parsed_resume") or profile
    parsed_jd = state.get("parsed_jd") or {}

    agent = ObstacleDetector()
    obstacles = agent.detect(resume=parsed_resume, jd=parsed_jd)

    return {
        "obstacles": obstacles,
        "stream_events": [
            _append_event(
                state,
                "obstacle_detector",
                "completed",
                {"obstacle_count": len(obstacles.get("obstacles", []))},
            )
        ],
        "response_time_ms": int((time.time() - start) * 1000),
    }
