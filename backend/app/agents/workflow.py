"""LangGraph workflow for the job skill-map and talent-matching engine."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.agents.graph_nodes import (
    advise_skill_node,
    detect_obstacles_node,
    match_talent_node,
    parse_jd_node,
    parse_resume_node,
    plan_learning_node,
    predict_trend_node,
    search_node,
)
from app.agents.graph_state import JobMatchState

logger = logging.getLogger(__name__)


def build_job_match_graph(session: Session) -> StateGraph:
    """构建岗位技能图谱与人才匹配工作流图。

    节点顺序：
      parse_jd → parse_resume（可选） → match → predict → plan → advise
      并在 parse_jd 后并行触发 search 与 obstacle_detection
    """
    builder = StateGraph(JobMatchState)

    builder.add_node("parse_jd", parse_jd_node)
    builder.add_node("parse_resume", parse_resume_node)
    builder.add_node("match", match_talent_node)
    builder.add_node("predict", predict_trend_node)
    builder.add_node("plan", plan_learning_node)
    builder.add_node("advise", advise_skill_node)
    builder.add_node("search", search_node)
    builder.add_node("obstacles", detect_obstacles_node)

    builder.add_edge(START, "parse_jd")
    builder.add_edge("parse_jd", "parse_resume")
    builder.add_edge("parse_resume", "match")
    builder.add_edge("match", "predict")
    builder.add_edge("predict", "plan")
    builder.add_edge("plan", "advise")
    builder.add_edge("advise", END)

    # parse_jd 后并行执行搜索与困境识别
    builder.add_edge("parse_jd", "search")
    builder.add_edge("parse_jd", "obstacles")
    builder.add_edge("search", "advise")
    builder.add_edge("obstacles", "advise")

    # 通过 configurable 传递数据库 session
    return builder.compile()


async def run_job_match_stream(
    session: Session,
    state: JobMatchState,
) -> AsyncIterator[dict[str, Any]]:
    """以 SSE 兼容格式流式执行工作流。

    每次 yield 一个事件对象，包含 node/status/payload 等字段。
    """
    graph = build_job_match_graph(session)
    config = {"configurable": {"session": session}}

    async for event in graph.astream_events(state, config=config, version="v2"):
        # 过滤节点完成事件
        if event.get("event") in ("on_chain_end",) and event.get("name") in (
            "parse_jd",
            "parse_resume",
            "match",
            "predict",
            "plan",
            "advise",
            "search",
            "obstacles",
        ):
            payload = {}
            data = event.get("data", {})
            output = data.get("output", {})
            if output.get("stream_events"):
                for stream_event in output["stream_events"]:
                    yield stream_event
            else:
                yield {
                    "node": event["name"],
                    "status": "completed",
                    "payload": payload,
                }


def run_job_match_sync(
    session: Session,
    state: JobMatchState,
) -> dict[str, Any]:
    """同步执行完整工作流并返回最终状态。"""
    graph = build_job_match_graph(session)
    config = {"configurable": {"session": session}}
    final_state = graph.invoke(state, config=config)
    return final_state
